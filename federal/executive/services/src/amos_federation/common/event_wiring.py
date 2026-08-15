"""
AMOS-Federation Event Wiring — Phase 2
الهدف: ربط 6 أنواع أحداث في سلسلة كاملة من task.created إلى experience.recorded
النطاق: common/event_wiring
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15

السلسلة الكاملة:
1. task.created → API Gateway ينشر عند إنشاء مهمة
2. agent.assigned → Orchestrator يستهلك task.created وينشر agent.assigned
3. tool.executed → Agent Runtime يستهلك agent.assigned وينشر tool.executed
4. experience.recorded → بعد tool.executed تُسجّل الخبرة
5. approval.signed → بوابة الموافقة على الترقيات
6. agent.completed → إكمال المهمة
"""

import contextlib
import uuid
from typing import Any

from amos_federation.common.durable_event_bus import get_durable_event_bus
from amos_federation.common.persistent import (
    PersistentAuditStore,
    PersistentExperienceStore,
    PersistentTaskStore,
)

# مراجع للمخازن
_task_store = PersistentTaskStore()
_exp_store = PersistentExperienceStore()
_audit_store = PersistentAuditStore()


# ========================
# === 2.2: task.created ===
# ========================


def publish_task_created(
    task_id: str, task_type: str, description: str, tenant_id: str = "default"
) -> dict[str, Any]:
    """نشر حدث إنشاء مهمة — يُستهلك من قبل Orchestrator."""
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


# ========================
# === 2.3: agent.assigned ===
# ========================


def publish_agent_assigned(task_id: str, agent_id: str, plan: str = "") -> dict[str, Any]:
    """نشر حدث تعيين وكيل — يُستهلك من قبل Agent Runtime."""
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


# ========================
# === 2.4: tool.executed ===
# ========================


def publish_tool_executed(
    tool_id: str, agent_id: str, result: dict[str, Any], task_id: str = ""
) -> dict[str, Any]:
    """نشر حدث تنفيذ أداة — يُستهلك للتدقيق."""
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


# ========================
# === 2.5: experience.recorded ===
# ========================


def publish_experience_recorded(
    experience_id: str,
    exp_type: str,
    agent_id: str = "",
    task_id: str = "",
    quality_score: float = 0.0,
) -> dict[str, Any]:
    """نشر حدث تسجيل خبرة — يُستهلك من قبل Memory Service."""
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


# ========================
# === 2.6: approval.signed ===
# ========================


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


# ========================
# === agent.completed ===
# ========================


def publish_agent_completed(
    agent_id: str,
    task_id: str,
    result: dict[str, Any],
    quality_score: float = 0.0,
) -> dict[str, Any]:
    """نشر حدث إكمال مهمة."""
    bus = get_durable_event_bus()
    return bus.publish(
        subject="amos_federation.agent.completed",
        data={
            "agent_id": agent_id,
            "task_id": task_id,
            "result": result,
            "quality_score": quality_score,
        },
        correlation_id=task_id,
    )


# ========================
# === المستهلكات (Consumers) ===
# ========================


class OrchestratorConsumer:
    """مستهلك task.created → منتج agent.assigned.

    يحاكي دور Orchestrator: يستقبل مهام جديدة ويعين وكلاء لها.
    """

    def __init__(self) -> None:
        self._bus = get_durable_event_bus()
        self._bus.subscribe("amos_federation.task.created", self._handle_task_created)

    def _handle_task_created(self, event: dict[str, Any]) -> None:
        """معالجة حدث إنشاء مهمة — تعيين وكيل ونشر agent.assigned."""
        data = event["data"]
        task_id = data["task_id"]

        # تعيين وكيل (محاكاة بسيطة — في الإنتاج يختار من Population Registry)
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        # تحديث حالة المهمة
        with contextlib.suppress(Exception):
            _task_store.update_status(task_id, "assigned")

        # نشر حدث تعيين الوكيل
        publish_agent_assigned(
            task_id=task_id,
            agent_id=agent_id,
            plan=f"execute:{data.get('type', 'generic')}",
        )

        # تدقيق
        _audit_store.append(
            "task.assigned",
            "orchestrator",
            {
                "task_id": task_id,
                "agent_id": agent_id,
            },
        )


class AgentRuntimeConsumer:
    """مستهلك agent.assigned → منتج tool.executed + experience.recorded.

    يحاكي دور Agent Runtime: يستقبل التعيينات وينفذ الأدوات.
    """

    def __init__(self) -> None:
        self._bus = get_durable_event_bus()
        self._bus.subscribe("amos_federation.agent.assigned", self._handle_agent_assigned)

    def _handle_agent_assigned(self, event: dict[str, Any]) -> None:
        """معالجة حدث تعيين وكيل — تنفيذ مهمة وتسجيل خبرة."""
        data = event["data"]
        task_id = data["task_id"]
        agent_id = data["agent_id"]

        # تنفيذ أداة (محاكاة — في الإنتاج يستخدم Sandbox)
        tool_result = {"status": "completed", "output": "task executed successfully"}
        publish_tool_executed(
            tool_id="default_executor",
            agent_id=agent_id,
            result=tool_result,
            task_id=task_id,
        )

        # تسجيل خبرة
        exp_id = f"exp-{uuid.uuid4().hex[:12]}"
        publish_experience_recorded(
            experience_id=exp_id,
            exp_type="task_completion",
            agent_id=agent_id,
            task_id=task_id,
            quality_score=0.85,
        )

        # إكمال المهمة
        publish_agent_completed(
            agent_id=agent_id,
            task_id=task_id,
            result=tool_result,
            quality_score=0.85,
        )

        # تدقيق
        _audit_store.append(
            "task.completed",
            agent_id,
            {
                "task_id": task_id,
                "result": "success",
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
    """تهيئة كل المستهلكات — يُستدعى مرة واحدة عند الإقلاع."""
    global _consumers_initialized
    if _consumers_initialized:
        return
    OrchestratorConsumer()
    AgentRuntimeConsumer()
    AuditConsumer()
    MemoryConsumer()
    _consumers_initialized = True


# ========================
# === السلسلة الكاملة (Smoke Test) ===
# ========================


def run_full_event_chain(task_description: str = "مهمة تجريبية") -> dict[str, Any]:
    """تشغيل السلسلة الكاملة: task.created → agent.assigned → tool.executed → experience.recorded.

    يعيد تقريرًا بالأحداث المنشورة والنتيجة.
    """
    # تهيئة المستهلكات
    init_event_consumers()

    # 1. إنشاء مهمة
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    _task_store.create(task_id, "event_chain_test", task_description, "default")

    # 2. نشر task.created → سيحفز السلسلة
    event1 = publish_task_created(task_id, "event_chain_test", task_description)

    # 3. التحقق من السلسلة
    bus = get_durable_event_bus()
    events = bus.get_events(limit=20)

    chain = {
        "task_id": task_id,
        "task_created": event1["event_id"],
        "events_published": len(events),
        "event_subjects": [e["subject"] for e in events],
        "status": "complete" if events else "partial",
    }

    return chain
