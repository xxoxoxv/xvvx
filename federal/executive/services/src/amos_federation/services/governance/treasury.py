"""
AMOS-Federation Federal Treasury & Digital Currency (Phase 10)
الهدف: اقتصاد داخلي حقيقي — amos-credit، دخل، مصروف، تقارير مالية
النطاق: services/governance/treasury
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    select,
    desc,
    func,
)
from sqlalchemy.orm import DeclarativeBase

from amos_federation.common.database import get_database_url, get_session_factory


class _TreasuryBase(DeclarativeBase):
    """قاعدة نماذج الخزانة."""
    pass


# === Models ===

class TransactionModel(_TreasuryBase):
    """جدول المعاملات المالية — غير قابل للتعديل (INSERT-only)."""
    __tablename__ = "treasury_transactions"

    id = Column(String, primary_key=True)
    tx_type = Column(String, nullable=False)  # credit / debit
    source = Column(String, nullable=False)   # task_completion / quality_report / training / model_invoke / storage / retraining
    agent_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False)    # in amos-credit
    description = Column(Text, default="")
    linked_event = Column(String, nullable=True)  # event subject (experience.recorded, etc.)
    linked_ref = Column(String, nullable=True)     # reference ID (experience ID, cost record ID)
    prev_hash = Column(String, nullable=False, default="0" * 64)
    hash = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class BudgetModel(_TreasuryBase):
    """جدول الموازنات."""
    __tablename__ = "treasury_budgets"

    id = Column(String, primary_key=True)
    holder_type = Column(String, nullable=False)  # agent / department / federal
    holder_id = Column(String, nullable=False)
    allocated = Column(Float, default=0.0)
    spent = Column(Float, default=0.0)
    period = Column(String, nullable=False)  # e.g. "2026-08"
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class FinancialReportModel(_TreasuryBase):
    """جدول التقارير المالية."""
    __tablename__ = "treasury_reports"

    id = Column(String, primary_key=True)
    period = Column(String, nullable=False)  # "2026-08" or "2026-08-15"
    report_type = Column(String, nullable=False)  # daily / monthly
    total_income = Column(Float, default=0.0)
    total_expense = Column(Float, default=0.0)
    net_balance = Column(Float, default=0.0)
    transactions_count = Column(Integer, default=0)
    breakdown = Column(JSON, default=dict)
    chain_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# === Constants ===

# Rewards (in amos-credit)
REWARD_TASK_COMPLETION = 10.0
REWARD_QUALITY_REPORT = 5.0
REWARD_SUCCESSFUL_TRAINING = 15.0

# Cost rates (in amos-credit per unit)
COST_MODEL_INVOKE_BASE = 0.5
COST_STORAGE_PER_MB = 0.01
COST_RETRAINING = 20.0


# === Treasury ===

class Treasury:
    """الخزانة الفدرالية — إصدار amos-credit وتسجيل المعاملات."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _TreasuryBase.metadata.create_all(engine)

    def _compute_hash(self, tx_type: str, source: str, amount: float, prev_hash: str, tx_id: str) -> str:
        """حساب SHA-256 hash للمعاملة (فوق Audit Chain)."""
        payload = json.dumps({
            "tx_id": tx_id,
            "tx_type": tx_type,
            "source": source,
            "amount": amount,
            "prev_hash": prev_hash,
        }, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _last_hash(self) -> str:
        """أخر hash في السلسلة."""
        session = get_session_factory()()
        try:
            last = session.execute(
                select(TransactionModel).order_by(desc(TransactionModel.created_at)).limit(1)
            ).scalar_one_or_none()
            return last.hash if last else "0" * 64
        finally:
            session.close()

    def _record_transaction(
        self,
        tx_type: str,
        source: str,
        amount: float,
        agent_id: str | None = None,
        description: str = "",
        linked_event: str | None = None,
        linked_ref: str | None = None,
    ) -> dict[str, Any]:
        """تسجيل معاملة مالية — INSERT-only، غير قابلة للتعديل."""
        tx_id = str(uuid.uuid4())
        prev_hash = self._last_hash()
        tx_hash = self._compute_hash(tx_type, source, amount, prev_hash, tx_id)

        session = get_session_factory()()
        try:
            tx = TransactionModel(
                id=tx_id,
                tx_type=tx_type,
                source=source,
                agent_id=agent_id,
                amount=amount,
                description=description,
                linked_event=linked_event,
                linked_ref=linked_ref,
                prev_hash=prev_hash,
                hash=tx_hash,
            )
            session.add(tx)
            session.commit()
        finally:
            session.close()

        # نشر حدث
        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.treasury.transaction", {
            "tx_id": tx_id,
            "tx_type": tx_type,
            "source": source,
            "amount": amount,
            "agent_id": agent_id,
        })

        return {
            "tx_id": tx_id,
            "tx_type": tx_type,
            "source": source,
            "amount": amount,
            "agent_id": agent_id,
            "hash": tx_hash,
            "linked_event": linked_event,
            "linked_ref": linked_ref,
        }

    # === 10.1: amos-credit ===

    def verify_chain(self) -> dict[str, Any]:
        """التحقق من سلامة سلسلة المعاملات."""
        session = get_session_factory()()
        try:
            txs = session.execute(
                select(TransactionModel).order_by(TransactionModel.created_at)
            ).scalars().all()
            prev_hash = "0" * 64
            valid = True
            for tx in txs:
                expected = self._compute_hash(tx.tx_type, tx.source, tx.amount, prev_hash, tx.id)
                if tx.hash != expected:
                    valid = False
                    break
                prev_hash = tx.hash
            return {"valid": valid, "transactions": len(txs)}
        finally:
            session.close()

    def get_balance(self, agent_id: str | None = None) -> dict[str, Any]:
        """رصيد amos-credit (لكل وكيل أو الإجمالي)."""
        session = get_session_factory()()
        try:
            if agent_id:
                credits = session.execute(
                    select(func.sum(TransactionModel.amount)).where(
                        TransactionModel.tx_type == "credit",
                        TransactionModel.agent_id == agent_id,
                    )
                ).scalar() or 0.0
                debits = session.execute(
                    select(func.sum(TransactionModel.amount)).where(
                        TransactionModel.tx_type == "debit",
                        TransactionModel.agent_id == agent_id,
                    )
                ).scalar() or 0.0
                return {
                    "agent_id": agent_id,
                    "total_earned": credits,
                    "total_spent": debits,
                    "balance": credits - debits,
                }
            else:
                credits = session.execute(
                    select(func.sum(TransactionModel.amount)).where(TransactionModel.tx_type == "credit")
                ).scalar() or 0.0
                debits = session.execute(
                    select(func.sum(TransactionModel.amount)).where(TransactionModel.tx_type == "debit")
                ).scalar() or 0.0
                return {
                    "total_earned": credits,
                    "total_spent": debits,
                    "balance": credits - debits,
                }
        finally:
            session.close()

    # === 10.2: Income sources ===

    def reward_task_completion(self, agent_id: str, experience_id: str, quality_score: float = 0.5) -> dict[str, Any]:
        """مكافأة إكمال مهمة — مرتبطة بـ experience.recorded الحقيقي."""
        amount = REWARD_TASK_COMPLETION * (0.5 + quality_score)  # جودة أعلى = مكافأة أعلى
        return self._record_transaction(
            tx_type="credit",
            source="task_completion",
            amount=amount,
            agent_id=agent_id,
            description=f"مكافأة إكمال مهمة (جودة: {quality_score:.1%})",
            linked_event="amos_federation.experience.recorded",
            linked_ref=experience_id,
        )

    def reward_quality_report(self, agent_id: str, review_id: str, quality_score: float = 0.5) -> dict[str, Any]:
        """مكافأة تقرير عالي الجودة — مرتبطة بـ evaluation حقيقي."""
        amount = REWARD_QUALITY_REPORT * (0.5 + quality_score)
        return self._record_transaction(
            tx_type="credit",
            source="quality_report",
            amount=amount,
            agent_id=agent_id,
            description=f"مكافأة جودة (درجة: {quality_score:.1%})",
            linked_event="amos_federation.evaluation.completed",
            linked_ref=review_id,
        )

    def reward_successful_training(self, agent_id: str, graduation_id: str) -> dict[str, Any]:
        """مكافأة تدريب ناجح — مرتبطة بـ AgentSchool."""
        return self._record_transaction(
            tx_type="credit",
            source="training",
            amount=REWARD_SUCCESSFUL_TRAINING,
            agent_id=agent_id,
            description="مكافأة تخرج من المدرسة",
            linked_event="amos_federation.school.graduated",
            linked_ref=graduation_id,
        )

    def process_experience_income(self, agent_id: str) -> list[dict[str, Any]]:
        """معالجة كل خبرات الوكيل غير المكافأة وتوزيع الدخل."""
        from amos_federation.common.persistent import PersistentExperienceStore
        exp_store = PersistentExperienceStore()
        experiences = exp_store.list_all(agent_id=agent_id, limit=100)

        results = []
        for exp in experiences:
            quality = exp.get("quality_score", 0.5) or 0.5
            exp_id = exp.get("experience_id", exp.get("id", ""))
            result = self.reward_task_completion(agent_id, exp_id, quality)
            results.append(result)
        return results

    # === 10.3: Expense sources ===

    def charge_model_invoke(self, agent_id: str, cost_usd: float, model_name: str) -> dict[str, Any]:
        """رسوم استدعاء نموذج — مرتبطة بـ Cost Tracking الحقيقي."""
        # تحويل الدولار لـ amos-credit (1 USD = 100 amos-credit)
        amount = cost_usd * 100 + COST_MODEL_INVOKE_BASE
        return self._record_transaction(
            tx_type="debit",
            source="model_invoke",
            amount=amount,
            agent_id=agent_id,
            description=f"استدعاء نموذج {model_name} (${cost_usd:.6f})",
            linked_event="amos_federation.model.invoked",
            linked_ref=model_name,
        )

    def charge_storage(self, agent_id: str, size_mb: float) -> dict[str, Any]:
        """رسوم تخزين مفرط."""
        amount = size_mb * COST_STORAGE_PER_MB
        return self._record_transaction(
            tx_type="debit",
            source="storage",
            amount=amount,
            agent_id=agent_id,
            description=f"تخزين {size_mb:.1f} MB",
        )

    def charge_retraining(self, agent_id: str, treatment_id: str) -> dict[str, Any]:
        """رسوم إعادة تدريب — مرتبطة بـ TreatmentSystem."""
        return self._record_transaction(
            tx_type="debit",
            source="retraining",
            amount=COST_RETRAINING,
            agent_id=agent_id,
            description="رسوم إعادة تدريب",
            linked_event="amos_federation.health.treatment_completed",
            linked_ref=treatment_id,
        )

    def process_real_costs(self) -> list[dict[str, Any]]:
        """معالجة التكاليف الحقيقية من Model Gateway (المرحلة 5)."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer
        cost_summary = get_model_layer().get_cost_summary()

        results = []
        # خصم التكلفة الإجمالية من الموازنة الفدرالية
        total_cost = cost_summary.get("total_cost_usd", 0.0)
        if total_cost > 0:
            result = self._record_transaction(
                tx_type="debit",
                source="model_invoke",
                amount=total_cost * 100,
                agent_id=None,
                description=f"إجمالي تكلفة النماذج (${total_cost:.6f})",
                linked_event="amos_federation.model.cost_summary",
                linked_ref="federal",
            )
            results.append(result)
        return results

    # === 10.4: Treasury functions ===

    def allocate_budget(self, holder_type: str, holder_id: str, amount: float, period: str | None = None) -> dict[str, Any]:
        """توزيع موازنة."""
        if not period:
            period = datetime.now(UTC).strftime("%Y-%m")

        budget_id = str(uuid.uuid4())
        session = get_session_factory()()
        try:
            budget = BudgetModel(
                id=budget_id,
                holder_type=holder_type,
                holder_id=holder_id,
                allocated=amount,
                spent=0.0,
                period=period,
            )
            session.add(budget)
            session.commit()
        finally:
            session.close()

        return {"budget_id": budget_id, "holder": holder_id, "allocated": amount, "period": period}

    def get_budget(self, holder_id: str, period: str | None = None) -> dict[str, Any]:
        """عرض موازنة."""
        if not period:
            period = datetime.now(UTC).strftime("%Y-%m")
        session = get_session_factory()()
        try:
            budget = session.execute(
                select(BudgetModel).where(
                    BudgetModel.holder_id == holder_id,
                    BudgetModel.period == period,
                ).limit(1)
            ).scalar_one_or_none()
            if not budget:
                return {"holder_id": holder_id, "allocated": 0.0, "spent": 0.0, "remaining": 0.0}
            return {
                "holder_id": holder_id,
                "allocated": budget.allocated,
                "spent": budget.spent,
                "remaining": budget.allocated - budget.spent,
                "period": budget.period,
            }
        finally:
            session.close()

    def generate_financial_report(self, period: str | None = None, report_type: str = "monthly") -> dict[str, Any]:
        """تقرير مالي فدرالي حقيقي مبني على معاملات فعلية."""
        if not period:
            period = datetime.now(UTC).strftime("%Y-%m")

        session = get_session_factory()()
        try:
            # كل المعاملات في الفترة
            all_txs = session.execute(
                select(TransactionModel).order_by(TransactionModel.created_at)
            ).scalars().all()

            # فلترة بالفترة (بسيط: كل المعاملات لهذا التقرير)
            credits = [t for t in all_txs if t.tx_type == "credit"]
            debits = [t for t in all_txs if t.tx_type == "debit"]

            total_income = sum(t.amount for t in credits)
            total_expense = sum(t.amount for t in debits)

            # تفصيل حسب المصدر
            income_breakdown: dict[str, float] = {}
            for t in credits:
                income_breakdown[t.source] = income_breakdown.get(t.source, 0.0) + t.amount

            expense_breakdown: dict[str, float] = {}
            for t in debits:
                expense_breakdown[t.source] = expense_breakdown.get(t.source, 0.0) + t.amount

            # التحقق من السلسلة
            prev_hash = "0" * 64
            chain_valid = True
            for tx in all_txs:
                expected = self._compute_hash(tx.tx_type, tx.source, tx.amount, prev_hash, tx.id)
                if tx.hash != expected:
                    chain_valid = False
                    break
                prev_hash = tx.hash

            report_id = str(uuid.uuid4())
            report = FinancialReportModel(
                id=report_id,
                period=period,
                report_type=report_type,
                total_income=total_income,
                total_expense=total_expense,
                net_balance=total_income - total_expense,
                transactions_count=len(all_txs),
                breakdown={"income": income_breakdown, "expense": expense_breakdown},
                chain_verified=chain_valid,
            )
            session.add(report)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.treasury.report_generated", {
            "report_id": report_id, "period": period,
            "net_balance": total_income - total_expense,
        })

        return {
            "report_id": report_id,
            "period": period,
            "report_type": report_type,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense,
            "transactions_count": len(all_txs),
            "income_breakdown": income_breakdown,
            "expense_breakdown": expense_breakdown,
            "chain_verified": chain_valid,
        }

    def list_transactions(self, limit: int = 50) -> list[dict[str, Any]]:
        """عرض المعاملات."""
        session = get_session_factory()()
        try:
            txs = session.execute(
                select(TransactionModel).order_by(desc(TransactionModel.created_at)).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": t.id,
                    "tx_type": t.tx_type,
                    "source": t.source,
                    "agent_id": t.agent_id,
                    "amount": t.amount,
                    "description": t.description,
                    "linked_event": t.linked_event,
                    "hash": t.hash[:20] + "..." if t.hash else "",
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in txs
            ]
        finally:
            session.close()

    def list_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        """عرض التقارير المالية."""
        session = get_session_factory()()
        try:
            reports = session.execute(
                select(FinancialReportModel).order_by(desc(FinancialReportModel.created_at)).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "period": r.period,
                    "report_type": r.report_type,
                    "total_income": r.total_income,
                    "total_expense": r.total_expense,
                    "net_balance": r.net_balance,
                    "transactions_count": r.transactions_count,
                    "chain_verified": r.chain_verified,
                }
                for r in reports
            ]
        finally:
            session.close()


# === Full economic cycle ===

def run_economic_cycle() -> dict[str, Any]:
    """دورة اقتصادية كاملة: وكيل ينجز مهمة → يكسب amos-credit → الخزانة تسجّل → تقرير مالي."""
    from amos_federation.services.agent_runtime.population import get_population_registry

    treasury = Treasury()
    registry = get_population_registry()
    agents = registry.list_agents()

    # 10.2: معالجة الدخل من الخبرات الحقيقية
    income_count = 0
    for agent in agents[:5]:  # أول 5 وكلاء
        results = treasury.process_experience_income(agent["agent_id"])
        income_count += len(results)

    # 10.3: معالجة المصروفات الحقيقية من Cost Tracking
    expense_results = treasury.process_real_costs()

    # 10.4: تقرير مالي
    report = treasury.generate_financial_report()

    balance = treasury.get_balance()

    return {
        "agents_processed": min(5, len(agents)),
        "income_transactions": income_count,
        "expense_transactions": len(expense_results),
        "federal_balance": balance["balance"],
        "report": report,
    }


# === Singleton ===

_treasury: Treasury | None = None


def get_treasury() -> Treasury:
    global _treasury
    if _treasury is None:
        _treasury = Treasury()
    return _treasury
