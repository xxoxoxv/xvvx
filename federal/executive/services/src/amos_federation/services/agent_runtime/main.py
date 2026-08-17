"""
AMOS-Federation Agent Runtime Service
الهدف: تنفيذ المهام المقبولة في الدولة عبر النواة التنفيذية حصرًا
النطاق: خدمة agent-runtime على المنفذ 8002
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

R1 — توحيد مسار التنفيذ الخارجي:

قبل R1 كانت `POST /v1/execute` أخطر باب في الدولة: تستقبل مهمّة وخطة **خامّتين**
من الخارج وتشغّل `WorkerAgent` عليهما مباشرة. لا مهمّة في القاعدة، ولا إذن سيادي،
ولا انتقال حالة، ولا قيد تدقيق، ولا حدث دائم. أي حامل رمز كان ينفّذ داخل الدولة
عملًا لا وجود له في سجلّها.

بعد R1: التنفيذ لا يبدأ إلا من مهمّة قانونية في القاعدة، ويُفوَّض كاملًا إلى
`ExecutiveCore.run` — هي من توزّع على وكيل مؤهَّل من جدول `agents`، وتنقل الحالة
ذرّيًّا، وتقيّد التدقيق، وتنشر الحدث الدائم. وطلبُ التنفيذ بحمل خامّ يُرفَض بـ403
بسبب مُعلَن (`execution_bypass_forbidden`) لا يُبتلَع صامتًا.

`WorkerAgent` لم يُحذف ولم يُغيَّر: صار يُستدعى من النواة لا من الحافة. وأمانة
المخرَج كما هي: `ToolSandbox` كله دوالّ `_mock_*`، فكل استجابة تحمل
`execution_fidelity = "SIMULATION"`.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.agent_runtime.worker import WorkerAgent
from amos_federation.services.executive_core.engine import (
    EXECUTION_FIDELITY,
    get_executive_core,
)
from amos_federation.services.executive_core.http_errors import (
    EXECUTION_BYPASS_FORBIDDEN,
    to_http_exception,
)

router = APIRouter(prefix="/v1", tags=["agent-runtime"])


class ExecuteRequest(BaseModel):
    """طلب تنفيذ مهمّة قانونية بمعرّفها.

    `task` و`plan` مقبولان في المخطَّط لسبب واحد: كشف محاولة التجاوز ورفضها برسالة
    مفهومة بدل 422 غامضة. وجود أيّهما = رفض صريح.
    """

    task_id: str | None = Field(default=None, min_length=1)
    task: dict[str, Any] | None = None
    plan: list[dict[str, Any]] | None = None
    agent_id: str | None = None

    @model_validator(mode="after")
    def _require_task_id(self) -> "ExecuteRequest":
        if self.task_id is None and self.task is None and self.plan is None:
            raise ValueError("task_id مطلوب")
        return self


class ExecuteResponse(BaseModel):
    """استجابة تنفيذ مهمّة عبر النواة — حالة الآلة وأثر الإذن مُعلَنان."""

    task_id: str
    final_state: str
    execution_fidelity: str
    agent_id: str | None = None
    status: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    result_summary: str | None = None
    audit_trail: list[str] = Field(default_factory=list)
    authority: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/execute", response_model=ExecuteResponse)
def execute_task(
    request: ExecuteRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ExecuteResponse:
    """تنفيذ مهمّة قانونية عبر النواة التنفيذية — لا تنفيذ من الحافة.

    متزامنة بقصد: النواة تستدعي الوكيل غير المتزامن عبر `asyncio.run`، وذلك ممنوع
    داخل حلقة حدث قائمة.
    """
    if request.task is not None or request.plan is not None:
        raise HTTPException(status_code=403, detail=EXECUTION_BYPASS_FORBIDDEN)
    if request.task_id is None:
        raise HTTPException(status_code=403, detail=EXECUTION_BYPASS_FORBIDDEN)

    try:
        outcome = get_executive_core().run(request.task_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc

    task = outcome["task"]
    result = task["result"] or {}
    return ExecuteResponse(
        task_id=task["id"],
        final_state=outcome["final_state"],
        execution_fidelity=str(result.get("execution_fidelity", EXECUTION_FIDELITY)),
        agent_id=task["assigned_agent"],
        status=result.get("status"),
        steps=list(result.get("steps") or []),
        started_at=result.get("started_at"),
        completed_at=result.get("completed_at"),
        result_summary=result.get("result_summary"),
        audit_trail=[transition["audit_id"] for transition in outcome["transitions"]],
        authority=[transition["authority"] for transition in outcome["transitions"]],
    )


@router.get("/agents/available", response_model=list[str])
def available_agents(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[str]:
    """الوكلاء القابلون للتوزيع فعلًا — من جدول `agents` لا قائمة ثابتة.

    قبل R1 كانت هذه القائمة أربعة معرّفات مكتوبة في الشِفرة لا علاقة لها بما
    تستطيع النواة توزيعه. صارت تقرأ ما يقرؤه الموزّع نفسه.
    """
    from amos_federation.services.executive_core.dispatcher import CapabilityDispatcher

    return [agent["id"] for agent in CapabilityDispatcher().available_agents()]


@router.get("/tools/available", response_model=list[str])
def available_tools(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[str]:
    """الأدوات المتاحة في الصندوق الرمل — محاكاة، وتُقال محاكاة."""
    return WorkerAgent().sandbox.available_tools()


_service = SERVICES["agent-runtime"]
app = create_service_app(_service["name"], _service["port"], "تنفيذ الوكلاء", [router])
