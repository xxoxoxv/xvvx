"""
AMOS-Federation evaluation Service
الهدف: توفير هيكل تشغيل واضح لخدمة evaluation
النطاق: خدمة evaluation ضمن Sprint الحالي
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi import APIRouter, HTTPException, status

from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["evaluation"])


@router.post("/evaluations/run")
async def not_implemented() -> None:
    """إعلان صريح عن الوظيفة المؤجلة بدل محاكاة تنفيذ غير موجود."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="وظيفة تشغيل التقييم مؤجلة إلى الأسبوع 9-10: Model Gateway + E2E",
    )


_service = SERVICES["evaluation"]
app = create_service_app(_service["name"], _service["port"], "تشغيل التقييم", [router])
