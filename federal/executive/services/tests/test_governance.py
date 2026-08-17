"""
اختبارات Governance: Policy Engine + Kill Switch + Promotion Gates + Canary
الهدف: التحقق من السياسات ومفتاح الإيقاف والترقية و Canary
النطاق: services/governance
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.governance.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": "Bearer "
    + create_access_token("tester", ["governance:read", "governance:write"])
}


# === Policy Engine Tests ===


def test_list_policies() -> None:
    """عرض كل السياسات."""
    resp = client.get("/v1/policies", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 3
    assert "promotion_policy" in data["policies"]
    assert "access_policy" in data["policies"]
    assert "budget_policy" in data["policies"]


def test_check_promotion_policy_allows_valid() -> None:
    """سياسة الترقية تسمح بسياق صحيح."""
    resp = client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={
            "policy_name": "promotion_policy",
            "context": {
                "gates_passed": ["evaluation", "shadow", "canary", "human_approval", "activation"],
                "quality_score": 0.85,
                "benchmark_pass_rate": 0.9,
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["allowed"] is True
    assert len(resp.json()["violations"]) == 0


def test_check_promotion_policy_blocks_invalid() -> None:
    """سياسة الترقية تمنع سياق غير صحيح."""
    resp = client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={
            "policy_name": "promotion_policy",
            "context": {
                "gates_passed": ["evaluation"],
                "quality_score": 0.5,
                "benchmark_pass_rate": 0.6,
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["allowed"] is False
    assert len(resp.json()["violations"]) > 0


def test_check_access_policy_restricted_tool() -> None:
    """سياسة الوصول تمنع الأدوات الخطيرة للمستخدمين العاديين."""
    resp = client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={
            "policy_name": "access_policy",
            "context": {"tool": "python_execute", "role": "user"},
        },
    )
    assert resp.json()["allowed"] is False


def test_check_access_policy_admin_allowed() -> None:
    """سياسة الوصول تسمح للأدمن."""
    resp = client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={
            "policy_name": "access_policy",
            "context": {"tool": "python_execute", "role": "admin"},
        },
    )
    assert resp.json()["allowed"] is True


def test_check_budget_policy_exceeds_limit() -> None:
    """سياسة الميزانية تمنع التجاوز."""
    resp = client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={"policy_name": "budget_policy", "context": {"daily_spend_usd": 150.0}},
    )
    assert resp.json()["allowed"] is False


# === Kill Switch Tests ===


def test_get_system_status_normal() -> None:
    """حالة النظام طبيعية."""
    resp = client.get("/v1/system/status", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["level"] in ["normal", "alert", "degraded", "halt"]


def test_activate_kill_switch() -> None:
    """تفعيل مفتاح الإيقاف."""
    resp = client.post(
        "/v1/system/kill-switch",
        headers=AUTH_HEADERS,
        json={"level": "halt", "reason": "اختبار طارئ", "activated_by": "admin"},
    )
    assert resp.status_code == 200
    assert resp.json()["level"] == "halt"
    assert resp.json()["reason"] == "اختبار طارئ"


def test_reset_kill_switch() -> None:
    """إعادة ضبط مفتاح الإيقاف."""
    client.post(
        "/v1/system/kill-switch",
        headers=AUTH_HEADERS,
        json={"level": "alert", "reason": "test", "activated_by": "admin"},
    )
    resp = client.post("/v1/system/kill-switch/reset", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["level"] == "normal"


def test_kill_switch_rejects_invalid_level() -> None:
    """مستوى غير صالح مرفوض."""
    resp = client.post(
        "/v1/system/kill-switch",
        headers=AUTH_HEADERS,
        json={"level": "invalid", "reason": "test", "activated_by": "admin"},
    )
    assert resp.status_code == 422


# === Promotion Gates Tests ===


def test_create_promotion() -> None:
    """إنشاء طلب ترقية."""
    resp = client.post("/v1/promotions", headers=AUTH_HEADERS, json={"model_id": "model-123"})
    assert resp.status_code == 201
    data = resp.json()
    assert "promotion_id" in data
    assert data["status"] == "in_progress"
    assert "evaluation" in data["gates"]
    assert "human_approval" in data["gates"]


def test_check_gate_passed() -> None:
    """فحص بوابة ناجحة."""
    create = client.post("/v1/promotions", headers=AUTH_HEADERS, json={"model_id": "model-1"})
    promo_id = create.json()["promotion_id"]
    resp = client.post(
        f"/v1/promotions/{promo_id}/gates",
        headers=AUTH_HEADERS,
        json={"gate_name": "evaluation", "passed": True},
    )
    assert resp.status_code == 200
    assert resp.json()["gates"]["evaluation"]["status"] == "passed"


def test_check_gate_failed_stops_promotion() -> None:
    """فشل بوابة يوقف الترقية."""
    create = client.post("/v1/promotions", headers=AUTH_HEADERS, json={"model_id": "model-2"})
    promo_id = create.json()["promotion_id"]
    resp = client.post(
        f"/v1/promotions/{promo_id}/gates",
        headers=AUTH_HEADERS,
        json={"gate_name": "evaluation", "passed": False},
    )
    assert resp.json()["status"] == "failed"


def test_all_gates_passed_promotes() -> None:
    """اجتياز كل البوابات يرقى النموذج."""
    create = client.post("/v1/promotions", headers=AUTH_HEADERS, json={"model_id": "model-3"})
    promo_id = create.json()["promotion_id"]
    for gate in ["evaluation", "shadow", "canary", "human_approval", "activation"]:
        client.post(
            f"/v1/promotions/{promo_id}/gates",
            headers=AUTH_HEADERS,
            json={"gate_name": gate, "passed": True},
        )
    resp = client.get(f"/v1/promotions/{promo_id}", headers=AUTH_HEADERS)
    assert resp.json()["status"] == "promoted"


def test_list_promotions() -> None:
    """عرض طلبات الترقية."""
    client.post("/v1/promotions", headers=AUTH_HEADERS, json={"model_id": "model-x"})
    resp = client.get("/v1/promotions", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_nonexistent_promotion_404() -> None:
    """ترقية غير موجودة تعيد 404."""
    resp = client.get("/v1/promotions/nonexistent", headers=AUTH_HEADERS)
    assert resp.status_code == 404


# === Canary Tests ===


def test_create_canary() -> None:
    """إنشاء Canary deployment."""
    resp = client.post(
        "/v1/canary",
        headers=AUTH_HEADERS,
        json={"model_id": "model-canary-1", "traffic_percentage": 5},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "canary_id" in data
    assert data["traffic_percentage"] == 5
    assert data["status"] == "active"


def test_get_canary() -> None:
    """استرجاع Canary."""
    create = client.post(
        "/v1/canary", headers=AUTH_HEADERS, json={"model_id": "model-c", "traffic_percentage": 10}
    )
    canary_id = create.json()["canary_id"]
    resp = client.get(f"/v1/canary/{canary_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_update_canary_metrics_healthy() -> None:
    """تحديث مقاييس Canary صحية."""
    create = client.post(
        "/v1/canary",
        headers=AUTH_HEADERS,
        json={"model_id": "model-healthy", "traffic_percentage": 5},
    )
    canary_id = create.json()["canary_id"]
    resp = client.patch(
        f"/v1/canary/{canary_id}/metrics",
        headers=AUTH_HEADERS,
        json={"requests": 100, "errors": 1, "avg_latency_ms": 200, "quality_score": 0.9},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_canary_auto_rollback_high_errors() -> None:
    """Canary يتراجع تلقائيًا عند ارتفاع الأخطاء."""
    create = client.post(
        "/v1/canary", headers=AUTH_HEADERS, json={"model_id": "model-bad", "traffic_percentage": 5}
    )
    canary_id = create.json()["canary_id"]
    resp = client.patch(
        f"/v1/canary/{canary_id}/metrics",
        headers=AUTH_HEADERS,
        json={"requests": 100, "errors": 20, "avg_latency_ms": 500, "quality_score": 0.8},
    )
    assert resp.json()["status"] == "rolled_back"


def test_canary_auto_rollback_low_quality() -> None:
    """Canary يتراجع تلقائيًا عند انخفاض الجودة."""
    create = client.post(
        "/v1/canary",
        headers=AUTH_HEADERS,
        json={"model_id": "model-low-q", "traffic_percentage": 5},
    )
    canary_id = create.json()["canary_id"]
    resp = client.patch(
        f"/v1/canary/{canary_id}/metrics",
        headers=AUTH_HEADERS,
        json={"requests": 50, "errors": 0, "avg_latency_ms": 100, "quality_score": 0.3},
    )
    assert resp.json()["status"] == "rolled_back"


def test_manual_canary_rollback() -> None:
    """تراجع يدوي عن Canary."""
    create = client.post(
        "/v1/canary",
        headers=AUTH_HEADERS,
        json={"model_id": "model-manual", "traffic_percentage": 5},
    )
    canary_id = create.json()["canary_id"]
    resp = client.post(f"/v1/canary/{canary_id}/rollback", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "rolled_back"


def test_list_canaries() -> None:
    """عرض Canary deployments."""
    client.post(
        "/v1/canary", headers=AUTH_HEADERS, json={"model_id": "model-list", "traffic_percentage": 5}
    )
    resp = client.get("/v1/canary", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# === Audit Log Tests ===


def test_audit_log_has_entries() -> None:
    """سجل التدقيق يحتوي على إدخالات."""
    client.get("/v1/policies", headers=AUTH_HEADERS)
    client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={"policy_name": "budget_policy", "context": {"daily_spend_usd": 50}},
    )
    resp = client.get("/v1/audit", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0


def test_audit_chain_is_valid() -> None:
    """سلسلة Audit Log سليمة."""
    client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={"policy_name": "budget_policy", "context": {"daily_spend_usd": 50}},
    )
    resp = client.get("/v1/audit/verify", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["valid"] is True


def test_audit_entries_have_hash() -> None:
    """كل إدخال في السجل له hash."""
    client.post(
        "/v1/policies/check",
        headers=AUTH_HEADERS,
        json={"policy_name": "budget_policy", "context": {"daily_spend_usd": 50}},
    )
    resp = client.get("/v1/audit", headers=AUTH_HEADERS)
    for entry in resp.json():
        assert "hash" in entry
        assert "prev_hash" in entry
        assert len(entry["hash"]) == 64


def test_governance_rejects_missing_auth() -> None:
    """الخدمة تتطلب مصادقة."""
    resp = client.get("/v1/policies")
    assert resp.status_code == 401
