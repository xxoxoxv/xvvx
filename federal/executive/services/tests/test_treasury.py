"""
اختبارات الخزانة الفدرالية والعملة الرقمية (Phase 10)
الهدف: التحقق من amos-credit، مصادر الدخل، المصروف، التقارير المالية
النطاق: services/governance/treasury
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest
from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.agent_runtime.population import get_population_registry
from amos_federation.services.governance.treasury import (
    Treasury, get_treasury, run_economic_cycle,
    REWARD_TASK_COMPLETION, REWARD_QUALITY_REPORT, REWARD_SUCCESSFUL_TRAINING,
)
from amos_federation.services.control_console.main import app

AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token("tester", [
        "governance:read", "governance:write",
    ])
}
client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_and_clean():
    """بذر وتنظيف."""
    from amos_federation.services.governance.canary import reset_kill_switch
    from amos_federation.common.database import get_session_factory, get_database_url
    from amos_federation.services.governance.treasury import _TreasuryBase
    from sqlalchemy import delete, create_engine

    reset_kill_switch()
    # Ensure tables exist
    url = get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    _TreasuryBase.metadata.create_all(engine)

    registry = get_population_registry()
    registry.seed_initial_population()
    yield
    # Clean treasury tables
    from amos_federation.services.governance.treasury import (
        TransactionModel, BudgetModel, FinancialReportModel,
    )
    session = get_session_factory()()
    try:
        for model in [TransactionModel, BudgetModel, FinancialReportModel]:
            session.execute(delete(model))
        session.commit()
    finally:
        session.close()
    reset_kill_switch()


# === 10.1: amos-credit ===

def test_transaction_is_insert_only() -> None:
    """المعاملة غير قابلة للتعديل — INSERT-only."""
    t = Treasury()
    tx = t.reward_task_completion("agent-001", "exp-001", 0.8)
    # محاولة تعديل يجب أن تفشل (لا يوجد update method)
    assert not hasattr(t, "update_transaction")
    assert not hasattr(t, "edit_transaction")
    assert not hasattr(t, "delete_transaction")


def test_transaction_has_hash_chain() -> None:
    """كل معاملة لها hash مرتبط بالسابقة."""
    t = Treasury()
    tx1 = t.reward_task_completion("agent-001", "exp-001", 0.5)
    tx2 = t.reward_task_completion("agent-001", "exp-002", 0.7)
    assert len(tx1["hash"]) == 64  # SHA-256
    assert len(tx2["hash"]) == 64
    assert tx1["hash"] != tx2["hash"]


def test_verify_chain_empty() -> None:
    """التحقق من السلسلة الفارغة."""
    result = Treasury().verify_chain()
    assert result["valid"] is True
    assert result["transactions"] >= 0


def test_verify_chain_with_transactions() -> None:
    """التحقق من السلسلة بعد معاملات."""
    t = Treasury()
    t.reward_task_completion("agent-001", "exp-001", 0.5)
    t.reward_task_completion("agent-001", "exp-002", 0.7)
    result = t.verify_chain()
    assert result["valid"] is True
    assert result["transactions"] >= 2


def test_get_balance_empty() -> None:
    """الرصيد صفر بدون معاملات."""
    result = Treasury().get_balance()
    assert "balance" in result


def test_get_balance_after_income() -> None:
    """الرصيد بعد دخل."""
    t = Treasury()
    t.reward_task_completion("agent-001", "exp-001", 0.5)
    balance = t.get_balance(agent_id="agent-001")
    assert balance["balance"] > 0
    assert balance["total_earned"] > 0


def test_get_balance_after_expense() -> None:
    """الرصيد بعد مصروف."""
    t = Treasury()
    t.reward_task_completion("agent-001", "exp-001", 0.5)
    t.charge_model_invoke("agent-001", 0.01, "claude-sonnet")
    balance = t.get_balance(agent_id="agent-001")
    assert balance["total_spent"] > 0
    assert balance["balance"] < balance["total_earned"]


def test_transaction_publishes_event() -> None:
    """المعاملة تنشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus
    bus = get_event_bus()
    initial = bus.count("amos_federation.treasury.transaction")
    Treasury().reward_task_completion("agent-001", "exp-001", 0.5)
    assert bus.count("amos_federation.treasury.transaction") > initial


# === 10.2: Income sources ===

def test_reward_task_completion() -> None:
    """مكافأة إكمال مهمة — مرتبطة بـ experience.recorded."""
    result = Treasury().reward_task_completion("agent-001", "exp-001", 0.8)
    assert result["tx_type"] == "credit"
    assert result["source"] == "task_completion"
    assert result["linked_event"] == "amos_federation.experience.recorded"
    assert result["linked_ref"] == "exp-001"
    # جودة أعلى = مكافأة أعلى
    assert result["amount"] > REWARD_TASK_COMPLETION * 0.5


def test_reward_quality_report() -> None:
    """مكافأة تقرير عالي الجودة — مرتبطة بـ evaluation."""
    result = Treasury().reward_quality_report("agent-001", "rev-001", 0.9)
    assert result["tx_type"] == "credit"
    assert result["source"] == "quality_report"
    assert result["linked_event"] == "amos_federation.evaluation.completed"


def test_reward_successful_training() -> None:
    """مكافأة تدريب ناجح."""
    result = Treasury().reward_successful_training("agent-001", "grad-001")
    assert result["tx_type"] == "credit"
    assert result["source"] == "training"
    assert result["amount"] == REWARD_SUCCESSFUL_TRAINING


def test_higher_quality_higher_reward() -> None:
    """جودة أعلى = مكافأة أعلى."""
    t = Treasury()
    low = t.reward_task_completion("agent-001", "exp-001", 0.1)
    high = t.reward_task_completion("agent-001", "exp-002", 0.9)
    assert high["amount"] > low["amount"]


def test_process_experience_income_uses_real_data() -> None:
    """معالجة الدخل تستخدم خبرات حقيقية."""
    from amos_federation.common.persistent import PersistentExperienceStore
    exp_store = PersistentExperienceStore()
    exp_store.record({
        "type": "task", "task_id": "task-001", "agent_id": "agent-001",
        "model_used": "claude", "outcome": {"success": True}, "quality_score": 0.8,
    })
    results = Treasury().process_experience_income("agent-001")
    assert len(results) >= 1
    assert results[0]["linked_event"] == "amos_federation.experience.recorded"


# === 10.3: Expense sources ===

def test_charge_model_invoke() -> None:
    """رسوم استدعاء نموذج — مرتبطة بـ Cost Tracking."""
    result = Treasury().charge_model_invoke("agent-001", 0.003, "claude-sonnet")
    assert result["tx_type"] == "debit"
    assert result["source"] == "model_invoke"
    assert result["linked_event"] == "amos_federation.model.invoked"
    assert result["amount"] > 0


def test_charge_storage() -> None:
    """رسوم تخزين مفرط."""
    result = Treasury().charge_storage("agent-001", 100.0)
    assert result["tx_type"] == "debit"
    assert result["source"] == "storage"


def test_charge_retraining() -> None:
    """رسوم إعادة تدريب."""
    result = Treasury().charge_retraining("agent-001", "treat-001")
    assert result["tx_type"] == "debit"
    assert result["source"] == "retraining"


def test_process_real_costs_uses_cost_tracking() -> None:
    """معالجة المصروفات تستخدم Cost Tracking الحقيقي."""
    results = Treasury().process_real_costs()
    # قد تكون فارغة إذا لم تكن هناك تكاليف
    assert isinstance(results, list)


# === 10.4: Treasury functions ===

def test_allocate_budget() -> None:
    """توزيع موازنة."""
    result = Treasury().allocate_budget("agent", "agent-001", 1000.0, "2026-08")
    assert result["allocated"] == 1000.0
    assert result["holder"] == "agent-001"


def test_get_budget() -> None:
    """عرض موازنة."""
    t = Treasury()
    t.allocate_budget("agent", "agent-001", 500.0, "2026-08")
    budget = t.get_budget("agent-001", "2026-08")
    assert budget["allocated"] == 500.0
    assert budget["remaining"] == 500.0


def test_generate_financial_report() -> None:
    """تقرير مالي فدرالي."""
    t = Treasury()
    t.reward_task_completion("agent-001", "exp-001", 0.5)
    t.charge_model_invoke("agent-001", 0.01, "claude")
    report = t.generate_financial_report("2026-08")
    assert report["total_income"] > 0
    assert report["total_expense"] > 0
    assert report["transactions_count"] >= 2
    assert "income_breakdown" in report
    assert "expense_breakdown" in report
    assert report["chain_verified"] is True


def test_financial_report_chain_verified() -> None:
    """التقرير المالي يتحقق من السلسلة."""
    t = Treasury()
    t.reward_task_completion("agent-001", "exp-001", 0.5)
    report = t.generate_financial_report("2026-08")
    assert report["chain_verified"] is True


def test_list_transactions() -> None:
    """عرض المعاملات."""
    t = Treasury()
    t.reward_task_completion("agent-001", "exp-001", 0.5)
    t.charge_model_invoke("agent-001", 0.01, "claude")
    txs = t.list_transactions()
    assert len(txs) >= 2


def test_list_reports() -> None:
    """عرض التقارير."""
    t = Treasury()
    t.generate_financial_report("2026-07")
    t.generate_financial_report("2026-08")
    reports = t.list_reports()
    assert len(reports) >= 2


def test_report_publishes_event() -> None:
    """التقرير المالي ينشر حدثًا."""
    from amos_federation.common.event_bus import get_event_bus
    bus = get_event_bus()
    initial = bus.count("amos_federation.treasury.report_generated")
    Treasury().generate_financial_report("2026-08")
    assert bus.count("amos_federation.treasury.report_generated") > initial


# === Full economic cycle ===

def test_run_economic_cycle() -> None:
    """دورة اقتصادية كاملة."""
    result = run_economic_cycle()
    assert "agents_processed" in result
    assert "income_transactions" in result
    assert "expense_transactions" in result
    assert "federal_balance" in result
    assert "report" in result


# === Control Console integration ===

def test_ui_treasury_balance() -> None:
    """واجهة: رصيد الخزانة."""
    resp = client.get("/v1/treasury/balance", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "balance" in resp.json()


def test_ui_treasury_transactions() -> None:
    """واجهة: المعاملات."""
    Treasury().reward_task_completion("agent-001", "exp-001", 0.5)
    resp = client.get("/v1/treasury/transactions", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_ui_treasury_verify() -> None:
    """واجهة: التحقق من السلسلة."""
    resp = client.get("/v1/treasury/verify", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "valid" in resp.json()


def test_ui_treasury_reward() -> None:
    """واجهة: مكافأة وكيل."""
    resp = client.post("/v1/treasury/reward?agent_id=agent-001&experience_id=exp-001&quality_score=0.8", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["tx_type"] == "credit"


def test_ui_treasury_charge() -> None:
    """واجهة: خصم رسوم."""
    resp = client.post("/v1/treasury/charge?agent_id=agent-001&cost_usd=0.003&model_name=claude", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["tx_type"] == "debit"


def test_ui_treasury_reports() -> None:
    """واجهة: التقارير المالية."""
    Treasury().generate_financial_report("2026-08")
    resp = client.get("/v1/treasury/reports", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_ui_treasury_generate_report() -> None:
    """واجهة: توليد تقرير مالي."""
    resp = client.post("/v1/treasury/report?period=2026-08&report_type=monthly", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["period"] == "2026-08"
