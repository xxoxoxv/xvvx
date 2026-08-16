"""الهدف: النواة التنفيذية الفدرالية — وصل التاج والسيادة بمسار تنفيذ المهام.

النطاق: federal/executive/services — النواة التنفيذية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16
"""

from amos_federation.services.executive_core.dispatcher import (
    AgentAssignment,
    CapabilityDispatcher,
    NoEligibleAgentError,
    register_agent,
)
from amos_federation.services.executive_core.engine import (
    ExecutionRefusedError,
    ExecutiveCore,
    TransitionOutcome,
    get_executive_core,
    reset_executive_core,
)
from amos_federation.services.executive_core.repository import (
    ExecutiveTaskRepository,
    TaskNotFoundError,
)
from amos_federation.services.executive_core.sovereignty_bridge import (
    AuthorityEvidence,
    ConstitutionalAuthorizer,
    SovereigntyUnavailableError,
    get_authorizer,
)
from amos_federation.services.executive_core.states import (
    TERMINAL_STATES,
    TRANSITIONS,
    IllegalTransitionError,
    TaskState,
    UnknownStateError,
    assert_transition,
    is_legal,
    is_terminal,
    next_states,
    parse_state,
)

__all__ = [
    "TERMINAL_STATES",
    "TRANSITIONS",
    "AgentAssignment",
    "AuthorityEvidence",
    "CapabilityDispatcher",
    "ConstitutionalAuthorizer",
    "ExecutionRefusedError",
    "ExecutiveCore",
    "ExecutiveTaskRepository",
    "IllegalTransitionError",
    "NoEligibleAgentError",
    "SovereigntyUnavailableError",
    "TaskNotFoundError",
    "TaskState",
    "TransitionOutcome",
    "UnknownStateError",
    "assert_transition",
    "get_authorizer",
    "get_executive_core",
    "is_legal",
    "is_terminal",
    "next_states",
    "parse_state",
    "register_agent",
    "reset_executive_core",
]
