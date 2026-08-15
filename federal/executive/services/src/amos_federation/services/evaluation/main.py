"""
AMOS-Federation Evaluation Service
الهدف: تسجيل الخبرات وتقييم النتائج واكتشاف الفجوات المعرفية
النطاق: خدمة evaluation على المنفذ 8006
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.evaluation.store import InMemoryExperienceStore

router = APIRouter(prefix="/v1", tags=["evaluation"])
experience_store = InMemoryExperienceStore()


class ExperienceRecord(BaseModel):
    """طلب تسجيل خبرة جديدة."""

    task_id: str | None = None
    type: str = Field(default="success", pattern="^(success|failure|gap|repair)$")
    agent_id: str | None = None
    model_used: str | None = None
    outcome: dict[str, Any] = Field(default_factory=dict)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    provenance: dict[str, Any] = Field(default_factory=dict)


@router.post("/experiences", response_model=dict, status_code=status.HTTP_201_CREATED)
async def record_experience(
    record: ExperienceRecord,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تسجيل خبرة جديدة مع تتبع المصدر."""
    return experience_store.record(record.model_dump())


@router.get("/experiences", response_model=list[dict])
async def list_experiences(
    _: Annotated[dict[str, object], Depends(require_auth)],
    type: str | None = Query(default=None, pattern="^(success|failure|gap|repair)$"),
    agent_id: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض الخبرات مع فلترة اختيارية."""
    return experience_store.list_all(
        exp_type=type, agent_id=agent_id, min_score=min_score, limit=limit
    )


@router.get("/experiences/{experience_id}", response_model=dict)
async def get_experience(
    experience_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع خبرة بالمعرّف."""
    exp = experience_store.get(experience_id)
    if exp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الخبرة غير موجودة")
    return exp


@router.post("/evaluations/run", response_model=dict)
async def run_evaluation(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تشغيل تقييم أساسي: إحصائيات الخبرات المتراكمة."""
    return {
        "total_experiences": experience_store.count(),
        "by_type": experience_store.by_type(),
        "status": "completed",
        "message": "تم تشغيل التقييم الأساسي",
    }


@router.get("/experiences/stats/summary", response_model=dict)
async def experience_stats(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إحصائيات الخبرات."""
    return {
        "total": experience_store.count(),
        "by_type": experience_store.by_type(),
    }


_service = SERVICES["evaluation"]
app = create_service_app(_service["name"], _service["port"], "تقييم النماذج وتسجيل الخبرات", [router])
