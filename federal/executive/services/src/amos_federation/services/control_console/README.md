# Control Console Service

واجهة التحكم البشري — تعرض الوكلاء والمهام والنماذج والتكلفة والتدقيق.

## التعريف
خدمة واجهة التحكم البشري: تعرض الوكلاء والمهام والنماذج والتكلفة وأثر التدقيق،
وتتيح للمالك البشري إيقاف وكيل أو تفعيل زر التوقف الطارئ.

## النطاق
العرض والتحكّم البشري على المنفذ 3000. لا تحسب هذه الخدمة رقمًا بنفسها — كل رقم
تعرضه يأتي من خدمة أخرى؛ ولا تتجاوز بوابة السيادة في أي أمر تحكّم.

## المالك
federal/executive/services/

## تاريخ الإنشاء
2026-08-15

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

## تاريخ آخر تعديل
2026-08-15

## المحتويات
- `README.md` — بطاقة هوية هذا المجلد (المادة التاسعة)
- `__init__.py` — AMOS-Federation Control Console Service
- `main.py` — AMOS-Federation Control Console Service
