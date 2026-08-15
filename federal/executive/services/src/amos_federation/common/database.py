"""
AMOS-Federation Database Manager
الهدف: إدارة اتصال PostgreSQL والمزامنات
النطاق: كل الخدمات التي تستخدم قاعدة البيانات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Any

from amos_federation.common.config import settings

try:
    import psycopg2
    import psycopg2.extras
    from sqlalchemy import create_engine
    from sqlalchemy.orm import DeclarativeBase, sessionmaker
except ImportError:
    _DB_AVAILABLE = False
    psycopg2 = None
else:
    _DB_AVAILABLE = True


if _DB_AVAILABLE:

    class Base(DeclarativeBase):
        """القاعدة لكل نماذج SQLAlchemy."""

else:

    class Base:
        """بديل خفيف حين لا تتوفر حزم قاعدة البيانات."""


if _DB_AVAILABLE:
    engine = create_engine(settings.postgres_dsn, pool_pre_ping=True, pool_size=10)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
else:
    engine = None
    SessionLocal = None


def get_db() -> Generator[Any, None, None]:
    """اعتماد FastAPI يولد جلسة قاعدة بيانات عندما تتوفر الحزمة والإعدادات."""
    if SessionLocal is None:
        raise RuntimeError("PostgreSQL/SQLAlchemy غير متاحين في هذه البيئة")
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()


@contextmanager
def db_cursor() -> Iterator[Any]:
    """مدير سياق لاستعلامات SQL الخام باستخدام قاموس صفوف."""
    if psycopg2 is None:
        raise RuntimeError("psycopg2 غير متاح في هذه البيئة")
    connection = psycopg2.connect(settings.postgres_dsn)
    try:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def generate_uuid() -> uuid.UUID:
    """توليد UUID عشوائي بمعادل gen_random_uuid."""
    return uuid.uuid4()
