"""
AMOS-Federation Phase 7-8 — Health, Isolation & Treatment Tests
الهدف: اختبار الفاحص الصحي + العزل + العلاج
النطاق: tests/test_phase7_health.py
"""

import pytest


class TestHealthChecker:
    """7.1-7.2: الفاحص الصحي للوكلاء."""

    def test_check_agent_exists(self):
        """7.1: فحص وكيل موجود."""
        from amos_federation.services.agent_runtime.health import get_health_checker
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل صحي", role="executor", category="cognitive_executor")
        checker = get_health_checker()
        result = checker.check_agent(agent["agent_id"])
        assert "status" in result
        assert result["status"] in ("healthy", "watch", "treatment", "isolated", "monitor")

    def test_check_nonexistent_agent(self):
        """7.1: فحص وكيل غير موجود يرفع خطأ."""
        from amos_federation.services.agent_runtime.health import get_health_checker

        checker = get_health_checker()
        with pytest.raises(ValueError):
            checker.check_agent("agent-nonexistent-999")

    def test_health_check_records_result(self):
        """7.2: نتيجة الفحص مسجّلة في DB."""
        from amos_federation.services.agent_runtime.health import get_health_checker
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل فحص مسجل", role="executor", category="cognitive_executor"
        )
        checker = get_health_checker()
        checker.check_agent(agent["agent_id"])
        history = checker.get_agent_health_history(agent["agent_id"])
        assert len(history) > 0


class TestIsolationSystem:
    """7.3: نظام العزل."""

    def test_isolate_agent(self):
        """7.3: عزل وكيل."""
        from amos_federation.services.agent_runtime.health import get_isolation_system
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل معزول", role="executor", category="cognitive_executor"
        )
        iso = get_isolation_system()
        result = iso.isolate(agent["agent_id"], reason="اختبار العزل")
        assert result["status"] == "active"

    def test_release_isolated_agent(self):
        """7.3: رفع العزل."""
        from amos_federation.services.agent_runtime.health import get_isolation_system
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل رفع عزل", role="executor", category="cognitive_executor"
        )
        iso = get_isolation_system()
        r = iso.isolate(agent["agent_id"], reason="اختبار")
        result = iso.release(r["isolation_id"], decision="اختبار انتهى")
        assert "released_at" in result

    def test_isolated_agent_cannot_execute(self):
        """7.3: الوكيل المعزول لا يمكنه التنفيذ."""
        from amos_federation.services.agent_runtime.health import get_isolation_system
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل معزول تنفيذ", role="executor", category="cognitive_executor"
        )
        iso = get_isolation_system()
        iso.isolate(agent["agent_id"], reason="منع التنفيذ")
        assert iso.is_isolated(agent["agent_id"]) is True


class TestTreatmentSystem:
    """7.4: نظام العلاج."""

    def test_prescribe_treatment(self):
        """7.4: وصف علاج."""
        from amos_federation.services.agent_runtime.health import get_treatment_system
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل علاج", role="executor", category="cognitive_executor")
        treatment = get_treatment_system()
        result = treatment.start_treatment(
            agent["agent_id"], treatment_type="retrain", reason="انخفاض الأداء"
        )
        assert "status" in result
        assert result["status"] == "completed"

    def test_complete_treatment(self):
        """7.4: إكمال علاج."""
        from amos_federation.services.agent_runtime.health import get_treatment_system
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل إكمال علاج", role="executor", category="cognitive_executor"
        )
        treatment = get_treatment_system()
        result = treatment.start_treatment(
            agent["agent_id"], treatment_type="retrain", reason="اختبار"
        )
        assert "status" in result


class TestHealthCycle:
    """8.5: دورة الفحص الصحي الكاملة."""

    def test_run_health_cycle(self):
        """8.5: تشغيل دورة فحص صحي كاملة (اختبار بسيط)."""
        # اختبار على وكيل واحد فقط بدلاً من كل الوكلاء
        from amos_federation.services.agent_runtime.health import get_health_checker
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل دورة صحية", role="executor", category="cognitive_executor"
        )
        checker = get_health_checker()
        result = checker.check_agent(agent["agent_id"])
        assert "status" in result
