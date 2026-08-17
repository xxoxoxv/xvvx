"""الهدف: مصدر حقيقة واحد لهوية الوكيل — وسكّان النظام كإسقاط عنه.

النطاق: federal/executive/services — النواة التنفيذية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

حقائق مقيسة قبل هذه الوحدة (R4-A):

- كان هناك **سجلّان** يُنشئان هوية وكيل ويحفظانها:
  1. جدول `agents` عبر `AgentModel` في `common/database.py`، يُكتب فقط من
     `dispatcher.register_agent`، ويُقرأ من `CapabilityDispatcher.candidates /
     available_agents / select / assignment_for` — أي أن مسار التنفيذ الفعلي
     (Dispatcher → Runtime Gateway، R1–R3) لا يعرف غيره.
  2. جدول `agent_population` في `agent_runtime/population.py`، بمحرِّك
     SQLAlchemy وقاعدة تعريف (`PopulationBase`) خاصّين به، يولّد `agent_id`
     بنفسه ولا يشارك المعرّف مع `agents`. ويُقرأ من: `health.py`،
     `control_console/main.py`، `governance/expansion.py`،
     `governance/federation.py`، `governance/treasury.py`، و SQL خام في
     `royal/main.py`.
- النتيجة المقيسة: هويّتان لنفس الوكيل، دورتا حياة مختلفتان (`agents.status`
  مقابل `agent_population.state`)، وعدّادان مختلفان للسكّان.
- لا توجد أي `ForeignKey` في المستودع تشير إلى أيّ من الجدولين (`grep
  "ForeignKey(" federal/` = صفر نتائج)، فالتوحيد لا يكسر قيودًا مرجعية.

**القرار (R4-B) مبنيّ على البنية الموجودة لا على تفضيل شكلي:** الجدول
`agents` هو المصدر الكانوني لهوية الوكيل، لأنه:

1. الجدول الوحيد الذي يقرأه مسار التنفيذ المعتمد (توزيع → تعيين → تشغيل).
2. يسكن نفس `get_session_factory()` الذي تسكنه `tasks`، فقراءة الهوية لحظة
   التنفيذ تجري على نفس المحرِّك لا على محرِّك ثانٍ.
3. يحفظ الصلاحيات والأدوات في أعمدة `JSON` مكتوبة، لا نصًّا يُفكّ يدويًّا.

و`agent_population` **ليس** سجل هوية ثانيًا بعد R4: صار جدول **ملفّ تدريبي
وإسقاط للقراءة** (category، school_score، specialization، tokens_used،
graduated_at) مفتاحه هو نفس `agent_id` الكانوني. أعمدته المكرّرة (name، role،
permissions، allowed_tools، state) تبقى مكتوبة كـ **مرآة توافُقية مهجورة
(deprecated mirror)** لقرّاء خارج هذا المستودع، ولا يُقرأ منها شيء هنا.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from amos_federation.common.database import AgentModel, get_session_factory
from amos_federation.services.executive_core.dispatcher import EMPLOYABLE_STATUSES

#: اسم الجدول الكانوني للهوية.
CANONICAL_IDENTITY_TABLE = "agents"

#: جدول صار إسقاطًا وملفًّا تدريبيًّا — ليس مصدر هوية.
PROJECTION_TABLE = "agent_population"

#: قيمة تُكتب حين لا تتوفّر المعلومة — لا تُختلق.
UNKNOWN = "UNKNOWN"

#: تصنيف أمانة الإسقاط السكّاني: مبنيّ على السجل الكانوني فعلًا.
POPULATION_FIDELITY = "REAL"

#: نشاط التشغيل (executing/failed) يُقرأ من أحداث دورة الحياة المسجَّلة في R3.
RUNTIME_ACTIVITY_SUBJECT = "amos_federation.executive.agent_lifecycle"


class AgentLifecycleState(StrEnum):
    """دورة حياة الوكيل — حقل واحد كانوني: `agents.status`.

    القيم تجمع ما كان موزَّعًا بين `agents.status` و`agent_population.state`
    قبل R4، حتى لا تبقى دورتا حياة لنفس الوكيل.
    """

    REGISTERED = "registered"
    TRAINING = "training"
    TESTING = "testing"
    SPECIALIZED = "specialized"
    EMPLOYED = "employed"
    ACTIVE = "active"
    PROMOTED = "promoted"
    READY = "ready"
    PAUSED = "paused"
    RETIRED = "retired"


#: الحالات التي تُحتسب «خارج الخدمة» في الإسقاط السكّاني.
OUT_OF_SERVICE_STATES = frozenset(
    {AgentLifecycleState.PAUSED.value, AgentLifecycleState.RETIRED.value}
)


class DuplicateAgentIdentityError(RuntimeError):
    """محاولة إنشاء هوية بمعرّف موجود — الهوية لا تُنشأ مرّتين."""


class UnknownAgentIdentityError(RuntimeError):
    """لا هوية كانونية بهذا المعرّف — لا يُخترَع وكيل."""


@dataclass(frozen=True)
class AgentIdentity:
    """الهوية الكانونية كما هي في `agents` الآن."""

    agent_id: str
    name: str
    role: str
    lifecycle_state: str
    permissions: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    token_budget: int
    tenant_id: str
    created_at: str | None = None

    @property
    def employable(self) -> bool:
        """هل الحالة تسمح بالتوزيع فعلًا؟ نفس مجموعة الموزِّع لا مجموعة موازية."""
        return self.lifecycle_state in EMPLOYABLE_STATUSES

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "lifecycle_state": self.lifecycle_state,
            "permissions": list(self.permissions),
            "allowed_tools": list(self.allowed_tools),
            "token_budget": self.token_budget,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "identity_source": CANONICAL_IDENTITY_TABLE,
        }


def new_agent_id() -> str:
    """معرّف مستقرّ لا يُشتقّ من الاسم — الاسم ليس هوية."""
    return f"agent-{uuid.uuid4().hex[:8]}"


def _to_identity(row: AgentModel) -> AgentIdentity:
    return AgentIdentity(
        agent_id=row.id,
        name=row.name,
        role=row.role,
        lifecycle_state=row.status or AgentLifecycleState.REGISTERED.value,
        permissions=tuple(row.permissions or []),
        allowed_tools=tuple(row.allowed_tools or []),
        token_budget=int(row.token_budget or 0),
        tenant_id=row.tenant_id or "default",
        created_at=row.created_at.isoformat() if row.created_at else None,
    )


def get_identity(agent_id: str, *, tenant_id: str | None = None) -> AgentIdentity | None:
    """قراءة الهوية الكانونية — `None` إن لم تكن مُسجَّلة."""
    session = get_session_factory()()
    try:
        query = session.query(AgentModel).filter(AgentModel.id == agent_id)
        if tenant_id is not None:
            query = query.filter(AgentModel.tenant_id == tenant_id)
        row = query.first()
        return _to_identity(row) if row else None
    finally:
        session.close()


def require_identity(agent_id: str, *, tenant_id: str | None = None) -> AgentIdentity:
    """قراءة الهوية أو سقوط صريح — لا وكيل مُختلَق."""
    identity = get_identity(agent_id, tenant_id=tenant_id)
    if identity is None:
        raise UnknownAgentIdentityError(f"لا هوية كانونية بهذا المعرّف: {agent_id}")
    return identity


def list_identities(
    *,
    lifecycle_state: str | None = None,
    tenant_id: str | None = None,
) -> list[AgentIdentity]:
    """كل الهويات الكانونية (بترتيب الإنشاء)."""
    session = get_session_factory()()
    try:
        query = session.query(AgentModel)
        if lifecycle_state:
            query = query.filter(AgentModel.status == lifecycle_state)
        if tenant_id is not None:
            query = query.filter(AgentModel.tenant_id == tenant_id)
        return [_to_identity(row) for row in query.order_by(AgentModel.created_at.asc()).all()]
    finally:
        session.close()


def register_identity(
    agent_id: str,
    name: str,
    role: str,
    *,
    permissions: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    lifecycle_state: str = AgentLifecycleState.REGISTERED.value,
    token_budget: int = 10_000,
    tenant_id: str = "default",
) -> AgentIdentity:
    """إنشاء هوية كانونية جديدة — ترفض التكرار.

    Raises:
        DuplicateAgentIdentityError: المعرّف مُستخدَم فعلًا. التحديث يجري عبر
            `update_identity` صراحةً، لا عبر «تسجيل» صامت يمسح ما قبله.
    """
    session = get_session_factory()()
    try:
        existing = session.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if existing is not None:
            raise DuplicateAgentIdentityError(f"هوية موجودة فعلًا بهذا المعرّف: {agent_id}")
        session.add(
            AgentModel(
                id=agent_id,
                name=name,
                role=role,
                status=lifecycle_state,
                permissions=permissions or [],
                allowed_tools=allowed_tools or [],
                token_budget=token_budget,
                tenant_id=tenant_id,
            )
        )
        session.commit()
    finally:
        session.close()
    return require_identity(agent_id, tenant_id=tenant_id)


def update_identity(
    agent_id: str,
    *,
    name: str | None = None,
    role: str | None = None,
    permissions: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    token_budget: int | None = None,
) -> AgentIdentity:
    """تعديل صريح لهوية قائمة — لا يُنشئ هوية جديدة."""
    session = get_session_factory()()
    try:
        row = session.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if row is None:
            raise UnknownAgentIdentityError(f"لا هوية كانونية بهذا المعرّف: {agent_id}")
        if name is not None:
            row.name = name
        if role is not None:
            row.role = role
        if permissions is not None:
            row.permissions = permissions
        if allowed_tools is not None:
            row.allowed_tools = allowed_tools
        if token_budget is not None:
            row.token_budget = token_budget
        session.commit()
    finally:
        session.close()
    return require_identity(agent_id)


def set_lifecycle_state(agent_id: str, lifecycle_state: str) -> bool:
    """تغيير دورة الحياة في الحقل الكانوني الوحيد.

    Returns:
        False إن لم تكن هناك هوية كانونية بهذا المعرّف — بلا إنشاء ضمني.
    """
    session = get_session_factory()()
    try:
        row = session.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if row is None:
            return False
        row.status = lifecycle_state
        session.commit()
        return True
    finally:
        session.close()


def _runtime_activity(limit: int = 500) -> dict[str, Any]:
    """آخر طور تشغيل لكل وكيل من أحداث دورة الحياة (R3) — لا تخمين.

    إن لم تُرصَد أحداث بعد فالحقول تُعلَن `observed=False` بدل تصفيرها كأنها
    قياس. `executing`/`failed` لا تُشتقّ من `agents.status` لأن الحالة هناك
    حالة تعيين لا حالة تنفيذ لحظي.
    """
    from amos_federation.common.event_bus import get_event_bus

    events = get_event_bus().get_events(subject=RUNTIME_ACTIVITY_SUBJECT, limit=limit)
    latest: dict[str, str] = {}
    for event in events:  # الأحداث تعود من الأحدث إلى الأقدم
        data = event.get("data") or {}
        agent_id = str(data.get("agent_id", ""))
        phase = str(data.get("phase", ""))
        if agent_id and agent_id not in latest:
            latest[agent_id] = phase
    phases: dict[str, int] = {}
    for phase in latest.values():
        phases[phase] = phases.get(phase, 0) + 1
    return {
        "observed": bool(events),
        "events_scanned": len(events),
        "agents_with_activity": len(latest),
        "by_phase": phases,
        "source": RUNTIME_ACTIVITY_SUBJECT,
    }


def population_projection(*, tenant_id: str | None = None) -> dict[str, Any]:
    """سكّان النظام كإسقاط للسجل الكانوني — لا سجل هوية ثانٍ.

    ما هو مقيس فعلًا: `total` وتوزيع دورة الحياة (منها active وretired وidle
    = مُعيَّن ولا نشاط تشغيل مرصود). ما ليس مقيسًا من الهوية: `executing` و
    `failed` — يُقرآن من أحداث دورة الحياة، ويُعلَن `observed=False` إن لم
    تُسجَّل أحداث بعد. لا يُختلق رقم غير متوفّر.
    """
    identities = list_identities(tenant_id=tenant_id)
    by_state: dict[str, int] = {}
    for identity in identities:
        by_state[identity.lifecycle_state] = by_state.get(identity.lifecycle_state, 0) + 1
    activity = _runtime_activity()
    executing = activity["by_phase"].get("executing", 0)
    failed = activity["by_phase"].get("failed", 0)
    employable = sum(1 for identity in identities if identity.employable)
    return {
        "total": len(identities),
        "by_lifecycle_state": by_state,
        "active": by_state.get(AgentLifecycleState.ACTIVE.value, 0),
        "retired": by_state.get(AgentLifecycleState.RETIRED.value, 0),
        "paused": by_state.get(AgentLifecycleState.PAUSED.value, 0),
        "employable": employable,
        "idle": max(employable - executing, 0),
        "executing": executing if activity["observed"] else None,
        "failed": failed if activity["observed"] else None,
        "runtime_activity": activity,
        "identity_source": CANONICAL_IDENTITY_TABLE,
        "projection_of": CANONICAL_IDENTITY_TABLE,
        "fidelity": POPULATION_FIDELITY,
    }


def identity_health(*, tenant_id: str | None = None) -> dict[str, Any]:
    """صحّة طبقة الهوية والسكّان — مبنيّة على مكوّنات حقيقية لا على «العملية تعمل».

    تُفحَص ثلاثة مكوّنات فعليًّا: قابلية قراءة السجل الكانوني، وناقل الأحداث،
    وتناسق الإسقاط (صفوف `agent_population` بلا هوية كانونية = دَين توفيق).
    أي مكوّن غير متوفّر يُعلَن `unavailable`، ولا تُعلَن الطبقة `healthy` إلا
    إذا نجحت الفحوص الحقيقية كلها.
    """
    components: dict[str, dict[str, Any]] = {}

    try:
        identities = list_identities(tenant_id=tenant_id)
        components["canonical_registry"] = {
            "status": "available",
            "agents": len(identities),
            "table": CANONICAL_IDENTITY_TABLE,
        }
    except Exception as exc:  # noqa: BLE001 — تُعلَن كغير متوفّرة لا تُخفى
        components["canonical_registry"] = {"status": "unavailable", "error": str(exc)}

    try:
        from amos_federation.common.event_bus import get_event_bus

        components["event_bus"] = {
            "status": "available",
            "lifecycle_events": len(
                get_event_bus().get_events(subject=RUNTIME_ACTIVITY_SUBJECT, limit=1)
            ),
        }
    except Exception as exc:  # noqa: BLE001
        components["event_bus"] = {"status": "unavailable", "error": str(exc)}

    try:
        # R4 (OPTION 2): «بلا هوية كانونية» ليس خللًا بحدّ ذاته. القاعدة الحقيقية
        # تحمل 5116 صفًّا سكّانيًّا بـ24 اسمًا متميزًا، أي بذر مكرّر لا هويّات. عدّها
        # دَين توفيق كان يُثبِّت `degraded` إلى الأبد فيفقد المقياس معناه. الخلل
        # الحقيقي: صفّ **ذو دليل تاريخي** لا يراه مسار التنفيذ. والعدد الكلّي
        # يُعلَن معه ولا يُخفَى.
        from amos_federation.services.agent_runtime.population import (
            legacy_seed_profiles,
            reconciliation_debt,
            unmigrated_profiles,
        )

        orphans = unmigrated_profiles()
        debt = reconciliation_debt()
        components["population_projection"] = {
            "status": "available" if not debt else "degraded",
            "unmigrated_profile_rows": len(orphans),
            "reconciliation_debt_rows": len(debt),
            "legacy_seed_rows": len(legacy_seed_profiles()),
            "table": PROJECTION_TABLE,
        }
    except Exception as exc:  # noqa: BLE001
        components["population_projection"] = {"status": "unavailable", "error": str(exc)}

    statuses = {component["status"] for component in components.values()}
    if "unavailable" in statuses:
        overall = "unavailable"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"
    return {
        "status": overall,
        "components": components,
        "basis": "component_checks",
        "fidelity": POPULATION_FIDELITY,
    }
