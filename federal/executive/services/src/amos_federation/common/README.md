# src/amos_federation/common/

## التعريف
المكتبة المشتركة لكل خدمات النظام.

## النطاق
- config.py: إعدادات موحدة (pydantic-settings)
- database.py: إدارة PostgreSQL (SQLAlchemy + psycopg2)
- events.py: ناشر أحداث NATS + Hash Chain للتدقيق
- logging.py: سجلات JSON موحدة (structlog)
- tracing.py: تتبع OpenTelemetry
- auth.py: إصدار والتحقق من JWT
- schemas.py: عقود Pydantic المشتركة
- service.py: مصنع تطبيقات FastAPI
- registry.py: سجل الخدمات الموحد
- event_schemas.py: تحقق مخططات الأحداث

## المالك
federal/executive/services
## تاريخ الإنشاء
2026-08-15

## تاريخ آخر تعديل
2026-08-15

## المحتويات
- `README.md` — بطاقة هوية هذا المجلد (المادة التاسعة)
- `__init__.py` — AMOS-Federation Common Library
- `auth.py` — AMOS-Federation Authentication
- `config.py` — AMOS-Federation Configuration
- `database.py` — AMOS-Federation Database Layer
- `durable_event_bus.py` — AMOS-Federation Durable Event Bus — Phase 2
- `event_bus.py` — AMOS-Federation Event Bus
- `event_schemas.py` — AMOS-Federation Event Schema Validation
- `event_wiring.py` — AMOS-Federation Event Wiring — Phase 2
- `events.py` — AMOS-Federation Event Publisher + Hash Chain
- `logging.py` — AMOS-Federation Structured Logging
- `persistent.py` — AMOS-Federation Persistent Stores
- `registry.py` — AMOS-Federation Service Registry
- `schemas.py` — AMOS-Federation Shared Schemas
- `service.py` — AMOS-Federation Service Application Factory
- `tracing.py` — AMOS-Federation OpenTelemetry Tracing
