"""
اختبارات المنسق
الهدف: التحقق من خطة حتمية تحتوي خطوات لجميع أنواع المهام
النطاق: services/orchestrator
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16 (R1)

ما تغيّر في R1: `POST /v1/plan` صارت تغيّر حالة الدولة عند إعطائها `task_id`،
فصارت تطلب مصادقة، وصار التخطيط غير المحفوظ يُطلَب صراحةً بـ`preview=true`.
اختبار الواجهة هنا يغطّي الوضع الاستطلاعي؛ الوضع القانوني مُغطّى في
`test_r1_canonical_execution_path.py` حيث تُقاس آثاره في القاعدة والتدقيق.
`build_plan` لم يتغيّر، واختباراه الحتميّان باقيان كما هما.
"""

import pytest
from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.orchestrator.main import PlanRequest, app, build_plan

AUTH_HEADERS = {"Authorization": f"Bearer {create_access_token('tester', ['tasks:write'])}"}


@pytest.mark.parametrize("task_type", ["analysis", "report", "data", "generic"])
def test_plan_has_ordered_steps_for_every_task_type(task_type: str) -> None:
    """كل نوع مدعوم ينتج سلسلة خطوات مع أداة ووكيل."""
    plan = build_plan(PlanRequest(type=task_type, description="اختبار"))
    assert len(plan) >= 2
    assert [step["number"] for step in plan] == list(range(1, len(plan) + 1))
    assert all(step["tool"] and step["agent"] for step in plan)


def test_planning_is_deterministic() -> None:
    """المدخل نفسه ينتج الخطة نفسها تمامًا."""
    task = PlanRequest(type="analysis", description="نفس المهمة", task_id="task-1")
    assert build_plan(task) == build_plan(task)


def test_preview_plan_endpoint_returns_unpersisted_steps() -> None:
    """الوضع الاستطلاعي يعرض الخطوات ويُعلن أنها غير محفوظة ولا سلطة عليها."""
    response = TestClient(app).post(
        "/v1/plan",
        headers=AUTH_HEADERS,
        json={"type": "report", "description": "تقرير", "preview": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]
    assert body["mode"] == "preview"
    assert body["persisted"] is False


def test_plan_endpoint_requires_authentication() -> None:
    """الواجهة تغيّر حالة الدولة في وضعها القانوني — فلا تعمل بلا مصادقة."""
    response = TestClient(app).post("/v1/plan", json={"type": "report", "description": "تقرير"})
    assert response.status_code == 401
