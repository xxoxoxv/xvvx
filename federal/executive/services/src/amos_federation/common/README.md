# src/amos_federation/common/

## التعريف
المكتبة المشتركة لكل خدمات النظام.

## النطاق
- config.py: إعدادات موحدة (pydantic-settings)
- database.py: إدارة PostgreSQL (SQLAlchemy + psycopg2)
- events.py: ناشر أحداث NATS + Hash Chain للتدقيق
- logging.py: سجلات JSON موحدة (structlog)
- tracing.py: تتبع OpenTelemetry

## المالك
federal/executive/services
## تاريخ الإنشاء
2026-08-15
