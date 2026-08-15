"""
AMOS-Federation critic Service
الهدف: توفير هيكل تشغيل واضح لخدمة critic
النطاق: خدمة critic ضمن Sprint الحالي
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi import APIRouter, HTTPException, status

from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["critic"])


@router.post("/reviews")
async def not_implemented() -> None:
    """إعلان صريح عن الوظيفة المؤجلة بدل محاكاة تنفيذ غير موجود."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="وظيفة مراجعة النتيجة مؤجلة إلى الأسبوع 9-10: Model Gateway + E2E",
    )


_service = SERVICES["critic"]
app = create_service_app(_service["name"], _service["port"], "مراجعة النتيجة", [router])
