<!--
File:        runtime/db_link.md
Purpose:     ربط مجال محرك التشغيل بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Runtime — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال محرك التشغيل بقاعدة بيانات Supabase.** يوثّق المهام ومخزن الأحداث،
> أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات مدمّرة — الربط للقراءة فقط.

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

### 1. `tasks` — المهام (1 صف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `type` | varchar | |
| `description` | text | |
| `status` | varchar | |
| `assigned_agent` | varchar | |
| `plan` | json | |
| `result` | json | |
| `tenant_id` | varchar | |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |
| `priority` | varchar | DEFAULT `'normal'` |
| `domain` | varchar | DEFAULT `'general'` |

### 2. `event_store` — مخزن الأحداث (157 صفًا)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `event_id` | varchar | **UNIQUE** |
| `subject` | varchar | |
| `data` | text | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- المهام حسب الحالة (tasks by status)
SELECT status, COUNT(*) AS count
FROM tasks
GROUP BY status
ORDER BY count DESC;

-- تفاصيل المهام حسب الأولوية والمجال
SELECT id, type, status, assigned_agent, priority, domain, created_at
FROM tasks
ORDER BY priority DESC, created_at;

-- الأحداث حسب الموضوع (events by subject)
SELECT subject, COUNT(*) AS count
FROM event_store
GROUP BY subject
ORDER BY count DESC;

-- أحدث الأحداث (recent events)
SELECT event_id, subject, created_at
FROM event_store
ORDER BY created_at DESC
LIMIT 50;

-- ربط الحدث بمهمة عبر data (إذا احتوى على task_id)
SELECT event_id, subject, data, created_at
FROM event_store
WHERE data ILIKE '%task_id%';
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- `event_store.event_id` فريد ويمثّل معرّف الحدث المنطقي؛ `id` تسلسلي داخلي.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
