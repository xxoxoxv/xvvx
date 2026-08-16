"""
AMOS-Federation Event Wiring — إسقاط دورة الحياة القانونية على أحداث النطاق
الهدف: ناشرو أحداث النطاق ومُسقِط واحد يقرأ انتقالات النواة التنفيذية
النطاق: common/event_wiring
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16 (R2)

ما كانت هذه الوحدة قبل R2، بالقياس لا بالوصف:

    سلسلة **دورة حياة ثانية**. `OrchestratorConsumer` كان يستهلك
    `task.created` ثم يخترع `agent-<uuid>` ويكتب `update_status(task_id,
    "assigned")` مباشرةً في جدول المهام — حالة ليست في آلة الحالات، وكتابة بلا
    إذن سيادي ولا انتقال ذرّي. و`AgentRuntimeConsumer` كان «ينفّذ» فيُصدر
    `tool.executed` بنتيجة ثابتة و`experience.recorded` بـ`quality_score=0.85`
    مُختلَقة، ثم يُعلن `agent.completed`. أي أن مهمّة يمكن أن «تكتمل» في
    الأحداث ولم يقع تنفيذ، ولم تُسأل البوابة السيادية. و`run_full_event_chain`
    كان يُنشئ صفّ مهمّة بنفسه (`_task_store.create`).

بعد R2:

- **لا كتابة حالة هنا إطلاقًا.** لا `create` ولا `update_status`؛ الوحدة لا
  تستورد مخزن المهام. تحريك دورة الحياة بيد `executive_core.engine` وحدها.
- المُستهلك الوحيد لدورة الحياة هو `CanonicalLifecycleProjector`: يقرأ حدث
  الانتقال الدائم الذي تُصدره النواة، ويُسقطه على أحداث النطاق القديمة
  (`agent.assigned` عند `dispatched`، و`agent.completed` عند `completed`)
  بمعطيات **مقروءة من الانتقال نفسه** لا مُخترعة.
- ما لا يُسقَط بقصد: `tool.executed` و`experience.recorded`. النواة لا تُصدر
  حدثًا لكل أداة، والخبرة تحتاج حكمًا على الجودة — واختلاق أيٍّ منهما كذب.
  هذه حدود مُعلَنة (PARTIAL) لا فراغ مُخفى.
- ناشرو الأحداث (`publish_*`) باقون كما هم: هم واجهة النشر على الناقل الدائم
  الموجود، ولم يُنشأ ناقل ثانٍ.
"""

import contextlib
from typing import Any

from amos_federation.common.durable_event_bus import get_durable_event_bus
from amos_federation.common.persistent import (
    PersistentAuditStore,
    PersistentExperienceStore,
)

# مراجع للمخازن — تدقيق وخبرات فقط. لا مخزن مهام: هذه الوحدة لا تكتب حالة مهمّة.
_exp_store = PersistentExperienceStore()
_audit_store = PersistentAuditStore()


def _transition_subject() -> str:
    """موضوع حدث الانتقال كما تُعلنه النواة — لا يُكرَّر نصُّه هنا.

    الاستيراد متأخّر بقصد: `common` طبقة تحت `services`، فلا تستوردها عند
    التحميل. المُسقِط يسأل النواة عن موضوعها لحظة التسجيل.
    """
    from amos_federation.services.executive_core.engine import TRANSITION_SUBJECT

    return TRANSITION_SUBJECT


# ========================
# === ناشرو أحداث النطاق ===
# ========================


def publish_task_created(
    task_id: str, task_type: str, description: str, tenant_id: str = "default"
) -> dict[str, Any]:
    """نشر حدث إنشاء مهمة — إعلان لا يُغيّر حالة."""
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.task.created",
        data={
            "task_id": task_id,
            "type": task_type,
            "description": description,
            "tenant_id": tenant_id,
        },
        correlation_id=task_id,
    )


def publish_agent_assigned(task_id: str, agent_id: str, plan: str = "") -> dict[str, Any]:
    """نشر حدث تعيين وكيل — يُسقَط من انتقال `dispatched` القانوني."""
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.agent.assigned",
        data={
            "task_id": task_id,
            "agent_id": agent_id,
            "plan": plan,
        },
        correlation_id=task_id,
        causation_id=task_id,
    )


def publish_tool_executed(
    tool_id: str, agent_id: str, result: dict[str, Any], task_id: str = ""
) -> dict[str, Any]:
    """نشر حدث تنفيذ أداة — يُستدعى من يملك نتيجة أداة حقيقية، ولا يُسقَط تلقائيًّا."""
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.tool.executed",
        data={
            "tool_id": tool_id,
            "agent_id": agent_id,
            "result": result,
            "task_id": task_id,
        },
        correlation_id=task_id or agent_id,
    )


def publish_experience_recorded(
    experience_id: str,
    exp_type: str,
    agent_id: str = "",
    task_id: str = "",
    quality_score: float = 0.0,
) -> dict[str, Any]:
    """نشر حدث تسجيل خبرة — الدرجة تأتي من مُقيّم حقيقي، لا من هذه الوحدة."""
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.experience.recorded",
        data={
            "experience_id": experience_id,
            "type": exp_type,
            "agent_id": agent_id,
            "task_id": task_id,
            "quality_score": quality_score,
        },
        correlation_id=task_id or experience_id,
    )


def publish_approval_signed(
    approval_id: str,
    decision: str,
    model_id: str = "",
    signed_by: str = "king",
) -> dict[str, Any]:
    """نشر حدث موافقة موقّعة — يُستهلك لبوابات الترقية."""
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.approval.signed",
        data={
            "approval_id": approval_id,
            "decision": decision,
            "model_id": model_id,
            "signed_by": signed_by,
        },
        correlation_id=approval_id,
    )


def publish_agent_completed(
    agent_id: str,
    task_id: str,
    result: dict[str, Any],
    quality_score: float | None = None,
) -> dict[str, Any]:
    """نشر حدث إكمال مهمة — تُحذف الدرجة إن لم يُقدّمها مُقيّم، ولا تُخترع صفرًا دالًّا."""
    data: dict[str, Any] = {
        "agent_id": agent_id,
        "task_id": task_id,
        "result": result,
    }
    if quality_score is not None:
        data["quality_score"] = quality_score
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.agent.completed",
        data=data,
        correlation_id=task_id,
    )


# ========================
# === المُسقِط والمستهلكات ===
# ========================


class CanonicalLifecycleProjector:
    """يقرأ انتقالات النواة التنفيذية ويُسقطها على أحداث النطاق القديمة.

    مُسقِط لا مُنفِّذ: لا يعيّن وكيلًا، ولا يُنفّذ أداة، ولا يكتب حالة. كل قيمة
    يُصدرها مقروءة من حمولة الانتقال الذي أصدرته النواة بعد إذن سيادي.
    """

    CONSUMER_NAME = "legacy_domain_projection"

    def __init__(self) -> None:
        self._bus = get_durable_event_bus()
        self._bus.subscribe(_transition_subject(), self._handle_transition)

    def _handle_transition(self, event: dict[str, Any]) -> None:
        data = event["data"]
        to_state = data.get("to_state")
        task_id = data.get("task_id", "")
        detail = data.get("detail") or {}

        if to_state == "dispatched":
            assignment = detail.get("assignment") or {}
            agent_id = assignment.get("agent_id")
            if agent_id:
                publish_agent_assigned(task_id=task_id, agent_id=agent_id)
            return

        if to_state == "completed":
            agent_id = detail.get("agent_id")
            if agent_id:
                publish_agent_completed(
                    agent_id=agent_id,
                    task_id=task_id,
                    result={
                        "status": "completed",
                        "steps": detail.get("steps"),
                        "execution_fidelity": detail.get("execution_fidelity"),
                    },
                )


class AuditConsumer:
    """مستهلك tool.executed → تدقيق كل تنفيذ أداة."""

    def __init__(self) -> None:
        self._bus = get_durable_event_bus()
        self._bus.subscribe("amos_federation.tool.executed", self._handle_tool_executed)

    def _handle_tool_executed(self, event: dict[str, Any]) -> None:
        """تدقيق كل استدعاء أداة."""
        data = event["data"]
        _audit_store.append(
            "tool.executed",
            data.get("agent_id", "unknown"),
            {
                "tool_id": data.get("tool_id"),
                "task_id": data.get("task_id"),
                "result_status": data.get("result", {}).get("status", "unknown"),
            },
        )


class MemoryConsumer:
    """مستهلك experience.recorded → تخزين في الذاكرة."""

    def __init__(self) -> None:
        self._bus = get_durable_event_bus()
        self._bus.subscribe("amos_federation.experience.recorded", self._handle_experience)

    def _handle_experience(self, event: dict[str, Any]) -> None:
        """تخزين الخبرة في الذاكرة المؤسسية."""
        data = event["data"]
        with contextlib.suppress(Exception):
            _exp_store.record(  # قد تكون الخبرة مسجّلة بالفعل
                experience_id=data["experience_id"],
                exp_type=data.get("type", "generic"),
                agent_id=data.get("agent_id", ""),
                task_id=data.get("task_id", ""),
                quality_score=data.get("quality_score", 0.0),
            )


# ========================
# === تهيئة المستهلكات ===
# ========================

_consumers_initialized = False


def init_event_consumers() -> None:
    """تهيئة المُسقِط والمستهلكات — يُستدعى مرة واحدة عند الإقلاع."""
    global _consumers_initialized
    if _consumers_initialized:
        return
    CanonicalLifecycleProjector()
    AuditConsumer()
    MemoryConsumer()
    _consumers_initialized = True


def reset_event_consumers() -> None:
    """السماح بإعادة التهيئة — للاختبارات التي تُبدّل قاعدة البيانات."""
    global _consumers_initialized
    _consumers_initialized = False


# ========================
# === السلسلة الكاملة عبر المسار القانوني ===
# ========================


def run_full_event_chain(task_description: str = "مهمة تجريبية") -> dict[str, Any]:
    """تشغيل دورة الحياة القانونية كاملة وقراءة ما نشرته من أحداث دائمة.

    لا تُنشئ صفّ مهمّة بنفسها ولا تكتب حالة: تُسلّم الأمر إلى النواة التنفيذية
    (`submit_and_run`)، فتقع الانتقالات بإذن سيادي وتُقيَّد وتُنشَر، ثم يُسقِطها
    `CanonicalLifecycleProjector` على أحداث النطاق. النتيجة تقول الحالة النهائية
    كما هي في القاعدة — بما فيها الفشل، إن لم يوجد وكيل مؤهَّل مثلًا.
    """
    from amos_federation.services.executive_core.engine import get_executive_core

    init_event_consumers()

    outcome = get_executive_core().submit_and_run("generic", task_description)
    task_id = outcome["task"]["id"]

    bus = get_durable_event_bus()
    events = [event for event in bus.get_events(limit=200) if event["correlation_id"] == task_id]

    return {
        "task_id": task_id,
        "final_state": outcome["final_state"],
        "terminal": outcome["terminal"],
        "transitions": len(outcome["transitions"]),
        "events_published": len(events),
        "event_subjects": sorted({event["subject"] for event in events}),
        "status": "complete" if outcome["terminal"] else "partial",
    }
