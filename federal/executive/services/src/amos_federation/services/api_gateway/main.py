"""
AMOS-Federation API Gateway
الهدف: استقبال المهام وإدارة بيانات الوكلاء والأدوات عبر واجهة موثقة
النطاق: خدمة api-gateway على المنفذ 8000
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from amos_federation.common.auth import require_auth
from amos_federation.common.events import event_publisher
from amos_federation.common.registry import SERVICES
from amos_federation.common.schemas import (
    AgentManifestModel,
    TaskAccepted,
    TaskDetails,
    TaskRequest,
    ToolManifestModel,
)
from amos_federation.common.service import create_service_app
from amos_federation.services.api_gateway.store import InMemoryTaskStore, TaskStore

router = APIRouter(prefix="/v1", tags=["api-gateway"])
task_store: TaskStore = InMemoryTaskStore()
agents: dict[str, AgentManifestModel] = {}
tools: dict[str, ToolManifestModel] = {}


@router.post("/tasks", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    task_request: TaskRequest, token: Annotated[dict[str, object], Depends(require_auth)]
) -> TaskAccepted:
    """قبول مهمة جديدة ونشر حدث task.created دون اشتراط توفر البنية الخارجية."""
    tenant_id = task_request.tenant_id or token.get("tenant_id")
    now = datetime.now(UTC)
    task = TaskDetails(
        **task_request.model_dump(exclude={"tenant_id"}),
        task_id=f"task-{uuid4()}",
        tenant_id=str(tenant_id) if tenant_id else None,
        status="pending",
        created_at=now,
    )
    task_store.create(task)
    event_type = {
        "analysis": "analysis",
        "report": "generation",
        "data": "transformation",
        "generic": "research",
    }
    event_data = {
        "task_id": task.task_id,
        "type": event_type[task.type],
        "description": task.description,
        "priority": task.priority,
        "domain": task.domain or "federal",
        "tenant_id": task.tenant_id,
    }
    await event_publisher.publish("task.created", "api-gateway", event_data)
    return TaskAccepted(task_id=task.task_id, status=task.status, accepted_at=now)


@router.get("/tasks/{task_id}", response_model=TaskDetails)
async def get_task(
    task_id: str, _: Annotated[dict[str, object], Depends(require_auth)]
) -> TaskDetails:
    """إرجاع حالة مهمة محفوظة أو 404 عند عدم وجودها."""
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المهمة غير موجودة")
    return task


@router.get("/agents", response_model=list[AgentManifestModel])
async def list_agents(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[AgentManifestModel]:
    """عرض بيانات الوكلاء المسجلين مؤقتًا في الذاكرة."""
    return list(agents.values())


@router.post("/agents", response_model=AgentManifestModel, status_code=status.HTTP_201_CREATED)
async def register_agent(
    manifest: AgentManifestModel, _: Annotated[dict[str, object], Depends(require_auth)]
) -> AgentManifestModel:
    """تسجيل بيان وكيل في المرحلة الحالية."""
    agents[manifest.agent_id] = manifest
    return manifest


@router.post("/tools", response_model=ToolManifestModel, status_code=status.HTTP_201_CREATED)
async def register_tool(
    manifest: ToolManifestModel, _: Annotated[dict[str, object], Depends(require_auth)]
) -> ToolManifestModel:
    """تسجيل بيان أداة في المرحلة الحالية."""
    tools[manifest.tool_id] = manifest
    return manifest


_service = SERVICES["api-gateway"]
app = create_service_app(_service["name"], _service["port"], "بوابة واجهات AMOS الموحدة", [router])
