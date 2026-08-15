"""
AMOS-Federation Orchestrator
الهدف: تخطيط المهام إلى خطوات حتمية قابلة للتوزيع
النطاق: خدمة orchestrator على المنفذ 8001
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Any

from fastapi import APIRouter

from amos_federation.common.events import event_publisher
from amos_federation.common.registry import SERVICES
from amos_federation.common.schemas import TaskRequest
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["orchestrator"])


class PlanRequest(TaskRequest):
    """طلب تخطيط مع معرّف اختياري للمهمة المقبولة."""

    task_id: str | None = None


def build_plan(task: PlanRequest) -> list[dict[str, Any]]:
    """تحويل نوع المهمة إلى خطة ثابتة وقابلة للاختبار."""
    templates: dict[str, list[tuple[str, str, str]]] = {
        "analysis": [
            ("جمع السياق والبيانات", "research_apis", "worker-researcher"),
            ("تحليل الأدلة", "data_analysis", "worker-analyst"),
            ("مراجعة الاستنتاجات", "critic_review", "critic-001"),
        ],
        "report": [
            ("جمع المصادر", "research_apis", "worker-researcher"),
            ("صياغة التقرير", "generation", "worker-writer"),
            ("مراجعة التقرير", "critic_review", "critic-001"),
        ],
        "data": [
            ("استعلام البيانات", "sql_query", "worker-data"),
            ("تحليل البيانات", "data_analysis", "worker-analyst"),
            ("إعداد المخرجات", "chart_generate", "worker-data"),
        ],
        "generic": [
            ("فهم الطلب", "task_classifier", "orchestrator-001"),
            ("تنفيذ العمل", "generation", "worker-general"),
            ("مراجعة النتيجة", "critic_review", "critic-001"),
        ],
    }
    return [
        {"number": number, "description": description, "tool": tool, "agent": agent}
        for number, (description, tool, agent) in enumerate(templates[task.type], start=1)
    ]


@router.post("/plan")
async def create_plan(task: PlanRequest) -> dict[str, Any]:
    """إنشاء خطة ونشر task.planned مع استمرار التشغيل إن غاب NATS أو PostgreSQL."""
    plan = build_plan(task)
    payload = {"task_id": task.task_id, "type": task.type, "plan": plan}
    await event_publisher.publish("task.planned", "orchestrator", payload)
    return payload


_service = SERVICES["orchestrator"]
app = create_service_app(_service["name"], _service["port"], "منسق تخطيط وتوزيع المهام", [router])
