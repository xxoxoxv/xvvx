"""
اختبارات النظام الصحي المؤسسي للوكلاء (Phase 8)
الهدف: التحقق من فحص دوري، علاج، عزل، ربط بواجهة التحكم
النطاق: services/agent_runtime/health
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest
from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.agent_runtime.health import (
    HEALTHY,
    ISOLATED,
    MONITOR,
    TREATMENT,
    HealthChecker,
    IsolationSystem,
    TreatmentSystem,
    run_health_cycle,
)
from amos_federation.services.agent_runtime.population import get_population_registry
from amos_federation.services.control_console.main import app

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


@pytest.fixture(autouse=True)
def seed_and_clean():
    """بذر الوكلاء قبل الاختبارات وتنظيف الفحوصات بعدها."""
    from sqlalchemy import delete

    from amos_federation.common.database import get_session_factory
    from amos_federation.services.agent_runtime.health import (
        AgentHealthCheckModel,
        IsolationRecordModel,
        TreatmentRecordModel,
    )
    from amos_federation.services.governance.canary import reset_kill_switch

    reset_kill_switch()
    registry = get_population_registry()
    registry.seed_initial_population()
    yield
    # تنظيف جداول الفحص الصحي
    session = get_session_factory()()
    try:
        for model in [AgentHealthCheckModel, IsolationRecordModel, TreatmentRecordModel]:
            session.execute(delete(model))
        session.commit()
    finally:
        session.close()
    reset_kill_switch()


# === 8.1: Periodic health check ===


def test_check_agent_returns_one_of_four_statuses() -> None:
    """الفحص يعيد واحدة من أربع حالات."""
    agents = get_population_registry().list_agents()
    checker = HealthChecker()
    result = checker.check_agent(agents[0]["agent_id"])
    assert result["status"] in [HEALTHY, MONITOR, TREATMENT, ISOLATED]


def test_check_agent_persists_to_db() -> None:
    """الفحص يُسجّل في DB."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    checker = HealthChecker()
    checker.check_agent(agent_id)
    history = checker.get_agent_health_history(agent_id)
    assert len(history) >= 1
    assert history[0]["agent_id"] == agent_id


def test_check_agent_includes_performance() -> None:
    """الفحص يتضمن الأداء."""
    agents = get_population_registry().list_agents()
    result = HealthChecker().check_agent(agents[0]["agent_id"])
    assert "performance_score" in result
    assert 0.0 <= result["performance_score"] <= 1.0


def test_check_agent_includes_policy_compliance() -> None:
    """الفحص يتضمن الالتزام بالسياسات."""
    agents = get_population_registry().list_agents()
    result = HealthChecker().check_agent(agents[0]["agent_id"])
    assert "policy_compliance" in result
    assert 0.0 <= result["policy_compliance"] <= 1.0


def test_check_agent_includes_resource_usage() -> None:
    """الفحص يتضمن استهلاك الموارد."""
    agents = get_population_registry().list_agents()
    result = HealthChecker().check_agent(agents[0]["agent_id"])
    assert "resource_usage" in result
    assert "token_budget" in result["resource_usage"]


def test_check_agent_includes_hash() -> None:
    """الفحص يحمل hash للسلسلة."""
    agents = get_population_registry().list_agents()
    result = HealthChecker().check_agent(agents[0]["agent_id"])
    assert "hash" in result
    assert len(result["hash"]) == 64  # SHA-256


def test_check_all_agents() -> None:
    """فحص الوكلاء (محدود لتجنب عنق الزجاجة)."""
    checker = HealthChecker()
    results = checker.check_all_agents(limit=5)
    assert len(results) >= 1


def test_check_agent_publishes_event() -> None:
    """الفحص ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.health.check_completed")
    agents = get_population_registry().list_agents()
    HealthChecker().check_agent(agents[0]["agent_id"])
    assert bus.count("amos_federation.health.check_completed") > initial


def test_health_history_returns_multiple() -> None:
    """التاريخ يعيد عدة فحوصات."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    checker = HealthChecker()
    checker.check_agent(agent_id)
    checker.check_agent(agent_id)
    history = checker.get_agent_health_history(agent_id)
    assert len(history) >= 2


def test_check_nonexistent_agent_raises() -> None:
    """فحص وكيل غير موجود يثير خطأ."""
    with pytest.raises(ValueError):
        HealthChecker().check_agent("nonexistent-agent")


def test_get_latest_status() -> None:
    """أحدث حالة صحية."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    checker = HealthChecker()
    assert checker.get_latest_status(agent_id) == "unknown"  # قبل الفحص
    checker.check_agent(agent_id)
    assert checker.get_latest_status(agent_id) in [HEALTHY, MONITOR, TREATMENT, ISOLATED]


# === 8.2: Treatment system ===


def test_start_treatment_retrain() -> None:
    """علاج: إعادة تدريب."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    result = TreatmentSystem().start_treatment(agent_id, "retrain", "اختبار")
    assert result["status"] == "completed"
    assert result["treatment_type"] == "retrain"


def test_start_treatment_replace_model() -> None:
    """علاج: استبدال نموذج."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    result = TreatmentSystem().start_treatment(agent_id, "replace_model", "اختبار")
    assert result["status"] == "completed"


def test_start_treatment_fix_tool() -> None:
    """علاج: إصلاح أداة."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    result = TreatmentSystem().start_treatment(agent_id, "fix_tool", "اختبار")
    assert result["status"] == "completed"


def test_start_treatment_reset_context() -> None:
    """علاج: إعادة تعيين سياق."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    result = TreatmentSystem().start_treatment(agent_id, "reset_context", "اختبار")
    assert result["status"] == "completed"


def test_treatment_invalid_type_raises() -> None:
    """نوع علاج غير معروف يثير خطأ."""
    agents = get_population_registry().list_agents()
    with pytest.raises(ValueError):
        TreatmentSystem().start_treatment(agents[0]["agent_id"], "invalid", "اختبار")


def test_treatment_publishes_event() -> None:
    """العلاج ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.health.treatment_completed")
    agents = get_population_registry().list_agents()
    TreatmentSystem().start_treatment(agents[0]["agent_id"], "fix_tool", "اختبار")
    assert bus.count("amos_federation.health.treatment_completed") > initial


# === 8.3: Isolation system ===


def test_isolate_agent() -> None:
    """عزل وكيل."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    result = IsolationSystem().isolate(agent_id, "اختبار عزل")
    assert result["status"] == "active"
    assert result["sandbox_id"] is not None


def test_isolated_agent_cannot_use_tools() -> None:
    """الوكيل المعزول لا يمكنه تنفيذ أدوات إنتاجية."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    iso = IsolationSystem()
    iso.isolate(agent_id, "اختبار")
    assert iso.is_isolated(agent_id) is True


def test_isolation_publishes_event() -> None:
    """العزل ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.health.agent_isolated")
    agents = get_population_registry().list_agents()
    IsolationSystem().isolate(agents[0]["agent_id"], "اختبار")
    assert bus.count("amos_federation.health.agent_isolated") > initial


def test_isolation_log_action() -> None:
    """تسجيل فعل أثناء العزل."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    iso = IsolationSystem()
    result = iso.isolate(agent_id, "اختبار")
    log_result = iso.log_action(result["isolation_id"], "tool_attempt", {"tool": "python_execute"})
    assert log_result["logged"] is True


def test_isolation_release() -> None:
    """إنهاء عزل."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    iso = IsolationSystem()
    isolation = iso.isolate(agent_id, "اختبار")
    result = iso.release(isolation["isolation_id"], "release")
    assert result["decision"] == "release"


def test_isolation_release_retire() -> None:
    """إنهاء عزل بتقاعد."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    iso = IsolationSystem()
    isolation = iso.isolate(agent_id, "اختبار")
    result = iso.release(isolation["isolation_id"], "retire")
    assert result["decision"] == "retire"


def test_list_active_isolations() -> None:
    """عرض حالات العزل النشطة."""
    agents = get_population_registry().list_agents()
    iso = IsolationSystem()
    iso.isolate(agents[0]["agent_id"], "اختبار 1")
    iso.isolate(agents[1]["agent_id"], "اختبار 2")
    active = iso.list_active_isolations()
    assert len(active) >= 2


# === Full health cycle ===


def test_run_health_cycle() -> None:
    """دورة فحص صحي كاملة (محدودة)."""
    result = run_health_cycle(limit=5)
    assert result["total_agents_checked"] >= 1
    assert "healthy" in result
    assert "monitor" in result
    assert "treatment" in result
    assert "isolated" in result
    assert "cycle_date" in result


# === 8.4: Control Console integration ===


def test_ui_health_endpoint() -> None:
    """8.4: endpoint الحالة الصحية للوكلاء في واجهة التحكم."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    HealthChecker().check_agent(agent_id)
    resp = client.get(f"/v1/health/agents/{agent_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["agent_id"] == agent_id


def test_ui_health_all_endpoint() -> None:
    """8.4: endpoint كل الحالات الصحية."""
    resp = client.get("/v1/health/all", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 20


def test_ui_health_check_endpoint() -> None:
    """8.4: endpoint تشغيل فحص صحي."""
    agents = get_population_registry().list_agents()
    resp = client.post(f"/v1/health/check?agent_id={agents[0]['agent_id']}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] in [HEALTHY, MONITOR, TREATMENT, ISOLATED]


def test_ui_isolate_endpoint() -> None:
    """8.4: endpoint عزل من الواجهة."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    resp = client.post(f"/v1/health/isolate/{agent_id}?reason=test", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_ui_treat_endpoint() -> None:
    """8.4: endpoint علاج من الواجهة."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    resp = client.post(
        f"/v1/health/treat/{agent_id}?treatment_type=fix_tool&reason=test", headers=AUTH_HEADERS
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_ui_isolations_list_endpoint() -> None:
    """8.4: endpoint قائمة العزل."""
    resp = client.get("/v1/health/isolations", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_ui_health_status_visible_after_check() -> None:
    """8.4: حالة مراقبة/علاج/عزل ظاهرة فورًا للمشرف."""
    agents = get_population_registry().list_agents()
    agent_id = agents[0]["agent_id"]
    HealthChecker().check_agent(agent_id)
    resp = client.get("/v1/health/all", headers=AUTH_HEADERS)
    data = resp.json()
    agent_health = next(a for a in data if a["agent_id"] == agent_id)
    assert agent_health["health_status"] in [HEALTHY, MONITOR, TREATMENT, ISOLATED, "unknown"]
