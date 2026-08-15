"""
AMOS-Federation Tool Registry Service
الهدف: تسجيل وعرض وحل الأدوات عبر مطابقة كلمات مفتاحية
النطاق: خدمة tool-registry على المنفذ 8003
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.schemas import ToolManifestModel
from amos_federation.common.service import create_service_app
from amos_federation.common.persistent import PersistentToolStore
from amos_federation.services.tool_registry.store import ToolStore

router = APIRouter(prefix="/v1", tags=["tool-registry"])
tool_store: ToolStore = PersistentToolStore()


@router.get("/tools", response_model=list[ToolManifestModel])
async def list_tools(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[ToolManifestModel]:
    """عرض كل الأدوات المسجلة."""
    return tool_store.list_all()


@router.get("/tools/{tool_id}", response_model=ToolManifestModel)
async def get_tool(
    tool_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ToolManifestModel:
    """إرجاع أداة بالمعرّف."""
    tool = tool_store.get(tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الأداة غير موجودة")
    return tool


@router.post("/tools", response_model=ToolManifestModel, status_code=status.HTTP_201_CREATED)
async def register_tool(
    manifest: ToolManifestModel,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ToolManifestModel:
    """تسجيل أداة جديدة أو تحديثها."""
    return tool_store.register(manifest)


@router.post("/tools/resolve", response_model=list[ToolManifestModel])
async def resolve_tools(
    _: Annotated[dict[str, object], Depends(require_auth)],
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=20),
) -> list[ToolManifestModel]:
    """حل استعلام نصي إلى أدوات مطابقة بالكلمات المفتاحية (Semantic Router)."""
    results = tool_store.resolve(query, limit=limit)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يتم العثور على أدوات مطابقة",
        )
    return results


_service = SERVICES["tool-registry"]
app = create_service_app(_service["name"], _service["port"], "تسجيل وحل الأدوات", [router])
