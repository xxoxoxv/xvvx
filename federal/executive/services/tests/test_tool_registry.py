"""
اختبارات سجل الأدوات
الهدف: التحقق من تسجيل وعرض وحل الأدوات
النطاق: services/tool-registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.tool_registry.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": f"Bearer {create_access_token('tester', ['tools:read', 'tools:write'])}"
}


def test_list_tools_returns_seed_data() -> None:
    """سجل الأدوات يحتوي على أدوات أولية من tool-index.yaml."""
    response = client.get("/v1/tools", headers=AUTH_HEADERS)
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) >= 10
    ids = {t["tool_id"] for t in tools}
    assert "sql_query" in ids
    assert "generation" in ids


def test_get_tool_by_id() -> None:
    """استرجاع أداة بالمعرّف يعمل."""
    response = client.get("/v1/tools/sql_query", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["tool_id"] == "sql_query"


def test_get_nonexistent_tool_returns_404() -> None:
    """أداة غير موجودة تعيد 404."""
    response = client.get("/v1/tools/nonexistent", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_register_new_tool() -> None:
    """تسجيل أداة جديدة ينجح."""
    response = client.post(
        "/v1/tools",
        headers=AUTH_HEADERS,
        json={
            "tool_id": "test_custom_tool",
            "name": "Custom Test Tool",
            "version": "0.1.0",
            "risk_level": "low",
        },
    )
    assert response.status_code == 201
    assert response.json()["tool_id"] == "test_custom_tool"


def test_resolve_tools_by_keyword() -> None:
    """حل الأدوات بالكلمات المفتاحية يطابق sql."""
    response = client.post(
        "/v1/tools/resolve",
        headers=AUTH_HEADERS,
        params={"query": "sql query database"},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert any(r["tool_id"] == "sql_query" for r in results)


def test_resolve_tools_no_match_returns_404() -> None:
    """استعلام بلا نتائج يعيد 404."""
    response = client.post(
        "/v1/tools/resolve",
        headers=AUTH_HEADERS,
        params={"query": "zzzznonexistent"},
    )
    assert response.status_code == 404


def test_resolve_rejects_missing_auth() -> None:
    """حل الأدوات يتطلب مصادقة."""
    response = client.post("/v1/tools/resolve", params={"query": "test"})
    assert response.status_code == 401
