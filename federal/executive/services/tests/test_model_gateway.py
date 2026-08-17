"""
اختبارات بوابة النماذج
الهدف: التحقق من التوجيه والاستدعاء مع fallback محلي
النطاق: services/model-gateway
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.model_gateway.main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {create_access_token('tester', ['models:invoke'])}"}


def test_route_model_returns_recommendation() -> None:
    """واجهة التوجيه تعيد نموذج موصى به وسلسلة fallback."""
    response = client.post("/v1/models/route", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_model" in data
    assert "available_models" in data
    assert "fallback_chain" in data
    assert len(data["fallback_chain"]) >= 1


def test_invoke_model_with_local_fallback() -> None:
    """الاستدعاء بدون مفتاح API يعيد fallback محلي."""
    response = client.post(
        "/v1/models/invoke",
        headers=AUTH_HEADERS,
        json={"prompt": "اكتب تقريراً عن المبيعات"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "local_fallback"
    assert data["model_used"] == "local-fallback"
    assert len(data["text"]) > 0
    assert data["tokens_used"] > 0
    assert data["latency_ms"] >= 0


def test_invoke_model_rejects_empty_prompt() -> None:
    """الاستدعاء بطلب فارغ يرفض بـ 422."""
    response = client.post(
        "/v1/models/invoke",
        headers=AUTH_HEADERS,
        json={"prompt": ""},
    )
    assert response.status_code == 422


def test_route_model_rejects_missing_auth() -> None:
    """التوجيه يتطلب مصادقة."""
    response = client.post("/v1/models/route")
    assert response.status_code == 401
