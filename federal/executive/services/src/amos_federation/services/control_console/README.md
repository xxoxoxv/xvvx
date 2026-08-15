# Control Console Service

واجهة التحكم البشري — تعرض الوكلاء والمهام والنماذج والتكلفة والتدقيق.

## المنفذ

3000

## الـ APIs

- `GET /v1/dashboard` — لوحة تحكم شاملة (كل الأرقام من خدمات حقيقية)
- `GET /v1/agents` — عرض كل الوكلاء
- `GET /v1/agents/{id}` — عرض وكيل واحد
- `POST /v1/agents/{id}/state` — إيقاف/تفعيل وكيل
- `GET /v1/audit` — سجل التدقيق
- `GET /v1/audit/verify` — التحقق من سلامة السلسلة
- `POST /v1/kill-switch` — تفعيل Kill Switch
- `POST /v1/kill-switch/reset` — إعادة ضبط Kill Switch
- `POST /v1/approval` — موافقة/رفض (يُكتمل في Phase 9)
- `GET /v1/cost` — التكلفة اللحظية والتراكمية
- `GET /v1/events` — الأحداث
- `GET /v1/ui` — واجهة HTML/JS
