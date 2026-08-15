"""
AMOS-Federation Critic Service
الهدف: مراجعة نتائج المهام وتقييم جودتها
النطاق: خدمة critic على المنفذ 8007
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.critic.store import InMemoryCriticStore

router = APIRouter(prefix="/v1", tags=["critic"])
critic_store = InMemoryCriticStore()


class ReviewRequest(BaseModel):
    """طلب مراجعة نتيجة مهمة."""

    task_id: str | None = None
    agent_id: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    result_summary: str = ""


class ReviewResponse(BaseModel):
    """استجابة مراجعة."""

    review_id: str
    task_id: str | None
    agent_id: str | None
    quality_score: float
    feedback: str
    approved: bool
    criteria: dict[str, Any]
    created_at: str


def _score_review(request: ReviewRequest) -> tuple[float, str, bool, dict[str, Any]]:
    """تقييم حتمي للنتيجة بناءً على معايير قابلة للقياس."""
    criteria: dict[str, Any] = {}
    score = 0.0
    feedback_parts: list[str] = []

    # معيار 1: اكتمال الخطوات
    total_steps = len(request.steps)
    completed_steps = sum(1 for s in request.steps if s.get("status") == "completed")
    skipped_steps = sum(1 for s in request.steps if s.get("status") == "skipped")
    completion_ratio = completed_steps / total_steps if total_steps > 0 else 0.0
    criteria["completion_ratio"] = round(completion_ratio, 4)
    score += completion_ratio * 0.4
    if skipped_steps > 0:
        feedback_parts.append(f"تم تخطي {skipped_steps} خطوة")

    # معيار 2: وجود نتيجة
    has_result = bool(request.result_summary)
    criteria["has_result"] = has_result
    score += 0.3 if has_result else 0.0
    if not has_result:
        feedback_parts.append("لا يوجد ملخص نتيجة")

    # معيار 3: معرّف المهمة موجود
    has_task_id = bool(request.task_id)
    criteria["has_task_id"] = has_task_id
    score += 0.1 if has_task_id else 0.0

    # معيار 4: معرّف الوكيل موجود
    has_agent_id = bool(request.agent_id)
    criteria["has_agent_id"] = has_agent_id
    score += 0.1 if has_agent_id else 0.0

    # معيار 5: جودة الخطوات (نتائج غير فارغة)
    non_empty_results = sum(
        1 for s in request.steps
        if s.get("result") and isinstance(s["result"], dict) and s["result"].get("error") is None
    )
    result_quality = non_empty_results / total_steps if total_steps > 0 else 0.0
    criteria["result_quality"] = round(result_quality, 4)
    score += result_quality * 0.1

    score = min(score, 1.0)
    approved = score >= 0.7

    if not feedback_parts:
        feedback_parts.append("النتيجة جيدة وتحقق معايير القبول")
    feedback = ". ".join(feedback_parts)

    return round(score, 2), feedback, approved, criteria


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def review_task(
    request: ReviewRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ReviewResponse:
    """مراجعة نتيجة مهمة وتعيين درجة جودة وتغذية راجعة."""
    score, feedback, approved, criteria = _score_review(request)
    record = critic_store.review({
        "task_id": request.task_id,
        "agent_id": request.agent_id,
        "quality_score": score,
        "feedback": feedback,
        "approved": approved,
        "criteria": criteria,
    })
    return ReviewResponse(**record)


@router.get("/reviews", response_model=list[dict])
async def list_reviews(
    _: Annotated[dict[str, object], Depends(require_auth)],
    task_id: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض المراجعات مع فلترة."""
    return critic_store.list_all(task_id=task_id, min_score=min_score, limit=limit)


@router.get("/reviews/{review_id}", response_model=dict)
async def get_review(
    review_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع مراجعة بالمعرّف."""
    rev = critic_store.get(review_id)
    if rev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المراجعة غير موجودة")
    return rev


@router.get("/reviews/stats/summary", response_model=dict)
async def review_stats(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إحصائيات المراجعات."""
    return {
        "total_reviews": critic_store.count(),
        "average_score": round(critic_store.average_score(), 4),
    }


_service = SERVICES["critic"]
app = create_service_app(_service["name"], _service["port"], "مراجعة وتقييم النتائج", [router])
