"""
اختبارات بوابة الواجهات
الهدف: التحقق من دورة إنشاء وقراءة المهام وحماية JWT
النطاق: services/api_gateway
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.api_gateway.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": f"Bearer {create_access_token('tester', ['tasks:write'], 'finance')}"
}


def test_task_creation_then_reading() -> None:
    """تقبل البوابة المهمة ثم تسمح بقراءتها بالرمز الصحيح."""
    response = client.post(
        "/v1/tasks",
        headers=AUTH_HEADERS,
        json={"type": "analysis", "description": "حلل المبيعات", "domain": "finance"},
    )
    assert response.status_code == 202
    accepted = response.json()
    assert accepted["task_id"].startswith("task-")
    details = client.get(f"/v1/tasks/{accepted['task_id']}", headers=AUTH_HEADERS)
    assert details.status_code == 200
    assert details.json()["description"] == "حلل المبيعات"
    assert details.json()["tenant_id"] == "finance"


def test_task_creation_rejects_missing_token() -> None:
    """تمنع البوابة الطلبات بلا Bearer token."""
    response = client.post("/v1/tasks", json={"description": "طلب بلا مصادقة"})
    assert response.status_code == 401


def test_task_fields_are_validated() -> None:
    """ترفض البوابة الوصف الفارغ ونوع المهمة غير المدعوم."""
    empty = client.post("/v1/tasks", headers=AUTH_HEADERS, json={"description": ""})
    invalid_type = client.post(
        "/v1/tasks", headers=AUTH_HEADERS, json={"type": "unknown", "description": "صالح"}
    )
    assert empty.status_code == 422
    assert invalid_type.status_code == 422
