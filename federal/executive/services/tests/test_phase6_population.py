"""
AMOS-Federation Phase 6 — Population & School Tests
الهدف: اختبار السجل السكاني + المدرسة + دورة حياة الوكيل
النطاق: tests/test_phase6_population.py
"""


class TestPopulationRegistry:
    """6.1: السجل السكاني فوق جدول agents الحقيقي."""

    def test_register_agent(self):
        """6.1: تسجيل وكيل جديد."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل اختبار",
            role="executor",
            category="cognitive_executor",
            permissions=["task:execute"],
            allowed_tools=["text_summary"],
        )
        assert agent["agent_id"].startswith("agent-")
        assert agent["state"] == "registered"

    def test_get_agent(self):
        """6.1: استرجاع وكيل."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل استرجاع", role="monitor", category="security_monitor")
        retrieved = reg.get_agent(agent["agent_id"])
        assert retrieved is not None
        assert retrieved["name"] == "وكيل استرجاع"

    def test_list_agents(self):
        """6.1: قائمة الوكلاء."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agents = reg.list_agents()
        assert isinstance(agents, list)
        assert len(agents) > 0

    def test_list_by_state(self):
        """6.1: تصفية حسب الحالة."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        registered = reg.list_agents(state="registered")
        assert all(a["state"] == "registered" for a in registered)

    def test_update_state(self):
        """6.4: تحديث حالة الوكيل — دورة الحياة."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل دورة حياة", role="executor", category="cognitive_executor"
        )
        # registered → training
        reg.update_state(agent["agent_id"], "training")
        updated = reg.get_agent(agent["agent_id"])
        assert updated["state"] == "training"

    def test_population_stats(self):
        """6.1: إحصائيات السكان."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        stats = reg.population_stats()
        assert "total" in stats
        assert stats["total"] > 0


class TestSchool:
    """6.2: المدرسة بمنهج ست خطوات."""

    def test_curriculum_has_six_steps(self):
        """6.2: المنهج له ست خطوات."""
        from amos_federation.services.agent_runtime.population import AgentSchool

        school = AgentSchool()
        assert len(school.CURRICULUM) == 6

    def test_take_step(self):
        """6.2: تسجيل نتيجة خطوة."""
        from amos_federation.services.agent_runtime.population import (
            AgentSchool,
            get_population_registry,
        )

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل مدرسة", role="learner", category="learner")
        school = AgentSchool()
        result = school.take_step(agent["agent_id"], 1, 90, "أداء ممتاز")
        assert result["passed"] is True
        assert result["score"] == 90

    def test_step_fail_below_threshold(self):
        """6.2: الرسوب تحت العتبة."""
        from amos_federation.services.agent_runtime.population import (
            AgentSchool,
            get_population_registry,
        )

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل راسب", role="learner", category="learner")
        school = AgentSchool()
        result = school.take_step(agent["agent_id"], 1, 50, "أداء ضعيف")
        assert result["passed"] is False

    def test_graduation_requires_all_steps(self):
        """6.2: التخرج يتطلب اجتياز كل الخطوات الست."""
        from amos_federation.services.agent_runtime.population import (
            AgentSchool,
            get_population_registry,
        )

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل تخرج", role="learner", category="learner")
        school = AgentSchool()
        # فقط 3 خطوات — لا يتخرج
        school.take_step(agent["agent_id"], 1, 90)
        school.take_step(agent["agent_id"], 2, 85)
        school.take_step(agent["agent_id"], 3, 88)
        result = school.graduate(agent["agent_id"])
        assert result["graduated"] is False

    def test_full_graduation(self):
        """6.2: تخرج كامل بعد اجتياز كل الخطوات."""
        from amos_federation.services.agent_runtime.population import (
            AgentSchool,
            get_population_registry,
        )

        reg = get_population_registry()
        agent = reg.register_agent(name="وكيل متخرج", role="learner", category="learner")
        school = AgentSchool()
        for step in range(1, 7):
            school.take_step(agent["agent_id"], step, 90)
        result = school.graduate(agent["agent_id"])
        assert result["graduated"] is True
        assert result["avg_score"] >= 85


class TestAgentLifecycle:
    """6.4: دورة حياة الوكيل تشغيليًا."""

    def test_full_lifecycle(self):
        """6.4: دورة حياة كاملة: registered → training → testing → specialized → employed → active."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل دورة كاملة", role="executor", category="cognitive_executor"
        )

        states = ["training", "testing", "specialized", "employed", "active"]
        for state in states:
            reg.update_state(agent["agent_id"], state)
            current = reg.get_agent(agent["agent_id"])
            assert current["state"] == state

    def test_retire_agent(self):
        """6.4: تقاعد الوكيل."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل متقاعد", role="executor", category="cognitive_executor"
        )
        reg.update_state(agent["agent_id"], "retired")
        retired = reg.get_agent(agent["agent_id"])
        assert retired["state"] == "retired"

    def test_agent_has_permissions(self):
        """6.1: كل وكيل له صلاحيات محددة."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل بصلاحيات",
            role="executor",
            category="cognitive_executor",
            permissions=["task:execute", "tool:use"],
            allowed_tools=["python_execute", "sql_query"],
        )
        assert len(agent["permissions"]) == 2
        assert len(agent["allowed_tools"]) == 2

    def test_agent_has_token_budget(self):
        """6.1: كل وكيل له ميزانية توكنز."""
        from amos_federation.services.agent_runtime.population import get_population_registry

        reg = get_population_registry()
        agent = reg.register_agent(
            name="وكيل بميزانية",
            role="executor",
            category="cognitive_executor",
            token_budget=5000,
        )
        assert agent["token_budget"] == 5000
