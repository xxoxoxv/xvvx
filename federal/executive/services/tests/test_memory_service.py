"""
اختبارات خدمة الذاكرة
الهدف: التحقق من تخزين واسترجاع وبحث الذاكرة
النطاق: services/memory-service
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.memory_service.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token('tester', ['memory:read', 'memory:write'])
}


def test_store_and_get_memory() -> None:
    """تخزين عنصر ثم استرجاعه بالمفتاح."""
    store_resp = client.post(
        "/v1/memory/store",
        headers=AUTH_HEADERS,
        json={"key": "test_key_1", "value": {"content": "تحليل المبيعات أظهر نمواً 20%"}},
    )
    assert store_resp.status_code == 200
    assert store_resp.json()["key"] == "test_key_1"

    get_resp = client.get("/v1/memory/test_key_1", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["key"] == "test_key_1"


def test_query_memory_by_keyword() -> None:
    """البحث بالكلمات المفتاحية يطابق المحتوى المخزن."""
    client.post(
        "/v1/memory/store",
        headers=AUTH_HEADERS,
        json={"key": "finance_report", "value": {"content": "تقرير المبيعات المالية"}},
    )
    client.post(
        "/v1/memory/store",
        headers=AUTH_HEADERS,
        json={"key": "health_data", "value": {"content": "بيانات صحية للموظفين"}},
    )

    query_resp = client.post(
        "/v1/memory/query",
        headers=AUTH_HEADERS,
        json={"query": "المبيعات المالية", "limit": 5},
    )
    assert query_resp.status_code == 200
    results = query_resp.json()
    assert len(results) > 0
    assert any(r["key"] == "finance_report" for r in results)


def test_query_no_match_returns_404() -> None:
    """استعلام بلا نتائج يعيد 404."""
    resp = client.post(
        "/v1/memory/query",
        headers=AUTH_HEADERS,
        json={"query": "zzzznonexistent"},
    )
    assert resp.status_code == 404


def test_search_alias_works() -> None:
    """واجهة /memory/search تعمل كبديل لـ /memory/query."""
    client.post(
        "/v1/memory/store",
        headers=AUTH_HEADERS,
        json={"key": "search_test", "value": {"content": "بحث اختبار"}},
    )
    resp = client.post(
        "/v1/memory/search",
        headers=AUTH_HEADERS,
        json={"query": "بحث", "limit": 5},
    )
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_get_nonexistent_returns_404() -> None:
    """عنصر غير موجود يعيد 404."""
    resp = client.get("/v1/memory/nonexistent_key", headers=AUTH_HEADERS)
    assert resp.status_code == 404


def test_memory_stats() -> None:
    """إحصائيات الذاكرة تعمل."""
    resp = client.get("/v1/memory/stats/summary", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "total_items" in resp.json()


def test_store_rejects_missing_auth() -> None:
    """التخزين يتطلب مصادقة."""
    resp = client.post("/v1/memory/store", json={"key": "x", "value": {}})
    assert resp.status_code == 401


def test_tenant_isolation() -> None:
    """عزل المستأجرين: عنصر لمستأجر A لا يظهر في بحث مستأجر B."""
    client.post(
        "/v1/memory/store",
        headers=AUTH_HEADERS,
        json={"key": "tenant_a_item", "value": {"content": "بيانات سرية للمستأجر A"}, "tenant_id": "tenant_a"},
    )
    # البحث كمستأجر B
    resp = client.post(
        "/v1/memory/query",
        headers=AUTH_HEADERS,
        json={"query": "بيانات سرية", "tenant_id": "tenant_b", "limit": 10},
    )
    # قد يعيد 404 أو قائمة فارغة — المهم أن لا يحصل على نتائج tenant_a
    if resp.status_code == 200:
        for item in resp.json():
            assert item.get("tenant_id") != "tenant_a"
