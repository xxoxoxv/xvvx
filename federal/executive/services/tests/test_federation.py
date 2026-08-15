"""
اختبارات المؤسسات الفدرالية + الحوكمة الكاملة (Phase 9)
الهدف: التحقق من Ed25519، بوابات الترقية، السلطات الأربع، الرقابة
النطاق: services/governance/federation
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest
from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.agent_runtime.population import get_population_registry
from amos_federation.services.control_console.main import app
from amos_federation.services.governance.federation import (
    GATE_ORDER,
    ApprovalSystem,
    Ed25519Signer,
    ExecutiveBranch,
    JudicialBranch,
    LegislativeBranch,
    PromotionSystem,
    SupremeOversight,
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
    """بذر الوكلاء وتنظيف الجداول."""
    from sqlalchemy import create_engine, delete

    from amos_federation.common.database import get_database_url, get_session_factory
    from amos_federation.services.governance.canary import reset_kill_switch
    from amos_federation.services.governance.federation import _GovBase

    reset_kill_switch()
    # Ensure all federation tables exist
    url = get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    _GovBase.metadata.create_all(engine)

    registry = get_population_registry()
    registry.seed_initial_population()
    yield
    # Clean up federation tables
    from amos_federation.services.governance.federation import (
        ApprovalModel,
        ComplianceReportModel,
        CourtCaseModel,
        ExecutiveRoleModel,
        LegislationModel,
        PromotionGateModel,
    )

    session = get_session_factory()()
    try:
        for model in [
            ApprovalModel,
            PromotionGateModel,
            LegislationModel,
            CourtCaseModel,
            ComplianceReportModel,
        ]:
            session.execute(delete(model))
        # Reset executive roles to vacant
        from sqlalchemy import select as sa_select

        roles = session.execute(sa_select(ExecutiveRoleModel)).scalars().all()
        for role in roles:
            role.agent_id = None
            role.status = "vacant"
        session.commit()
    finally:
        session.close()
    reset_kill_switch()


# === 9.1: Expanded Policy Engine ===


def test_policy_rules_cover_all_services() -> None:
    """9.1: Policy Engine يغطي كل الخدمات."""
    from amos_federation.services.governance.federation import POLICY_RULES_EXPANDED

    services = set(r["service"] for r in POLICY_RULES_EXPANDED)
    assert "tool-registry" in services
    assert "model-gateway" in services
    assert "agent-runtime" in services
    assert "governance" in services
    assert "memory-service" in services
    assert "evaluation" in services


def test_policy_rules_count() -> None:
    """عدد القواعد الموسّعة ≥ 10."""
    from amos_federation.services.governance.federation import POLICY_RULES_EXPANDED

    assert len(POLICY_RULES_EXPANDED) >= 10


# === 9.3: Ed25519 Signing ===


def test_ed25519_generate_keypair() -> None:
    """توليد زوج مفاتيح."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    assert len(priv) > 0
    assert len(pub) > 0
    assert priv != pub


def test_ed25519_sign_and_verify() -> None:
    """التوقيع والتحقق."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    message = "test message"
    signature = signer.sign(priv, message)
    assert len(signature) > 0
    assert signer.verify(pub, message, signature) is True


def test_ed25519_verify_fails_wrong_sig() -> None:
    """التحقق يفشل بتوقيع خاطئ."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    assert signer.verify(pub, "message", "wrong_signature") is False


# === 9.2 + 9.3: Approval System ===


def test_request_approval() -> None:
    """طلب موافقة مع توقيع."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    result = ApprovalSystem().request_approval(
        "model_promotion", "model-001", "agent-001", priv, pub, "اختبار"
    )
    assert result["status"] == "pending"
    assert result["verified"] is True
    assert len(result["signature"]) > 0


def test_decide_approval_approve() -> None:
    """موافقة فعليًا."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    system = ApprovalSystem()
    req = system.request_approval("model_promotion", "model-001", "agent-001", priv, pub)
    result = system.decide_approval(req["approval_id"], "approve", priv, pub)
    assert result["decision"] == "approve"
    assert result["verified"] is True


def test_decide_approval_reject() -> None:
    """رفض فعليًا."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    system = ApprovalSystem()
    req = system.request_approval("agent_promotion", "agent-001", "agent-002", priv, pub)
    result = system.decide_approval(req["approval_id"], "reject", priv, pub)
    assert result["decision"] == "reject"


def test_verify_approval_signature() -> None:
    """التحقق من توقيع موافقة."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    system = ApprovalSystem()
    req = system.request_approval("model_promotion", "model-001", "agent-001", priv, pub)
    verification = system.verify_approval(req["approval_id"])
    assert verification["signature_valid"] is True


def test_decide_already_decided_raises() -> None:
    """البت مرتين يثير خطأ."""
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    system = ApprovalSystem()
    req = system.request_approval("model_promotion", "model-001", "agent-001", priv, pub)
    system.decide_approval(req["approval_id"], "approve", priv, pub)
    with pytest.raises(ValueError):
        system.decide_approval(req["approval_id"], "reject", priv, pub)


def test_approval_publishes_event() -> None:
    """طلب موافقة ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.governance.approval_requested")
    signer = Ed25519Signer()
    priv, pub = signer.generate_keypair()
    ApprovalSystem().request_approval("model_promotion", "model-001", "agent-001", priv, pub)
    assert bus.count("amos_federation.governance.approval_requested") > initial


# === 9.4: Promotion Gates ===


def test_start_promotion_creates_five_gates() -> None:
    """بدء ترقية ينشئ 5 بوابات."""
    result = PromotionSystem().start_promotion("model", "model-001", "agent-001")
    assert len(result["gates"]) == 5
    assert [g["gate"] for g in result["gates"]] == GATE_ORDER


def test_pass_gate_sequentially() -> None:
    """اجتياز البوابات بالترتيب."""
    system = PromotionSystem()
    system.start_promotion("model", "model-002", "agent-001")
    result = system.pass_gate("model", "model-002", "evaluation", {"score": 0.85})
    assert result["status"] == "passed"


def test_cannot_skip_gate() -> None:
    """لا يمكن تجاوز بوابة دون اجتياز السابقة."""
    system = PromotionSystem()
    system.start_promotion("model", "model-003", "agent-001")
    with pytest.raises(ValueError):
        system.pass_gate("model", "model-003", "canary", {})


def test_fail_gate() -> None:
    """رسوب في بوابة."""
    system = PromotionSystem()
    system.start_promotion("model", "model-004", "agent-001")
    result = system.fail_gate("model", "model-004", "evaluation", "درجة منخفضة")
    assert result["status"] == "failed"


def test_promotion_status_all_passed() -> None:
    """حالة الترقية بعد اجتياز كل البوابات."""
    system = PromotionSystem()
    system.start_promotion("model", "model-005", "agent-001")
    for gate in GATE_ORDER:
        system.pass_gate("model", "model-005", gate, {"score": 0.9})
    status = system.get_promotion_status("model", "model-005")
    assert status["all_passed"] is True
    assert status["can_activate"] is True


def test_promotion_status_not_all_passed() -> None:
    """حالة الترقية قبل اجتياز كل البوابات."""
    system = PromotionSystem()
    system.start_promotion("model", "model-006", "agent-001")
    system.pass_gate("model", "model-006", "evaluation", {"score": 0.9})
    status = system.get_promotion_status("model", "model-006")
    assert status["all_passed"] is False


def test_gate_passed_publishes_event() -> None:
    """اجتياز بوابة ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.governance.gate_passed")
    system = PromotionSystem()
    system.start_promotion("model", "model-007", "agent-001")
    system.pass_gate("model", "model-007", "evaluation", {"score": 0.9})
    assert bus.count("amos_federation.governance.gate_passed") > initial


# === 9.5: Executive Branch ===


def test_executive_roles_initialized() -> None:
    """الأدوار التنفيذية الخمسة مهيأة."""
    branch = ExecutiveBranch()
    roles = branch.list_roles()
    assert len(roles) >= 5
    role_names = [r["role_name"] for r in roles]
    assert "coordinator" in role_names
    assert "planning_advisor" in role_names
    assert "security_advisor" in role_names
    assert "spokesperson" in role_names
    assert "operations_manager" in role_names


def test_appoint_executive_role() -> None:
    """تعيين وكيل في دور تنفيذي."""
    agents = get_population_registry().list_agents()
    branch = ExecutiveBranch()
    result = branch.appoint("coordinator", agents[0]["agent_id"])
    assert result["status"] == "filled"
    assert result["agent_id"] == agents[0]["agent_id"]


def test_fill_all_executive_roles() -> None:
    """ملء كل الأدوار بوكلاء حقيقيين."""
    branch = ExecutiveBranch()
    result = branch.fill_all_roles()
    assert result["appointed"] >= 1
    roles = branch.list_roles()
    filled = [r for r in roles if r["status"] == "filled"]
    assert len(filled) >= 1


def test_appoint_nonexistent_agent_raises() -> None:
    """تعيين وكيل غير موجود يثير خطأ."""
    with pytest.raises(ValueError):
        ExecutiveBranch().appoint("coordinator", "nonexistent")


def test_appoint_invalid_role_raises() -> None:
    """دور غير معروف يثير خطأ."""
    agents = get_population_registry().list_agents()
    with pytest.raises(ValueError):
        ExecutiveBranch().appoint("invalid_role", agents[0]["agent_id"])


# === 9.6: Legislative Branch ===


def test_propose_legislation() -> None:
    """اقتراح قانون."""
    result = LegislativeBranch().propose("قانون 1", "نص القانون", "agent-001")
    assert result["status"] == "proposed"


def test_full_legislative_cycle() -> None:
    """دورة تشريعية كاملة: اقتراح → مناقشة → تصويت → إقرار."""
    branch = LegislativeBranch()
    voters = [
        ("agent-001", "for"),
        ("agent-002", "for"),
        ("agent-003", "for"),
        ("agent-004", "against"),
        ("agent-005", "abstain"),
    ]
    result = branch.run_full_legislative_cycle(
        "قانون الأمن", "يحظر الأدوات الخطيرة بدون موافقة", "agent-001", voters
    )
    assert result["final_status"] == "enacted"
    assert result["votes_for"] == 3
    assert result["rule_name"] is not None


def test_legislation_rejected_when_more_against() -> None:
    """القانون يُرفض إذا كان الأصوات ضد أكثر."""
    branch = LegislativeBranch()
    voters = [("agent-001", "for"), ("agent-002", "against"), ("agent-003", "against")]
    result = branch.run_full_legislative_cycle("قانون مرفوض", "نص", "agent-001", voters)
    assert result["final_status"] == "rejected"


def test_double_vote_raises() -> None:
    """التصويت مرتين يثير خطأ."""
    branch = LegislativeBranch()
    prop = branch.propose("قانون 2", "نص", "agent-001")
    branch.open_debate(prop["legislation_id"])
    branch.open_voting(prop["legislation_id"])
    branch.vote(prop["legislation_id"], "agent-001", "for")
    with pytest.raises(ValueError):
        branch.vote(prop["legislation_id"], "agent-001", "against")


def test_legislation_enacted_adds_to_policy_engine() -> None:
    """القانون المُقر يُضاف لـ Policy Engine."""
    branch = LegislativeBranch()
    voters = [("agent-001", "for"), ("agent-002", "for")]
    result = branch.run_full_legislative_cycle("قانون الاختبار", "نص", "agent-001", voters)
    assert result["final_status"] == "enacted"
    assert result["rule_name"] is not None
    assert result["rule_name"].startswith("legislated_")


def test_legislation_publishes_events() -> None:
    """الدورة التشريعية تنشر أحداثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.legislative.proposed")
    LegislativeBranch().propose("قانون 3", "نص", "agent-001")
    assert bus.count("amos_federation.legislative.proposed") > initial


# === 9.7: Judicial Branch ===


def test_file_case() -> None:
    """رفع دعوى."""
    result = JudicialBranch().file_case("agent-001", "agent-002", "نزاع على مورد")
    assert result["status"] == "open"


def test_add_argument() -> None:
    """إضافة مرافعة."""
    court = JudicialBranch()
    case = court.file_case("agent-001", "agent-002", "نزاع")
    result = court.add_argument(case["case_id"], "مرافعة الادعاء", "agent-001")
    assert result["argument_added"] is True


def test_rule_on_case() -> None:
    """إصدار حكم."""
    court = JudicialBranch()
    case = court.file_case("agent-001", "agent-002", "نزاع")
    court.add_argument(case["case_id"], "مرافعة", "agent-001")
    result = court.rule(case["case_id"], "حكم لصالح الادعاء", "judge-001")
    assert result["status"] == "ruled"
    assert result["ruling"] == "حكم لصالح الادعاء"


def test_judicial_publishes_events() -> None:
    """رفع دعوى ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.judicial.case_filed")
    JudicialBranch().file_case("a", "b", "نزاع")
    assert bus.count("amos_federation.judicial.case_filed") > initial


def test_list_cases() -> None:
    """عرض القضايا."""
    court = JudicialBranch()
    court.file_case("a", "b", "نزاع 1")
    court.file_case("c", "d", "نزاع 2")
    cases = court.list_cases()
    assert len(cases) >= 2


# === 9.8: Supreme Oversight ===


def test_generate_compliance_report() -> None:
    """تقرير امتثال شهري حقيقي."""
    result = SupremeOversight().generate_compliance_report("2026-08")
    assert "compliance_rate" in result
    assert "total_audits" in result
    assert "findings" in result
    assert "chain_verified" in result
    assert result["period"] == "2026-08"


def test_compliance_report_uses_real_audit() -> None:
    """التقرير مبني على Audit Chain الحقيقي."""
    from amos_federation.common.persistent import PersistentAuditStore

    audit = PersistentAuditStore()
    audit.append("test_action", "tester", {"test": True})
    result = SupremeOversight().generate_compliance_report("2026-08")
    assert result["total_audits"] >= 1


def test_list_reports() -> None:
    """عرض التقارير."""
    SupremeOversight().generate_compliance_report("2026-07")
    SupremeOversight().generate_compliance_report("2026-08")
    reports = SupremeOversight().list_reports()
    assert len(reports) >= 2


def test_oversight_publishes_event() -> None:
    """توليد تقرير ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    initial = bus.count("amos_federation.oversight.report_generated")
    SupremeOversight().generate_compliance_report("2026-08")
    assert bus.count("amos_federation.oversight.report_generated") > initial


# === Control Console integration ===


def test_ui_approvals_endpoint() -> None:
    """واجهة التحكم تعرض الموافقات."""
    resp = client.get("/v1/approvals", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_ui_legislations_endpoint() -> None:
    """واجهة التحكم تعرض التشريعات."""
    resp = client.get("/v1/legislations", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_ui_court_cases_endpoint() -> None:
    """واجهة التحكم تعرض القضايا."""
    resp = client.get("/v1/court-cases", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_ui_compliance_reports_endpoint() -> None:
    """واجهة التحكم تعرض تقارير الامتثال."""
    resp = client.get("/v1/compliance-reports", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_ui_executive_roles_endpoint() -> None:
    """واجهة التحكم تعرض الأدوار التنفيذية."""
    resp = client.get("/v1/executive-roles", headers=AUTH_HEADERS)
    assert resp.status_code == 200
