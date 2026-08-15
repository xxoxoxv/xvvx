"""
AMOS-Federation Event Bus
الهدف: نظام أحداث حقيقي مع تخزين دائم واشتراكات
النطاق: common/event_bus
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any, Callable

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from amos_federation.common.database import get_database_url


class EventBase(DeclarativeBase):
    pass


class EventModel(EventBase):
    """جدول الأحداث المنشورة."""
    __tablename__ = "event_store"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, unique=True)
    subject = Column(String, nullable=False, index=True)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class EventBus:
    """ناقل أحداث حقيقي مع تخزين دائم واشتراكات."""

    def __init__(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        if url.startswith("postgresql"):
            connect_args = {"sslmode": "require", "connect_timeout": 15}
        self._engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True, pool_size=5, max_overflow=10)
        EventBase.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def subscribe(self, subject: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """اشتراك معالج لـ subject معين."""
        if subject not in self._handlers:
            self._handlers[subject] = []
        self._handlers[subject].append(handler)

    def publish(self, subject: str, data: dict[str, Any]) -> dict[str, Any]:
        """نشر حدث وتخزينه واستدعاء المعالجات."""
        event_id = f"evt-{uuid.uuid4()}"
        event = {
            "event_id": event_id,
            "subject": subject,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # تخزين دائم
        session = self._Session()
        try:
            row = EventModel(
                event_id=event_id,
                subject=subject,
                data=json.dumps(data, ensure_ascii=False),
            )
            session.add(row)
            session.commit()
        finally:
            session.close()

        # استدعاء المعالجات المسجّلة
        handlers = self._handlers.get(subject, [])
        # أيضًا فحص wildcards (amos_federation.*)
        for pattern, pattern_handlers in self._handlers.items():
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if subject.startswith(prefix + "."):
                    handlers = handlers + pattern_handlers

        for handler in handlers:
            try:
                handler(data)
            except Exception:
                pass  # لا نوقف النشر بسبب فشل معالج

        return event

    def get_events(self, subject: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """استرجاع الأحداث المخزَّنة."""
        session = self._Session()
        try:
            q = session.query(EventModel)
            if subject:
                q = q.filter(EventModel.subject == subject)
            rows = q.order_by(EventModel.id.desc()).limit(limit).all()
            return [
                {
                    "event_id": r.event_id,
                    "subject": r.subject,
                    "data": json.loads(r.data),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        finally:
            session.close()

    def count(self, subject: str | None = None) -> int:
        """عدد الأحداث."""
        session = self._Session()
        try:
            q = session.query(EventModel)
            if subject:
                q = q.filter(EventModel.subject == subject)
            return q.count()
        finally:
            session.close()


# Singleton
_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """الحصول على ناقل الأحداث (Singleton)."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


# === عقود الأحداث (Event Contracts) ===

EVENT_CONTRACTS = {
    "amos_federation.task.created": {
        "required_fields": ["task_id", "type", "description"],
        "optional_fields": ["tenant_id", "priority"],
    },
    "amos_federation.task.planned": {
        "required_fields": ["task_id", "plan"],
        "optional_fields": ["agent_id"],
    },
    "amos_federation.agent.assigned": {
        "required_fields": ["task_id", "agent_id"],
        "optional_fields": ["plan"],
    },
    "amos_federation.agent.started": {
        "required_fields": ["agent_id", "task_id"],
        "optional_fields": [],
    },
    "amos_federation.tool.executed": {
        "required_fields": ["tool_id", "agent_id", "result"],
        "optional_fields": ["task_id"],
    },
    "amos_federation.agent.completed": {
        "required_fields": ["agent_id", "task_id", "result"],
        "optional_fields": ["quality_score"],
    },
    "amos_federation.experience.recorded": {
        "required_fields": ["experience_id", "type"],
        "optional_fields": ["agent_id", "task_id", "quality_score"],
    },
    "amos_federation.memory.stored": {
        "required_fields": ["key"],
        "optional_fields": ["value", "keywords"],
    },
    "amos_federation.model.invoked": {
        "required_fields": ["model", "tokens_used"],
        "optional_fields": ["cost_usd", "latency_ms"],
    },
    "amos_federation.critic.reviewed": {
        "required_fields": ["review_id", "quality_score"],
        "optional_fields": ["task_id", "agent_id", "approved"],
    },
    "amos_federation.approval.signed": {
        "required_fields": ["approval_id", "decision"],
        "optional_fields": ["model_id", "signed_by"],
    },
    "amos_federation.policy.checked": {
        "required_fields": ["policy_name", "allowed"],
        "optional_fields": ["violations"],
    },
}


def validate_event(subject: str, data: dict[str, Any]) -> tuple[bool, str]:
    """التحقق من مطابقة الحدث لعقدة."""
    contract = EVENT_CONTRACTS.get(subject)
    if contract is None:
        return False, f"لا يوجد عقد للحدث '{subject}'"
    for field in contract["required_fields"]:
        if field not in data:
            return False, f"الحقل المطلوب '{field}' مفقود في حدث '{subject}'"
    return True, "صالح"
