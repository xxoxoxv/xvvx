"""
اختبارات R7-A — السجل الفدرالي للمؤسسات
الهدف: التحقّق أن أول نظام دولة يعمل فعلًا: قيود مرجعية مفروضة، تخويل، تدقيق، أحداث
النطاق: federal/executive/services
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R7-A)

هذه اختبارات مركَّزة على نطاق واحد: لا تشغيل نظام كامل، ولا شبكة، ولا مزوّد
خارجي. وأهمّها الأربعة الأولى، لأنها تفحص ما يُدَّعى كثيرًا ولا يُفرَض:

1. المفتاح الأجنبي **مفروض** لا مكتوب — الصفّ اليتيم يُرفَض من القاعدة.
2. التخويل من سياق مُشتقّ من جلسة، والدور لا يُقال في الطلب.
3. حدّ المستأجر يُرفَض عند العبور.
4. كل كتابة تُترك أثرًا في سلسلة التدقيق وحدثًا دائمًا يُتتبَّع إلى فاعله.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from amos_federation.common.database import get_session_factory, init_db
from amos_federation.common.durable_event_bus import get_durable_event_bus
from amos_federation.common.persistent import PersistentAuditStore
from amos_federation.common.principal import (
    DEFAULT_TENANT,
    AuthorizationContext,
    Principal,
    PrincipalUnverifiedError,
    SessionInvalidError,
    TenantIsolationError,
    unverified_context,
)
from amos_federation.common.registry import SERVICES
from amos_federation.services.executive_core.agent_identity import register_identity
from amos_federation.services.governance.security import DEFAULT_ROLES
from amos_federation.services.state_registry.authorization import (
    DOMAIN_PERMISSIONS,
    RegistryAuthorizationError,
)
from amos_federation.services.state_registry.models import (
    INSTITUTION_BRANCHES,
    INSTITUTION_KINDS,
    DepartmentModel,
    InstitutionModel,
    OfficialModel,
)
from amos_federation.services.state_registry.service import (
    EVENT_DEPARTMENT_CREATED,
    EVENT_INSTITUTION_REGISTERED,
    EVENT_OFFICIAL_APPOINTED,
    EVENT_OFFICIAL_REVOKED,
    REGISTRY_EVENTS,
    DepartmentHeadConflictError,
    DepartmentNotFoundError,
    DuplicateCodeError,
    InstitutionInactiveError,
    InstitutionNotEmptyError,
    InstitutionNotFoundError,
    RegistryError,
    StateRegistry,
    UnknownAgentError,
    get_state_registry,
    reset_state_registry,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "amos_federation"
REGISTRY_SRC = SRC / "services" / "state_registry"

_ROLE_PERMISSIONS = {role["role_id"]: tuple(role["permissions"]) for role in DEFAULT_ROLES}


def _strip_comments(source: str) -> str:
    """أزِل التعليقات وسلاسل التوثيق قبل أي تأكيد على المصدر.

    الدرس من R6 وR6.1: حرسٌ يبحث عن نصٍّ في المصدر يمرّ أو يفشل بسبب **تعليق**
    يشرح الأمر لا بسبب شيفرة تفعله.
    """
    no_docstrings = re.sub(r'"""(?:.|\n)*?"""', "", source)
    return "\n".join(line.split("#", 1)[0] for line in no_docstrings.splitlines())


def _context(
    role_id: str,
    *,
    tenant_id: str | None = None,
    expires_at: datetime | None = None,
    username: str = "r7-user",
) -> AuthorizationContext:
    """سياق `SESSION_VERIFIED` بصلاحيات الدور **كما هي مزروعة في `security_roles`**.

    الصلاحيات تُقرأ من `DEFAULT_ROLES` لا تُكتَب في الاختبار: لو كتبها الاختبار
    لأمكنه أن يمنح دورًا صلاحيةً لا يملكها في النظام، فيمرّ اختبارٌ على واقع لا
    وجود له.
    """
    return AuthorizationContext.from_principal(
        Principal.from_session_record(
            session_id=f"r7-{role_id}-{username}",
            username=f"{username}-{role_id}",
            role_id=role_id,
            permissions=_ROLE_PERMISSIONS[role_id],
            expires_at=expires_at,
            tenant_id=tenant_id,
        )
    )


@pytest.fixture
def registry() -> StateRegistry:
    """سجل نظيف على قاعدة الاختبار."""
    reset_state_registry()
    init_db()
    return get_state_registry()


@pytest.fixture
def crown() -> AuthorizationContext:
    """سياق التاج — يملك `*` فيمرّ في كل حدّ عبر `has_permission` نفسها."""
    return _context("king")


def _agent(tenant_id: str = DEFAULT_TENANT) -> str:
    """وكيلٌ حقيقي في `agents` — التقليد يشير إليه بمفتاح أجنبي."""
    agent_id = f"agent-r7-{uuid.uuid4().hex[:10]}"
    register_identity(agent_id, f"وكيل {agent_id}", "executor", tenant_id=tenant_id)
    return agent_id


def _code(prefix: str = "INST") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


# ── 1. القيود المرجعية مفروضة فعلًا ───────────────────────────────────────


def test_01_foreign_keys_are_enforced_not_decorative(registry: StateRegistry) -> None:
    """الصفّ اليتيم يُرفَض من القاعدة — لا من تعليق في النموذج.

    هذا أوّل اختبار بقصد: SQLite يقبل `REFERENCES` في المخطَّط ثم لا يفرضه بلا
    `PRAGMA foreign_keys=ON`. فلو كان الفرض مُطفأً لمرّ كل ما بعده وهو يكتب صفوفًا
    يتيمة بنجاح، ولصحّ أن نقول «قيود مرجعية» ونحن نكذب.
    """
    session = get_session_factory()()
    try:
        session.add(
            OfficialModel(
                id=f"offl-orphan-{uuid.uuid4().hex[:8]}",
                agent_id="agent-does-not-exist-anywhere",
                institution_id="inst-does-not-exist",
                title="منصب بلا مؤسسة",
                appointed_by="test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_02_department_requires_existing_institution(registry: StateRegistry) -> None:
    """لا إدارة بلا مؤسسة — على مستوى القاعدة أيضًا لا الخدمة وحدها."""
    session = get_session_factory()()
    try:
        session.add(
            DepartmentModel(
                id=f"dept-orphan-{uuid.uuid4().hex[:8]}",
                institution_id="inst-ghost",
                code="D1",
                name="إدارة بلا مؤسسة",
                created_by="test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_03_check_constraint_rejects_unknown_kind(registry: StateRegistry) -> None:
    """مفردة الأنواع قيدٌ في القاعدة — لا قائمةً في التوثيق."""
    session = get_session_factory()()
    try:
        session.add(
            InstitutionModel(
                id=f"inst-bad-{uuid.uuid4().hex[:8]}",
                code=_code(),
                name="كيان بنوع مُختَرع",
                kind="wizardry",
                branch="executive",
                created_by="test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


# ── 2. التخويل: الدور من الجلسة لا من الطلب ───────────────────────────────


def test_04_founding_an_institution_requires_royal_authority(registry: StateRegistry) -> None:
    """المواطن والوكيل والمسؤول لا يؤسّسون مؤسسة — الملكي والتاج يؤسّسان."""
    for role_id in ("citizen", "agent", "official"):
        with pytest.raises(RegistryAuthorizationError) as denied:
            registry.register_institution(
                context=_context(role_id),
                code=_code(),
                name="وزارة غير مأذونة",
                kind="ministry",
                branch="executive",
            )
        assert denied.value.role == role_id
        assert "manage:all" in denied.value.required

    for role_id in ("royal", "king"):
        result = registry.register_institution(
            context=_context(role_id),
            code=_code(),
            name="وزارة مأذونة",
            kind="ministry",
            branch="executive",
        )
        assert result["status"] == "active"
        assert result["audit_id"]


def test_05_unverified_context_is_denied_before_permissions(registry: StateRegistry) -> None:
    """سياق غير مُتحقَّق منه يُرفَض ولو ادّعى الدور — لا يُسأل عن صلاحيته أصلًا."""
    with pytest.raises(PrincipalUnverifiedError):
        registry.register_institution(
            context=unverified_context("ادّعاء في اختبار R7", claimed_role="king"),
            code=_code(),
            name="وزارة مُدَّعاة",
            kind="ministry",
            branch="executive",
        )


def test_06_expired_session_cannot_write_or_read(registry: StateRegistry) -> None:
    """الجلسة الميّتة لا تكتب ولا تقرأ — الرفض `SessionInvalidError` لا 403 مبهم."""
    expired = _context("king", expires_at=datetime.now(UTC) - timedelta(minutes=1))
    with pytest.raises(SessionInvalidError):
        registry.register_institution(
            context=expired,
            code=_code(),
            name="وزارة بجلسة ميّتة",
            kind="ministry",
            branch="executive",
        )
    with pytest.raises(SessionInvalidError):
        registry.list_institutions(context=expired)


def test_07_reading_the_registry_is_authorized_too(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """القراءة ليست مفتوحة: المواطن والوكيل يُحجَبان، والمسؤول يقرأ."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة للقراءة", kind="ministry", branch="executive"
    )
    for role_id in ("citizen", "agent"):
        with pytest.raises(RegistryAuthorizationError):
            registry.get_institution(code, context=_context(role_id))
    assert registry.get_institution(code, context=_context("official"))["code"] == code


def test_08_no_request_model_accepts_role_or_permissions() -> None:
    """حرس ساكن: لا نموذج طلب في هذا النطاق يقبل دورًا ولا صلاحية ولا مستأجرًا.

    ثغرة R6 كانت أن المُستدعي يقول دوره. أُغلقت في النواة، وهذا يمنع عودتها من
    باب النطاق: لو ظهر `tenant_id` في نموذج طلب لصار المستأجر حقلًا يقوله العميل.
    """
    api_source = _strip_comments((REGISTRY_SRC / "main.py").read_text(encoding="utf-8"))
    for forbidden in ("role:", "role =", "permissions:", "tenant_id:", "tenant_id ="):
        assert forbidden not in api_source, f"نموذج الطلب يقبل '{forbidden}' من العميل"
    assert "require_context" in api_source, "النقاط لا تشتقّ سياقًا من الرمز"

    service_source = _strip_comments((REGISTRY_SRC / "service.py").read_text(encoding="utf-8"))
    assert "unverified_context" not in service_source, "الخدمة تبني سياقًا غير مُتحقَّق منه"
    for signature_fragment in ("role: str", "role=role", "permissions: list"):
        assert signature_fragment not in service_source


def test_09_domain_reuses_existing_permission_vocabulary() -> None:
    """كل صلاحية يفحصها النطاق مزروعة فعلًا في `security_roles` — لا مفردة ثالثة.

    الدَّين القائم من R6 مفردتان للأدوار. ولو اخترع هذا النطاق مفردة صلاحيات
    ثالثة لصار الدَّين ثلاثيًّا، ولكان `king` وحده يمرّ فيها لأن `*` يمرّ في كل شيء.
    """
    seeded = {permission for role in DEFAULT_ROLES for permission in role["permissions"]}
    unknown = [permission for permission in DOMAIN_PERMISSIONS if permission not in seeded]
    assert unknown == [], f"صلاحيات مُختَرعة لا وجود لها في الأدوار المزروعة: {unknown}"


# ── 3. حدّ المستأجر ────────────────────────────────────────────────────────


def test_10_tenant_boundary_denies_cross_tenant_read(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """مؤسسة المستأجر «أ» غير مرئيّة لسياق المستأجر «ب»."""
    code = _code()
    tenant_a = _context("king", tenant_id="tenant-a", username="a")
    tenant_b = _context("king", tenant_id="tenant-b", username="b")
    registry.register_institution(
        context=tenant_a, code=code, name="وزارة أ", kind="ministry", branch="executive"
    )

    assert registry.get_institution(code, context=tenant_a)["tenant_id"] == "tenant-a"
    with pytest.raises(InstitutionNotFoundError):
        registry.get_institution(code, context=tenant_b)
    assert [row["code"] for row in registry.list_institutions(context=tenant_b)] == []


def test_11_federal_tenant_crosses_and_says_so(
    registry: StateRegistry,
) -> None:
    """العبور محصور بـ`federal`، وهو نفسه لا يُنال إلا من جلسة أو رمز موقَّع."""
    code = _code()
    tenant_a = _context("king", tenant_id="tenant-a", username="a")
    federal = _context("king", tenant_id="federal", username="fed")
    registry.register_institution(
        context=tenant_a, code=code, name="وزارة أ", kind="ministry", branch="executive"
    )
    # `federal` يعبر بحكم `tenant_matches`، لكن السرد مُقيَّد بمستأجر السياق نفسه،
    # فلا يظهر صفّ «أ» في سرده — وهذا حدٌّ يُقال لا يُخفى.
    assert registry.list_institutions(context=federal) == []


def test_12_appointment_across_tenants_is_denied(registry: StateRegistry) -> None:
    """تقليد وكيلٍ من مستأجر آخر يُرفَض بحدّ المستأجر نفسه لا بفحص موازٍ."""
    tenant_a = _context("king", tenant_id="tenant-a", username="a")
    code = _code()
    registry.register_institution(
        context=tenant_a, code=code, name="وزارة أ", kind="ministry", branch="executive"
    )
    foreign_agent = _agent(tenant_id="tenant-b")
    with pytest.raises(TenantIsolationError):
        registry.appoint_official(
            context=tenant_a, agent_id=foreign_agent, institution_code=code, title="مدير"
        )


# ── 4. الأثر: تدقيق وحدث دائم لكل كتابة ───────────────────────────────────


def test_13_every_write_leaves_audit_and_durable_event(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """التأسيس والإدارة والتقليد والعزل: أربع كتابات، أربعة آثار مُتتبَّعة."""
    bus = get_durable_event_bus()
    audit = PersistentAuditStore()
    code = _code()

    institution = registry.register_institution(
        context=crown, code=code, name="وزارة الأثر", kind="ministry", branch="executive"
    )
    department = registry.create_department(
        context=crown, institution_code=code, code="D-OPS", name="إدارة التشغيل"
    )
    agent_id = _agent()
    official = registry.appoint_official(
        context=crown,
        agent_id=agent_id,
        institution_code=code,
        title="مدير التشغيل",
        department_code="D-OPS",
        is_head=True,
    )
    revoked = registry.revoke_official(
        context=crown, official_id=official["id"], reason="إعادة تنظيم في اختبار R7"
    )

    for record in (institution, department, official, revoked):
        assert record["audit_id"], "كتابة بلا سجلّ تدقيق"
        assert record["event_id"], "كتابة بلا حدث دائم"

    # الحدث يُتتبَّع إلى الكيان والفاعل والارتباط — لا حدثًا مجهول النسب.
    published = {
        subject: bus.get_events(subject=subject, limit=10)
        for subject in (
            EVENT_INSTITUTION_REGISTERED,
            EVENT_DEPARTMENT_CREATED,
            EVENT_OFFICIAL_APPOINTED,
            EVENT_OFFICIAL_REVOKED,
        )
    }
    for subject, events in published.items():
        assert events, f"لا حدث منشور على '{subject}'"
        latest = events[0]
        assert latest["correlation_id"] == crown.correlation_id
        assert latest["data"]["actor"] == crown.principal_id
        assert latest["data"]["audit_id"]

    # وسلسلة التدقيق تحمل الفعل نفسه بفاعله. (السلسلة تراكمية عبر الاختبارات،
    # فالمطلوب وجود أثرٍ لهذا الفاعل بعينه لا أن يكون آخر أثرٍ له.)
    entries = audit.list_all(limit=200)
    for action in (
        "registry.institution.register",
        "registry.department.create",
        "registry.official.appoint",
        "registry.official.revoke",
    ):
        matching = [
            entry
            for entry in entries
            if entry["action"] == action and entry["actor"] == crown.principal_id
        ]
        assert matching, f"لا أثر تدقيق للفعل '{action}' بفاعله '{crown.principal_id}'"
        assert matching[0]["details"]["role"] == "king"


def test_14_all_registry_events_have_contracts() -> None:
    """كل حدث نطاق له عقد مُسجَّل — لا حدثًا يُنشَر ويُسجِّل الناقل مخالفته."""
    from amos_federation.common.event_bus import validate_event

    for subject in REGISTRY_EVENTS:
        valid, message = validate_event(
            subject,
            {
                "institution_id": "inst-x",
                "department_id": "dept-x",
                "official_id": "offl-x",
                "agent_id": "agent-x",
                "code": "C",
                "kind": "ministry",
                "from_status": "active",
                "to_status": "suspended",
                "reason": "سبب",
                "actor": "tester",
            },
        )
        assert valid, f"{subject}: {message}"


# ── 5. قواعد النطاق ──────────────────────────────────────────────────────


def test_15_official_must_be_an_existing_agent(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """المسؤول وكيلٌ مُقلَّد — ولا هوية تُختَرع في السجل."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة الهوية", kind="ministry", branch="executive"
    )
    with pytest.raises(UnknownAgentError):
        registry.appoint_official(
            context=crown, agent_id="agent-ghost-r7", institution_code=code, title="مدير وهمي"
        )


def test_16_one_head_per_department(registry: StateRegistry, crown: AuthorizationContext) -> None:
    """رئيسٌ واحد لكل إدارة — مفروضٌ في الخدمة، ويُقال إنه ليس قيدًا في المخطَّط."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة الرئاسة", kind="ministry", branch="executive"
    )
    registry.create_department(
        context=crown, institution_code=code, code="D-HEAD", name="إدارة برئيس"
    )
    first = registry.appoint_official(
        context=crown,
        agent_id=_agent(),
        institution_code=code,
        title="الرئيس الأول",
        department_code="D-HEAD",
        is_head=True,
    )
    with pytest.raises(DepartmentHeadConflictError):
        registry.appoint_official(
            context=crown,
            agent_id=_agent(),
            institution_code=code,
            title="الرئيس الثاني",
            department_code="D-HEAD",
            is_head=True,
        )
    # وبعد العزل تُتاح الرئاسة لغيره — العزل يُفرِج الموضع ولا يمحو أثره.
    registry.revoke_official(context=crown, official_id=first["id"], reason="نقل")
    second = registry.appoint_official(
        context=crown,
        agent_id=_agent(),
        institution_code=code,
        title="الرئيس الثاني",
        department_code="D-HEAD",
        is_head=True,
    )
    assert second["is_head"] is True
    revoked_rows = registry.list_officials(
        context=crown, institution_code=code, include_revoked=True
    )
    assert any(row["id"] == first["id"] and row["status"] == "revoked" for row in revoked_rows)


def test_17_head_requires_a_department(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """لا رئيس بلا إدارة."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة بلا إدارات", kind="ministry", branch="executive"
    )
    with pytest.raises(RegistryError):
        registry.appoint_official(
            context=crown,
            agent_id=_agent(),
            institution_code=code,
            title="رئيس معلّق",
            is_head=True,
        )


def test_18_duplicate_codes_are_rejected(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """رمز المؤسسة فريد في المستأجر، ورمز الإدارة فريد في مؤسستها."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة الرمز", kind="ministry", branch="executive"
    )
    with pytest.raises(DuplicateCodeError):
        registry.register_institution(
            context=crown, code=code, name="وزارة مكرّرة", kind="authority", branch="executive"
        )
    registry.create_department(context=crown, institution_code=code, code="D1", name="إدارة")
    with pytest.raises(DuplicateCodeError):
        registry.create_department(
            context=crown, institution_code=code, code="D1", name="إدارة مكرّرة"
        )


def test_19_suspended_institution_accepts_nothing_new(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """المؤسسة الموقوفة لا تُنشئ إدارة ولا تُقلِّد مسؤولًا."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة تُوقَف", kind="ministry", branch="executive"
    )
    changed = registry.set_institution_status(
        context=crown, code=code, status="suspended", reason="تحقيق في اختبار R7"
    )
    assert changed["from_status"] == "active"
    assert changed["status"] == "suspended"
    with pytest.raises(InstitutionInactiveError):
        registry.create_department(context=crown, institution_code=code, code="D2", name="إدارة")
    with pytest.raises(InstitutionInactiveError):
        registry.appoint_official(
            context=crown, agent_id=_agent(), institution_code=code, title="مدير"
        )


def test_20_dissolution_is_refused_while_the_institution_is_alive(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """لا يُحلّ ما تحته إدارة نشطة أو مسؤول مُقلَّد — ولا تُحذَف صفوفٌ تابعة صامتة."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة تُحلّ", kind="ministry", branch="executive"
    )
    registry.create_department(context=crown, institution_code=code, code="D-X", name="إدارة قائمة")
    official = registry.appoint_official(
        context=crown,
        agent_id=_agent(),
        institution_code=code,
        title="مدير",
        department_code="D-X",
    )
    with pytest.raises(InstitutionNotEmptyError):
        registry.set_institution_status(
            context=crown, code=code, status="dissolved", reason="حلّ مرفوض"
        )

    registry.revoke_official(context=crown, official_id=official["id"], reason="حلّ الوزارة")
    session = get_session_factory()()
    try:
        row = session.query(DepartmentModel).filter(DepartmentModel.code == "D-X").first()
        row.status = "closed"
        session.commit()
    finally:
        session.close()

    dissolved = registry.set_institution_status(
        context=crown, code=code, status="dissolved", reason="حلّ بعد إخلاء"
    )
    assert dissolved["status"] == "dissolved"
    # والمحلولة لا تُحيا في هذا المسار — والقول صريح لا صامت.
    with pytest.raises(RegistryError):
        registry.set_institution_status(
            context=crown, code=code, status="active", reason="محاولة إحياء"
        )


def test_21_parent_institution_is_a_real_reference(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """التبعية المؤسسية صفٌّ يشير إلى صفّ، لا نصٌّ في وصف."""
    parent_code, child_code = _code("COUNCIL"), _code("MIN")
    parent = registry.register_institution(
        context=crown, code=parent_code, name="مجلس أعلى", kind="council", branch="executive"
    )
    child = registry.register_institution(
        context=crown,
        code=child_code,
        name="وزارة تابعة",
        kind="ministry",
        branch="executive",
        parent_code=parent_code,
    )
    assert child["parent_institution_id"] == parent["id"]
    with pytest.raises(InstitutionNotFoundError):
        registry.register_institution(
            context=crown,
            code=_code(),
            name="وزارة بأمّ وهمية",
            kind="ministry",
            branch="executive",
            parent_code="GHOST-PARENT",
        )


def test_22_unknown_department_code_is_refused(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """تقليد في إدارة لا وجود لها يُرفَض باسمه."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة", kind="ministry", branch="executive"
    )
    with pytest.raises(DepartmentNotFoundError):
        registry.appoint_official(
            context=crown,
            agent_id=_agent(),
            institution_code=code,
            title="مدير",
            department_code="D-GHOST",
        )


def test_23_unknown_kind_or_branch_refused_before_the_database(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """المفردة تُفحَص في الخدمة أيضًا — برسالة مفهومة قبل خطأ قيدٍ خام."""
    with pytest.raises(RegistryError, match="نوع مؤسسة"):
        registry.register_institution(
            context=crown, code=_code(), name="كيان", kind="wizardry", branch="executive"
        )
    with pytest.raises(RegistryError, match="فرع"):
        registry.register_institution(
            context=crown, code=_code(), name="كيان", kind="ministry", branch="wonderland"
        )
    assert set(INSTITUTION_KINDS) >= {"ministry", "court", "bank", "university"}
    assert set(INSTITUTION_BRANCHES) == {"executive", "legislative", "judicial", "treasury"}


# ── 6. المُخطَّط والإحصاء ──────────────────────────────────────────────────


def test_24_institution_chart_is_built_from_rows(
    registry: StateRegistry, crown: AuthorizationContext
) -> None:
    """المُخطَّط تجميعٌ لصفوف موجودة، لا شكلٌ مُصطنَع."""
    code = _code()
    registry.register_institution(
        context=crown, code=code, name="وزارة المُخطَّط", kind="ministry", branch="executive"
    )
    registry.create_department(context=crown, institution_code=code, code="D-A", name="إدارة أ")
    registry.create_department(context=crown, institution_code=code, code="D-B", name="إدارة ب")
    registry.appoint_official(
        context=crown,
        agent_id=_agent(),
        institution_code=code,
        title="مدير أ",
        department_code="D-A",
        is_head=True,
    )
    unassigned_agent = _agent()
    registry.appoint_official(
        context=crown, agent_id=unassigned_agent, institution_code=code, title="مستشار"
    )

    chart = registry.institution_chart(code, context=crown)
    assert chart["institution"]["code"] == code
    assert [d["code"] for d in chart["departments"]] == ["D-A", "D-B"]
    head = chart["departments"][0]["officials"]
    assert len(head) == 1 and head[0]["is_head"] is True
    assert chart["departments"][1]["officials"] == []
    assert [o["agent_id"] for o in chart["unassigned_officials"]] == [unassigned_agent]


def test_25_registry_health_counts_rows_not_guesses(
    registry: StateRegistry,
) -> None:
    """الإحصاء من القاعدة — وفي مستأجر معزول ليكون الرقم قابلًا للتأكيد."""
    tenant = _context("king", tenant_id=f"tenant-{uuid.uuid4().hex[:8]}", username="health")
    before = registry.registry_health(context=tenant)
    assert before["institutions"] == 0
    code = _code()
    registry.register_institution(
        context=tenant, code=code, name="وزارة الإحصاء", kind="ministry", branch="executive"
    )
    registry.create_department(context=tenant, institution_code=code, code="D-1", name="إدارة")
    after = registry.registry_health(context=tenant)
    assert after["institutions"] == 1
    assert after["institutions_by_status"]["active"] == 1
    assert after["departments"] == 1 and after["departments_active"] == 1
    assert after["officials"] == 0


# ── 7. الخدمة مُسجَّلة ─────────────────────────────────────────────────────


def test_26_service_is_registered_and_serves_health() -> None:
    """الخدمة في سجلّ الخدمات وتُقلع فعلًا — لا مجلَّدًا بلا تطبيق."""
    from fastapi.testclient import TestClient

    from amos_federation.services.state_registry.main import app

    assert SERVICES["state-registry"]["port"] == 8010
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "healthy", "service": "state-registry"}
    # ونقطة نطاق بلا رمز تُرفَض 401/403 — لا تُجيب بمحتوى.
    assert client.get("/registry/institutions").status_code in (401, 403)
