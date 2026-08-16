"""الهدف: واجهة HTTP للنواة التنفيذية — منفذ 8008.

النطاق: خدمة executive-core على المنفذ 8008
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

نقاط النهاية متزامنة (`def` لا `async def`) بقصد: النواة تستدعي وكيلًا غير
متزامن عبر `asyncio.run`، وذلك ممنوع داخل حلقة حدث قائمة. FastAPI ينفّذ الدوالّ
المتزامنة في خيط منفصل بلا حلقة، فيصحّ الاستدعاء. البديل — إخفاء المشكلة بحلقة
متداخلة — كان سيعمل في الاختبار ويسقط تحت الحمل.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.executive_core.dispatcher import register_agent
from amos_federation.services.executive_core.engine import get_executive_core
from amos_federation.services.executive_core.http_errors import to_http_exception

router = APIRouter(prefix="/v1/executive", tags=["executive-core"])


class SubmitRequest(BaseModel):
    """طلب قبول مهمّة جديدة في الدولة."""

    type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: str = "normal"
    domain: str = "general"
    tenant_id: str = "default"
    run: bool = False


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)


class AgentRegistration(BaseModel):
    """تسجيل وكيل قابل للتوزيع — القدرات هنا هي ما يُختار على أساسه."""

    agent_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = "worker"
    permissions: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    status: str = "registered"
    tenant_id: str = "default"


@router.post("/tasks")
def submit_task(request: SubmitRequest) -> dict[str, Any]:
    """قبول مهمّة، وتشغيلها حتى النهاية إن طُلب ذلك صراحةً."""
    core = get_executive_core()
    try:
        if request.run:
            return core.submit_and_run(
                request.type,
                request.description,
                priority=request.priority,
                domain=request.domain,
                tenant_id=request.tenant_id,
            )
        return core.submit(
            request.type,
            request.description,
            priority=request.priority,
            domain=request.domain,
            tenant_id=request.tenant_id,
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/tasks/{task_id}/advance")
def advance_task(task_id: str) -> dict[str, Any]:
    try:
        return get_executive_core().advance(task_id).as_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/tasks/{task_id}/run")
def run_task(task_id: str) -> dict[str, Any]:
    try:
        return get_executive_core().run(task_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, request: CancelRequest) -> dict[str, Any]:
    try:
        return get_executive_core().cancel(task_id, request.reason).as_dict()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/tasks/{task_id}")
def task_status(task_id: str) -> dict[str, Any]:
    try:
        return get_executive_core().status(task_id)
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.post("/agents")
def register_workforce_agent(request: AgentRegistration) -> dict[str, Any]:
    """تسجيل وكيل في القاعدة — بلا هذا لا توزيع، والمهمّة تسقط صريحًا."""
    return register_agent(
        request.agent_id,
        request.name,
        request.role,
        permissions=request.permissions,
        allowed_tools=request.allowed_tools,
        status=request.status,
        tenant_id=request.tenant_id,
    )


@router.post("/recover")
def recover_tasks() -> dict[str, Any]:
    """استرداد المهام غير المنتهية بعد إعادة تشغيل."""
    try:
        return get_executive_core().recover()
    except Exception as exc:
        raise to_http_exception(exc) from exc


@router.get("/state")
def executive_state() -> dict[str, Any]:
    """حالة النواة: التاج، أعلى سلطة، والمهام المعلّقة."""
    try:
        return get_executive_core().health()
    except Exception as exc:
        raise to_http_exception(exc) from exc


_service = SERVICES["executive-core"]
app = create_service_app(
    _service["name"],
    _service["port"],
    "النواة التنفيذية الفدرالية: دورة حياة المهمة تحت البوابة السيادية",
    [router],
)
