"""
AMOS-Federation memory-service Service
الهدف: توفير هيكل تشغيل واضح لخدمة memory-service
النطاق: خدمة memory-service ضمن Sprint الحالي
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi import APIRouter, HTTPException, status

from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["memory-service"])


@router.post("/memory/search")
async def not_implemented() -> None:
    """إعلان صريح عن الوظيفة المؤجلة بدل محاكاة تنفيذ غير موجود."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="وظيفة البحث في الذاكرة مؤجلة إلى الأسبوع 11-13: Memory + Hardening",
    )


_service = SERVICES["memory-service"]
app = create_service_app(_service["name"], _service["port"], "البحث في الذاكرة", [router])
