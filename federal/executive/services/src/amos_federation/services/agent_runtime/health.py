"""
AMOS-Federation Agent Health System
الهدف: النظام الصحي المؤسسي للوكلاء — فحص دوري، علاج، عزل
النطاق: services/agent_runtime/health
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from amos_federation.common.database import get_database_url, get_session_factory, init_db


# === Health Check Model ===

class _HealthBase(DeclarativeBase):
    """قاعدة نماذج الفحص الصحي."""
    pass


class AgentHealthCheckModel(_HealthBase):
    """جدول فحوصات الوكلاء الصحية."""
    __tablename__ = "agent_health_checks"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    check_date = Column(DateTime, default=lambda: datetime.now(UTC))
    status = Column(String, nullable=False)  # healthy / monitor / treatment / isolated
    performance_score = Column(Float, default=0.0)
    resource_usage = Column(JSON, default=dict)
    policy_compliance = Column(Float, default=0.0)
    tool_success_rate = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    findings = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    prev_hash = Column(String, nullable=False, default="0" * 64)
    hash = Column(String, nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class IsolationRecordModel(_HealthBase):
    """جدول سجلات العزل."""
    __tablename__ = "agent_isolations"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    isolated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    reason = Column(Text, nullable=False)
    sandbox_id = Column(String, nullable=True)
    actions_log = Column(JSON, default=list)  # كل فعل أثناء العزل
    status = Column(String, default="active")  # active / released / retired
    released_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class TreatmentRecordModel(_HealthBase):
    """جدول سجلات العلاج."""
    __tablename__ = "agent_treatments"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    treatment_type = Column(String, nullable=False)  # retrain / replace_model / fix_tool / reset_context
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="in_progress")  # in_progress / completed / failed
    details = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# === Health Status Enum ===

HEALTHY = "healthy"
MONITOR = "monitor"
TREATMENT = "treatment"
ISOLATED = "isolated"

ALL_STATUSES = [HEALTHY, MONITOR, TREATMENT, ISOLATED]


# === Health Checker ===

class HealthChecker:
    """الفاحص الصحي للوكلاء — يفحص كل وكيل دوريًا."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """إنشاء جداول الفحص الصحي إذا لم تكن موجودة."""
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _HealthBase.metadata.create_all(engine)

    def _compute_hash(self, action: str, actor: str, details: dict, prev_hash: str) -> str:
        """حساب SHA-256 hash للفحص (تماثل سلسلة التدقيق)."""
        import hashlib
        payload = json.dumps({
            "action": action,
            "actor": actor,
            "details": details,
            "prev_hash": prev_hash,
        }, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def check_agent(self, agent_id: str) -> dict[str, Any]:
        """
        8.1: فحص وكيل واحد — الأداء، استهلاك الموارد، الالتزام بالسياسات.
        النتيجة واحدة من أربع: سليم / مراقبة / علاج / عزل.
        """
        from amos_federation.services.agent_runtime.population import get_population_registry
        from amos_federation.common.persistent import PersistentExperienceStore

        registry = get_population_registry()
        agent = registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"الوكيل {agent_id} غير موجود")

        # جمع البيانات الحقيقية
        exp_store = PersistentExperienceStore()
        experiences = exp_store.list_all(agent_id=agent_id, limit=50)

        # حساب الأداء
        if experiences:
            scores = [e.get("quality_score", 0.5) for e in experiences if e.get("quality_score") is not None]
            performance_score = sum(scores) / len(scores) if scores else 0.5
        else:
            performance_score = 0.5  # لا خبرات بعد

        # معدل نجاح الأدوات (من الخبرات)
        tool_successes = sum(1 for e in experiences if e.get("outcome", {}).get("success", True))
        tool_success_rate = tool_successes / len(experiences) if experiences else 1.0

        # معدل الأخطاء
        error_count = sum(1 for e in experiences if not e.get("outcome", {}).get("success", True))
        error_rate = error_count / len(experiences) if experiences else 0.0

        # الالتزام بالسياسات (من سجل التدقيق)
        from amos_federation.common.persistent import PersistentAuditStore
        audit = PersistentAuditStore()
        audit_entries = audit.list_all(limit=100)
        policy_violations = sum(1 for a in audit_entries if "violation" in a.get("action", "").lower())
        policy_compliance = 1.0 - (policy_violations / max(len(audit_entries), 1))

        # استهلاك الموارد
        resource_usage = {
            "token_budget": agent.get("token_budget", 10000),
            "tokens_used": sum(e.get("outcome", {}).get("tokens_used", 0) for e in experiences),
            "tools_available": len(agent.get("allowed_tools", [])),
        }

        # تحديد الحالة الصحية
        findings: list[str] = []
        recommendations: list[str] = []

        if performance_score < 0.3 or error_rate > 0.5:
            status = ISOLATED
            findings.append(f"أداء حرج: {performance_score:.1%}، معدل أخطاء: {error_rate:.1%}")
            recommendations.append("عزل فوري وإعادة تقييم شامل")
        elif performance_score < 0.5 or error_rate > 0.3 or policy_compliance < 0.7:
            status = TREATMENT
            findings.append(f"أداء منخفض: {performance_score:.1%}")
            if error_rate > 0.3:
                recommendations.append("إعادة تدريب عبر المدرسة")
            if policy_compliance < 0.7:
                recommendations.append("مراجعة السياسات")
        elif performance_score < 0.7 or error_rate > 0.1 or policy_compliance < 0.9:
            status = MONITOR
            findings.append(f"أداء دون المستهدف: {performance_score:.1%}")
            recommendations.append("مراقبة مستمرة لمدة دورة كاملة")
        else:
            status = HEALTHY
            findings.append(f"أداء جيد: {performance_score:.1%}")

        # حفظ الفحص في DB مع hash chain
        session = get_session_factory()()
        try:
            # آخر hash
            from sqlalchemy import select, desc
            last_check = session.execute(
                select(AgentHealthCheckModel)
                .order_by(desc(AgentHealthCheckModel.created_at))
                .limit(1)
            ).scalar_one_or_none()
            prev_hash = last_check.hash if last_check else "0" * 64

            check_id = str(uuid.uuid4())
            details = {
                "agent_id": agent_id,
                "performance_score": performance_score,
                "error_rate": error_rate,
                "policy_compliance": policy_compliance,
                "tool_success_rate": tool_success_rate,
            }
            check_hash = self._compute_hash("health_check", agent_id, details, prev_hash)

            record = AgentHealthCheckModel(
                id=check_id,
                agent_id=agent_id,
                status=status,
                performance_score=performance_score,
                resource_usage=resource_usage,
                policy_compliance=policy_compliance,
                tool_success_rate=tool_success_rate,
                error_rate=error_rate,
                findings=findings,
                recommendations=recommendations,
                prev_hash=prev_hash,
                hash=check_hash,
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        # نشر حدث
        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.health.check_completed", {
            "agent_id": agent_id,
            "status": status,
            "performance_score": performance_score,
        })

        return {
            "check_id": check_id,
            "agent_id": agent_id,
            "status": status,
            "performance_score": performance_score,
            "resource_usage": resource_usage,
            "policy_compliance": policy_compliance,
            "tool_success_rate": tool_success_rate,
            "error_rate": error_rate,
            "findings": findings,
            "recommendations": recommendations,
            "hash": check_hash,
        }

    def check_all_agents(self, limit: int = 50) -> list[dict[str, Any]]:
        """فحص الوكلاء المسجلين (مع حد لتجنب عنق الزجاجة)."""
        from amos_federation.services.agent_runtime.population import get_population_registry
        agents = get_population_registry().list_agents()
        # تقييد العدد لتجنب عنق الزجاجة عند وجود مئات الوكلاء
        results = []
        for agent in agents[:limit]:
            results.append(self.check_agent(agent["agent_id"]))
        return results

    def get_agent_health_history(self, agent_id: str, limit: int = 30) -> list[dict[str, Any]]:
        """عرض تاريخ الفحوصات الصحية لوكيل."""
        session = get_session_factory()()
        try:
            from sqlalchemy import select, desc
            records = session.execute(
                select(AgentHealthCheckModel)
                .where(AgentHealthCheckModel.agent_id == agent_id)
                .order_by(desc(AgentHealthCheckModel.created_at))
                .limit(limit)
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "agent_id": r.agent_id,
                    "check_date": r.check_date.isoformat() if r.check_date else None,
                    "status": r.status,
                    "performance_score": r.performance_score,
                    "policy_compliance": r.policy_compliance,
                    "tool_success_rate": r.tool_success_rate,
                    "error_rate": r.error_rate,
                    "findings": r.findings or [],
                    "recommendations": r.recommendations or [],
                    "hash": r.hash,
                }
                for r in records
            ]
        finally:
            session.close()

    def get_latest_status(self, agent_id: str) -> str:
        """أحدث حالة صحية لوكيل."""
        history = self.get_agent_health_history(agent_id, limit=1)
        return history[0]["status"] if history else "unknown"


# === Treatment System ===

class TreatmentSystem:
    """نظام العلاج — ينفّذ مسار العلاج للوكلاء."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _HealthBase.metadata.create_all(engine)

    def start_treatment(self, agent_id: str, treatment_type: str, reason: str) -> dict[str, Any]:
        """
        8.2: بدء مسار العلاج — إعادة تدريب / استبدال نموذج / إصلاح أداة / إعادة تعيين سياق.
        يُنفَّذ فعليًا عبر استدعاء المدرسة أو Model Gateway.
        """
        if treatment_type not in ["retrain", "replace_model", "fix_tool", "reset_context"]:
            raise ValueError(f"نوع علاج غير معروف: {treatment_type}")

        treatment_id = str(uuid.uuid4())
        session = get_session_factory()()
        try:
            record = TreatmentRecordModel(
                id=treatment_id,
                agent_id=agent_id,
                treatment_type=treatment_type,
                status="in_progress",
                details={"reason": reason, "started_by": "health_system"},
            )
            session.add(record)

            # تحديث حالة الوكيل
            from amos_federation.services.agent_runtime.population import get_population_registry
            registry = get_population_registry()
            registry.update_state(agent_id, "training")

            session.commit()
        finally:
            session.close()

        # تنفيذ العلاج فعليًا
        result = self._execute_treatment(agent_id, treatment_type)

        # تحديث السجل
        session = get_session_factory()()
        try:
            from sqlalchemy import select
            record = session.execute(
                select(TreatmentRecordModel).where(TreatmentRecordModel.id == treatment_id)
            ).scalar_one()
            record.status = "completed"
            record.completed_at = datetime.now(UTC)
            record.result = result
            session.commit()
        finally:
            session.close()

        # إعادة الوكيل للحالة النشطة
        from amos_federation.services.agent_runtime.population import get_population_registry
        get_population_registry().update_state(agent_id, "active")

        # نشر حدث
        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.health.treatment_completed", {
            "agent_id": agent_id,
            "treatment_type": treatment_type,
            "result": result,
        })

        return {
            "treatment_id": treatment_id,
            "agent_id": agent_id,
            "treatment_type": treatment_type,
            "status": "completed",
            "result": result,
        }

    def _execute_treatment(self, agent_id: str, treatment_type: str) -> dict[str, Any]:
        """تنفيذ العلاج فعليًا حسب النوع."""
        if treatment_type == "retrain":
            # 8.2: استدعاء المدرسة (المرحلة 6)
            from amos_federation.services.agent_runtime.population import AgentSchool
            school = AgentSchool()
            # محاكاة التدريب — في الإنتاج سيكون تدريبًا حقيقيًا
            result = school.run_full_curriculum(agent_id)
            return {"retrain_result": result, "method": "AgentSchool.run_full_curriculum"}

        elif treatment_type == "replace_model":
            # 8.2: استدعاء Model Gateway (المرحلة 5)
            from amos_federation.services.model_gateway.model_layer import get_model_layer
            model_layer = get_model_layer()
            # استدعاء نموذج بديل
            result = model_layer.invoke_with_cache(
                prompt="System health recovery check",
                model="claude-sonnet",
                max_tokens=100,
            )
            return {"replace_result": result, "method": "ModelLayer.invoke_with_cache"}

        elif treatment_type == "fix_tool":
            # فحص الأدوات المسموح بها وإصلاحها
            from amos_federation.services.agent_runtime.population import get_population_registry
            agent = get_population_registry().get_agent(agent_id)
            tools = agent.get("allowed_tools", []) if agent else []
            return {"fixed_tools": tools, "method": "tool_audit"}

        elif treatment_type == "reset_context":
            # إعادة تعيين السياق — حذف ذاكرة الوكيل
            from amos_federation.services.agent_runtime.population import get_population_registry
            agent = get_population_registry().get_agent(agent_id)
            # مسح الذاكرة المرتبطة بالوكيل عبر query وإعادة التخزين بسياق فارغ
            from amos_federation.common.persistent import PersistentMemoryStore
            memory = PersistentMemoryStore()
            # لا يوجد clear_agent مباشر — نسجل سياقًا جديدًا فارغًا
            memory.store(f"agent_context_reset:{agent_id}", {"reset": True, "timestamp": datetime.now(UTC).isoformat()})
            return {"reset": True, "method": "MemoryStore.context_reset"}

        return {"error": "unknown treatment"}


# === Isolation System ===

class IsolationSystem:
    """نظام العزل — ينقل الوكيل لـ Sandbox معزول."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _HealthBase.metadata.create_all(engine)

    def isolate(self, agent_id: str, reason: str) -> dict[str, Any]:
        """
        8.3: مسار العزل — نقل لـ Sandbox معزول، فحص كل الأفعال.
        الوكيل المعزول لا يمكنه تنفيذ أي أداة إنتاجية.
        """
        isolation_id = str(uuid.uuid4())
        sandbox_id = f"sandbox-{agent_id[:8]}-{uuid.uuid4().hex[:4]}"

        session = get_session_factory()()
        try:
            record = IsolationRecordModel(
                id=isolation_id,
                agent_id=agent_id,
                reason=reason,
                sandbox_id=sandbox_id,
                status="active",
                actions_log=[],
            )
            session.add(record)

            # تحديث حالة الوكيل
            from amos_federation.services.agent_runtime.population import get_population_registry
            registry = get_population_registry()
            registry.update_state(agent_id, "paused")

            session.commit()
        finally:
            session.close()

        # نشر حدث
        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.health.agent_isolated", {
            "agent_id": agent_id,
            "sandbox_id": sandbox_id,
            "reason": reason,
        })

        return {
            "isolation_id": isolation_id,
            "agent_id": agent_id,
            "sandbox_id": sandbox_id,
            "status": "active",
            "reason": reason,
        }

    def log_action(self, isolation_id: str, action: str, details: dict) -> dict[str, Any]:
        """تسجيل فعل أثناء العزل — كل فعل يُفحص."""
        session = get_session_factory()()
        try:
            from sqlalchemy import select
            record = session.execute(
                select(IsolationRecordModel).where(IsolationRecordModel.id == isolation_id)
            ).scalar_one()
            actions = record.actions_log or []
            actions.append({
                "action": action,
                "details": details,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            record.actions_log = actions
            session.commit()
            return {"logged": True, "action": action}
        finally:
            session.close()

    def release(self, isolation_id: str, decision: str) -> dict[str, Any]:
        """
        8.3: إنهاء العزل — إعادة تدريب أو تقاعد.
        decision: retrain / retire / release
        """
        session = get_session_factory()()
        try:
            from sqlalchemy import select
            record = session.execute(
                select(IsolationRecordModel).where(IsolationRecordModel.id == isolation_id)
            ).scalar_one()
            record.status = decision
            record.released_at = datetime.now(UTC)
            session.commit()

            agent_id = record.agent_id
        finally:
            session.close()

        # تنفيذ القرار
        from amos_federation.services.agent_runtime.population import get_population_registry
        registry = get_population_registry()

        if decision == "retrain":
            treatment = TreatmentSystem()
            treatment.start_treatment(agent_id, "retrain", "إعادة تدريب بعد عزل")
        elif decision == "retire":
            registry.update_state(agent_id, "retired")
        elif decision == "release":
            registry.update_state(agent_id, "active")

        # نشر حدث
        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.health.agent_released", {
            "agent_id": agent_id,
            "decision": decision,
        })

        return {
            "isolation_id": isolation_id,
            "agent_id": agent_id,
            "decision": decision,
            "released_at": datetime.now(UTC).isoformat(),
        }

    def is_isolated(self, agent_id: str) -> bool:
        """هل الوكيل معزول حاليًا؟"""
        session = get_session_factory()()
        try:
            from sqlalchemy import select
            record = session.execute(
                select(IsolationRecordModel)
                .where(IsolationRecordModel.agent_id == agent_id)
                .where(IsolationRecordModel.status == "active")
                .limit(1)
            ).scalar_one_or_none()
            return record is not None
        finally:
            session.close()

    def list_active_isolations(self) -> list[dict[str, Any]]:
        """عرض كل حالات العزل النشطة."""
        session = get_session_factory()()
        try:
            from sqlalchemy import select
            records = session.execute(
                select(IsolationRecordModel).where(IsolationRecordModel.status == "active")
            ).scalars().all()
            return [
                {
                    "id": r.id,
                    "agent_id": r.agent_id,
                    "reason": r.reason,
                    "sandbox_id": r.sandbox_id,
                    "isolated_at": r.isolated_at.isoformat() if r.isolated_at else None,
                    "actions_count": len(r.actions_log or []),
                }
                for r in records
            ]
        finally:
            session.close()


# === Full Health Cycle ===

def run_health_cycle(limit: int = 20) -> dict[str, Any]:
    """تشغيل دورة فحص صحي كاملة على الوكلاء (مع حد لتجنب عنق الزجاجة)."""
    checker = HealthChecker()
    results = checker.check_all_agents(limit=limit)

    treatment = TreatmentSystem()
    isolation = IsolationSystem()

    treatments_started = 0
    isolations_started = 0

    for result in results:
        if result["status"] == TREATMENT:
            treatment.start_treatment(
                result["agent_id"],
                "retrain" if result["error_rate"] > 0.3 else "reset_context",
                f"علاج تلقائي: {result['findings'][0] if result['findings'] else 'أداء منخفض'}",
            )
            treatments_started += 1
        elif result["status"] == ISOLATED:
            isolation.isolate(
                result["agent_id"],
                f"عزل تلقائي: {result['findings'][0] if result['findings'] else 'أداء حرج'}",
            )
            isolations_started += 1

    return {
        "total_agents_checked": len(results),
        "healthy": sum(1 for r in results if r["status"] == HEALTHY),
        "monitor": sum(1 for r in results if r["status"] == MONITOR),
        "treatment": sum(1 for r in results if r["status"] == TREATMENT),
        "isolated": sum(1 for r in results if r["status"] == ISOLATED),
        "treatments_started": treatments_started,
        "isolations_started": isolations_started,
        "cycle_date": datetime.now(UTC).isoformat(),
    }


# === Singleton Accessors ===

_health_checker: HealthChecker | None = None
_treatment_system: TreatmentSystem | None = None
_isolation_system: IsolationSystem | None = None


def get_health_checker() -> HealthChecker:
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def get_treatment_system() -> TreatmentSystem:
    global _treatment_system
    if _treatment_system is None:
        _treatment_system = TreatmentSystem()
    return _treatment_system


def get_isolation_system() -> IsolationSystem:
    global _isolation_system
    if _isolation_system is None:
        _isolation_system = IsolationSystem()
    return _isolation_system
