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
from amos_federation.common.persistent import PersistentExperienceStore
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.evaluation.benchmark import analyze_gaps, run_benchmark
from amos_federation.services.executive_core.fidelity import ExecutionFidelity
from amos_federation.services.executive_core.subsystem_boundary import (
    ActivityKind,
    SubsystemRefusedError,
    get_subsystem_boundary,
)

router = APIRouter(prefix="/v1", tags=["evaluation"])
experience_store = PersistentExperienceStore()


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
    """تسجيل خبرة مع نسب مُصنّف لا مُدّعَى.

    `task_id` كانت نصًّا حرًّا يُخزّن كما ورد، فكانت الذاكرة المؤسّسية تتراكم
    على خبرات منسوبة إلى مهمّات لا وجود لها. الآن يُقرأ المعرّف من المستودع
    القانوني ويُوسم `canonical` أو `unverified`، ويُقيد الأثر عبر حدّ النواة —
    بلا تغيير حالة المهمّة، وبلا اختراع درجة جودة لم يُرسلها مُقيّم.
    """
    boundary = get_subsystem_boundary()
    provenance, linked_task_id = boundary.classify_provenance(record.task_id)

    try:
        activity = boundary.authorized_activity(
            ActivityKind.EVALUATION_RUN,
            f"experience:{record.type}",
            ExecutionFidelity.REAL,
            {
                "experience_type": record.type,
                "agent_id": record.agent_id,
                "quality_score": record.quality_score,
                "task_provenance": provenance,
                "claimed_task_id": record.task_id,
            },
            task_id=linked_task_id,
            context={"provenance": provenance},
        )
    except SubsystemRefusedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    payload = record.model_dump()
    payload["provenance"] = {
        "source": "api",  # يُحفظ ما كان المخزن يضعه تلقائيًّا حين لا نسب مع الطلب
        **(record.provenance or {}),
        "task_provenance": provenance,
        "activity_id": activity.activity_id,
        "authority_decision": activity.authority["decision"],
    }
    stored = experience_store.record(payload)
    return {**stored, "task_provenance": provenance, "activity_id": activity.activity_id}


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
    """تشغيل تقييم أساسي: إحصائيات الخبرات + تشغيل المعيار."""
    benchmark_result = run_benchmark()
    return {
        "total_experiences": experience_store.count(),
        "by_type": experience_store.by_type(),
        "benchmark": {
            "total": benchmark_result["total"],
            "passed": benchmark_result["passed"],
            "failed": benchmark_result["failed"],
            "pass_rate": benchmark_result["pass_rate"],
        },
        "status": "completed",
        "message": "تم تشغيل التقييم والمعيار القياسي",
    }


@router.post("/evaluations/benchmark", response_model=dict)
async def run_benchmark_suite(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تشغيل مجموعة المهام القياسية (20 مهمة)."""
    return run_benchmark()


@router.get("/evaluations/gaps", response_model=dict)
async def identify_gaps(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """اكتشاف الفجوات المعرفية بناءً على الخبرات المتراكمة."""
    all_experiences = experience_store.list_all(limit=1000)
    return analyze_gaps(all_experiences)


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
app = create_service_app(
    _service["name"], _service["port"], "تقييم النماذج وتسجيل الخبرات", [router]
)
