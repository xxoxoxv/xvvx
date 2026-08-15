"""
اختبارات شاملة من البداية للنهاية (E2E)
الهدف: التحقق من دورة: طلب → تخطيط → تنفيذ → نتيجة
النطاق: orchestrator → agent-runtime
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.orchestrator.main import app as orchestrator_app
from amos_federation.services.agent_runtime.main import app as agent_app
from amos_federation.services.api_gateway.main import app as gateway_app

orchestrator_client = TestClient(orchestrator_app)
agent_client = TestClient(agent_app)
gateway_client = TestClient(gateway_client_app := gateway_app)

AUTH_HEADERS = {
    "Authorization": f"Bearer {create_access_token('e2e-tester', ['tasks:write', 'tasks:read', 'tasks:execute'])}"
}


def test_e2e_plan_then_execute() -> None:
    """دورة كاملة: تخطيط مهمة ثم تنفيذها عبر الوكيل."""
    # الخطوة 1: التخطيط
    plan_response = orchestrator_client.post(
        "/v1/plan",
        json={
            "type": "analysis",
            "description": "حلل أداء المبيعات في الربع الثاني",
            "task_id": "task-e2e-001",
        },
    )
    assert plan_response.status_code == 200
    plan_data = plan_response.json()
    assert len(plan_data["plan"]) >= 2

    # الخطوة 2: التنفيذ
    execute_response = agent_client.post(
        "/v1/execute",
        headers=AUTH_HEADERS,
        json={
            "task": {
                "task_id": "task-e2e-001",
                "type": "analysis",
                "description": "حلل أداء المبيعات في الربع الثاني",
                "domain": "finance",
            },
            "plan": plan_data["plan"],
        },
    )
    assert execute_response.status_code == 200
    exec_data = execute_response.json()
    assert exec_data["status"] == "completed"
    assert exec_data["task_id"] == "task-e2e-001"
    assert all(step["status"] == "completed" for step in exec_data["steps"])


def test_e2e_task_creation_then_plan() -> None:
    """دورة: إنشاء مهمة في البوابة ثم تخطيطها."""
    # إنشاء المهمة
    create_response = gateway_client.post(
        "/v1/tasks",
        headers=AUTH_HEADERS,
        json={
            "type": "report",
            "description": "تقرير سنوي عن الأداء",
            "priority": "high",
        },
    )
    assert create_response.status_code == 202
    task_id = create_response.json()["task_id"]

    # استرجاع المهمة
    get_response = gateway_client.get(
        f"/v1/tasks/{task_id}",
        headers=AUTH_HEADERS,
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "pending"

    # تخطيط المهمة
    plan_response = orchestrator_client.post(
        "/v1/plan",
        json={
            "type": "report",
            "description": "تقرير سنوي عن الأداء",
            "task_id": task_id,
        },
    )
    assert plan_response.status_code == 200
    assert len(plan_response.json()["plan"]) >= 2


def test_e2e_all_task_types_complete() -> None:
    """كل أنواع المهام تكتمل دورتها من التخطيط للتنفيذ."""
    for task_type in ["analysis", "report", "data", "generic"]:
        # التخطيط
        plan_resp = orchestrator_client.post(
            "/v1/plan",
            json={"type": task_type, "description": f"مهمة {task_type}"},
        )
        assert plan_resp.status_code == 200
        plan = plan_resp.json()["plan"]

        # التنفيذ
        exec_resp = agent_client.post(
            "/v1/execute",
            headers=AUTH_HEADERS,
            json={
                "task": {
                    "task_id": f"task-e2e-{task_type}",
                    "type": task_type,
                    "description": f"مهمة {task_type}",
                },
                "plan": plan,
            },
        )
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "completed"
