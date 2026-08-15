<!--
File:        tools/db_link.md
Purpose:     ربط مجال الأدوات والنماذج بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Tools — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال الأدوات بقاعدة بيانات Supabase.** يوثّق الجداول المرتبطة بمجال
> الأدوات، أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات مدمّرة — الربط للقراءة فقط.

## مرجع مشروع Supabase

| الخاصية | القيمة |
|---|---|
| Project Ref | `mqcfmwtdaymrmwvthqyw` |
| Project URL | https://mqcfmwtdaymrmwvthqyw.supabase.co |
| PostgreSQL Host | `db.mqcfmwtdaymrmwvthqyw.supabase.co:5432` |
| Database | `postgres` |
| المستخدم | `postgres` |
| متغيرات الاتصال | `.env.example` — `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_DB_HOST` |

> نهج الربط: للقراءة فقط عبر Supabase REST API / PostgreSQL. لا تُنفّذ هجرات مدمّرة.

## الجداول المرتبطة

### 1. `tools` — سجل الأدوات (10 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `name` | varchar | **UNIQUE** |
| `description` | text | |
| `category` | varchar | |
| `keywords` | json | |
| `endpoint` | varchar | |
| `permissions_required` | json | |
| `sandbox_required` | bool | |
| `tenant_id` | varchar | |
| `created_at` | timestamp | |

### 2. `tool_generation_queue` — طابور توليد الأدوات (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `request_id` | varchar | **UNIQUE** |
| `tool_name` | varchar | |
| `description` | text | |
| `requested_by` | varchar | |
| `tool_type` | varchar | |
| `permissions_required` | json | |
| `status` | varchar | |
| `generated_code` | text | |
| `created_at` | timestamp | |
| `completed_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- قائمة كل الأدوات
SELECT id, name, category, endpoint, sandbox_required, created_at
FROM tools
ORDER BY category, name;

-- عدد الأدوات حسب الفئة (category)
SELECT category, COUNT(*) AS count
FROM tools
GROUP BY category
ORDER BY count DESC;

-- طلبات التوليد المعلّقة (pending generation requests)
SELECT request_id, tool_name, tool_type, status, requested_by, created_at
FROM tool_generation_queue
WHERE status = 'pending'
ORDER BY created_at;

-- بحث بالكلمات المفتاحية داخل keywords (json)
SELECT name, category, keywords
FROM tools
WHERE keywords @> '["search"]'::jsonb;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- جدولا الأدوات الفرعيان (النماذج) موثّقان في `tools/models/db_link.md`.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
