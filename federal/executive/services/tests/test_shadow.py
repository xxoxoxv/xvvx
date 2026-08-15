"""
اختبارات Shadow Testing و Cost Tracking
الهدف: التحقق من تشغيل shadow tests وتتبع التكلفة
النطاق: services/model_gateway (shadow + cost)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.model_gateway.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token("tester", ["model:read", "model:write"])
}


def test_shadow_test_creates_comparison() -> None:
    """اختبار shadow ينشئ مقارنة بين ألفا وبيتا."""
    resp = client.post("/v1/shadow/test", headers=AUTH_HEADERS, json={"prompt": "حلل بيانات المبيعات"})
    assert resp.status_code == 201
    data = resp.json()
    assert "shadow_id" in data
    assert "alpha" in data
    assert "beta" in data
    assert "comparison" in data
    assert "metrics" in data


def test_shadow_comparison_has_similarity() -> None:
    """مقارنة shadow تحتوي على درجة تشابه نصي."""
    resp = client.post("/v1/shadow/test", headers=AUTH_HEADERS, json={"prompt": "تقرير الأداء المالي"})
    comparison = resp.json()["comparison"]
    assert "text_similarity" in comparison
    assert 0.0 <= comparison["text_similarity"] <= 1.0
    assert "latency_diff_ms" in comparison


def test_shadow_results_list() -> None:
    """عرض نتائج shadow."""
    client.post("/v1/shadow/test", headers=AUTH_HEADERS, json={"prompt": "تقرير سريع"})
    resp = client.get("/v1/shadow/results", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0


def test_shadow_result_by_id() -> None:
    """استرجاع نتيجة shadow بالمعرّف."""
    create_resp = client.post("/v1/shadow/test", headers=AUTH_HEADERS, json={"prompt": "تحليل"})
    shadow_id = create_resp.json()["shadow_id"]
    resp = client.get(f"/v1/shadow/results/{shadow_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["shadow_id"] == shadow_id


def test_shadow_nonexistent_404() -> None:
    """نتيجة shadow غير موجودة تعيد 404."""
    resp = client.get("/v1/shadow/results/nonexistent", headers=AUTH_HEADERS)
    assert resp.status_code == 404


def test_shadow_stats() -> None:
    """إحصائيات shadow تعمل."""
    client.post("/v1/shadow/test", headers=AUTH_HEADERS, json={"prompt": "اختبار"})
    resp = client.get("/v1/shadow/stats", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "avg_similarity" in data
    assert data["total"] > 0


def test_shadow_rejects_missing_auth() -> None:
    """اختبار shadow يتطلب مصادقة."""
    resp = client.post("/v1/shadow/test", json={"prompt": "اختبار"})
    assert resp.status_code == 401


def test_invoke_tracks_cost() -> None:
    """استدعاء النموذج يسجل التكلفة."""
    resp = client.post("/v1/models/invoke", headers=AUTH_HEADERS, json={"prompt": "اختبار التكلفة"})
    assert resp.status_code == 200
    assert "cost_usd" in resp.json()


def test_cost_summary() -> None:
    """ملخص التكاليف يعمل."""
    client.post("/v1/models/invoke", headers=AUTH_HEADERS, json={"prompt": "اختبار"})
    resp = client.get("/v1/cost/summary", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_invocations" in data
    assert "total_cost_usd" in data
    assert "by_model" in data
    assert data["total_invocations"] > 0


def test_cost_summary_by_model() -> None:
    """ملخص التكاليف يصنّف حسب النموذج."""
    client.post("/v1/models/invoke", headers=AUTH_HEADERS, json={"prompt": "اختبار 1"})
    client.post("/v1/models/invoke", headers=AUTH_HEADERS, json={"prompt": "اختبار 2"})
    resp = client.get("/v1/cost/summary", headers=AUTH_HEADERS)
    by_model = resp.json()["by_model"]
    assert len(by_model) > 0
    for model_data in by_model.values():
        assert "invocations" in model_data
        assert "total_tokens" in model_data
        assert "total_cost" in model_data
