"""
AMOS-Federation Agent Runtime Service
الهدف: تنفيذ المهام عبر وكلاء عاملين باستخدام الأدوات المسجلة
النطاق: خدمة agent-runtime على المنفذ 8002
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.agent_runtime.worker import WorkerAgent

router = APIRouter(prefix="/v1", tags=["agent-runtime"])


class ExecuteRequest(BaseModel):
    """طلب تنفيذ مهمة عبر وكيل."""

    task: dict[str, Any] = Field(..., description="بيانات المهمة")
    plan: list[dict[str, Any]] = Field(..., min_length=1, description="خطوات الخطة من Orchestrator")
    agent_id: str | None = None


class ExecuteResponse(BaseModel):
    """استجابة تنفيذ مهمة."""

    task_id: str | None
    agent_id: str
    status: str
    steps: list[dict[str, Any]]
    started_at: str
    completed_at: str
    result_summary: str


@router.post("/execute", response_model=ExecuteResponse)
async def execute_task(
    request: ExecuteRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ExecuteResponse:
    """تنفيذ مهمة كاملة عبر وكيل عامل يتبع الخطوات بالترتيب."""
    agent = WorkerAgent(
        agent_id=request.agent_id or "worker-generic-001",
        domain=request.task.get("domain", "federal"),
    )
    result = await agent.execute(request.task, request.plan)
    return ExecuteResponse(**result)


@router.get("/agents/available", response_model=list[str])
async def available_agents(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[str]:
    """عرض معرّفات الوكلاء المتاحين."""
    return ["worker-generic-001", "worker-researcher", "worker-analyst", "critic-001"]


@router.get("/tools/available", response_model=list[str])
async def available_tools(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[str]:
    """عرض الأدوات المتاحة في الصندوق الرمل."""
    agent = WorkerAgent()
    return agent.sandbox.available_tools()


_service = SERVICES["agent-runtime"]
app = create_service_app(_service["name"], _service["port"], "تنفيذ الوكلاء", [router])
