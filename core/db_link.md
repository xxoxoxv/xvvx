<!--
File:        core/db_link.md
Purpose:     ربط مجال الدستور والذاكرة بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Core — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال الدستور والذاكرة والخبرات بقاعدة بيانات Supabase.**
> يوثّق جدولَي الذاكرة والخبرات، أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات
> مدمّرة — الربط للقراءة فقط.

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

### 1. `memories` — ذاكرة الدولة (2 صفان)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `key` | varchar | **PK** |
| `value` | text | |
| `keywords` | json | |
| `tenant_id` | varchar | |
| `created_at` | timestamp | |

### 2. `experiences` — الخبرات المكتسبة (1 صف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `type` | varchar | |
| `task_id` | varchar | |
| `agent_id` | varchar | |
| `model_used` | varchar | |
| `outcome` | json | |
| `quality_score` | float | |
| `provenance` | json | |
| `tenant_id` | varchar | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- كل الذكريات (all memories)
SELECT key, value, keywords, tenant_id, created_at
FROM memories
ORDER BY created_at;

-- الذكريات حسب كلمة مفتاحية (json)
SELECT key, value, keywords
FROM memories
WHERE keywords @> '["governance"]'::jsonb;

-- الخبرات حسب النوع (experiences by type)
SELECT type, COUNT(*) AS count
FROM experiences
GROUP BY type
ORDER BY count DESC;

-- الخبرات عالية الجودة (high-quality experiences)
SELECT id, type, task_id, agent_id, model_used, quality_score, created_at
FROM experiences
WHERE quality_score >= 0.8
ORDER BY quality_score DESC;

-- مصدر الخبرات (provenance)
SELECT id, type, agent_id, model_used, provenance, created_at
FROM experiences
ORDER BY created_at DESC;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- `memories.key` هو المفتاح الأساسي (نصي) — يُستخدم كمفتاح منطقي للذاكرة.
- `experiences.task_id` يربط الخبرة بمهمة في جدول `tasks`؛ `agent_id` بـ `agent_population`.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
