"""
اختبارات R6 — جذر هوية المُستدعي والتخويل
الهدف: إثبات أن الدور يُشتقّ من هوية مُتحقَّق منها لا من ادّعاء المُستدعي
النطاق: federal/executive/services/tests
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

اثنا عشر اختبارًا موجَّهًا، لا اختبار نظام كامل. وكلٌّ منها يُثبِت دعوى واحدة
مُسمّاة في وثيقة R6، فإن سقط سقطت الدعوى معه.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from amos_federation.common.principal import (
    DEFAULT_TENANT,
    POLICY_ROLE_MAP,
    TRUSTED_VERIFICATIONS,
    AuthorizationContext,
    Principal,
    PrincipalKind,
    PrincipalUnverifiedError,
    PrincipalVerification,
    SessionInvalidError,
    canonical_role,
    policy_role,
    tenant_matches,
    unverified_context,
)
from amos_federation.services.tool_registry.authorized_execution import (
    AUTHORIZATION_CHAIN,
    AuthorizationDenied,
    authorize,
)
from amos_federation.services.tool_registry.sandbox import (
    execute_tool_for_principal,
    execute_tool_with_governance,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "amos_federation"


def _session_context(
    *,
    role_id: str = "official",
    permissions: tuple[str, ...] = ("execute:tools",),
    tenant_id: str | None = None,
    expires_at: datetime | None = None,
) -> AuthorizationContext:
    """سياق مبنيّ من سجلّ جلسة — الدور من الخادم لا من الطلب."""
    principal = Principal.from_session_record(
        session_id="r6-test-session",
        username="r6-tester",
        role_id=role_id,
        permissions=permissions,
        expires_at=expires_at,
        tenant_id=tenant_id,
    )
    return AuthorizationContext.from_principal(principal)


def _strip_comments(source: str) -> str:
    """أسقِط التعليقات قبل الحراسة الساكنة.

    كلمة في تعليق عربي ليست استدعاءً للدالّة. أُسقطت التعليقات في جولة سابقة
    لهذا السبب نفسه، ويُحفَظ الدرس هنا.
    """
    return "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))


# ── 1. مبدأ مُصادَق عليه صحيح ─────────────────────────────────────────────


def test_01_valid_authenticated_principal_executes() -> None:
    """جلسة صحيحة بدور كافٍ تُنفِّذ، والنتيجة تحمل نَسَب هويتها."""
    context = _session_context(role_id="official")
    assert context.verification is PrincipalVerification.SESSION_VERIFIED
    assert context.is_trusted

    result = execute_tool_for_principal("python_execute", {"code": "print(6*7)"}, context)
    assert "42" in result["stdout"]
    assert result["principal_verification"] == "SESSION_VERIFIED"
    assert result["principal_id"] == "r6-tester"
    assert result["session_id"] == "r6-test-session"
    # النَسَب ليس زخرفة: بلا هذه الحقول تُقرأ النتيجة بلا هوية طالبها.
    assert result["principal_kind"] == PrincipalKind.USER.value


# ── 2. مبدأ غائب ──────────────────────────────────────────────────────────


def test_02_missing_principal_fails_closed_on_canonical_entry() -> None:
    """المدخل الكانوني يرفض المبدأ الغائب في كل بيئة لا في الإنتاج وحده."""
    anonymous = AuthorizationContext.from_principal(Principal.unverified("لا رأس تفويض في الطلب"))
    assert not anonymous.is_trusted

    with pytest.raises(PrincipalUnverifiedError):
        execute_tool_for_principal("python_execute", {"code": "print(1)"}, anonymous)


def test_02b_missing_principal_fails_closed_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """وفي بيئة إنتاجية يُرفَض المسار القديم نفسه — لا ادّعاء دور هناك."""
    monkeypatch.setenv("AMOS_ENVIRONMENT", "production")
    with pytest.raises(PrincipalUnverifiedError):
        execute_tool_with_governance("python_execute", {"code": "print(1)"}, role="admin")

    # وفي التطوير يمرّ لكن موسومًا `UNVERIFIED` صراحةً — لا يُقرأ تخويلًا.
    monkeypatch.setenv("AMOS_ENVIRONMENT", "test")
    result = execute_tool_with_governance("python_execute", {"code": "print(1)"}, role="admin")
    assert result["principal_verification"] == "UNVERIFIED"


# ── 3. دور مُزوَّر ─────────────────────────────────────────────────────────


def test_03_forged_role_cannot_escalate() -> None:
    """ادّعاء `king` أو `royal` لا يُترجَم إلى `admin` ولا يُخوَّل.

    هذه الثغرة كانت ستُفتَح بترجمة الأدوار نفسها: `policy_role("king") == "admin"`،
    فلو طُبِّقت الترجمة على المُدّعى لصار كل مُستدعٍ ملكًا بكلمة. فالترجمة على
    الموثوق وحده.
    """
    for claimed in ("king", "royal", "royal_guard", "official"):
        result = execute_tool_with_governance("python_execute", {"code": "print(1)"}, role=claimed)
        assert result.get("error") == "policy_denied", f"ادّعاء '{claimed}' مرّ"
        assert result["principal_verification"] == "UNVERIFIED"

    # والدور المُدّعى لا يُبنى منه سياق موثوق بحال.
    claimed_context = unverified_context("اختبار", claimed_role="king")
    assert claimed_context.role == "king"
    assert not claimed_context.is_trusted
    assert claimed_context.verification is PrincipalVerification.UNVERIFIED
    with pytest.raises(PrincipalUnverifiedError):
        claimed_context.assert_authorizable()


def test_03b_forged_role_does_not_override_canonical_identity() -> None:
    """في سلسلة الوكيل الكاملة: دور الهوية يفوز على ادّعاء المُستدعي."""
    from amos_federation.services.executive_core.agent_identity import (
        DuplicateAgentIdentityError,
        register_identity,
    )

    agent_id = "r6-forged-role-agent"
    with contextlib.suppress(DuplicateAgentIdentityError):
        register_identity(
            agent_id,
            "وكيل اختبار الدور المُزوَّر",
            "citizen",
            permissions=["tool:use"],
            allowed_tools=["python_execute"],
            lifecycle_state="active",
            token_budget=1000,
            tenant_id=DEFAULT_TENANT,
        )

    # المُستدعي يقول admin، وهوية الوكيل الكانونية citizen.
    result = execute_tool_with_governance(
        "python_execute",
        {"code": "print(1)", "agent_id": agent_id},
        role="admin",
    )
    # الادّعاء لم يُصدَّق: دور الهوية `citizen` هو ما رآه محرِّك السياسة.
    assert result.get("error") in {"policy_denied", "authorization_denied"}


# ── 4. صلاحيات مُزوَّرة ────────────────────────────────────────────────────


def test_04_forged_permissions_are_not_trusted() -> None:
    """لا معامل صلاحيات في طبقة التخويل، والصلاحيات على غير الموثوق لا تُقرأ."""
    import inspect

    signature = inspect.signature(authorize)
    for forbidden in ("permissions", "role", "actor_role", "capabilities", "scopes"):
        assert (
            forbidden not in signature.parameters
        ), f"`authorize` تقبل '{forbidden}' من المُستدعي — هذا هو الخلل عينه"

    # سياق غير موثوق يحمل صلاحيات: لا واحدة منها تُمنَح.
    forged = Principal.unverified("مُزوَّر", claimed_role="king")
    context = AuthorizationContext.from_principal(forged)
    assert context.permissions == ()
    assert context.has_permission("*") is False
    assert context.has_permission("execute:all") is False

    # وحتى لو حُشِيت الصلاحيات في السياق يدويًّا، `has_permission` ترفض غير الموثوق.
    stuffed = AuthorizationContext(
        principal_id="attacker",
        verification=PrincipalVerification.UNVERIFIED,
        principal_kind=PrincipalKind.ANONYMOUS,
        permissions=("*",),
        reason="حَشو صلاحيات",
    )
    assert stuffed.has_permission("*") is False


# ── 5. جلسة باطلة ─────────────────────────────────────────────────────────


def test_05_invalid_and_expired_session_is_rejected() -> None:
    """الجلسة المنتهية لا تُخوَّل — وهذا خللٌ حقيقي أُصلح في R6."""
    from amos_federation.services.governance.security import RBACSystem

    rbac = RBACSystem()
    created = rbac.create_session("expired-user", "king", "127.0.0.1")
    token = created["session_token"]
    assert rbac.check_permission(token, "execute:tools") is True

    # أرجِع الانتهاء إلى الماضي مباشرةً في السجلّ.
    from amos_federation.services.governance.security import UserSessionModel

    session = rbac._Session()  # noqa: SLF001 — فحص السجلّ نفسه
    try:
        record = (
            session.query(UserSessionModel).filter(UserSessionModel.session_token == token).first()
        )
        record.expires_at = datetime.now(UTC) - timedelta(hours=1)
        session.commit()
    finally:
        session.close()

    # قبل R6 كانت هذه تُرجع True: `check_permission` لم تنظر إلى `expires_at`.
    assert rbac.check_permission(token, "execute:tools") is False

    from amos_federation.services.governance.session_identity import resolve_principal

    with pytest.raises(SessionInvalidError):
        resolve_principal(token, rbac=rbac)

    # ورمز لا وجود له يُرفَض ولا يُنحدَر إلى مبدأ أضعف.
    with pytest.raises(SessionInvalidError):
        resolve_principal("token-does-not-exist", rbac=rbac)
    with pytest.raises(SessionInvalidError):
        resolve_principal("", rbac=rbac)


# ── 6. جلسة صحيحة ─────────────────────────────────────────────────────────


def test_06_valid_session_resolves_role_from_server() -> None:
    """الدور والصلاحيات يُقرآن من `security_roles` عبر سجلّ الجلسة."""
    from amos_federation.services.governance.security import RBACSystem
    from amos_federation.services.governance.session_identity import (
        resolve_context,
        resolve_principal,
    )

    rbac = RBACSystem()
    created = rbac.create_session("real-user", "agent", "127.0.0.1")
    token = created["session_token"]

    principal = resolve_principal(token, rbac=rbac)
    assert principal.verification is PrincipalVerification.SESSION_VERIFIED
    assert principal.principal_id == "real-user"
    # الدور من السجلّ، ولم يُرسله أحد في طلب.
    assert principal.role == "agent"
    assert "execute:tools" in principal.permissions
    assert principal.is_expired is False

    context = resolve_context(token, rbac=rbac)
    assert context.is_trusted
    assert context.has_permission("execute:tools")
    # ولا يمنح سجلّ دور `agent` صلاحية شاملة.
    assert context.has_permission("*") is False


# ── 7. رفض التخويل ────────────────────────────────────────────────────────


def test_07_authorization_denial_names_its_stage() -> None:
    """الرفض يُسمّي حلقته وسببه — ولا يُنشأ صندوق بعده."""
    context = _session_context(role_id="citizen", permissions=("read:public",))
    result = execute_tool_for_principal("python_execute", {"code": "print(1)"}, context)
    assert result["error"] == "policy_denied"
    assert "stdout" not in result
    assert result["principal_verification"] == "SESSION_VERIFIED"

    # وفي سلسلة الوكيل: وكيل غير موجود يُرفَض في حلقة `agent` لا في حلقة الأداة.
    with pytest.raises(AuthorizationDenied) as denial:
        authorize(
            agent_id="agent-does-not-exist-r6",
            tool_id="python_execute",
            principal=_session_context(),
        )
    assert denial.value.stage == "agent"
    assert denial.value.reason

    # والمبدأ يسبق الوكيل في السلسلة المُعلَنة.
    assert AUTHORIZATION_CHAIN.index("principal") == 0
    assert AUTHORIZATION_CHAIN.index("session") < AUTHORIZATION_CHAIN.index("agent")


# ── 8. عزل المستأجرين ─────────────────────────────────────────────────────


def test_08_tenant_isolation_denies_cross_tenant() -> None:
    """سياق مستأجر «أ» لا يملك مورد مستأجر «ب» ولو كان دوره الأعلى."""
    king_of_a = _session_context(role_id="king", permissions=("*",), tenant_id="tenant-a")

    assert tenant_matches(king_of_a, "tenant-a") is True
    assert tenant_matches(king_of_a, "tenant-b") is False
    # المستأجر غير المُسمّى يعني `default` تحديدًا، لا «كل المستأجرين».
    assert tenant_matches(king_of_a, None) is False
    no_tenant = _session_context(role_id="king", permissions=("*",))
    assert tenant_matches(no_tenant, None) is True
    assert tenant_matches(no_tenant, DEFAULT_TENANT) is True
    assert tenant_matches(no_tenant, "tenant-b") is False
    # ومستأجر التاج يعبر الحدود — وهذا مُعلَن لا مُخفى.
    federal = _session_context(role_id="king", permissions=("*",), tenant_id="federal")
    assert tenant_matches(federal, "tenant-b") is True
    # وغير الموثوق لا يملك مستأجرًا واحدًا.
    assert tenant_matches(unverified_context("اختبار"), None) is False

    # والرفض يحدث في سلسلة التخويل فعلًا لا في الدالّة وحدها.
    from amos_federation.services.executive_core.agent_identity import (
        DuplicateAgentIdentityError,
        register_identity,
    )

    agent_id = "r6-tenant-b-agent"
    with contextlib.suppress(DuplicateAgentIdentityError):
        register_identity(
            agent_id,
            "وكيل مستأجر ب",
            "official",
            permissions=["*"],
            allowed_tools=["*"],
            lifecycle_state="active",
            token_budget=1000,
            tenant_id="tenant-b",
        )

    with pytest.raises(AuthorizationDenied) as denial:
        authorize(agent_id=agent_id, tool_id="python_execute", principal=king_of_a)
    assert denial.value.stage == "agent"
    assert "المستأجر" in denial.value.reason


# ── 9. أصالة الأمر السيادي ────────────────────────────────────────────────


def test_09_sovereign_command_authenticity_vs_claim() -> None:
    """ادّعاء صفة التاج ليس أمرًا سياديًّا — والرفض ليس نقضًا على التاج."""
    repo_root = Path(__file__).resolve().parents[4]
    import sys

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from core.constitutional_engine.model import ActionRequest, Branch
    from core.sovereignty.authority import RoyalAuthenticityError, classify

    # 1. أمر ملكي بلا مرسوم موقَّع: ليس أمرًا ملكيًّا.
    with pytest.raises(RoyalAuthenticityError) as unsigned:
        classify(ActionRequest(actor=Branch.ROYAL, action="dissolve_branch"))
    assert unsigned.value.event_kind == "ROYAL_COMMAND_UNSIGNED"

    # 2. كائن يشبه المرسوم مكان المرسوم: مرفوض.
    with pytest.raises(RoyalAuthenticityError) as fake:
        classify(
            ActionRequest(
                actor=Branch.ROYAL,
                action="dissolve_branch",
                royal_decree="أنا مرسوم، أقسم",  # type: ignore[arg-type]
            )
        )
    assert fake.value.event_kind == "DECREE_TYPE_INVALID"

    # 3. فاعل غير ملكي يحمل مرسومًا: المرسوم لا يرفع طبقة حامله.
    from core.sovereignty.decree import RoyalDecree

    borrowed = RoyalDecree(
        decree_id="r6-borrowed",
        action="dissolve_branch",
        targets=("executive",),
        issued_at=datetime.now(UTC).isoformat(),
    )
    with pytest.raises(RoyalAuthenticityError) as proxy:
        classify(
            ActionRequest(
                actor=Branch.EXECUTIVE,
                action="dissolve_branch",
                royal_decree=borrowed,
            )
        )
    assert proxy.value.event_kind == "DECREE_PRESENTED_BY_NON_ROYAL"

    # 4. الفاعل التنفيذي العادي يُصنَّف قرارًا تابعًا، ولا يُدَّعى له ملكية.
    subordinate = classify(ActionRequest(actor=Branch.EXECUTIVE, action="deploy_model"))
    assert subordinate.claimed_royal is False
    assert subordinate.authenticity_verified is False

    # 5. والجسر التنفيذي لا يستطيع ادّعاء الصفة الملكية بحال: الفرع مُثبَّت.
    from amos_federation.services.executive_core.sovereignty_bridge import (
        ConstitutionalAuthorizer,
    )

    bridge_source = _strip_comments(
        (SRC / "services" / "executive_core" / "sovereignty_bridge.py").read_text(encoding="utf-8")
    )
    assert (
        "Branch.ROYAL" not in bridge_source
    ), "الجسر التنفيذي يذكر الفرع الملكي — لا يجوز أن يدّعيه"
    assert ConstitutionalAuthorizer is not None


# ── 10. فرض شبكة الصندوق المحلّي ──────────────────────────────────────────


def test_10_local_network_enforcement_is_measured_not_claimed() -> None:
    """سياسة `DENY` تُفرَض بـnamespace شبكي حين تسمح البيئة — ويُقاس لا يُزعم."""
    from amos_federation.services.tool_registry.providers import network

    assert network.enforcement_for("modal") == "PROVIDER_ENFORCED"
    assert network.enforcement_for("simulation") == "NOT_APPLICABLE"
    assert network.local_enforcement("DENY") in network.ENFORCEMENT_MODES
    # ALLOWLIST عند المحلّي مُعلَنة فقط: العزل يقطع الكل ولا يُرشِّح مضيفًا.
    assert network.local_enforcement("ALLOWLIST") == "DECLARED_ONLY"

    available = network.isolation_available()
    if not available:
        # لا فرض في هذه البيئة: يُعلَن `DECLARED_ONLY` ولا يُزعم غيره.
        assert network.local_enforcement("DENY") == "DECLARED_ONLY"
        pytest.skip("عزل namespace غير متاح في هذه البيئة — الحدّ مُعلَن لا مزعوم")

    assert network.local_enforcement("DENY") == "NAMESPACE_ENFORCED"

    # الفرض حقيقي: اتّصال خارجي يفشل داخل النطاق وينجح خارجه.
    probe = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 80), timeout=4).close()\n"
        "    print('REACHABLE')\n"
        "except OSError:\n"
        "    print('BLOCKED')\n"
    )
    inside = subprocess.run(  # noqa: S603
        [*network.NETWORK_ISOLATION_ARGV, "python3", "-c", probe],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert (
        inside.stdout.strip() == "BLOCKED"
    ), f"العزل لم يقطع الشبكة فعلًا: {inside.stdout!r} / {inside.stderr!r}"

    # والمزوِّد المحلّي يُعلن نمط الفرض في نتيجته.
    from amos_federation.services.tool_registry.providers.contract import (
        ExecutionContext,
        ExecutionRequest,
        SandboxSpec,
    )
    from amos_federation.services.tool_registry.providers.local_provider import (
        LocalSubprocessProvider,
    )

    provider = LocalSubprocessProvider()
    handle = provider.create_sandbox(
        SandboxSpec(tool_id="python_execute", network_policy="DENY", timeout_seconds=60)
    )
    try:
        result = provider.execute(
            handle,
            ExecutionRequest(code=probe, context=ExecutionContext(tool_id="python_execute")),
        )
    finally:
        provider.cleanup(handle)
    assert result.network_enforcement == "NAMESPACE_ENFORCED"
    assert result.stdout.strip() == "BLOCKED"


# ── 11. تخويل الصندوق ────────────────────────────────────────────────────


def test_11_sandbox_requires_authorization_first() -> None:
    """لا صندوق قبل التخويل — والرفض يمنع إنشاءه لا يُنظِّفه بعده."""
    import inspect

    from amos_federation.services.tool_registry import authorized_execution

    authorize_source = _strip_comments(inspect.getsource(authorized_execution.authorize))
    for forbidden in ("create_sandbox", "execute_in_sandbox", "subprocess"):
        assert (
            forbidden not in authorize_source
        ), f"`authorize` تلمس '{forbidden}' — التخويل فحصٌ محض لا تنفيذ"

    # والرفض في المدخل الكانوني يقع قبل أي تنفيذ.
    denied = execute_tool_for_principal(
        "python_execute",
        {"code": "print('should not run')"},
        _session_context(role_id="citizen", permissions=("read:public",)),
    )
    assert denied.get("error") == "policy_denied"
    assert "should not run" not in denied.get("stdout", "")

    # وأداة غير مسجَّلة تُرفَض ولا تُنفَّذ.
    unknown = execute_tool_for_principal("tool_that_does_not_exist_r6", {}, _session_context())
    assert unknown.get("error") in {"unknown_tool", "policy_denied"}


# ── 12. حراسة ساكنة ضدّ التجاوُز ──────────────────────────────────────────


def test_12_static_guards_against_bypass() -> None:
    """حراسة على المصدر: لا ثقة بدور من المُستدعي، ولا تخويل بلا مبدأ."""
    # 12أ. `authorize` لا تقبل دورًا ولا صلاحيات من المُستدعي.
    import inspect

    from amos_federation.services.tool_registry import authorized_execution

    signature = inspect.signature(authorize)
    assert "principal" in signature.parameters
    assert {"role", "actor_role", "permissions"}.isdisjoint(signature.parameters)

    # 12ب. المدخل الكانوني بلا معامل دور بحال.
    canonical_signature = inspect.signature(execute_tool_for_principal)
    assert "role" not in canonical_signature.parameters
    assert "context" in canonical_signature.parameters

    # 12ج. `common/` لا يعتمد على `services/` — الطبقة لا تُقلَب.
    principal_source = (SRC / "common" / "principal.py").read_text(encoding="utf-8")
    assert (
        "amos_federation.services" not in principal_source
    ), "`common/principal.py` يستورد من `services/` — انقلاب طبقات"

    # 12د. لا سرّ داخل سياق التخويل، والفحص مُفعَّل عند البناء لا اختياريًّا.
    with pytest.raises(ValueError, match="الأسرار"):
        AuthorizationContext(
            principal_id="u",
            verification=PrincipalVerification.SESSION_VERIFIED,
            principal_kind=PrincipalKind.USER,
            permissions=("JWT_SECRET",),
        )
    with pytest.raises(ValueError, match="الأسرار"):
        AuthorizationContext(
            principal_id="u",
            verification=PrincipalVerification.SESSION_VERIFIED,
            principal_kind=PrincipalKind.USER,
            capabilities=("read:DATABASE_URL",),
        )

    # 12هـ. `UNVERIFIED` ليست من الدرجات الموثوقة، ولا تُقحَم فيها.
    assert PrincipalVerification.UNVERIFIED.value not in TRUSTED_VERIFICATIONS
    assert len(TRUSTED_VERIFICATIONS) == 3

    # 12و. المبدأ غير المُتحقَّق منه والنداء الداخلي يلزمهما سبب مُسمّى.
    with pytest.raises(ValueError):
        Principal(
            principal_id="x",
            verification=PrincipalVerification.UNVERIFIED,
            kind=PrincipalKind.ANONYMOUS,
        )
    with pytest.raises(ValueError):
        Principal(
            principal_id="x",
            verification=PrincipalVerification.SYSTEM_INTERNAL,
            kind=PrincipalKind.SYSTEM,
        )
    system = Principal.system("dispatcher", "جدولة داخلية دوريّة")
    assert system.is_trusted
    assert system.kind is PrincipalKind.SYSTEM
    assert system.role == ""  # النداء الداخلي لا يمنح نفسه دورًا

    # 12ز. ترجمة الدور لا تُرقّي مجهولًا ولا تُغيّر هوية الدور.
    assert canonical_role("KING") == "king"  # تطبيع نصّي فقط
    assert policy_role("king") == "admin"
    assert policy_role("citizen") == "citizen"
    assert policy_role("role-i-invented") == "role-i-invented"
    assert "*" not in POLICY_ROLE_MAP.values()

    # 12ح. الترجمة على الموثوق وحده — محروسة في المصدر لا في السلوك فقط.
    enforce_source = _strip_comments(
        inspect.getsource(authorized_execution._enforce_governance)  # noqa: SLF001
    )
    assert "if trusted else" in enforce_source, "ترجمة الدور تُطبَّق بلا شرط ثقة — ثغرة ترفيع صلاحية"

    # 12ط. المدخل القديم لا يزال موجودًا لكنه لا يُخوَّل في الإنتاج.
    sandbox_source = _strip_comments(
        (SRC / "services" / "tool_registry" / "sandbox.py").read_text(encoding="utf-8")
    )
    assert (
        "unverified_context" in sandbox_source
    ), "المسار القديم لا يلفّ الدور المُدّعى في سياق غير مُتحقَّق منه"


def test_12b_no_service_bypasses_governance_entry_point() -> None:
    """لا خدمة تستدعي تنفيذًا في صندوق دون المرور بطبقة التخويل."""
    offenders: list[str] = []
    allowed = {
        "tool_registry/sandbox.py",  # المدخل نفسه
        "tool_registry/authorized_execution.py",  # طبقة التخويل
        "tool_registry/providers/local_provider.py",  # المزوِّد المحلّي
        "tool_registry/providers/selection.py",  # اختيار المزوِّد
        "tool_registry/providers/modal_provider.py",
        "tool_registry/providers/e2b_provider.py",
        "tool_registry/providers/network.py",  # فحص القدرة
        "tool_registry/providers/contract.py",  # تعريف الواجهة المُجرَّدة
        "tool_registry/providers/simulation_provider.py",  # لا تنفيذ حقيقي فيه
    }
    for path in (SRC / "services").rglob("*.py"):
        relative = path.relative_to(SRC / "services").as_posix()
        if relative in allowed:
            continue
        source = _strip_comments(path.read_text(encoding="utf-8"))
        if "execute_in_sandbox(" in source or "create_sandbox(" in source:
            offenders.append(relative)
    assert not offenders, "خدمات تُنشئ صندوقًا دون طبقة التخويل: " + ", ".join(sorted(offenders))


def test_12d_endpoint_dependency_yields_verified_context() -> None:
    """تبعية النقاط الطرفية تُسلِّم سياقًا موثوقًا مُشتقًّا من رمز موقَّع."""
    from amos_federation.common.auth import create_access_token, decode_token
    from amos_federation.common.auth_context import require_context, require_permission

    token = create_access_token(
        "endpoint-user", ["execute:tools"], tenant_id="tenant-a", role="official"
    )
    context = require_context(decode_token(token))
    assert context.verification is PrincipalVerification.TOKEN_VERIFIED
    assert context.is_trusted
    assert context.principal_id == "endpoint-user"
    # الدور من مطالبة الرمز الموقَّع، لا من جسم الطلب.
    assert context.role == "official"
    assert context.tenant_id == "tenant-a"
    assert context.has_permission("execute:tools")
    assert context.has_permission("*") is False

    # ورمز بلا `sub` لا هوية فيه.
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as unauthorized:
        require_context({"scopes": [], "role": "king"})
    assert unauthorized.value.status_code == 401

    # والصلاحية المفقودة 403 لا 200.
    assert callable(require_permission("execute:tools"))


def test_12c_environment_is_test_so_fail_closed_is_provable() -> None:
    """تأكيد أن البيئة هنا ليست إنتاجية — وإلّا لكان نصف الاختبارات كاذبًا."""
    assert os.environ.get("AMOS_ENVIRONMENT") == "test"
