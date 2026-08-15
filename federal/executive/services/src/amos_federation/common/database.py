"""
AMOS-Federation Database Layer
الهدف: طبقة تخزين دائمة بـ SQLAlchemy (SQLite للبيئة الحالية، PostgreSQL للإنتاج)
النطاق: common/database
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import contextlib
import os
import uuid
from collections.abc import Generator
from datetime import UTC, datetime

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
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """القاعدة لكل النماذج."""

    pass


# === النماذج ===


class AgentModel(Base):
    """جدول الوكلاء."""

    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default="registered")
    permissions = Column(JSON, default=list)
    allowed_tools = Column(JSON, default=list)
    token_budget = Column(Integer, default=10000)
    tenant_id = Column(String, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class ToolModel(Base):
    """جدول الأدوات."""

    __tablename__ = "tools"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, default="")
    category = Column(String, default="general")
    keywords = Column(JSON, default=list)
    endpoint = Column(String, default="")
    permissions_required = Column(JSON, default=list)
    sandbox_required = Column(Boolean, default=False)
    tenant_id = Column(String, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class TaskModel(Base):
    """جدول المهام."""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="created")
    priority = Column(String, default="normal")
    domain = Column(String, default="general")
    assigned_agent = Column(String, nullable=True)
    plan = Column(JSON, default=list)
    result = Column(JSON, default=dict)
    tenant_id = Column(String, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class MemoryModel(Base):
    """جدول الذاكرة التشغيلية."""

    __tablename__ = "memories"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)
    tenant_id = Column(String, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ExperienceModel(Base):
    """جدول الخبرات."""

    __tablename__ = "experiences"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    task_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    outcome = Column(JSON, default=dict)
    quality_score = Column(Float, nullable=True)
    provenance = Column(JSON, default=dict)
    tenant_id = Column(String, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ReviewModel(Base):
    """جدول مراجعات الناقد."""

    __tablename__ = "reviews"

    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=True)
    quality_score = Column(Float, nullable=False)
    feedback = Column(Text, default="")
    approved = Column(Boolean, default=False)
    criteria = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class AuditEntryModel(Base):
    """جدول سجل التدقيق."""

    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    details = Column(JSON, default=dict)
    prev_hash = Column(String, nullable=False, default="0" * 64)
    hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# === إدارة الاتصال ===


def get_database_url() -> str:
    """الحصول على رابط قاعدة البيانات."""
    return os.environ.get(
        "AMOS_DATABASE_URL",
        f"sqlite:///{os.path.join(os.getcwd(), 'amos_federation.db')}",
    )


def _is_postgres() -> bool:
    return get_database_url().startswith("postgresql")


def _pg_connect_args() -> dict:
    """معاملات اتصال إضافية لـ PostgreSQL (Supabase يتطلب SSL)."""
    if not _is_postgres():
        return {"check_same_thread": False}
    return {
        "sslmode": "require",
        "connect_timeout": 15,
    }


_engine = None
_SessionLocal = None


def get_engine():
    """الحصول على محرك قاعدة البيانات (Singleton)."""
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        if url.startswith("postgresql"):
            connect_args = {"sslmode": "require", "connect_timeout": 15}
        _engine = create_engine(
            url,
            connect_args=connect_args,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def reset_engine() -> None:
    """إعادة تعيين المحرك — للاختبارات والتغيير بين SQLite و PostgreSQL."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_session_factory():
    """الحصول على مصنع الجلسات (Singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SessionLocal


def init_db() -> None:
    """إنشاء كل الجداول عند الإقلاع."""
    Base.metadata.create_all(get_engine())


def get_db() -> Generator[Session, None, None]:
    """Dependency للحصول على جلسة قاعدة بيانات."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def with_db(func):
    """Decorator لتوفير جلسة DB تلقائيًا."""

    def wrapper(*args, **kwargs):
        session = get_session_factory()()
        try:
            result = func(*args, session=session, **kwargs)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return wrapper


# === توافق عكسي مع الوحدات القديمة ===


def generate_uuid() -> uuid.UUID:
    """توليد معرّف فريد (توافق عكسي)."""
    return uuid.uuid4()


@contextlib.contextmanager
def db_cursor():
    """محرّك قاعدة البيانات للتوافق العكسي مع events.py."""
    import sqlite3

    db_url = get_database_url()
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            conn.close()
    else:
        # PostgreSQL path for production (Supabase)
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(db_url, sslmode="require", connect_timeout=15)
        try:
            yield conn.cursor(cursor_factory=RealDictCursor)
            conn.commit()
        finally:
            conn.close()
