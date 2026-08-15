"""
اختبارات وقت تشغيل الوكلاء
الهدف: التحقق من تنفيذ المهام عبر Worker Agent
النطاق: services/agent-runtime
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.agent_runtime.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": f"Bearer {create_access_token('tester', ['tasks:execute'])}"
}


def test_execute_task_with_plan() -> None:
    """تنفيذ مهمة بخطة كاملة ينتج نتائج لكل خطوة."""
    response = client.post(
        "/v1/execute",
        headers=AUTH_HEADERS,
        json={
            "task": {
                "task_id": "task-test-001",
                "type": "analysis",
                "description": "حلل أداء المبيعات",
                "domain": "finance",
            },
            "plan": [
                {"number": 1, "description": "جمع البيانات", "tool": "research_apis", "agent": "worker-researcher"},
                {"number": 2, "description": "تحليل", "tool": "data_analysis", "agent": "worker-analyst"},
                {"number": 3, "description": "رسم بياني", "tool": "chart_generate", "agent": "worker-analyst"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["task_id"] == "task-test-001"
    assert len(data["steps"]) == 3
    assert all(step["status"] == "completed" for step in data["steps"])
    assert "اكتملت" in data["result_summary"]


def test_execute_unknown_tool_is_skipped() -> None:
    """خطوة بأداة غير معروفة تُتخطى ولا تفشل المهمة."""
    response = client.post(
        "/v1/execute",
        headers=AUTH_HEADERS,
        json={
            "task": {"task_id": "task-test-002", "description": "اختبار"},
            "plan": [
                {"number": 1, "description": "خطوة صحيحة", "tool": "generation", "agent": "worker"},
                {"number": 2, "description": "أداة غير معروفة", "tool": "nonexistent_tool", "agent": "worker"},
            ],
        },
    )
    assert response.status_code == 200
    steps = response.json()["steps"]
    assert steps[0]["status"] == "completed"
    assert steps[1]["status"] == "skipped"


def test_execute_rejects_empty_plan() -> None:
    """خطة فارغة تُرفض بـ 422."""
    response = client.post(
        "/v1/execute",
        headers=AUTH_HEADERS,
        json={"task": {"description": "اختبار"}, "plan": []},
    )
    assert response.status_code == 422


def test_execute_rejects_missing_auth() -> None:
    """التنفيذ يتطلب مصادقة."""
    response = client.post("/v1/execute", json={"task": {}, "plan": [{}]})
    assert response.status_code == 401


def test_available_agents() -> None:
    """عرض الوكلاء المتاحين."""
    response = client.get("/v1/agents/available", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_available_tools() -> None:
    """عرض الأدوات المتاحة في الصندوق الرمل."""
    response = client.get("/v1/tools/available", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert "sql_query" in response.json()
    assert "generation" in response.json()
