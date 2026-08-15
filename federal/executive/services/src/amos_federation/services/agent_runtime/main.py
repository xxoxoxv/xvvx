"""
AMOS-Federation agent-runtime Service
الهدف: توفير هيكل تشغيل واضح لخدمة agent-runtime
النطاق: خدمة agent-runtime ضمن Sprint الحالي
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi import APIRouter, HTTPException, status

from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["agent-runtime"])


@router.post("/execute")
async def not_implemented() -> None:
    """إعلان صريح عن الوظيفة المؤجلة بدل محاكاة تنفيذ غير موجود."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="وظيفة تنفيذ الوكلاء مؤجلة إلى الأسبوع 7-8: Agent Runtime + Tools",
    )


_service = SERVICES["agent-runtime"]
app = create_service_app(_service["name"], _service["port"], "تنفيذ الوكلاء", [router])
