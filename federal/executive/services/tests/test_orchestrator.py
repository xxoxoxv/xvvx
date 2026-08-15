"""
اختبارات المنسق
الهدف: التحقق من خطة حتمية تحتوي خطوات لجميع أنواع المهام
النطاق: services/orchestrator
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest
from fastapi.testclient import TestClient

from amos_federation.services.orchestrator.main import PlanRequest, app, build_plan


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


def test_plan_endpoint_returns_steps() -> None:
    """واجهة التخطيط تعرض الخطوات الناتجة."""
    response = TestClient(app).post("/v1/plan", json={"type": "report", "description": "تقرير"})
    assert response.status_code == 200
    assert response.json()["plan"]
