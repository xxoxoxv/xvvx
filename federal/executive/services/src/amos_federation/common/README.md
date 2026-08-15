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
