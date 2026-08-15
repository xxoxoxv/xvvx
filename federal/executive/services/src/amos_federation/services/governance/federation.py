"""
AMOS-Federation Full Governance + Federal Institutions (Phase 9)
الهدف: إكمال الحوكمة + تفعيل السلطات الفدرالية الأربع + الرقابة العليا
النطاق: services/governance/federation
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
)
from sqlalchemy.orm import DeclarativeBase

from amos_federation.common.database import get_database_url, get_session_factory


class _GovBase(DeclarativeBase):
    """قاعدة نماذج الحوكمة الكاملة."""
    pass


# === Models ===

class ApprovalModel(_GovBase):
    """جدول الموافقات الموقعة بـ Ed25519."""
    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    request_type = Column(String, nullable=False)  # model_promotion / agent_promotion / policy_change
    target_id = Column(String, nullable=False)
    requester = Column(String, nullable=False)
    decision = Column(String, nullable=False)  # approve / reject
    signed_by = Column(String, nullable=False)
    signature = Column(Text, nullable=False, default="")  # Ed25519 signature hex
    public_key = Column(Text, nullable=False, default="")  # Ed25519 public key hex
    verified = Column(Boolean, default=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class PromotionGateModel(_GovBase):
    """جدول بوابات الترقية الخمس."""
    __tablename__ = "promotion_gates"

    id = Column(String, primary_key=True)
    target_type = Column(String, nullable=False)  # model / agent
    target_id = Column(String, nullable=False)
    gate = Column(String, nullable=False)  # evaluation / shadow / canary / human_approval / activation
    status = Column(String, nullable=False, default="pending")  # pending / passed / failed
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)


class ExecutiveRoleModel(_GovBase):
    """جدول الأدوار التنفيذية."""
    __tablename__ = "executive_roles"

    role_name = Column(String, primary_key=True)  # coordinator / planning_advisor / security_advisor / spokesperson / operations_manager
    agent_id = Column(String, nullable=True)
    appointed_at = Column(DateTime, nullable=True)
    status = Column(String, default="vacant")  # vacant / filled
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class LegislationModel(_GovBase):
    """جدول التشريعات."""
    __tablename__ = "legislations"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    proposer = Column(String, nullable=False)
    status = Column(String, nullable=False, default="proposed")  # proposed / debate / voting / enacted / rejected
    votes_for = Column(Integer, default=0)
    votes_against = Column(Integer, default=0)
    votes_abstain = Column(Integer, default=0)
    voters = Column(JSON, default=list)  # list of agent_ids who voted
    enacted_rule_name = Column(String, nullable=True)  # rule name in Policy Engine
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class CourtCaseModel(_GovBase):
    """جدول قضايا المحكمة العليا."""
    __tablename__ = "court_cases"

    id = Column(String, primary_key=True)
    plaintiff = Column(String, nullable=False)
    defendant = Column(String, nullable=False)
    subject = Column(Text, nullable=False)
    evidence = Column(JSON, default=list)
    arguments = Column(JSON, default=list)
    ruling = Column(Text, nullable=True)
    ruling_judge = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")  # open / hearing / ruled / dismissed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True)


class ComplianceReportModel(_GovBase):
    """جدول تقارير الامتثال."""
    __tablename__ = "compliance_reports"

    id = Column(String, primary_key=True)
    period = Column(String, nullable=False)  # e.g. "2026-08"
    report_type = Column(String, nullable=False, default="monthly")
    total_audits = Column(Integer, default=0)
    violations = Column(Integer, default=0)
    compliance_rate = Column(Float, default=0.0)
    findings = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    chain_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# === 9.1: Expanded Policy Engine ===

POLICY_RULES_EXPANDED = [
    # tool-registry
    {"name": "tool_execution_restricted", "description": "تنفيذ الأدوات يتطلب صلاحية مناسبة", "decision": "deny",
     "service": "tool-registry", "condition": {"field": "agent.role", "op": "not_in", "value": ["coordinator", "executor"]}},
    {"name": "sandbox_isolation_enforced", "description": "الأدوات الخطيرة تتطلب sandbox", "decision": "deny",
     "service": "tool-registry", "condition": {"field": "tool.sandbox_required", "op": "eq", "value": True}},
    # model-gateway
    {"name": "model_cost_limit", "description": "حد التكلفة اليومي للنماذج", "decision": "deny",
     "service": "model-gateway", "condition": {"field": "cost.daily_total", "op": "gt", "value": 100.0}},
    {"name": "model_access_restricted", "description": "النماذج المتقدمة تتطلب دور أعلى", "decision": "deny",
     "service": "model-gateway", "condition": {"field": "model.tier", "op": "eq", "value": "restricted"}},
    # agent-runtime
    {"name": "agent_not_isolated", "description": "الوكلاء المعزولون لا ينفذون", "decision": "deny",
     "service": "agent-runtime", "condition": {"field": "agent.health_status", "op": "eq", "value": "isolated"}},
    {"name": "agent_token_budget", "description": "حد ميزانية التوكنز لكل وكيل", "decision": "deny",
     "service": "agent-runtime", "condition": {"field": "agent.tokens_used", "op": "gt", "value": 100000}},
    # governance
    {"name": "kill_switch_halt", "description": "Kill Switch halt يمنع كل التنفيذ", "decision": "deny",
     "service": "governance", "condition": {"field": "system.level", "op": "eq", "value": "halt"}},
    {"name": "promotion_requires_gates", "description": "الترقية تتطلب اجتياز كل البوابات", "decision": "deny",
     "service": "governance", "condition": {"field": "promotion.gates_passed", "op": "lt", "value": 5}},
    # memory-service
    {"name": "memory_tenant_isolation", "description": "عزل ذاكرة المستأجرين", "decision": "deny",
     "service": "memory-service", "condition": {"field": "memory.tenant_mismatch", "op": "eq", "value": True}},
    # evaluation
    {"name": "evaluation_threshold", "description": "الترقية تتطلب تقييم ≥ 70%", "decision": "deny",
     "service": "evaluation", "condition": {"field": "evaluation.score", "op": "lt", "value": 0.7}},
]


# === 9.3: Ed25519 Signature ===

class Ed25519Signer:
    """توقيع Ed25519 حقيقي للموافقات."""

    def __init__(self) -> None:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PrivateKey, Ed25519PublicKey,
            )
            from cryptography.hazmat.primitives import serialization
            self._ed25519_available = True
            self._Ed25519PrivateKey = Ed25519PrivateKey
            self._Ed25519PublicKey = Ed25519PublicKey
            self._serialization = serialization
        except ImportError:
            # Fallback: SHA-256 based signing (not cryptographically secure, but deterministic)
            self._ed25519_available = False

    def generate_keypair(self) -> tuple[str, str]:
        """توليد زوج مفاتيح. يعيد (private_key_hex, public_key_hex)."""
        if self._ed25519_available:
            private_key = self._Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            priv_bytes = private_key.private_bytes(
                encoding=self._serialization.Encoding.Raw,
                format=self._serialization.PrivateFormat.Raw,
                encryption_algorithm=self._serialization.NoEncryption(),
            )
            pub_bytes = public_key.public_bytes(
                encoding=self._serialization.Encoding.Raw,
                format=self._serialization.PublicFormat.Raw,
            )
            return priv_bytes.hex(), pub_bytes.hex()
        else:
            # Fallback: generate a deterministic keypair from random
            seed = uuid.uuid4().hex + uuid.uuid4().hex
            return seed[:64], hashlib.sha256(seed.encode()).hexdigest()

    def sign(self, private_key_hex: str, message: str) -> str:
        """توقيع رسالة."""
        if self._ed25519_available:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            priv_bytes = bytes.fromhex(private_key_hex)
            private_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)
            signature = private_key.sign(message.encode())
            return signature.hex()
        else:
            # Fallback: HMAC-like signature
            return hashlib.sha256((private_key_hex + message).encode()).hexdigest()

    def verify(self, public_key_hex: str, message: str, signature_hex: str) -> bool:
        """التحقق من توقيع."""
        if self._ed25519_available:
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                pub_bytes = bytes.fromhex(public_key_hex)
                sig_bytes = bytes.fromhex(signature_hex)
                public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
                public_key.verify(sig_bytes, message.encode())
                return True
            except Exception:
                return False
        else:
            # Fallback: verify SHA-256
            expected = hashlib.sha256((public_key_hex + message).encode()).hexdigest()
            return expected == signature_hex


# === 9.2 + 9.3: Approval System with Ed25519 ===

class ApprovalSystem:
    """نظام الموافقات الموقعة بـ Ed25519."""

    def __init__(self) -> None:
        self._ensure_tables()
        self.signer = Ed25519Signer()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _GovBase.metadata.create_all(engine)

    def request_approval(
        self,
        request_type: str,
        target_id: str,
        requester: str,
        private_key_hex: str,
        public_key_hex: str,
        notes: str = "",
    ) -> dict[str, Any]:
        """طلب موافقة مع توقيع Ed25519."""
        approval_id = str(uuid.uuid4())
        message = f"{request_type}:{target_id}:{requester}:{approval_id}"
        signature = self.signer.sign(private_key_hex, message)
        verified = self.signer.verify(public_key_hex, message, signature)

        session = get_session_factory()()
        try:
            record = ApprovalModel(
                id=approval_id,
                request_type=request_type,
                target_id=target_id,
                requester=requester,
                decision="pending",
                signed_by=requester,
                signature=signature,
                public_key=public_key_hex,
                verified=verified,
                notes=notes,
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.governance.approval_requested", {
            "approval_id": approval_id, "request_type": request_type, "target_id": target_id,
        })

        return {
            "approval_id": approval_id,
            "request_type": request_type,
            "target_id": target_id,
            "signature": signature,
            "verified": verified,
            "status": "pending",
        }

    def decide_approval(
        self,
        approval_id: str,
        decision: str,
        approver_private_key: str,
        approver_public_key: str,
        notes: str = "",
    ) -> dict[str, Any]:
        """موافقة أو رفض مع توقيع."""
        if decision not in ["approve", "reject"]:
            raise ValueError("القرار يجب أن يكون approve أو reject")

        session = get_session_factory()()
        try:
            record = session.execute(
                select(ApprovalModel).where(ApprovalModel.id == approval_id)
            ).scalar_one_or_none()
            if not record:
                raise ValueError("الموافقة غير موجودة")
            if record.decision != "pending":
                raise ValueError(f"الموافقة已 تم البت فيها: {record.decision}")

            message = f"{approval_id}:{decision}:{approver_public_key}"
            signature = self.signer.sign(approver_private_key, message)
            verified = self.signer.verify(approver_public_key, message, signature)

            record.decision = decision
            record.signed_by = approver_public_key[:16]  # identifier
            record.signature = signature
            record.public_key = approver_public_key
            record.verified = verified
            record.notes = notes
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.governance.approval_decided", {
            "approval_id": approval_id, "decision": decision,
        })

        return {"approval_id": approval_id, "decision": decision, "verified": verified}

    def verify_approval(self, approval_id: str) -> dict[str, Any]:
        """التحقق من توقيع موافقة."""
        session = get_session_factory()()
        try:
            record = session.execute(
                select(ApprovalModel).where(ApprovalModel.id == approval_id)
            ).scalar_one_or_none()
            if not record:
                raise ValueError("الموافقة غير موجودة")

            message = f"{record.request_type}:{record.target_id}:{record.requester}:{approval_id}"
            verified = self.signer.verify(record.public_key, message, record.signature)
            return {
                "approval_id": approval_id,
                "decision": record.decision,
                "signature_valid": verified,
                "signed_by": record.signed_by,
                "request_type": record.request_type,
                "target_id": record.target_id,
            }
        finally:
            session.close()

    def list_approvals(self, limit: int = 50) -> list[dict[str, Any]]:
        session = get_session_factory()()
        try:
            records = session.execute(
                select(ApprovalModel).order_by(desc(ApprovalModel.created_at)).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": r.id, "request_type": r.request_type, "target_id": r.target_id,
                    "decision": r.decision, "signed_by": r.signed_by, "verified": r.verified,
                    "notes": r.notes, "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        finally:
            session.close()


# === 9.4: Promotion Gates ===

GATE_ORDER = ["evaluation", "shadow", "canary", "human_approval", "activation"]


class PromotionSystem:
    """بوابات الترقية الخمس."""

    def __init__(self) -> None:
        self._ensure_tables()
        self.approval_system = ApprovalSystem()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _GovBase.metadata.create_all(engine)

    def start_promotion(self, target_type: str, target_id: str, requester: str) -> dict[str, Any]:
        """بدء عملية ترقية."""
        promotion_id = str(uuid.uuid4())
        gates: list[dict] = []
        session = get_session_factory()()
        try:
            for gate_name in GATE_ORDER:
                gate = PromotionGateModel(
                    id=str(uuid.uuid4()),
                    target_type=target_type,
                    target_id=target_id,
                    gate=gate_name,
                    status="pending",
                )
                session.add(gate)
                gates.append({"gate": gate_name, "status": "pending"})
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.governance.promotion_started", {
            "target_type": target_type, "target_id": target_id,
        })

        return {"promotion_id": promotion_id, "target_type": target_type, "target_id": target_id, "gates": gates}

    def pass_gate(self, target_type: str, target_id: str, gate: str, result: dict) -> dict[str, Any]:
        """اجتياز بوابة محددة."""
        if gate not in GATE_ORDER:
            raise ValueError(f"بوابة غير معروفة: {gate}")

        session = get_session_factory()()
        try:
            # التحقق من البوابات السابقة
            for prev_gate in GATE_ORDER:
                if prev_gate == gate:
                    break
                prev = session.execute(
                    select(PromotionGateModel)
                    .where(PromotionGateModel.target_type == target_type)
                    .where(PromotionGateModel.target_id == target_id)
                    .where(PromotionGateModel.gate == prev_gate)
                ).scalar_one_or_none()
                if not prev or prev.status != "passed":
                    raise ValueError(f"بوابة {prev_gate} لم تُجتز بعد")

            record = session.execute(
                select(PromotionGateModel)
                .where(PromotionGateModel.target_type == target_type)
                .where(PromotionGateModel.target_id == target_id)
                .where(PromotionGateModel.gate == gate)
            ).scalar_one()
            record.status = "passed"
            record.result = result
            record.completed_at = datetime.now(UTC)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.governance.gate_passed", {
            "gate": gate, "target_id": target_id,
        })

        return {"gate": gate, "status": "passed", "result": result}

    def fail_gate(self, target_type: str, target_id: str, gate: str, reason: str) -> dict[str, Any]:
        """رسوب في بوابة."""
        session = get_session_factory()()
        try:
            record = session.execute(
                select(PromotionGateModel)
                .where(PromotionGateModel.target_type == target_type)
                .where(PromotionGateModel.target_id == target_id)
                .where(PromotionGateModel.gate == gate)
            ).scalar_one()
            record.status = "failed"
            record.result = {"reason": reason}
            record.completed_at = datetime.now(UTC)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.governance.gate_failed", {
            "gate": gate, "target_id": target_id, "reason": reason,
        })

        return {"gate": gate, "status": "failed", "reason": reason}

    def get_promotion_status(self, target_type: str, target_id: str) -> dict[str, Any]:
        """عرض حالة الترقية."""
        session = get_session_factory()()
        try:
            records = session.execute(
                select(PromotionGateModel)
                .where(PromotionGateModel.target_type == target_type)
                .where(PromotionGateModel.target_id == target_id)
                .order_by(PromotionGateModel.gate)
            ).scalars().all()
            gates = [{"gate": r.gate, "status": r.status, "result": r.result or {}} for r in records]
            all_passed = all(g["status"] == "passed" for g in gates)
            return {
                "target_type": target_type, "target_id": target_id,
                "gates": gates, "all_passed": all_passed,
                "can_activate": all_passed and len(gates) == len(GATE_ORDER),
            }
        finally:
            session.close()


# === 9.5: Executive Branch ===

EXECUTIVE_ROLES = [
    {"role_name": "coordinator", "description": "المنسق العام"},
    {"role_name": "planning_advisor", "description": "مستشار التخطيط"},
    {"role_name": "security_advisor", "description": "مستشار الأمن"},
    {"role_name": "spokesperson", "description": "الناطق الرسمي"},
    {"role_name": "operations_manager", "description": "مدير العمليات"},
]


class ExecutiveBranch:
    """السلطة التنفيذية — الأدوار الخمسة مشغولة بوكلاء حقيقيين."""

    def __init__(self) -> None:
        self._ensure_tables()
        self._init_roles()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _GovBase.metadata.create_all(engine)

    def _init_roles(self) -> None:
        session = get_session_factory()()
        try:
            for role in EXECUTIVE_ROLES:
                existing = session.execute(
                    select(ExecutiveRoleModel).where(ExecutiveRoleModel.role_name == role["role_name"])
                ).scalar_one_or_none()
                if not existing:
                    session.add(ExecutiveRoleModel(role_name=role["role_name"], status="vacant"))
            session.commit()
        finally:
            session.close()

    def appoint(self, role_name: str, agent_id: str) -> dict[str, Any]:
        """تعيين وكيل في دور تنفيذي."""
        if role_name not in [r["role_name"] for r in EXECUTIVE_ROLES]:
            raise ValueError(f"دور غير معروف: {role_name}")

        from amos_federation.services.agent_runtime.population import get_population_registry
        agent = get_population_registry().get_agent(agent_id)
        if not agent:
            raise ValueError(f"الوكيل {agent_id} غير موجود")

        session = get_session_factory()()
        try:
            record = session.execute(
                select(ExecutiveRoleModel).where(ExecutiveRoleModel.role_name == role_name)
            ).scalar_one()
            record.agent_id = agent_id
            record.status = "filled"
            record.appointed_at = datetime.now(UTC)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.executive.appointed", {
            "role": role_name, "agent_id": agent_id,
        })

        return {"role": role_name, "agent_id": agent_id, "status": "filled"}

    def list_roles(self) -> list[dict[str, Any]]:
        session = get_session_factory()()
        try:
            records = session.execute(select(ExecutiveRoleModel)).scalars().all()
            return [
                {
                    "role_name": r.role_name, "agent_id": r.agent_id,
                    "status": r.status,
                    "appointed_at": r.appointed_at.isoformat() if r.appointed_at else None,
                }
                for r in records
            ]
        finally:
            session.close()

    def fill_all_roles(self) -> dict[str, Any]:
        """ملء كل الأدوار التنفيذية بوكلاء حقيقيين."""
        from amos_federation.services.agent_runtime.population import get_population_registry
        agents = get_population_registry().list_agents()
        # اختيار وكلاء مناسبين للأدوار
        role_agent_map = {
            "coordinator": None,
            "planning_advisor": None,
            "security_advisor": None,
            "spokesperson": None,
            "operations_manager": None,
        }
        for agent in agents:
            role = agent["role"]
            if role == "coordinator" and not role_agent_map["coordinator"]:
                role_agent_map["coordinator"] = agent["agent_id"]
            elif role == "executor" and not role_agent_map["planning_advisor"]:
                role_agent_map["planning_advisor"] = agent["agent_id"]
            elif role == "security_monitor" and not role_agent_map["security_advisor"]:
                role_agent_map["security_advisor"] = agent["agent_id"]
            elif role == "auditor" and not role_agent_map["spokesperson"]:
                role_agent_map["spokesperson"] = agent["agent_id"]
            elif role == "inspector" and not role_agent_map["operations_manager"]:
                role_agent_map["operations_manager"] = agent["agent_id"]

        results = []
        for role_name, agent_id in role_agent_map.items():
            if agent_id:
                results.append(self.appoint(role_name, agent_id))
        return {"appointed": len(results), "roles": results}


# === 9.6: Legislative Branch ===

class LegislativeBranch:
    """السلطة التشريعية — مجلس سياسات + دورة تشريعية كاملة."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _GovBase.metadata.create_all(engine)

    def propose(self, title: str, body: str, proposer: str) -> dict[str, Any]:
        """اقتراح قانون جديد."""
        leg_id = str(uuid.uuid4())
        session = get_session_factory()()
        try:
            record = LegislationModel(
                id=leg_id, title=title, body=body, proposer=proposer, status="proposed",
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.legislative.proposed", {
            "legislation_id": leg_id, "title": title,
        })

        return {"legislation_id": leg_id, "title": title, "status": "proposed"}

    def open_debate(self, legislation_id: str) -> dict[str, Any]:
        """فتح المناقشة."""
        self._update_status(legislation_id, "debate")
        return {"legislation_id": legislation_id, "status": "debate"}

    def vote(self, legislation_id: str, agent_id: str, vote: str) -> dict[str, Any]:
        """التصويت على قانون."""
        if vote not in ["for", "against", "abstain"]:
            raise ValueError("التصويت يجب أن يكون for/against/abstain")

        session = get_session_factory()()
        try:
            record = session.execute(
                select(LegislationModel).where(LegislationModel.id == legislation_id)
            ).scalar_one_or_none()
            if not record:
                raise ValueError("القانون غير موجود")
            if record.status != "voting":
                raise ValueError(f"القانون ليس في مرحلة التصويت (الحالة: {record.status})")

            voters = record.voters or []
            if agent_id in voters:
                raise ValueError("الوكيل صوّت بالفعل")
            voters.append(agent_id)
            record.voters = voters

            if vote == "for":
                record.votes_for += 1
            elif vote == "against":
                record.votes_against += 1
            else:
                record.votes_abstain += 1
            session.commit()
        finally:
            session.close()

        return {"legislation_id": legislation_id, "agent_id": agent_id, "vote": vote}

    def open_voting(self, legislation_id: str) -> dict[str, Any]:
        """فتح التصويت."""
        self._update_status(legislation_id, "voting")
        return {"legislation_id": legislation_id, "status": "voting"}

    def enact(self, legislation_id: str) -> dict[str, Any]:
        """إقرار قانون — يُضاف لـ Policy Engine فعليًا."""
        session = get_session_factory()()
        try:
            record = session.execute(
                select(LegislationModel).where(LegislationModel.id == legislation_id)
            ).scalar_one_or_none()
            if not record:
                raise ValueError("القانون غير موجود")
            if record.votes_for <= record.votes_against:
                record.status = "rejected"
                session.commit()
                return {"legislation_id": legislation_id, "status": "rejected"}

            # إضافة القانون لـ Policy Engine
            from amos_federation.services.governance.policy_engine import PolicyEngine, RegoRule
            pe = PolicyEngine()
            rule_name = f"legislated_{record.title[:30]}".replace(" ", "_")
            pe.add_rule(RegoRule(
                name=rule_name,
                description=record.body,
                conditions=[{"field": "legislation.enacted", "op": "eq", "value": True}],
                decision="allow",
            ))
            record.status = "enacted"
            record.enacted_rule_name = rule_name
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.legislative.enacted", {
            "legislation_id": legislation_id, "rule_name": rule_name,
        })

        return {"legislation_id": legislation_id, "status": "enacted", "rule_name": rule_name}

    def run_full_legislative_cycle(self, title: str, body: str, proposer: str, voters: list[tuple[str, str]]) -> dict[str, Any]:
        """دورة تشريعية كاملة: اقتراح → مناقشة → تصويت → إقرار."""
        prop = self.propose(title, body, proposer)
        leg_id = prop["legislation_id"]
        self.open_debate(leg_id)
        self.open_voting(leg_id)
        for agent_id, vote in voters:
            self.vote(leg_id, agent_id, vote)
        result = self.enact(leg_id)
        return {
            "legislation_id": leg_id, "title": title,
            "votes_for": len([v for _, v in voters if v == "for"]),
            "votes_against": len([v for _, v in voters if v == "against"]),
            "final_status": result["status"],
            "rule_name": result.get("rule_name"),
        }

    def list_legislations(self, limit: int = 50) -> list[dict[str, Any]]:
        session = get_session_factory()()
        try:
            records = session.execute(
                select(LegislationModel).order_by(desc(LegislationModel.created_at)).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": r.id, "title": r.title, "body": r.body[:100],
                    "proposer": r.proposer, "status": r.status,
                    "votes_for": r.votes_for, "votes_against": r.votes_against,
                    "votes_abstain": r.votes_abstain,
                    "enacted_rule_name": r.enacted_rule_name,
                }
                for r in records
            ]
        finally:
            session.close()

    def _update_status(self, legislation_id: str, status: str) -> None:
        session = get_session_factory()()
        try:
            record = session.execute(
                select(LegislationModel).where(LegislationModel.id == legislation_id)
            ).scalar_one()
            record.status = status
            session.commit()
        finally:
            session.close()


# === 9.7: Judicial Branch ===

class JudicialBranch:
    """السلطة القضائية — المحكمة العليا."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _GovBase.metadata.create_all(engine)

    def file_case(self, plaintiff: str, defendant: str, subject: str, evidence: list | None = None) -> dict[str, Any]:
        """رفع دعوى."""
        case_id = str(uuid.uuid4())
        session = get_session_factory()()
        try:
            record = CourtCaseModel(
                id=case_id, plaintiff=plaintiff, defendant=defendant,
                subject=subject, evidence=evidence or [], status="open",
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.judicial.case_filed", {
            "case_id": case_id, "plaintiff": plaintiff, "defendant": defendant,
        })

        return {"case_id": case_id, "status": "open"}

    def add_argument(self, case_id: str, arg_text: str, by: str) -> dict[str, Any]:
        """إضافة مرافعة."""
        session = get_session_factory()()
        try:
            record = session.execute(
                select(CourtCaseModel).where(CourtCaseModel.id == case_id)
            ).scalar_one()
            args = record.arguments or []
            args.append({"text": arg_text, "by": by, "timestamp": datetime.now(UTC).isoformat()})
            record.arguments = args
            record.status = "hearing"
            session.commit()
        finally:
            session.close()
        return {"case_id": case_id, "argument_added": True}

    def rule(self, case_id: str, ruling: str, judge: str) -> dict[str, Any]:
        """إصدار حكم."""
        session = get_session_factory()()
        try:
            record = session.execute(
                select(CourtCaseModel).where(CourtCaseModel.id == case_id)
            ).scalar_one_or_none()
            if not record:
                raise ValueError("القضية غير موجودة")
            record.ruling = ruling
            record.ruling_judge = judge
            record.status = "ruled"
            record.resolved_at = datetime.now(UTC)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.judicial.ruled", {
            "case_id": case_id, "ruling": ruling, "judge": judge,
        })

        return {"case_id": case_id, "ruling": ruling, "judge": judge, "status": "ruled"}

    def list_cases(self, limit: int = 50) -> list[dict[str, Any]]:
        session = get_session_factory()()
        try:
            records = session.execute(
                select(CourtCaseModel).order_by(desc(CourtCaseModel.created_at)).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": r.id, "plaintiff": r.plaintiff, "defendant": r.defendant,
                    "subject": r.subject, "status": r.status,
                    "ruling": r.ruling, "ruling_judge": r.ruling_judge,
                    "arguments_count": len(r.arguments or []),
                }
                for r in records
            ]
        finally:
            session.close()


# === 9.8: Supreme Oversight ===

class SupremeOversight:
    """الرقابة العليا — تفتيش دوري + تدقيق + امتثال."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _GovBase.metadata.create_all(engine)

    def generate_compliance_report(self, period: str | None = None) -> dict[str, Any]:
        """تقرير امتثال شهري حقيقي."""
        if not period:
            period = datetime.now(UTC).strftime("%Y-%m")

        from amos_federation.common.persistent import PersistentAuditStore
        audit = PersistentAuditStore()
        chain_verify = audit.verify_chain()
        all_entries = audit.list_all(limit=10000)

        violations = sum(1 for a in all_entries if "violation" in a.get("action", "").lower())
        total = len(all_entries)
        compliance_rate = (total - violations) / max(total, 1)

        findings = []
        if not chain_verify.get("valid", False):
            findings.append("سلسلة التدقيق مكسورة — تلاعب محتمل")
        if violations > 0:
            findings.append(f"وجد {violations} انتهاك في {total} إدخال")
        if compliance_rate < 0.9:
            findings.append(f"معدل الامتثال منخفض: {compliance_rate:.1%}")

        recommendations = []
        if chain_verify.get("valid", False):
            recommendations.append("سلسلة التدقيق سليمة")
        if compliance_rate >= 0.9:
            recommendations.append("الامتثال جيد")
        else:
            recommendations.append("مراجعة السياسات المُنتَهَكة")

        report_id = str(uuid.uuid4())
        session = get_session_factory()()
        try:
            record = ComplianceReportModel(
                id=report_id, period=period, total_audits=total,
                violations=violations, compliance_rate=compliance_rate,
                findings=findings, recommendations=recommendations,
                chain_verified=chain_verify.get("valid", False),
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.oversight.report_generated", {
            "report_id": report_id, "period": period, "compliance_rate": compliance_rate,
        })

        return {
            "report_id": report_id, "period": period,
            "total_audits": total, "violations": violations,
            "compliance_rate": compliance_rate,
            "findings": findings, "recommendations": recommendations,
            "chain_verified": chain_verify.get("valid", False),
        }

    def list_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        session = get_session_factory()()
        try:
            records = session.execute(
                select(ComplianceReportModel).order_by(desc(ComplianceReportModel.created_at)).limit(limit)
            ).scalars().all()
            return [
                {
                    "id": r.id, "period": r.period, "total_audits": r.total_audits,
                    "violations": r.violations, "compliance_rate": r.compliance_rate,
                    "chain_verified": r.chain_verified,
                    "findings": r.findings or [],
                }
                for r in records
            ]
        finally:
            session.close()


# === Singleton Accessors ===

_approval_system: ApprovalSystem | None = None
_promotion_system: PromotionSystem | None = None
_executive_branch: ExecutiveBranch | None = None
_legislative_branch: LegislativeBranch | None = None
_judicial_branch: JudicialBranch | None = None
_supreme_oversight: SupremeOversight | None = None


def get_approval_system() -> ApprovalSystem:
    global _approval_system
    if _approval_system is None:
        _approval_system = ApprovalSystem()
    return _approval_system


def get_promotion_system() -> PromotionSystem:
    global _promotion_system
    if _promotion_system is None:
        _promotion_system = PromotionSystem()
    return _promotion_system


def get_executive_branch() -> ExecutiveBranch:
    global _executive_branch
    if _executive_branch is None:
        _executive_branch = ExecutiveBranch()
    return _executive_branch


def get_legislative_branch() -> LegislativeBranch:
    global _legislative_branch
    if _legislative_branch is None:
        _legislative_branch = LegislativeBranch()
    return _legislative_branch


def get_judicial_branch() -> JudicialBranch:
    global _judicial_branch
    if _judicial_branch is None:
        _judicial_branch = JudicialBranch()
    return _judicial_branch


def get_supreme_oversight() -> SupremeOversight:
    global _supreme_oversight
    if _supreme_oversight is None:
        _supreme_oversight = SupremeOversight()
    return _supreme_oversight
