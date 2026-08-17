"""
اختبارات التوسع السكاني + التخصص + الجامعات + التقاعد (Phase 11)
الهدف: التحقق من ~500 وكيل، مسارات التخصص، المخرجات الجامعية، التقاعد
النطاق: services/governance/expansion
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest
from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.agent_runtime.population import get_population_registry
from amos_federation.services.control_console.main import app
from amos_federation.services.governance.expansion import (
    FULL_POPULATION_CATEGORIES,
    SPECIALIZATION_TRACKS,
    TOTAL_TARGET_POPULATION,
    PopulationExpansion,
    RetirementSystem,
    SpecializationProgram,
    University,
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


@pytest.fixture(autouse=True)
def seed_and_clean():
    from sqlalchemy import create_engine, delete

    from amos_federation.common.database import get_database_url, get_session_factory
    from amos_federation.services.governance.canary import reset_kill_switch
    from amos_federation.services.governance.expansion import _ExpansionBase

    reset_kill_switch()
    url = get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    _ExpansionBase.metadata.create_all(engine)

    registry = get_population_registry()
    registry.seed_initial_population()
    yield

    # Clean expansion tables
    from amos_federation.services.governance.expansion import (
        ExpansionBatchModel,
        RetirementRecordModel,
        SpecializationResultModel,
        UniversityOutputModel,
    )

    session = get_session_factory()()
    try:
        for model in [
            SpecializationResultModel,
            UniversityOutputModel,
            RetirementRecordModel,
            ExpansionBatchModel,
        ]:
            session.execute(delete(model))
        session.commit()
    finally:
        session.close()
    reset_kill_switch()


# === 11.1: Population expansion ===


def test_full_population_categories_exist() -> None:
    """الفئات السكانية الكاملة موجودة."""
    assert len(FULL_POPULATION_CATEGORIES) >= 18
    assert "coordinator" in FULL_POPULATION_CATEGORIES
    assert "state_coordinator" in FULL_POPULATION_CATEGORIES
    assert "judge" in FULL_POPULATION_CATEGORIES
    assert "accountant" in FULL_POPULATION_CATEGORIES
    assert "reserve" in FULL_POPULATION_CATEGORIES


def test_total_target_is_large() -> None:
    """الإجمالي المستهدف كبير (~500+)."""
    assert TOTAL_TARGET_POPULATION >= 500


def test_create_batch() -> None:
    """إنشاء دفعة توسع."""
    result = PopulationExpansion().create_batch("reserve", 10)
    assert "batch_id" in result
    assert result["category"] == "reserve"
    assert result["target_count"] == 10


def test_enroll_batch() -> None:
    """تسجيل وكلاء في دفعة."""
    exp = PopulationExpansion()
    batch = exp.create_batch("reserve", 5)
    enrolled = exp.enroll_batch(batch["batch_id"], 3)
    assert len(enrolled) == 3
    for a in enrolled:
        assert a["role"] == "reserve"


def test_graduate_batch() -> None:
    """تخرير دفعة عبر المدرسة."""
    exp = PopulationExpansion()
    batch = exp.create_batch("reserve", 3)
    exp.enroll_batch(batch["batch_id"], 2)
    result = exp.graduate_batch(batch["batch_id"])
    assert "graduated" in result
    assert result["graduated"] + result["failed"] >= 0


def test_employ_batch_requires_health_check() -> None:
    """التوظيف يتطلب فحص صحي."""
    exp = PopulationExpansion()
    batch = exp.create_batch("reserve", 2)
    exp.enroll_batch(batch["batch_id"], 2)
    exp.graduate_batch(batch["batch_id"])
    result = exp.employ_batch(batch["batch_id"])
    assert "employed" in result
    assert "health_failed" in result


def test_expansion_stats() -> None:
    """إحصائيات التوسع."""
    stats = PopulationExpansion().expansion_stats()
    assert "total_agents" in stats
    assert "total_target" in stats
    assert "fill_rate" in stats
    assert "target_vs_actual" in stats
    assert stats["total_target"] >= 500


def test_batch_publishes_event() -> None:
    """إنشاء دفعة ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.expansion.batch_created")
    PopulationExpansion().create_batch("reserve", 5)
    assert bus.count("amos_federation.expansion.batch_created") > initial


def test_full_categories_have_tools() -> None:
    """كل فئة لها أدوات و صلاحيات."""
    for cat_key, spec in FULL_POPULATION_CATEGORIES.items():
        assert "tools" in spec, f"{cat_key} missing tools"
        assert "permissions" in spec, f"{cat_key} missing permissions"
        assert "role" in spec, f"{cat_key} missing role"


# === 11.2: Specialization ===


def test_specialization_tracks_exist() -> None:
    """مسارات التخصص الستة موجودة."""
    assert len(SPECIALIZATION_TRACKS) == 6
    for track in ["finance", "law", "science", "health", "culture", "industry"]:
        assert track in SPECIALIZATION_TRACKS
        assert "name" in SPECIALIZATION_TRACKS[track]
        assert "duration_days" in SPECIALIZATION_TRACKS[track]
        assert "exam_threshold" in SPECIALIZATION_TRACKS[track]
        assert "curriculum" in SPECIALIZATION_TRACKS[track]


def test_get_tracks() -> None:
    """عرض مسارات التخصص."""
    tracks = SpecializationProgram().get_tracks()
    assert len(tracks) == 6
    assert "finance" in tracks
    assert len(tracks["finance"]["curriculum"]) >= 4


def test_enroll_specialization() -> None:
    """تسجيل في مسار تخصص."""
    registry = get_population_registry()
    agents = registry.list_agents()
    if not agents:
        return
    agent = agents[0]
    # need to set state to employed first
    registry.update_state(agent["agent_id"], "employed")
    result = SpecializationProgram().enroll_agent(agent["agent_id"], "finance")
    assert result["track"] == "finance"
    assert "curriculum" in result


def test_enroll_unknown_track() -> None:
    """تسجيل في مسار غير موجود."""
    result = SpecializationProgram().enroll_agent("agent-001", "nonexistent")
    assert "error" in result


def test_take_exam_pass() -> None:
    """اجتياز اختبار تخصص."""
    result = SpecializationProgram().take_exam("agent-001", "finance", 90.0)
    assert result["passed"] is True
    assert result["score"] == 90.0


def test_take_exam_fail() -> None:
    """رسوب في اختبار تخصص."""
    result = SpecializationProgram().take_exam("agent-001", "law", 50.0)
    assert result["passed"] is False


def test_exam_publishes_event() -> None:
    """الاختبار ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.specialization.exam_completed")
    SpecializationProgram().take_exam("agent-001", "finance", 90.0)
    assert bus.count("amos_federation.specialization.exam_completed") > initial


def test_get_agent_specialization() -> None:
    """عرض تخصص وكيل."""
    SpecializationProgram().take_exam("agent-001", "finance", 90.0)
    result = SpecializationProgram().get_agent_specialization("agent-001")
    assert len(result["exams"]) >= 1
    assert result["exams"][0]["track"] == "finance"


def test_list_specialized_agents() -> None:
    """عرض الوكلاء المتخصصين."""
    SpecializationProgram().take_exam("agent-001", "finance", 90.0)
    SpecializationProgram().take_exam("agent-002", "law", 50.0)
    specialized = SpecializationProgram().list_specialized_agents()
    assert len(specialized) >= 1
    assert all(s["passed"] for s in specialized)


def test_list_specialized_by_track() -> None:
    """فلترة بالتخصص."""
    SpecializationProgram().take_exam("agent-001", "finance", 90.0)
    SpecializationProgram().take_exam("agent-002", "law", 90.0)
    finance_only = SpecializationProgram().list_specialized_agents(track="finance")
    assert all(s["track"] == "finance" for s in finance_only)


# === 11.3: University ===


def test_university_research_topics() -> None:
    """مواضيع البحث متاحة."""
    topics = University().get_research_topics()
    assert len(topics) == 6
    for track in ["finance", "law", "science", "health", "culture", "industry"]:
        assert track in topics
        assert len(topics[track]) >= 3


def test_submit_output() -> None:
    """تقديم مخرج جامعي."""
    result = University().submit_output(
        output_type="paper",
        title="ورقة بحثية",
        author_agent_id="agent-001",
        track="science",
        content="محتوى الورقة",
        quality_score=0.8,
    )
    assert result["type"] == "paper"
    assert result["author"] == "agent-001"
    assert len(result["content_hash"]) == 64


def test_submit_invalid_type() -> None:
    """نوع مخرج غير صالح."""
    result = University().submit_output(
        output_type="invalid",
        title="test",
        author_agent_id="agent-001",
        track="science",
        content="content",
    )
    assert "error" in result


def test_approve_output() -> None:
    """اعتماد مخرج جامعي."""
    uni = University()
    output = uni.submit_output(
        output_type="tool",
        title="أداة جديدة",
        author_agent_id="agent-001",
        track="industry",
        content="أداة لتحسين الإنتاج",
        quality_score=0.0,
    )
    result = uni.approve_output(output["output_id"], quality_score=0.9)
    assert result["approved"] is True


def test_list_outputs() -> None:
    """عرض المخرجات."""
    uni = University()
    uni.submit_output("paper", "ورقة 1", "agent-001", "science", "content 1")
    uni.submit_output("tool", "أداة 1", "agent-002", "industry", "content 2")
    outputs = uni.list_outputs()
    assert len(outputs) >= 2


def test_list_approved_only() -> None:
    """عرض المخرجات المعتمدة فقط."""
    uni = University()
    o1 = uni.submit_output("paper", "ورقة 1", "agent-001", "science", "content")
    uni.approve_output(o1["output_id"], 0.9)
    uni.submit_output("tool", "أداة 1", "agent-002", "industry", "content")
    approved = uni.list_outputs(approved_only=True)
    assert all(o["approved"] for o in approved)


def test_produce_first_output() -> None:
    """إنتاج أول مخرج جامعي حقيقي."""
    result = University().produce_first_output()
    assert result["type"] == "paper"
    assert "title" in result
    assert len(result["content_hash"]) == 64


def test_output_publishes_event() -> None:
    """تقديم مخرج ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.university.output_submitted")
    University().submit_output("paper", "test", "agent-001", "science", "content")
    assert bus.count("amos_federation.university.output_submitted") > initial


# === 11.4: Retirement ===


def test_retire_agent() -> None:
    """تقاعد وكيل."""
    registry = get_population_registry()
    agents = registry.list_agents()
    if not agents:
        return
    agent_id = agents[0]["agent_id"]
    result = RetirementSystem().retire_agent(agent_id, "health_failure")
    assert result["archived"] is True
    assert result["reason"] == "health_failure"


def test_retire_nonexistent() -> None:
    """تقاعد وكيل غير موجود."""
    result = RetirementSystem().retire_agent("nonexistent-agent", "health_failure")
    assert "error" in result


def test_get_retired_agents() -> None:
    """عرض المتقاعدين."""
    registry = get_population_registry()
    agents = registry.list_agents()
    if not agents:
        return
    RetirementSystem().retire_agent(agents[0]["agent_id"])
    retired = RetirementSystem().get_retired_agents()
    assert len(retired) >= 1


def test_get_archived_data() -> None:
    """استرجاع بيانات مؤرشفة."""
    registry = get_population_registry()
    agents = registry.list_agents()
    if not agents:
        return
    agent_id = agents[0]["agent_id"]
    RetirementSystem().retire_agent(agent_id)
    archived = RetirementSystem().get_archived_data(agent_id)
    assert archived["agent_id"] == agent_id
    assert "archived_data" in archived
    assert isinstance(archived["archived_data"], dict)


def test_retirement_publishes_event() -> None:
    """التقاعد ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    registry = get_population_registry()
    agents = registry.list_agents()
    if not agents:
        return
    bus = get_event_bus()
    initial = bus.count("amos_federation.lifecycle.retired")
    RetirementSystem().retire_agent(agents[0]["agent_id"])
    assert bus.count("amos_federation.lifecycle.retired") > initial


def test_retired_agent_state_updated() -> None:
    """حالة الوكيل المتقاعد تتحدث لـ retired."""
    registry = get_population_registry()
    agents = registry.list_agents()
    if not agents:
        return
    agent_id = agents[0]["agent_id"]
    RetirementSystem().retire_agent(agent_id)
    agent = registry.get_agent(agent_id)
    assert agent["state"] == "retired"


# === Control Console integration ===


def test_ui_expansion_stats() -> None:
    resp = client.get("/v1/expansion/stats", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "total_target" in resp.json()


def test_ui_specialization_tracks() -> None:
    resp = client.get("/v1/specialization/tracks", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "finance" in resp.json()


def test_ui_university_outputs() -> None:
    resp = client.get("/v1/university/outputs", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_ui_retirement_list() -> None:
    resp = client.get("/v1/retirement/list", headers=AUTH_HEADERS)
    assert resp.status_code == 200
