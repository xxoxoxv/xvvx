"""الهدف: حدّ واحد بين النواة التنفيذية وبيئة تشغيل الوكلاء القائمة.

النطاق: federal/executive/services — النواة التنفيذية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16

المشكلة المقيسة قبل R3 — القدرة كانت تُمنَح لا تُتحقَّق:

`_dispatch_step` في المحرّك كان يبني `AgentAssignment` حقيقيًّا من جدول `agents`
(دور الوكيل وأدواته المسموحة وصلاحياته) ثم **يُلقيه**: لا يُحفَظ من التعيين إلا
`assigned_agent`. وحين يحين التنفيذ كان `_execute_step` يُعيد تلفيق تعيين آخر
هكذا:

```python
AgentAssignment(
    agent_id=agent_id,
    agent_role="worker",                       # ثابت مكتوب في الشِفرة
    permissions=(),                            # فارغة
    allowed_tools=tuple(step["tool"] for step in plan),   # ← أدوات الخطة نفسها
)
```

ثم يُبنى `WorkerAgent(permissions=list(assignment.allowed_tools))`. أي أن الوكيل
كان يُمنَح **بالضبط** الأدوات التي تطلبها الخطة، فيصير فحص `can_use_tool` في
`BaseAgent` صحيحًا دائمًا بحكم البناء: الخطة هي من تمنح صلاحيتها. فحصُ قدرةٍ
مُجابُه دائمًا «نعم» ليس فحصًا، وسجل الوكلاء لم يكن يُقرأ لحظة التنفيذ إطلاقًا —
حتى لو حُذف الوكيل من السجل أو ضُيِّقت أدواته بعد التوزيع.

ولم يكن هناك سياق تنفيذ: لا `execution_id`، ولا ربط بين نتيجة الوكيل وقرار الإذن
الذي أباحها، ولا دورة حياة معلَنة للوكيل، ولا فصل بين صدق **بيئة التشغيل** وصدق
**الأداة**. وكان `WorkerAgent` يُرجع `status: "completed"` حتى إذا تخطّى كل خطواته
لعدم الصلاحية — نجاح مُعلَن على عمل لم يقع.

ما تفرضه هذه الوحدة:

1. **قدرة مُتحقَّقة من السجل، fail-closed:** أدوات الخطة تُقارَن بأدوات الوكيل
   **كما هي في `agents`** لحظة التنفيذ، وبمخزون أدوات بيئة التشغيل. أي نقص =
   `CapabilityDeniedError` بسبب مُسمّى، ولا تنفيذ. لا تخفيض للمتطلَّب ولا fallback.
2. **سياق تنفيذ صريح:** `ExecutionContext` يحمل `task_id` و`agent_id`
   و`execution_id` و`correlation_id` وسياق الإذن — بلا أسرار، وليس بديلًا عن
   الحفظ (مصدر الحقيقة يبقى جدول `tasks`).
3. **دورة حياة وكيل مُعلَنة:** RESOLVED → STARTED → EXECUTING → COMPLETED/FAILED
   → IDLE، تُقيَّد في التدقيق وتُنشَر على الناقل الدائم القائم بموضوع واحد. وهي
   **منفصلة** عن آلة حالات المهمّة: لا تُدمج النموذجان، ولا تُحرَّك حالة مهمّة من هنا.
4. **نسب النتيجة:** كل نتيجة تُسند إلى مهمّة ووكيل وتنفيذ وأدوات مُستدعاة فعلًا،
   وما لا يُعرف يُقال `UNKNOWN` أو يُترك غائبًا — لا يُخترع.
5. **حدّ المحاكاة:** بيئة التشغيل تُنفَّذ فعلًا داخل العملية (`runtime_fidelity =
   REAL`) بينما الأدوات كلها `_mock_*` (`tool_execution_fidelity = SIMULATION`).
   الحقلان منفصلان بقصد، كي لا يُقرأ صدق البيئة صدقًا للأداة.

وما **لا** تفعله هذه الوحدة، بقصد: لا تستدعي `compare_and_set`، ولا تكتب في
`tasks`، ولا تُنشئ مهمّة، ولا تُصدر قرارًا سياديًّا، ولا تُنشئ بيئة تشغيل جديدة —
تربط `WorkerAgent` و`ToolSandbox` القائمين كما هما. ويحرس هذا كلَّه اختبارٌ ساكن
يفحص هذه الوحدة نفسها.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from amos_federation.common.durable_event_bus import get_durable_event_bus
from amos_federation.common.persistent import PersistentAuditStore
from amos_federation.services.executive_core.dispatcher import (
    WILDCARD,
    AgentAssignment,
)
from amos_federation.services.executive_core.fidelity import ExecutionFidelity

#: موضوع الحدث الدائم لدورة حياة الوكيل — منفصل عن موضوع انتقال المهمّة.
AGENT_LIFECYCLE_SUBJECT = "amos_federation.executive.agent_lifecycle"

#: الفاعل في سلسلة التدقيق: النواة تُقيّد، لا بيئة التشغيل.
AUDIT_ACTOR = "federal.executive.core"

#: صدق بيئة التشغيل: الوكيل يُستدعى فعلًا ويُنفّذ خطواته داخل العملية.
RUNTIME_FIDELITY = ExecutionFidelity.REAL.value

#: صدق تنفيذ الأدوات: `ToolSandbox` كله دوالّ `_mock_*` — ولا يُزعم غير ذلك.
TOOL_EXECUTION_FIDELITY = ExecutionFidelity.SIMULATION.value

#: سبب إلزامي مرافق لإعلان محاكاة الأدوات (`declare` ترفض إعلانًا بلا سبب).
TOOL_FIDELITY_REASON = "tool_sandbox_handlers_are_mocks"

#: قيمة ما لا يُعرف. تُقال ولا تُبدَّل بقيمة تبدو معلومة.
UNKNOWN = "UNKNOWN"


class AgentLifecycle(StrEnum):
    """دورة حياة الوكيل داخل تنفيذ واحد — لا تُخزَّن كحالة مهمّة."""

    RESOLVED = "resolved"
    STARTED = "started"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    IDLE = "idle"


class CapabilityDeniedError(PermissionError):
    """القدرة المطلوبة غير ممنوحة للوكيل أو غير متاحة في بيئة التشغيل."""


class RuntimeDispatchError(RuntimeError):
    """فشل التنفيذ داخل بيئة التشغيل — يُنقل كما هو ولا يُبتلَع."""


@dataclass(frozen=True)
class ExecutionContext:
    """سياق تنفيذ واحد: من ينفّذ، لأي مهمّة، بأي إذن، وبأي معرّف تتبُّع.

    لا يحتوي أسرارًا: لا رموز مصادقة ولا مفاتيح. وليس مخزنًا — مصدر الحقيقة
    لحالة المهمّة يبقى جدول `tasks`، وهذا السياق أثر مرافق للتنفيذ فقط.
    """

    task_id: str
    agent_id: str
    execution_id: str
    correlation_id: str
    tenant_id: str
    agent_role: str
    authorization: dict[str, Any] = field(default_factory=dict)
    capabilities_granted: tuple[str, ...] = ()
    capabilities_required: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "tenant_id": self.tenant_id,
            "agent_role": self.agent_role,
            "authorization": dict(self.authorization),
            "capabilities_granted": list(self.capabilities_granted),
            "capabilities_required": list(self.capabilities_required),
        }


@dataclass(frozen=True)
class AgentExecutionResult:
    """نتيجة تنفيذ وكيل، قابلة للإسناد بالكامل.

    `status` يُحسب من الخطوات لا يُنقل عن الوكيل: وكيل يُعلن `completed` وقد
    تخطّى خطواته كلَّها يُعلن نجاحًا لم يقع، فتُصحّح الحقيقة هنا إلى `partial`.
    """

    task_id: str
    agent_id: str
    execution_id: str
    agent_role: str
    status: str
    steps: tuple[dict[str, Any], ...]
    tools_invoked: tuple[str, ...]
    capabilities_granted: tuple[str, ...]
    result_summary: str
    started_at: str
    completed_at: str
    lifecycle: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "execution_id": self.execution_id,
            "agent_role": self.agent_role,
            "status": self.status,
            "steps": [dict(step) for step in self.steps],
            "tools_invoked": list(self.tools_invoked),
            "capabilities_granted": list(self.capabilities_granted),
            "result_summary": self.result_summary,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "agent_lifecycle": list(self.lifecycle),
            "runtime_fidelity": RUNTIME_FIDELITY,
            "tool_execution_fidelity": TOOL_EXECUTION_FIDELITY,
            "tool_fidelity_reason": TOOL_FIDELITY_REASON,
        }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _granted(assignment: AgentAssignment) -> tuple[str, ...]:
    """الأدوات الممنوحة فعلًا للوكيل حسب سجل الوكلاء، لا حسب الخطة."""
    return tuple(assignment.allowed_tools)


class AgentRuntimeGateway:
    """الحدّ الوحيد الذي تعبره النواة إلى بيئة تشغيل الوكلاء.

    `dispatch(task, assignment, ...) → runtime → result`. النواة تبقى صاحبة قرار
    بدء التنفيذ؛ هذه الوحدة تنفّذ القرار ولا تتّخذه، ولا تملك سلطة على الحالة.
    """

    def __init__(
        self,
        agent_factory: Any | None = None,
        audit_store: Any | None = None,
        event_bus: Any | None = None,
        tool_inventory: Any | None = None,
    ) -> None:
        self._agent_factory = agent_factory
        self._audit = audit_store or PersistentAuditStore()
        self._bus = event_bus or get_durable_event_bus()
        self._tool_inventory = tool_inventory

    # ── مخزون أدوات بيئة التشغيل ─────────────────────────────────────────
    def available_tools(self) -> tuple[str, ...]:
        """أدوات بيئة التشغيل القائمة — من `ToolSandbox` نفسه لا قائمة موازية."""
        if self._tool_inventory is not None:
            return tuple(self._tool_inventory())
        from amos_federation.services.agent_runtime.sandbox import ToolSandbox

        return tuple(ToolSandbox().available_tools())

    # ── القدرة والصلاحية: fail-closed ────────────────────────────────────
    def verify_capabilities(self, assignment: AgentAssignment) -> tuple[str, ...]:
        """التحقّق من سلسلة Agent → Role → Capability → Permission → Tool.

        Returns:
            الأدوات الممنوحة كما في سجل الوكلاء.

        Raises:
            CapabilityDeniedError: إن طلبت الخطة أداة غير ممنوحة للوكيل، أو أداة
                غير موجودة في بيئة التشغيل. السبب مُسمّى في الرسالة، ولا يُنفَّذ
                جزء من الخطة على أمل أن يمرّ الباقي.
        """
        granted = _granted(assignment)
        required = tuple(tool for tool in assignment.required_tools if tool)
        inventory = self.available_tools()

        missing_in_runtime = [tool for tool in required if tool not in inventory]
        if missing_in_runtime:
            raise CapabilityDeniedError(
                "tool_not_available_in_runtime:" + ",".join(sorted(missing_in_runtime))
            )
        if WILDCARD not in granted:
            not_granted = [tool for tool in required if tool not in granted]
            if not_granted:
                raise CapabilityDeniedError(
                    "capability_not_granted_to_agent:" + ",".join(sorted(not_granted))
                )
        return granted

    # ── سياق التنفيذ ─────────────────────────────────────────────────────
    def build_context(
        self,
        task: dict[str, Any],
        assignment: AgentAssignment,
        *,
        authorization: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> ExecutionContext:
        """سياق تنفيذ مبنيّ على تعيين مُتحقَّق — يُبنى بعد فحص القدرة لا قبله."""
        granted = self.verify_capabilities(assignment)
        return ExecutionContext(
            task_id=str(task["id"]),
            agent_id=assignment.agent_id,
            execution_id=execution_id or f"exec-{uuid.uuid4()}",
            correlation_id=str(task["id"]),
            tenant_id=str(task.get("tenant_id") or "default"),
            agent_role=assignment.agent_role or UNKNOWN,
            authorization=dict(authorization or {}),
            capabilities_granted=granted,
            capabilities_required=tuple(tool for tool in assignment.required_tools if tool),
        )

    # ── دورة حياة الوكيل ─────────────────────────────────────────────────
    def record_lifecycle(
        self,
        context: ExecutionContext,
        phase: AgentLifecycle,
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """قيد تدقيق ثم حدث دائم لمرحلة من دورة حياة الوكيل.

        `task_state_effect: False` صريح: هذه المرحلة لا تنقل حالة مهمّة. تحريك
        الحالة بيد آلة الحالات في `engine.py` وحدها.
        """
        entry = self._audit.append(
            f"executive.agent.{phase.value}",
            AUDIT_ACTOR,
            {
                "phase": phase.value,
                "context": context.as_dict(),
                "detail": dict(detail or {}),
            },
        )
        event = self._bus.publish(
            AGENT_LIFECYCLE_SUBJECT,
            {
                "phase": phase.value,
                "task_id": context.task_id,
                "agent_id": context.agent_id,
                "execution_id": context.execution_id,
                "agent_role": context.agent_role,
                "audit_id": entry["audit_id"],
                "runtime_fidelity": RUNTIME_FIDELITY,
                "tool_execution_fidelity": TOOL_EXECUTION_FIDELITY,
                "task_state_effect": False,
                "detail": dict(detail or {}),
            },
            correlation_id=context.correlation_id,
            causation_id=context.execution_id,
        )
        return {"audit_id": entry["audit_id"], "event_id": event["event_id"]}

    # ── التنفيذ ──────────────────────────────────────────────────────────
    def _agent_for(self, context: ExecutionContext) -> Any:
        """وكيل قابل للتنفيذ من بيئة التشغيل القائمة — `WorkerAgent` كما هو.

        الصلاحيات المُمرَّرة هي الممنوحة من سجل الوكلاء، لا أدوات الخطة. فإن
        ضاقت صلاحية الوكيل بعد التوزيع، ضاق ما يستطيع فعلًا.
        """
        if self._agent_factory is not None:
            return self._agent_factory(context)
        from amos_federation.services.agent_runtime.worker import WorkerAgent

        return WorkerAgent(
            agent_id=context.agent_id,
            permissions=list(context.capabilities_granted),
        )

    def dispatch(
        self,
        task: dict[str, Any],
        assignment: AgentAssignment,
        *,
        authorization: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> AgentExecutionResult:
        """توزيع فعلي إلى بيئة التشغيل: قدرة → سياق → دورة حياة → نتيجة.

        Raises:
            CapabilityDeniedError: قبل أي تنفيذ، إن لم تُتحقَّق القدرة.
            RuntimeDispatchError: إن فشل الوكيل داخل بيئة التشغيل — يُسجَّل الفشل
                في دورة الحياة ثم يُرفع، ولا يُحوَّل إلى نتيجة تبدو ناجحة.
        """
        context = self.build_context(
            task, assignment, authorization=authorization, execution_id=execution_id
        )
        lifecycle: list[str] = []
        self.record_lifecycle(context, AgentLifecycle.RESOLVED)
        lifecycle.append(AgentLifecycle.RESOLVED.value)

        agent = self._agent_for(context)
        self.record_lifecycle(context, AgentLifecycle.STARTED)
        lifecycle.append(AgentLifecycle.STARTED.value)

        plan = list(task.get("plan") or [])
        started_at = _now()
        self.record_lifecycle(context, AgentLifecycle.EXECUTING, {"steps_planned": len(plan)})
        lifecycle.append(AgentLifecycle.EXECUTING.value)

        try:
            raw = asyncio.run(agent.execute(task, plan))
        except Exception as exc:
            self.record_lifecycle(
                context,
                AgentLifecycle.FAILED,
                {"error": type(exc).__name__, "message": str(exc)},
            )
            self.record_lifecycle(context, AgentLifecycle.IDLE)
            raise RuntimeDispatchError(f"{type(exc).__name__}: {exc}") from exc

        steps = tuple(dict(step) for step in (raw.get("steps") or []))
        status = _honest_status(steps)
        self.record_lifecycle(
            context,
            AgentLifecycle.COMPLETED,
            {"status": status, "steps_executed": len(steps)},
        )
        lifecycle.append(AgentLifecycle.COMPLETED.value)
        self.record_lifecycle(context, AgentLifecycle.IDLE)
        lifecycle.append(AgentLifecycle.IDLE.value)
        return AgentExecutionResult(
            task_id=context.task_id,
            agent_id=context.agent_id,
            execution_id=context.execution_id,
            agent_role=context.agent_role,
            status=status,
            steps=steps,
            tools_invoked=_tools_invoked(steps),
            capabilities_granted=context.capabilities_granted,
            result_summary=str(raw.get("result_summary") or ""),
            started_at=str(raw.get("started_at") or started_at),
            completed_at=str(raw.get("completed_at") or _now()),
            lifecycle=tuple(lifecycle),
        )


def _honest_status(steps: tuple[dict[str, Any], ...]) -> str:
    """حالة التنفيذ محسوبة من الخطوات لا منقولة عن الوكيل.

    `WorkerAgent` يُرجع `status: "completed"` دائمًا — حتى إن تخطّى كل خطواته.
    فهنا تُصنَّف الخطوات إلى ثلاث فئات ولا تُخلط:

    - `completed` — الخطوة تقول صراحةً إنها اكتملت.
    - `skipped`/`failed`/`error` — الخطوة تقول صراحةً إنها لم تُنفَّذ.
    - غير ذلك — الخطوة لا تُعلن حالتها. لا تُحسَب نجاحًا ولا فشلًا: تُقال
      `unreported`. اعتبارها نجاحًا اختراعٌ، واعتبارها فشلًا اتهامٌ بلا دليل.
    """
    if not steps:
        return "empty"
    completed = 0
    refused = 0
    for step in steps:
        state = str(step.get("status", "")).strip()
        if state == "completed":
            completed += 1
        elif state in {"skipped", "failed", "error"}:
            refused += 1
    if completed == len(steps):
        return "completed"
    if completed == 0 and refused == len(steps):
        return "failed"
    if completed == 0 and refused == 0:
        return "unreported"
    return "partial"


def _tools_invoked(steps: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    """الأدوات التي استُدعيت فعلًا — من خطوات مكتملة فقط، بلا تكرار."""
    invoked: list[str] = []
    for step in steps:
        tool = str(step.get("tool", "")).strip()
        if step.get("status") == "completed" and tool and tool not in invoked:
            invoked.append(tool)
    return tuple(invoked)


_gateway: AgentRuntimeGateway | None = None


def get_agent_runtime_gateway() -> AgentRuntimeGateway:
    """حدّ واحد لبيئة التشغيل في العملية — يُبنى عند أول طلب."""
    global _gateway
    if _gateway is None:
        _gateway = AgentRuntimeGateway()
    return _gateway


def reset_agent_runtime_gateway() -> None:
    """إسقاط الحدّ المحفوظ — تستخدمه الاختبارات بعد تغيير قاعدة البيانات."""
    global _gateway
    _gateway = None
