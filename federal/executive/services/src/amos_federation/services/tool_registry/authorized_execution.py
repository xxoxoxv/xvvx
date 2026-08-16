"""الهدف: لا صندوق رملي قبل التخويل — سلسلة كاملة أو فشل مُغلَق.

النطاق: services/tool_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

السلسلة المحفوظة، بهذا الترتيب لا بغيره:

    Agent → Role → Capability → Permission → Tool → Sandbox

قبل هذه الوحدة كان `execute_tool_with_governance` يفحص الـkill switch ومحرِّك
السياسة ثم **يُنشئ الصندوق فورًا**، بلا أن يعرف من هو الوكيل ولا ما أدواته
المسموحة: كان يكفي أن يسمح الدور بالأداة. فوكيل لا يملك الأداة في
`allowed_tools` كان ينفّذها إن كان دوره يسمح بها عمومًا.

الترتيب المُنفَّذ هنا في `authorize()`، ولا يُنشأ صندوق إلا بعد اكتماله:

1. **Agent** — هوية كانونية موجودة في `agents`. المجهول يُرفَض.
2. **Role** — الدور من الهوية نفسها لا من مُعطى الطلب. دورٌ يأتي من العميل
   يعني تصعيد صلاحية بسطر واحد.
3. **Capability** — حالة دورة الحياة تسمح بالتنفيذ (`employable`). وكيل مُقاعَد
   أو معزول أو موقوف لا ينفّذ ولو كان دوره كافيًا.
4. **Permission** — الأداة في `allowed_tools` للهوية، أو `*` صراحةً.
5. **Tool** — الأداة مسجَّلة في سجلّ الأدوات. لا تنفيذ لأداة غير معرَّفة.
6. **Sandbox** — الآن فقط: `create_sandbox`.

و**FAIL CLOSED** في كل نقطة: الرفض هو الافتراضي، والخطأ أثناء الفحص رفضٌ لا
سماح. `AuthorizationDecision.allowed` تبدأ `False` ولا تصير `True` إلا بعد
اجتياز الحلقات كلها.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from amos_federation.services.tool_registry.providers.contract import (
    ExecutionContext,
    ExecutionRequest,
    ExecutionResult,
    SandboxSpec,
)

#: أسماء حلقات السلسلة بترتيبها — تُفحَص في الاختبارات ضدّ إعادة الترتيب.
AUTHORIZATION_CHAIN: tuple[str, ...] = (
    "agent",
    "role",
    "capability",
    "permission",
    "tool",
    "sandbox",
)

#: صلاحية شاملة معروفة في بيانات الهوية.
WILDCARD_PERMISSION = "*"


class AuthorizationDenied(PermissionError):  # noqa: N818 — رفض تخويل، لا عطل
    """التخويل رُفِض — ولا يُنشأ صندوق. تحمل الحلقة التي سقطت وسببها."""

    def __init__(self, stage: str, reason: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(f"{stage}: {reason}")
        self.stage = stage
        self.reason = reason
        self.detail = detail or {}


@dataclass
class AuthorizationDecision:
    """قرار التخويل — يبدأ رفضًا ولا يُقلَب إلا باكتمال السلسلة."""

    allowed: bool = False
    agent_id: str | None = None
    role: str | None = None
    actor_role: str | None = None
    tool_id: str | None = None
    lifecycle_state: str | None = None
    stages_passed: tuple[str, ...] = ()
    denied_at: str | None = None
    reason: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "agent_id": self.agent_id,
            "role": self.role,
            "actor_role": self.actor_role,
            "tool_id": self.tool_id,
            "lifecycle_state": self.lifecycle_state,
            "stages_passed": list(self.stages_passed),
            "denied_at": self.denied_at,
            "reason": self.reason,
            "detail": self.detail,
        }


def _known_tools() -> tuple[str, ...]:
    """أدوات سجلّ الأدوات — من السجلّ نفسه لا من قائمة موازية.

    فشل قراءة السجلّ يُعامَل قائمةً فارغة، أي رفضًا لكل أداة (fail closed)، لا
    سماحًا عامًّا.
    """
    try:
        from amos_federation.services.tool_registry.catalog import TOOL_CATALOG

        return tuple(TOOL_CATALOG)
    except Exception:  # noqa: BLE001 — تعذُّر القراءة = رفض لا سماح
        return ()


def authorize(
    *,
    agent_id: str | None,
    tool_id: str,
    system_state: str | None = None,
    tenant_id: str | None = None,
    actor_role: str | None = None,
) -> AuthorizationDecision:
    """اجتَز سلسلة التخويل كاملة أو ارفع `AuthorizationDenied`.

    لا يُنشأ صندوق في هذه الدالّة بحال — هي فحص محض، وهذا ما يجعل «لا صندوق قبل
    التخويل» قابلًا للحراسة ساكنًا.

    Args:
        actor_role: دور المُستدعي الفعّال، يُمرَّر إلى kill switch ومحرِّك السياسة
            في حلقة `tool`. إن غاب فدور الهوية هو المُستعمَل. وهو **لا يوسِّع**
            منح الهوية بحال: حلقات `agent` و`capability` و`permission` تُفحَص
            على الهوية وحدها قبله، فالمحصّلة تقاطع لا اتحاد.

            حدٌّ معروف يُقال ولا يُخفى: هذا الدور مُدّعىً من المُستدعي ولا يُتحقَّق
            من رمز جلسة هنا — وهو نموذج الثقة القائم في `execute_tool_with_governance`
            قبل R5، لم تُغيّره R5 ولم تدّعِ إصلاحه.
    """
    decision = AuthorizationDecision(tool_id=tool_id, agent_id=agent_id)
    passed: list[str] = []

    # 1. Agent — هوية كانونية موجودة.
    if not agent_id:
        raise _deny(decision, "agent", "لا معرّف وكيل في الطلب")
    try:
        from amos_federation.services.executive_core.agent_identity import get_identity

        identity = get_identity(agent_id, tenant_id=tenant_id)
    except Exception as exc:  # noqa: BLE001 — تعذُّر القراءة = رفض
        raise _deny(decision, "agent", f"تعذّر قراءة الهوية الكانونية: {exc}") from exc
    if identity is None:
        raise _deny(decision, "agent", f"لا هوية كانونية للوكيل '{agent_id}'")
    passed.append("agent")

    # 2. Role — من الهوية. ودور المُستدعي، إن وُجد، يحكم حلقة السياسة وحدها.
    role = identity.role
    if not role:
        raise _deny(decision, "role", "الهوية الكانونية بلا دور")
    decision.role = role
    decision.actor_role = actor_role or role
    passed.append("role")

    # 3. Capability — حالة دورة الحياة تسمح بالتنفيذ.
    decision.lifecycle_state = identity.lifecycle_state
    if not identity.employable:
        raise _deny(
            decision,
            "capability",
            f"حالة دورة الحياة '{identity.lifecycle_state}' لا تسمح بالتنفيذ",
        )
    passed.append("capability")

    # 4. Permission — الأداة في أدوات الهوية المسموحة.
    allowed_tools = tuple(identity.allowed_tools)
    permissions = tuple(identity.permissions)
    wildcard = WILDCARD_PERMISSION in allowed_tools or WILDCARD_PERMISSION in permissions
    if not wildcard and tool_id not in allowed_tools:
        raise _deny(
            decision,
            "permission",
            f"الأداة '{tool_id}' ليست في أدوات الوكيل المسموحة",
            {"allowed_tools": list(allowed_tools)},
        )
    passed.append("permission")

    # 5. Tool — الأداة مسجَّلة، ومحرِّك السياسة والـkill switch يسمحان بها.
    known = _known_tools()
    if tool_id not in known:
        raise _deny(
            decision,
            "tool",
            f"الأداة '{tool_id}' غير مسجَّلة في سجلّ الأدوات",
            {"registered_tools": list(known)},
        )
    _enforce_governance(
        decision,
        tool_id=tool_id,
        role=decision.actor_role or role,
        system_state=system_state,
    )
    passed.append("tool")

    decision.stages_passed = tuple(passed)
    decision.allowed = True
    return decision


def _enforce_governance(
    decision: AuthorizationDecision,
    *,
    tool_id: str,
    role: str,
    system_state: str | None,
) -> None:
    """kill switch ثم محرِّك السياسة — داخل حلقة Tool لا قبل السلسلة."""
    from amos_federation.services.governance.canary import (
        enforce_kill_switch,
        get_system_status,
    )
    from amos_federation.services.governance.policy_engine import get_policy_engine

    enforce_kill_switch(tool_id, role)

    state = system_state or get_system_status()["level"]
    verdict = get_policy_engine().evaluate_tool_access(tool_id, role, state)
    if not verdict.get("allowed"):
        raise _deny(
            decision,
            "tool",
            "محرِّك السياسة رفض الأداة لهذا الدور",
            {"denied_by": verdict.get("denied_by"), "system_state": state},
        )


def _deny(
    decision: AuthorizationDecision,
    stage: str,
    reason: str,
    detail: dict[str, Any] | None = None,
) -> AuthorizationDenied:
    decision.allowed = False
    decision.denied_at = stage
    decision.reason = reason
    decision.detail = detail or {}
    return AuthorizationDenied(stage, reason, decision.as_dict())


def execute_authorized_tool(
    *,
    tool_id: str,
    agent_id: str | None,
    code: str = "",
    command: tuple[str, ...] = (),
    task_id: str | None = None,
    correlation_id: str | None = None,
    spec: SandboxSpec | None = None,
    tenant_id: str | None = None,
    provider: Any = None,
) -> ExecutionResult:
    """المسار الوحيد لتنفيذ أداة في صندوق مزوِّد: تخويل ثم صندوق.

    `authorize()` تُستدعى قبل أي `create_sandbox`؛ ورفضها يرفع
    `AuthorizationDenied` فلا يُنشأ صندوق ولا تُستهلَك موارد مزوِّد.
    """
    decision = authorize(agent_id=agent_id, tool_id=tool_id, tenant_id=tenant_id)

    from amos_federation.services.tool_registry.providers.selection import execute_in_sandbox

    sandbox_spec = spec or SandboxSpec(tool_id=tool_id)
    context = ExecutionContext(
        tool_id=tool_id,
        agent_id=decision.agent_id,
        task_id=task_id,
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )
    request = ExecutionRequest(code=code, command=command, context=context)
    result = execute_in_sandbox(sandbox_spec, request, provider=provider)
    _publish_execution(result, decision)
    return result


def _publish_execution(result: ExecutionResult, decision: AuthorizationDecision) -> None:
    """أعلِن التنفيذ بنَسَبه وصدقه — فشل الناقل لا يُبطل النتيجة."""
    try:
        from amos_federation.common.event_bus import get_event_bus

        payload = result.as_dict()
        payload["authorization_stages"] = list(decision.stages_passed)
        get_event_bus().publish("amos_federation.tool.executed", payload)
    except Exception:  # noqa: BLE001 — الناقل قد يكون غير مُهيّأ
        pass
