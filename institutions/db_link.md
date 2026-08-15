<!--
File:        institutions/db_link.md
Purpose:     ربط مجال المؤسسات بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Institutions — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال المؤسسات (بنوك، جامعات، محاكم، مصانع) بقاعدة بيانات Supabase.**
> يوثّق الجدول المرتبط بالمجال، أعمدته، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات
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

### 1. `institutions` — سجل المؤسسات (8 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `institution_id` | varchar | **UNIQUE** |
| `name` | varchar | |
| `type` | varchar | |
| `state` | varchar | |
| `status` | varchar | DEFAULT `'active'` |
| `head_agent_id` | varchar | |
| `budget` | int | DEFAULT `0` |
| `established_at` | timestamp | |
| `closed_at` | timestamp | |
| `metadata` | json | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- المؤسسات حسب النوع (by type)
SELECT type, COUNT(*) AS count
FROM institutions
GROUP BY type
ORDER BY count DESC;

-- المؤسسات حسب الولاية (by state)
SELECT state, COUNT(*) AS count
FROM institutions
GROUP BY state
ORDER BY count DESC;

-- المؤسسات النشطة (active institutions)
SELECT institution_id, name, type, state, head_agent_id, budget, established_at
FROM institutions
WHERE status = 'active'
ORDER BY type, established_at;

-- أكبر المؤسسات ميزانية
SELECT name, type, state, budget
FROM institutions
ORDER BY budget DESC NULLS LAST
LIMIT 10;

-- المؤسسات المغلقة
SELECT institution_id, name, type, established_at, closed_at
FROM institutions
WHERE status = 'closed' OR closed_at IS NOT NULL;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- `institution_id` هو المعرّف المنطقي الفريد؛ `id` تسلسلي داخلي.
- `head_agent_id` يربط المؤسسة بوكيل في جدول `agent_population`.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
