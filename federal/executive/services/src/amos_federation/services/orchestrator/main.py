"""
AMOS-Federation Orchestrator
الهدف: تخطيط المهام إلى خطوات حتمية، وتثبيت الخطة عبر النواة التنفيذية
النطاق: خدمة orchestrator على المنفذ 8001
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

R1 — توحيد مسار التنفيذ الخارجي:

قبل R1 كانت `POST /v1/plan` تبني خطة، وتنشرها كحدث إخطاري، ثم **تنساها**: لا صفّ
في القاعدة يحملها، ولا إذن سيادي عليها، ولا انتقال حالة، ولا قيد تدقيق. أي منفّذ
تالٍ كان يستلم خطة لا أصل قانوني لها في الدولة.

بعد R1 للواجهة وضعان صريحان لا وضع ملتبس واحد:

- **الوضع القانوني** (`task_id` لمهمّة قائمة): التفويض إلى
  `ExecutiveCore.advance_to(..., TaskState.PLANNED)`. النواة هي من تستأذن البوابة
  وتكتب الخطة في صفّ المهمّة بانتقال ذرّي وتقيّدها في التدقيق وتنشر حدثًا دائمًا.
- **الوضع الاستطلاعي** (`preview=true` بلا `task_id`): خطة تُعاد للقارئ ولا تُحفَظ
  ولا تُنشَر ولا تُعتبر أمرًا. مُعلَنة في الاستجابة بـ`mode="preview"` و
  `persisted=false`، لأن خطة غير محفوظة تُقدَّم كأنها محفوظة كذبة تشغيلية.

`build_plan` لم يُنقل ولم يُنسخ: هو **مصدر التخطيط الوحيد**، وتستدعيه النواة
نفسها في `_plan_for`. فالتوجيه هنا لم يُنشئ منطق تخطيط ثانيًا.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from amos_federation.common.auth import require_auth
from amos_federation.common.events import event_publisher
from amos_federation.common.registry import SERVICES
from amos_federation.common.schemas import TaskRequest
from amos_federation.common.service import create_service_app
from amos_federation.services.executive_core.engine import get_executive_core
from amos_federation.services.executive_core.http_errors import (
    PLAN_REQUIRES_CANONICAL_TASK,
    to_http_exception,
)
from amos_federation.services.executive_core.states import TaskState

router = APIRouter(prefix="/v1", tags=["orchestrator"])


class PlanRequest(TaskRequest):
    """طلب تخطيط. `task_id` يعني تخطيطًا قانونيًّا؛ `preview` يعني استطلاعًا."""

    task_id: str | None = None
    preview: bool = Field(
        default=False,
        description="خطة استطلاعية لا تُحفَظ ولا تُنشَر — تُطلَب صراحةً عند غياب task_id",
    )


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
def create_plan(
    task: PlanRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تخطيط قانوني عبر النواة، أو استطلاع مُعلَن لا يُحفَظ.

    نقطة النهاية متزامنة بقصد: النواة قد تستدعي وكيلًا غير متزامن عبر
    `asyncio.run`، وذلك ممنوع داخل حلقة حدث قائمة.
    """
    if task.task_id is None:
        if not task.preview:
            raise HTTPException(status_code=400, detail=PLAN_REQUIRES_CANONICAL_TASK)
        return {
            "task_id": None,
            "type": task.type,
            "plan": build_plan(task),
            "mode": "preview",
            "persisted": False,
            "authority": None,
        }

    core = get_executive_core()
    try:
        result = core.advance_to(task.task_id, TaskState.PLANNED)
    except Exception as exc:
        raise to_http_exception(exc) from exc

    stored = result["task"]
    return {
        "task_id": stored["id"],
        "type": stored["type"],
        "plan": stored["plan"] or [],
        "mode": "canonical",
        "persisted": bool(stored["plan"]),
        "final_state": result["final_state"],
        "reached_planned": result["reached"],
        "transitions": result["transitions"],
        "authority": [transition["authority"] for transition in result["transitions"]],
    }


@router.post("/plan/notify")
async def notify_plan(
    payload: dict[str, Any],
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إخطار الطبقة القديمة بخطة **سبق** تثبيتها قانونيًّا — إعلان لا تنفيذ.

    فُصل الإخطار عن التخطيط لأن نشر `task.planned` من داخل مسار التخطيط كان يجعل
    الإخطار يبدو أثرًا تنفيذيًّا وهو ليس كذلك. من يريد الإخطار يطلبه صراحةً.
    """
    await event_publisher.publish("task.planned", "orchestrator", payload)
    return {"published": True, "subject": "task.planned", "execution_effect": False}


_service = SERVICES["orchestrator"]
app = create_service_app(_service["name"], _service["port"], "منسق تخطيط وتوزيع المهام", [router])
