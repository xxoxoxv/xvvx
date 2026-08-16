"""
AMOS-Federation API Gateway
الهدف: استقبال المهام وإدارة بيانات الوكلاء والأدوات عبر واجهة موثقة
النطاق: خدمة api-gateway على المنفذ 8000
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

R1 — توحيد مسار التنفيذ الخارجي:

قبل R1 كانت `POST /v1/tasks` تكتب صفًّا في `tasks` بحالة نصّية `pending` — وهي
حالة لا وجود لها في آلة حالات النواة التنفيذية — ثم تنشر إخطارًا وتنسى المهمّة.
لا إذن سيادي، ولا قيد تدقيق، ولا حدث دائم. أي طلب خارجي كان يدخل الدولة من باب
لا يمرّ بالبوابة.

بعد R1: القبول كله عبر `ExecutiveCore.submit` — هو من يستأذن البوابة السيادية،
ويكتب الصفّ داخل الإذن، ويقيّد في سلسلة التدقيق، وينشر الحدث الدائم. هذه الوحدة
لا تحتفظ بنسخة من ذلك المنطق: تترجم HTTP وتفوّض.

الإخطار القديم `task.created` على ناقل `common/events` باقٍ كإخطار فقط (لا يُشغّل
تنفيذًا)، ويُنشَر **بعد** نجاح القبول القانوني لا قبله.
"""

from datetime import UTC, datetime
from typing import Annotated

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
from amos_federation.services.api_gateway.store import DatabaseTaskStore, TaskStore
from amos_federation.services.executive_core.engine import get_executive_core
from amos_federation.services.executive_core.http_errors import to_http_exception

router = APIRouter(prefix="/v1", tags=["api-gateway"])

# مصدر الحقيقة الدائم للمهام هو طبقة قاعدة البيانات (`TaskModel`) — لا بديل ذاكرة
# تلقائي، ولا تحويل حقول يدوي هنا: التحويل كله في `store.py`.
task_store: TaskStore = DatabaseTaskStore()

# تصنيف الإخطار القديم فقط — لا يُشتقّ منه أي قرار تنفيذي.
_EVENT_TYPE_BY_TASK_TYPE = {
    "analysis": "analysis",
    "report": "generation",
    "data": "transformation",
    "generic": "research",
}
agents: dict[str, AgentManifestModel] = {}
tools: dict[str, ToolManifestModel] = {}


@router.post("/tasks", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    task_request: TaskRequest, token: Annotated[dict[str, object], Depends(require_auth)]
) -> TaskAccepted:
    """قبول مهمة جديدة عبر النواة التنفيذية — لا كتابة مباشرة في الجدول.

    الحالة المُعادة هي حالة آلة الحالات الحقيقية (`created`) لا كلمة `pending`
    التي كانت خارج الآلة. الطلب الذي لا تأذن به البوابة لا يُقبَل هنا أصلًا.
    """
    tenant_id = task_request.tenant_id or token.get("tenant_id")
    core = get_executive_core()
    try:
        task = core.submit(
            task_request.type,
            task_request.description,
            priority=task_request.priority,
            domain=task_request.domain or "general",
            tenant_id=str(tenant_id) if tenant_id else "default",
        )
    except Exception as exc:
        raise to_http_exception(exc) from exc

    accepted_at = task.get("created_at") or datetime.now(UTC)
    if isinstance(accepted_at, str):
        accepted_at = datetime.fromisoformat(accepted_at)

    # إخطار الطبقة القديمة — إعلان لا تشغيل، وبعد القبول القانوني لا قبله.
    await event_publisher.publish(
        "task.created",
        "api-gateway",
        {
            "task_id": task["id"],
            "type": _EVENT_TYPE_BY_TASK_TYPE[task_request.type],
            "description": task["description"],
            "priority": task["priority"],
            "domain": task["domain"],
            "tenant_id": task["tenant_id"],
            "canonical_state": task["status"],
            "audit_id": task["submission"]["audit_id"],
        },
    )
    return TaskAccepted(task_id=task["id"], status=task["status"], accepted_at=accepted_at)


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
