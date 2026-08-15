"""
AMOS-Federation Memory Service
الهدف: تخزين واسترجاع الذاكرة التشغيلية والمعرفية
النطاق: خدمة memory-service على المنفذ 8005
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.schemas import MemoryQuery, MemoryStore as MemoryStoreModel
from amos_federation.common.service import create_service_app
from amos_federation.services.memory_service.store import InMemoryVectorStore

router = APIRouter(prefix="/v1", tags=["memory-service"])
memory_store = InMemoryVectorStore()


@router.post("/memory/store", response_model=dict)
async def store_memory(
    entry: MemoryStoreModel,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """حفظ عنصر ذاكرة جديد."""
    return memory_store.store(entry.key, entry.value, entry.tenant_id)


@router.post("/memory/query", response_model=list[dict])
async def query_memory(
    query: MemoryQuery,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """البحث في الذاكرة بنص استعلام."""
    results = memory_store.query(query.query, query.tenant_id, query.limit)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يتم العثور على ذكريات مطابقة",
        )
    return results


@router.post("/memory/search", response_model=list[dict])
async def search_memory(
    query: MemoryQuery,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """بحث في الذاكرة — اسم بديل لـ /memory/query."""
    results = memory_store.query(query.query, query.tenant_id, query.limit)
    return results  # قد تكون قائمة فارغة


@router.get("/memory/{key}", response_model=dict)
async def get_memory(
    key: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع عنصر ذاكرة بالمفتاح."""
    item = memory_store.get(key)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="العنصر غير موجود")
    return item


@router.get("/memory/stats/summary", response_model=dict)
async def memory_stats(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إحصائيات الذاكرة."""
    return {
        "total_items": memory_store.count(),
        "store_type": "in_memory_keyword",
    }


_service = SERVICES["memory-service"]
app = create_service_app(_service["name"], _service["port"], "ذاكرة تشغيلية ومعرفية", [router])
