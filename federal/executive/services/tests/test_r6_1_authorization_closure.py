"""
اختبارات R6.1 — إغلاق ثغرات جذر التخويل المتبقّية
الهدف: التحقّق أن مسار الدور المُدّعى لم يبقَ بابًا، وأن المستأجر صار حدًّا مفروضًا
النطاق: federal/executive/services
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R6.1)

R6 أثبتت أن الدور يُشتَقّ من هوية مُتحقَّق منها. لكنها أبقت `role=` معاملًا في
دالّة الإنتاج، فبقي للثقة مسارَان؛ وأبقت جدول الجلسات بلا `tenant_id`، فبقي
المستأجر حقلًا يقوله المُستدعي عن نفسه. هذه الاختبارات تحرس إغلاق البابين.

**ما يُفحَص هنا سلوكٌ وتوقيعُ مصدر، لا نظام كامل.** لا تُشغَّل خدمات ولا شبكة.
"""

from __future__ import annotations

import contextlib
import inspect
import re
import warnings
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from amos_federation.common.principal import (
    DEFAULT_TENANT,
    FEDERAL_TENANT,
    TENANCY_MODE,
    TENANCY_MODES,
    AuthorizationContext,
    Principal,
    PrincipalUnverifiedError,
    PrincipalVerification,
    SessionInvalidError,
    TenantIsolationError,
    assert_tenant,
    tenant_matches,
    unverified_context,
)
from amos_federation.services.tool_registry import authorized_execution, sandbox
from amos_federation.services.tool_registry.authorized_execution import (
    AUTHORIZATION_CHAIN,
    AuthorizationDenied,
    authorize,
)
from amos_federation.services.tool_registry.deprecated_role_path import (
    DEPRECATED_MARKER,
    DeprecatedRolePathUnavailableError,
    execute_tool_with_declared_role,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "amos_federation"


def _strip_comments(source: str) -> str:
    """أزِل التعليقات وسلاسل التوثيق قبل أي تأكيد على المصدر.

    الدرس مأخوذ من R6: حرسٌ يبحث عن نصٍّ في المصدر يمرّ أو يفشل بسبب **تعليق**
    يشرح الثغرة لا بسبب شيفرة تفتحها. فالتعليق يُطرح أوّلًا.
    """
    no_docstrings = re.sub(r'"""(?:.|\n)*?"""', "", source)
    return "\n".join(line.split("#", 1)[0] for line in no_docstrings.splitlines())


def _session_context(
    role_id: str,
    *,
    username: str = "r61-user",
    tenant_id: str | None = None,
    expires_at: datetime | None = None,
) -> AuthorizationContext:
    """سياق `SESSION_VERIFIED` كما يبنيه حلّ الجلسة — بلا لمس قاعدة بيانات."""
    return AuthorizationContext.from_principal(
        Principal.from_session_record(
            session_id=f"r61-{role_id}-{username}",
            username=username,
            role_id=role_id,
            permissions=("execute:tools", "tool:use"),
            expires_at=expires_at,
            tenant_id=tenant_id,
        )
    )


# ── 1. مسار الدور القديم مرفوض ────────────────────────────────────────────


def test_01_legacy_role_argument_no_longer_exists() -> None:
    """`execute_tool_with_governance` لم يبقَ فيها معامل دور، و`principal` لازم.

    هذا أهمّ تأكيد في R6.1، ولذلك يُفحَص على **التوقيع** لا على السلوك: السلوك
    يمكن أن يُرمَّم بفحص داخلي يُنسى، أمّا غياب المعامل فيمنع النداء من أن يُكتَب.
    """
    signature = inspect.signature(sandbox.execute_tool_with_governance)
    assert "role" not in signature.parameters, "معامل الدور المُدّعى ما زال في دالّة الإنتاج"

    principal_param = signature.parameters["principal"]
    assert principal_param.kind is inspect.Parameter.KEYWORD_ONLY
    assert principal_param.default is inspect.Parameter.empty, "المبدأ اختياري — أي أن الغياب مسموح"

    # ونداء بلا مبدأ يفشل عند الحدّ نفسه، لا بعد أن يبدأ العمل.
    with pytest.raises(TypeError):
        sandbox.execute_tool_with_governance("python_execute", {"code": "print(1)"})  # type: ignore[call-arg]

    # وكذلك `authorize` لا تقبل دورًا ولا صلاحيات ولا مستأجرًا من المُستدعي.
    authorize_params = set(inspect.signature(authorize).parameters)
    assert not (authorize_params & {"role", "permissions", "tenant_id", "actor_role"})


def test_02_declared_role_is_never_trusted() -> None:
    """الدور المُدّعى عبر المُهاجر المُهمَل لا يُخوَّل ولا يُترجَم إلى مدير."""
    for claimed in ("king", "royal", "royal_guard", "official"):
        with pytest.warns(DeprecationWarning, match=DEPRECATED_MARKER):
            result = execute_tool_with_declared_role(
                "python_execute", {"code": "print(1)"}, claimed, reason="اختبار R6.1"
            )
        assert result["principal_verification"] == "UNVERIFIED"
        assert result.get("error") == "policy_denied", f"ادّعاء '{claimed}' نفّذ أداة خطيرة"

    claimed_context = unverified_context("اختبار", claimed_role="king")
    assert not claimed_context.is_trusted
    with pytest.raises(PrincipalUnverifiedError):
        claimed_context.assert_authorizable()


def test_02b_literal_policy_admin_string_still_passes_the_deprecated_path() -> None:
    """حقيقة تُقال لا تُخفى: ادّعاء `admin` نصًّا **ينفّذ** عبر المسار المُهمَل.

    مفردتا الأدوار مختلفتان: سجلّ الأدوار يقول `king/royal/official/...` ومحرِّك
    السياسة يقول `admin`. والترجمة بينهما محصورة بالسياق الموثوق، فادّعاء `king`
    يبقى `king` ويُرفَض. لكن من يقول `admin` **مباشرةً** يخاطب محرِّك السياسة
    بمفردته، فلا يحتاج ترجمةً ويمرّ.

    ولذلك لم يُكتفَ في R6.1 بوسم الإهمال: المُهاجر **معدوم في الإنتاج**، وهذا
    الاختبار يوثّق سبب ذلك بدل أن يزعم رفضًا لا يقع. وسدُّه سدًّا كاملًا يلزمه
    توحيد مفردتَي الأدوار — دَينٌ مُعلَن في وثيقة R6 لم تفتحه R6.1.
    """
    with pytest.warns(DeprecationWarning):
        result = execute_tool_with_declared_role(
            "python_execute", {"code": "print(1)"}, "admin", reason="توثيق ثغرة المفردة"
        )
    # نفّذ فعلًا — والنتيجة تُعلِن عدم التحقّق فلا تُقرأ تخويلًا.
    assert result["principal_verification"] == "UNVERIFIED"
    assert result.get("error") is None

    # وفي الإنتاج لا يوجد هذا الباب بحال.
    import os

    previous = os.environ.get("AMOS_ENVIRONMENT")
    os.environ["AMOS_ENVIRONMENT"] = "production"
    try:
        with pytest.raises(DeprecatedRolePathUnavailableError):
            execute_tool_with_declared_role("python_execute", {"code": "print(1)"}, "admin")
    finally:
        if previous is None:
            os.environ.pop("AMOS_ENVIRONMENT", None)
        else:
            os.environ["AMOS_ENVIRONMENT"] = previous


# ── 2. المُهاجر المُهمَل معدوم في الإنتاج ──────────────────────────────────


@pytest.mark.parametrize("environment", ["production", "prod", "staging"])
def test_03_deprecated_path_unavailable_in_production(
    environment: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """في كل بيئة إنتاجية: المُهاجر يرفع قبل أن يلمس شيئًا — fail closed."""
    monkeypatch.setenv("AMOS_ENVIRONMENT", environment)
    with pytest.raises(DeprecatedRolePathUnavailableError):
        execute_tool_with_declared_role("python_execute", {"code": "print(1)"}, "admin")


def test_03b_production_check_is_read_per_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """الفحص يقرأ البيئة عند كل نداء — لا يُثبَّت وقت الاستيراد.

    لو قُرئت البيئة مرّةً عند الاستيراد، لبقيت عملية بدأت في التطوير تقبل الادّعاء
    بعد أن تصير إنتاجًا. فتُفحَص التحوّلات في الاتجاهين على وحدة مُستورَدة سابقًا.
    """
    monkeypatch.setenv("AMOS_ENVIRONMENT", "development")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        execute_tool_with_declared_role("text_summary", {"text": "نصّ."}, "citizen")

    monkeypatch.setenv("AMOS_ENVIRONMENT", "production")
    with pytest.raises(DeprecatedRolePathUnavailableError):
        execute_tool_with_declared_role("text_summary", {"text": "نصّ."}, "citizen")

    monkeypatch.setenv("AMOS_ENVIRONMENT", "test")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        execute_tool_with_declared_role("text_summary", {"text": "نصّ."}, "citizen")


# ── 3. الجلسة مصدر الدور ──────────────────────────────────────────────────


def test_04_valid_session_yields_canonical_role_and_tenant() -> None:
    """جلسة صحيحة ⇒ دور من الخادم ومستأجر من عمود الجلسة."""
    from amos_federation.services.governance.security import RBACSystem
    from amos_federation.services.governance.session_identity import resolve_context

    rbac = RBACSystem()
    created = rbac.create_session("r61-tenant-user", "agent", "127.0.0.1", tenant_id="tenant-a")
    assert created["tenant_id"] == "tenant-a"

    context = resolve_context(created["session_token"], rbac=rbac)
    assert context.is_trusted
    assert context.verification is PrincipalVerification.SESSION_VERIFIED
    assert context.role == "agent"  # من `security_roles` لا من نداء
    assert context.tenant_id == "tenant-a"  # من عمود الجلسة لا من جسم الطلب


def test_05_expired_session_denies() -> None:
    """جلسة منتهية لا تُخوَّل — لا في الجلسة ولا في السياق المبني منها."""
    from amos_federation.services.governance.security import RBACSystem, UserSessionModel
    from amos_federation.services.governance.session_identity import resolve_principal

    rbac = RBACSystem()
    token = rbac.create_session("r61-expired", "official", "127.0.0.1")["session_token"]

    session = rbac._Session()  # noqa: SLF001 — فحص السجلّ نفسه
    try:
        record = (
            session.query(UserSessionModel).filter(UserSessionModel.session_token == token).first()
        )
        record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.commit()
    finally:
        session.close()

    with pytest.raises(SessionInvalidError):
        resolve_principal(token, rbac=rbac)

    # والسياق المنتهي لا يُخوَّل حتى لو حُمل في الذاكرة — أُصلح في R6.1.
    #
    # قبله كان `AuthorizationContext` **لا يحمل** الانتهاء أصلًا: يُفحَص عند
    # الحلّ ثم يُسقَط، فمن أمسك سياقًا في عملية طويلة بقي مُخوَّلًا بعد موت جلسته.
    expired_context = _session_context(
        "official", expires_at=datetime.now(UTC) - timedelta(minutes=1)
    )
    assert expired_context.is_expired
    assert not expired_context.is_trusted, "جلسة ميّتة ما زالت موثوقة"
    assert not expired_context.has_permission("execute:tools")
    assert not tenant_matches(expired_context, DEFAULT_TENANT)
    with pytest.raises(SessionInvalidError):
        expired_context.assert_authorizable()

    # ولا تُخوَّل في السلسلة الكاملة.
    _register("r61-agent-expiry", DEFAULT_TENANT)
    with pytest.raises(AuthorizationDenied) as chain_denial:
        authorize(agent_id="r61-agent-expiry", tool_id="python_execute", principal=expired_context)
    assert chain_denial.value.stage == "principal"


# ── 4. حدّ المستأجر ───────────────────────────────────────────────────────


def _register(agent_id: str, tenant_id: str) -> None:
    from amos_federation.services.executive_core.agent_identity import (
        DuplicateAgentIdentityError,
        register_identity,
    )

    with contextlib.suppress(DuplicateAgentIdentityError):
        register_identity(
            agent_id,
            f"وكيل {tenant_id}",
            "official",
            permissions=["*"],
            allowed_tools=["*"],
            lifecycle_state="active",
            token_budget=1000,
            tenant_id=tenant_id,
        )


def test_06_same_tenant_is_allowed() -> None:
    """مستأجر «أ» ⇒ مورد «أ»: يُسمَح، وتُدرَج حلقة المستأجر مُجتازةً."""
    _register("r61-agent-a", "tenant-a")
    decision = authorize(
        agent_id="r61-agent-a",
        tool_id="python_execute",
        principal=_session_context("official", tenant_id="tenant-a"),
    )
    assert decision.allowed
    assert "tenant" in decision.stages_passed
    assert decision.tenant_id == "tenant-a"
    assert decision.resource_tenant_id == "tenant-a"


def test_07_cross_tenant_is_denied_at_the_tenant_stage() -> None:
    """مستأجر «أ» ⇒ مورد «ب»: يُرفَض، وباسم الحدّ الذي مُنع عنده.

    ويُتحقَّق أن الرفض **ليس** «لا هوية بهذا الاسم»: الهوية موجودة، والكذب في
    سبب الرفض يُخفي محاولة عبور الحدّ ويجعل السجلّ يقول غير ما وقع.
    """
    _register("r61-agent-b", "tenant-b")
    with pytest.raises(AuthorizationDenied) as denial:
        authorize(
            agent_id="r61-agent-b",
            tool_id="python_execute",
            principal=_session_context("official", tenant_id="tenant-a"),
        )
    assert denial.value.stage == "tenant"
    assert "المستأجر" in denial.value.reason
    assert "tenant" not in denial.value.detail.get("stages_passed", ())


def test_08_forged_tenant_is_denied() -> None:
    """مستأجر مُدّعىً في سياق غير مُتحقَّق منه لا يُقبل — ولو طابق نصًّا."""
    _register("r61-agent-forge", "tenant-a")

    forged = unverified_context("مُزوَّر", claimed_role="official")
    assert not tenant_matches(forged, "tenant-a")

    # وادّعاء مستأجر التاج نفسه لا يعبر شيئًا بلا ثقة.
    assert not tenant_matches(forged, FEDERAL_TENANT)
    with pytest.raises(TenantIsolationError):
        assert_tenant(forged, "tenant-a")

    with pytest.raises(AuthorizationDenied) as denial:
        authorize(agent_id="r61-agent-forge", tool_id="python_execute", principal=forged)
    # يُرفَض — والحلقة التي سقطت عندها ليست `tenant` بالضرورة: السياق غير الموثوق
    # يسقط عند أوّل حلقة تسأل عن ثقة، وقد تكون `principal` أو `tenant` أو `tool`.
    # فالمُؤكَّد هنا أنه **رُفِض**، ولا يُزعَم مكانٌ لم يُلاحَظ.
    assert denial.value.stage in {"principal", "tenant", "role", "tool"}
    assert "tenant" not in denial.value.detail.get("stages_passed", ())


def test_09_unnamed_tenant_is_not_a_wildcard() -> None:
    """المستأجر غير المُسمّى يعني `default` لا «كل المستأجرين»."""
    unnamed = _session_context("official", tenant_id=None)
    assert tenant_matches(unnamed, None)
    assert tenant_matches(unnamed, DEFAULT_TENANT)
    assert not tenant_matches(unnamed, "tenant-a"), "غياب المستأجر صار مفتاحًا عامًّا"

    # وعبور الحدود محصور بمستأجر التاج، ولا يُنال إلا بسياق موثوق.
    federal = _session_context("king", tenant_id=FEDERAL_TENANT)
    assert tenant_matches(federal, "tenant-a")
    assert tenant_matches(federal, "tenant-b")


def test_10_tenancy_mode_is_classified_honestly() -> None:
    """التصنيف `SINGLE_TENANT` — ولا يُرفَع إلى `MULTI_TENANT` بلا سجلّ مستأجرين.

    المخطَّط قادر (أعمدة `tenant_id` موجودة) والحدّ مفروض في التخويل، لكن لا
    تسجيل مستأجرين ولا تخصيص، وكل صفوف الإنتاج `default`. فالقدرة ليست وضعًا.
    """
    assert TENANCY_MODE in TENANCY_MODES
    assert TENANCY_MODE == "SINGLE_TENANT", "رُفع تصنيف الإيجار — يلزمه سجلّ مستأجرين ودليل"


# ── 5. أصالة التاج محفوظة ─────────────────────────────────────────────────


def test_11_crown_is_not_obtainable_by_string() -> None:
    """`king` نصًّا لا يمنح سلطة، والقرار السيادي يبقى موقَّعًا."""
    import sys

    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from core.constitutional_engine.model import ActionRequest, Branch
    from core.sovereignty.authority import RoyalAuthenticityError, classify

    claimed_king = unverified_context("ادّعاء", claimed_role="king")
    assert claimed_king.role == "king"  # النصّ محفوظ
    assert not claimed_king.is_trusted  # ولا يُقرأ سلطةً
    with pytest.raises(PrincipalUnverifiedError):
        claimed_king.assert_authorizable()

    # وأمرٌ ملكيّ بلا مرسوم موقَّع يُرفَض بحدث مُسمّى لا بصمت — نموذج R6 بحاله.
    with pytest.raises(RoyalAuthenticityError) as unsigned:
        classify(ActionRequest(actor=Branch.ROYAL, action="dissolve_branch"))
    assert unsigned.value.event_kind == "ROYAL_COMMAND_UNSIGNED"


# ── 6. حرس ساكن ───────────────────────────────────────────────────────────


def test_12_static_guards_against_caller_supplied_identity() -> None:
    """المصدر نفسه محروس: لا دور ولا صلاحيات ولا مستأجر يُقبَل من المُستدعي."""
    # 12أ. لا معامل دور/صلاحيات/مستأجر في توقيعَي التخويل والتنفيذ.
    for func in (authorize, sandbox.execute_tool_with_governance):
        params = set(inspect.signature(func).parameters)
        assert not (params & {"role", "permissions", "tenant_id"}), f"{func.__name__} يقبل ادّعاءً"

    # 12ب. `authorize` لا تقرأ الدور ولا المستأجر من `params` الأداة.
    authorize_source = _strip_comments(inspect.getsource(authorize))
    for claim in ('params.get("role"', 'params.get("tenant', 'params.get("permissions'):
        assert claim not in authorize_source, f"قراءة ادّعاء من جسم الطلب: {claim}"

    # 12ج. الترجمة إلى مفردة السياسة على الموثوق وحده — وإلّا فادّعاء `king` يُرقّي.
    enforce_source = _strip_comments(
        inspect.getsource(authorized_execution._enforce_governance)  # noqa: SLF001
    )
    assert "if trusted else" in enforce_source

    # 12د. دالّة الإنتاج لا تبني سياقًا غير مُتحقَّق منه بحال.
    sandbox_source = _strip_comments(
        (SRC / "services" / "tool_registry" / "sandbox.py").read_text(encoding="utf-8")
    )
    assert "unverified_context" not in sandbox_source

    # 12هـ. والمُهاجر المُهمَل يحمل فحص الإنتاج والوسم.
    deprecated_source = (SRC / "services" / "tool_registry" / "deprecated_role_path.py").read_text(
        encoding="utf-8"
    )
    assert "PRODUCTION_ENVIRONMENTS" in _strip_comments(deprecated_source)
    assert "DeprecationWarning" in _strip_comments(deprecated_source)
    assert DEPRECATED_MARKER in deprecated_source

    # 12و. حلقة المستأجر في السلسلة، وقبل الدور.
    assert "tenant" in AUTHORIZATION_CHAIN
    assert AUTHORIZATION_CHAIN.index("tenant") < AUTHORIZATION_CHAIN.index("role")
    assert AUTHORIZATION_CHAIN.index("principal") == 0


def test_13_no_production_module_calls_the_deprecated_path() -> None:
    """لا شيفرة إنتاج تستدعي المُهاجر المُهمَل — الاختبارات وحدها.

    وسمُ الإهمال بلا هذا الحرس دعوى: تُوسَم الدالّة ثم تُستدعى من خدمة، فيبقى
    المسار الثاني عاملًا باسم جديد.
    """
    offenders: list[str] = []
    for path in (SRC).rglob("*.py"):
        if path.name == "deprecated_role_path.py":
            continue
        if "execute_tool_with_declared_role" in _strip_comments(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(SRC)))
    assert not offenders, f"شيفرة إنتاج تستدعي المسار المُهمَل: {offenders}"


def test_14_memory_endpoints_do_not_read_tenant_from_request_body() -> None:
    """نقاط الذاكرة تأخذ المستأجر من السياق لا من جسم الطلب.

    كانت تقرأ `entry.tenant_id`/`query.tenant_id`، أي أن حاملَ رمزٍ صالح كان
    يُسمّي مستأجرًا غير مستأجره فيُصدَّق. والحقل باقٍ في المخطَّط للتوافُق، فالحرس
    على **قراءته** لا على وجوده.
    """
    source = _strip_comments(
        (SRC / "services" / "memory_service" / "main.py").read_text(encoding="utf-8")
    )
    for claim in ("entry.tenant_id", "query.tenant_id"):
        assert claim not in source, f"مستأجر يُقرأ من جسم الطلب: {claim}"
    assert "require_context" in source, "النقاط لا تُشتقّ سياقًا من الرمز الموقَّع"
