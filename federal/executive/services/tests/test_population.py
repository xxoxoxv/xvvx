"""
اختبارات السكان الأوائل (Phase 6)
الهدف: التحقق من Population Registry، School، 20 وكيل، دورة الحياة، اليوم التشغيلي
النطاق: services/agent_runtime/population
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from amos_federation.services.agent_runtime.population import (
    DAILY_SCHEDULE,
    AgentSchool,
    PopulationRegistry,
    run_daily_routine,
)

# === 6.1: Population Registry ===


def test_register_agent() -> None:
    """تسجيل وكيل جديد."""
    registry = PopulationRegistry()
    agent = registry.register_agent(
        name="وكيل اختبار",
        role="cognitive_executor",
        category="cognitive",
        permissions=["task:execute"],
        allowed_tools=["python_execute"],
    )
    assert agent["agent_id"] is not None
    assert agent["state"] == "registered"
    assert "task:execute" in agent["permissions"]


def test_seed_initial_population_20() -> None:
    """بذر 20 وكيل."""
    registry = PopulationRegistry()
    agents = registry.seed_initial_population()
    assert len(agents) == 20
    roles = [a["role"] for a in agents]
    assert "coordinator" in roles
    assert "cognitive_executor" in roles
    assert "security_monitor" in roles
    assert "trainer" in roles
    assert "learner" in roles


def test_population_persistent() -> None:
    """السكان يبقون بعد إعادة التشغيل."""
    registry1 = PopulationRegistry()
    registry1.register_agent("وكيل بقاء", "auditor", "audit")
    count1 = registry1.population_stats()["total"]

    registry2 = PopulationRegistry()
    count2 = registry2.population_stats()["total"]
    assert count2 == count1


def test_agent_has_manifest() -> None:
    """كل وكيل له عقد تشغيلي (manifest)."""
    registry = PopulationRegistry()
    agent = registry.register_agent(
        name="وكيل بعقد",
        role="cognitive_executor",
        category="cognitive",
        permissions=["task:execute", "tool:use"],
        allowed_tools=["python_execute", "sql_query"],
        token_budget=5000,
    )
    assert len(agent["permissions"]) >= 2
    assert len(agent["allowed_tools"]) >= 2
    assert agent["token_budget"] == 5000


def test_population_stats() -> None:
    """إحصائيات السكان."""
    registry = PopulationRegistry()
    registry.seed_initial_population()
    stats = registry.population_stats()
    assert stats["total"] >= 20
    assert "by_state" in stats
    assert "by_category" in stats


# === 6.2: School (six-step curriculum) ===


def test_school_curriculum_six_steps() -> None:
    """المنهج من ست خطوات."""
    assert len(AgentSchool.CURRICULUM) == 6
    steps = [c["name"] for c in AgentSchool.CURRICULUM]
    assert "فهم التعليمات" in steps
    assert "اختبار نهائي" in steps


def test_school_take_step() -> None:
    """تسجيل نتيجة خطوة."""
    school = AgentSchool()
    result = school.take_step("agent-test-001", 1, 85)
    assert result["passed"] is True
    assert result["score"] == 85


def test_school_fail_step() -> None:
    """رسوب في خطوة."""
    school = AgentSchool()
    result = school.take_step("agent-test-002", 1, 50)
    assert result["passed"] is False


def test_school_graduation_all_passed() -> None:
    """تخرج وكيل اجتاز كل الخطوات."""
    registry = PopulationRegistry()
    agent = registry.register_agent("متخرج", "cognitive_executor", "cognitive")

    school = AgentSchool()
    result = school.run_full_curriculum(agent["agent_id"], [85, 85, 85, 90, 85, 90])
    assert result["graduation"]["graduated"] is True
    assert result["graduation"]["avg_score"] >= 85


def test_school_graduation_failed() -> None:
    """عدم تخرج وكيل رسب في خطوة."""
    registry = PopulationRegistry()
    agent = registry.register_agent("راسب", "cognitive_executor", "cognitive")

    school = AgentSchool()
    result = school.run_full_curriculum(agent["agent_id"], [85, 50, 85, 90, 85, 90])
    assert result["graduation"]["graduated"] is False


def test_school_graduation_incomplete() -> None:
    """عدم تخرج وكيل لم يكمل كل الخطوات."""
    registry = PopulationRegistry()
    agent = registry.register_agent("ناقص", "cognitive_executor", "cognitive")

    school = AgentSchool()
    school.take_step(agent["agent_id"], 1, 85)
    result = school.graduate(agent["agent_id"])
    assert result["graduated"] is False
    assert "1/6" in result["reason"]


def test_school_85_percent_threshold() -> None:
    """عتبة التخرج 85%."""
    curriculum = AgentSchool.CURRICULUM
    for c in curriculum:
        assert c["pass_threshold"] >= 80


# === 6.3: 20 real agents ===


def test_20_agents_seeded_and_graduated() -> None:
    """20 وكيل يُسجَّلون ويتخرجون."""
    registry = PopulationRegistry()
    agents = registry.seed_initial_population()
    assert len(agents) == 20

    school = AgentSchool()
    graduated = 0
    for agent in agents:
        result = school.run_full_curriculum(agent["agent_id"])
        if result["graduation"]["graduated"]:
            graduated += 1

    assert graduated == 20  # كلهم تخرجوا


def test_agent_lifecycle_states() -> None:
    """دورة حياة الوكيل: registered → training → testing → employed → active."""
    registry = PopulationRegistry()
    agent = registry.register_agent("وكيل دورة حياة", "cognitive_executor", "cognitive")

    # registered → training
    registry.update_state(agent["agent_id"], "training")
    assert registry.get_agent(agent["agent_id"])["state"] == "training"

    # training → testing
    registry.update_state(agent["agent_id"], "testing")
    assert registry.get_agent(agent["agent_id"])["state"] == "testing"

    # testing → employed (يتخرج)
    registry.update_state(agent["agent_id"], "employed")
    updated = registry.get_agent(agent["agent_id"])
    assert updated["state"] == "employed"
    assert updated["graduated_at"] is not None

    # employed → active
    registry.update_state(agent["agent_id"], "active")
    assert registry.get_agent(agent["agent_id"])["state"] == "active"


def test_agent_persists_across_restart() -> None:
    """الوكيل يبقى عبر إعادة التشغيل."""
    registry1 = PopulationRegistry()
    agent = registry1.register_agent("وكيل استمرارية", "trainer", "education")
    agent_id = agent["agent_id"]
    registry1.update_state(agent_id, "active")

    registry2 = PopulationRegistry()
    agent2 = registry2.get_agent(agent_id)
    assert agent2 is not None
    assert agent2["state"] == "active"
    assert agent2["name"] == "وكيل استمرارية"


# === 6.5: Daily operational schedule ===


def test_daily_schedule_four_points() -> None:
    """اليوم التشغيلي أربع نقاط."""
    assert len(DAILY_SCHEDULE) == 4
    times = [p["time"] for p in DAILY_SCHEDULE]
    assert "02:00" in times
    assert "04:00" in times
    assert "08:00" in times
    assert "23:00" in times


def test_run_daily_routine_publishes_events() -> None:
    """تشغيل اليوم التشغيلي ينشر أحداثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.daily.health_check")
    results = run_daily_routine()
    assert len(results) == 4
    assert bus.count("amos_federation.daily.health_check") > initial


# === Integration: agent executes real task ===


def test_agent_can_execute_tool() -> None:
    """وكيل متخرج ينفذ مهمة حقيقية بأداة حقيقية."""
    from amos_federation.services.tool_registry.sandbox import execute_tool_with_governance

    registry = PopulationRegistry()
    agent = registry.register_agent(
        "وكيل منفذ",
        "cognitive_executor",
        "cognitive",
        permissions=["task:execute", "tool:use"],
        allowed_tools=["python_execute"],
    )

    # تنفيذ أداة حقيقية بمبدأ مُتحقَّق منه.
    #
    # تغيَّر هذا الاختبار في R6: كان يُمرِّر `role="admin"` فيُصدَّق ادّعاؤه.
    # الآن الدور المُدّعى لا يوسِّع شيئًا — دور الهوية الكانونية هو ما يراه
    # محرِّك السياسة عند مبدأ غير مُتحقَّق منه، ودور المبدأ عند المُتحقَّق منه.
    from amos_federation.common.principal import AuthorizationContext, Principal

    principal = Principal.from_session_record(
        session_id="test-session-population",
        username="tester",
        role_id="official",
        permissions=("execute:tools",),
        expires_at=None,
    )
    result = execute_tool_with_governance(
        "python_execute",
        {"code": "print(2+2)", "agent_id": agent["agent_id"]},
        principal=AuthorizationContext.from_principal(principal),
    )
    assert result.get("returncode") == 0
    assert "4" in result.get("stdout", "")
    # والهوية المُتحقَّق منها تظهر في النتيجة، فلا تُقرأ النتيجة بلا نَسَب.
    assert result["principal_verification"] == "SESSION_VERIFIED"
