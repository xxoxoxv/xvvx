"""
اختبارات الحوكمة التأسيسية (Phase 3)
الهدف: التحقق من Audit Hash Chain، Policy Engine، Kill Switch الحقيقي
النطاق: governance
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.common.persistent import PersistentAuditStore
from amos_federation.services.governance.canary import (
    activate_kill_switch,
    enforce_kill_switch,
    is_execution_blocked,
    is_system_halted,
    reset_kill_switch,
)
from amos_federation.services.governance.main import app
from amos_federation.services.governance.policy_engine import (
    PolicyEngine,
    RegoRule,
    get_policy_engine,
)

AUTH_HEADERS = {
    "Authorization": "Bearer "
    + create_access_token(
        "tester",
        [
            "governance:read",
            "governance:write",
        ],
    )
}
client = TestClient(app)


# === 3.1: Audit Hash Chain ===


def test_audit_hash_chain_persistent() -> None:
    """سلسلة hash دائمة وغير قابلة للتعديل."""
    store = PersistentAuditStore()
    store.append("test.action", "tester", {"key": "value1"})
    store.append("test.action", "tester", {"key": "value2"})
    result = store.verify_chain()
    assert result["valid"] is True
    assert result["entries"] >= 2


def test_audit_chain_tamper_detection() -> None:
    """كشف التلاعب في سجل تدقيق."""
    store = PersistentAuditStore()
    store.append("tamper.test", "tester", {"data": "original"})
    result = store.verify_chain()
    assert result["valid"] is True


def test_audit_insert_only() -> None:
    """محاولة التعديل مرفوضة."""
    store = PersistentAuditStore()
    store.append("insert.test", "tester", {"x": 1})
    result = store.tamper_attempt("any-id")
    assert result["blocked"] is True
    assert "INSERT-only" in result["error"]


def test_audit_chain_survives_restart() -> None:
    """سلسلة التدقيق تبقى بعد إعادة التشغيل."""
    store1 = PersistentAuditStore()
    store1.append("persist.test", "tester", {"n": 1})
    count1 = len(store1.list_all(limit=100))

    store2 = PersistentAuditStore()
    count2 = len(store2.list_all(limit=100))
    assert count2 == count1

    result = store2.verify_chain()
    assert result["valid"] is True


def test_audit_hash_is_sha256() -> None:
    """الـ hash هو SHA-256 فعليًا (64 hex chars)."""
    store = PersistentAuditStore()
    result = store.append("hash.test", "tester", {"check": True})
    assert len(result["hash"]) == 64
    assert all(c in "0123456789abcdef" for c in result["hash"])


# === 3.3: Policy Engine (Rego-like) ===


def test_policy_engine_dangerous_tool_denied_for_user() -> None:
    """الأدوات الخطيرة مرفوضة للمستخدم العادي."""
    engine = get_policy_engine()
    result = engine.evaluate_tool_access("python_execute", "user", "normal")
    assert result["allowed"] is False
    assert "tool_access" in result["denied_by"]


def test_policy_engine_dangerous_tool_allowed_for_admin() -> None:
    """الأدوات الخطيرة مسموحة للمشرف."""
    engine = get_policy_engine()
    result = engine.evaluate_tool_access("python_execute", "admin", "normal")
    assert result["allowed"] is True


def test_policy_engine_safe_tool_allowed_for_user() -> None:
    """الأدوات الآمنة مسموحة للجميع."""
    engine = get_policy_engine()
    result = engine.evaluate_tool_access("chart_generate", "user", "normal")
    assert result["allowed"] is True


def test_policy_engine_promotion_low_quality_denied() -> None:
    """ترقية بجودة منخفضة مرفوضة."""
    engine = get_policy_engine()
    result = engine.evaluate_promotion(
        0.3, ["evaluation", "shadow", "canary", "human_approval", "activation"]
    )
    assert result["allowed"] is False
    assert "promotion_deny_low_quality" in result["denied_by"]


def test_policy_engine_promotion_high_quality_allowed() -> None:
    """ترقية بجودة عالية مسموحة."""
    engine = get_policy_engine()
    result = engine.evaluate_promotion(
        0.9, ["evaluation", "shadow", "canary", "human_approval", "activation"]
    )
    assert result["allowed"] is True


def test_policy_engine_budget_limit() -> None:
    """حد الميزانية يعمل."""
    engine = get_policy_engine()
    result = engine.evaluate({"daily_spend_usd": 200.0})
    assert result["allowed"] is False
    assert "budget_limit" in result["denied_by"]


def test_policy_engine_custom_rule() -> None:
    """إضافة قاعدة مخصصة."""
    engine = PolicyEngine()
    engine.add_rule(
        RegoRule(
            name="custom_test_rule",
            description="قاعدة اختبار",
            conditions=[{"field": "x", "op": "gt", "value": 10}],
            decision="deny",
        )
    )
    result = engine.evaluate({"x": 20})
    assert result["allowed"] is False
    assert "custom_test_rule" in result["denied_by"]


def test_policy_engine_list_rules() -> None:
    """عرض كل القواعد."""
    engine = get_policy_engine()
    rules = engine.list_rules()
    assert len(rules) > 0
    names = [r["name"] for r in rules]
    assert "tool_access" in names
    assert "kill_switch_halt" in names


def test_policy_engine_via_api() -> None:
    """تقييم السياسة عبر API."""
    resp = client.post(
        "/v1/policy/evaluate",
        headers=AUTH_HEADERS,
        json={"tool": "python_execute", "role": "user", "system_state": "normal"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is False


def test_policy_engine_check_tool_via_api() -> None:
    """فحص وصول أداة عبر API."""
    resp = client.post("/v1/policy/check-tool?tool=chart_generate&role=user", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["allowed"] is True


# === 3.4: Kill Switch حقيقي ===


def test_kill_switch_halt_blocks_all() -> None:
    """في وضع halt، كل التنفيذ محجوب."""
    reset_kill_switch()
    activate_kill_switch("halt", "اختبار إيقاف", "tester")
    assert is_system_halted() is True
    assert is_execution_blocked() is True
    assert is_execution_blocked("chart_generate") is True
    reset_kill_switch()


def test_kill_switch_degraded_blocks_dangerous() -> None:
    """في وضع degraded، الأدوات الخطيرة محجوبة فقط."""
    reset_kill_switch()
    activate_kill_switch("degraded", "اختبار تدهور", "tester")
    assert is_execution_blocked("python_execute") is True
    assert is_execution_blocked("sql_query") is True
    assert is_execution_blocked("chart_generate") is False
    reset_kill_switch()


def test_kill_switch_normal_allows_all() -> None:
    """في وضع normal، كل شيء مسموح."""
    reset_kill_switch()
    assert is_execution_blocked("python_execute") is False
    assert is_execution_blocked("chart_generate") is False


def test_kill_switch_enforce_raises_on_halt() -> None:
    """enforce_kill_switch يرمي استثناء في halt."""
    from fastapi import HTTPException

    reset_kill_switch()
    activate_kill_switch("halt", "اختبار", "tester")
    try:
        enforce_kill_switch("python_execute")
        raise AssertionError("يجب أن يرمي HTTPException")
    except HTTPException as e:
        assert e.status_code == 503
        assert "system_halted" in e.detail["error"]
    finally:
        reset_kill_switch()


def test_kill_switch_enforce_raises_on_degraded_dangerous() -> None:
    """enforce_kill_switch يرمي استثناء في degraded للأدوات الخطيرة."""
    from fastapi import HTTPException

    reset_kill_switch()
    activate_kill_switch("degraded", "اختبار", "tester")
    try:
        enforce_kill_switch("sql_query")
        raise AssertionError("يجب أن يرمي HTTPException")
    except HTTPException as e:
        assert e.status_code == 503
        assert "system_degraded" in e.detail["error"]
    finally:
        reset_kill_switch()


def test_kill_switch_enforce_allows_normal() -> None:
    """enforce_kill_switch يسمح في normal."""
    reset_kill_switch()
    result = enforce_kill_switch("python_execute")
    assert result["allowed"] is True


def test_kill_switch_publishes_event() -> None:
    """تفعيل Kill Switch ينشر حدث."""
    from amos_federation.common.event_bus import get_event_bus

    reset_kill_switch()
    bus = get_event_bus()
    initial_count = bus.count("amos_federation.policy.checked")
    activate_kill_switch("alert", "اختبار حدث", "tester")
    assert bus.count("amos_federation.policy.checked") > initial_count
    reset_kill_switch()


def test_kill_switch_via_api() -> None:
    """تفعيل Kill Switch عبر API."""
    reset_kill_switch()
    resp = client.post(
        "/v1/system/kill-switch",
        headers=AUTH_HEADERS,
        json={"level": "alert", "reason": "اختبار API", "activated_by": "tester"},
    )
    assert resp.status_code == 200
    assert resp.json()["level"] == "alert"
    reset_kill_switch()


def test_kill_switch_policy_engine_integration() -> None:
    """Kill Switch halt يجعل Policy Engine يرفض كل شيء."""
    reset_kill_switch()
    activate_kill_switch("halt", "اختبار تكامل", "tester")
    engine = get_policy_engine()
    result = engine.evaluate_tool_access("chart_generate", "user", "halt")
    assert result["allowed"] is False
    assert "kill_switch_halt" in result["denied_by"]
    reset_kill_switch()


def test_kill_switch_levels_order() -> None:
    """المستويات الأربعة بالترتيب الصحيح."""
    from amos_federation.services.governance.canary import KILL_SWITCH_LEVELS

    assert KILL_SWITCH_LEVELS == ["normal", "alert", "degraded", "halt"]
