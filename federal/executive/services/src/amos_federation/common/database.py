"""
AMOS-Federation Database Manager
الهدف: إدارة اتصال PostgreSQL والمزامنات
النطاق: كل الخدمات التي تستخدم قاعدة البيانات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""
import uuid
from contextlib import contextmanager
from typing import Any

try:
    import psycopg2
    import psycopg2.extras
    from sqlalchemy import create_engine
    from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False
    psycopg2 = None

from amos_federation.common.config import settings


if _DB_AVAILABLE:
    class Base(DeclarativeBase):
        """القاعدة لكل نماذج SQLAlchemy"""
        pass
else:
    class Base:
        """Placeholder when SQLAlchemy not available."""
        pass


if _DB_AVAILABLE:
    engine = create_engine(settings.postgres_dsn, pool_pre_ping=True, pool_size=10)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
else:
    engine = None
    SessionLocal = None


def get_db() -> Session:
    """Dependency لـ FastAPI — يُرجع جلسة قاعدة بيانات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_cursor():
    """Context manager لاستعلامات raw SQL مع dict cursor"""
    conn = psycopg2.connect(settings.postgres_dsn)
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def generate_uuid() -> uuid.UUID:
    """توليد UUID عشوائي (gen_random_uuid معادلة)"""
    return uuid.uuid4()
