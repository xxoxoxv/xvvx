<!--
File:        royal/security/db_link.md
Purpose:     ربط الأمن الملكي (العزل) بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Royal / Security — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط الأمن الملكي (عزل الوكلاء) بقاعدة بيانات Supabase.**
> يوثّق جدول العزل، أعمدته، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات مدمّرة —
> الربط للقراءة فقط. **الجدول فارغ حاليًا.**

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

### 1. `agent_isolations` — عزل الوكلاء (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `agent_id` | varchar | |
| `isolated_at` | timestamp | |
| `reason` | text | |
| `sandbox_id` | varchar | |
| `actions_log` | json | |
| `status` | varchar | |
| `released_at` | timestamp | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- العزلات النشطة (active isolations)
SELECT id, agent_id, isolated_at, reason, sandbox_id, status, created_at
FROM agent_isolations
WHERE status = 'active' OR (status IS NULL AND released_at IS NULL)
ORDER BY isolated_at DESC;

-- سجل عزل وكيل (isolation history by agent)
SELECT agent_id, isolated_at, reason, sandbox_id, status, released_at, actions_log
FROM agent_isolations
WHERE agent_id = :agent_id
ORDER BY isolated_at DESC;

-- الوكلاء المعزولون حاليًا
SELECT DISTINCT agent_id
FROM agent_isolations
WHERE released_at IS NULL
ORDER BY agent_id;

-- مدة العزل لكل حالة مُفرَج عنها
SELECT
  id, agent_id, reason,
  isolated_at, released_at,
  EXTRACT(EPOCH FROM (released_at - isolated_at))/3600 AS isolation_hours
FROM agent_isolations
WHERE released_at IS NOT NULL
ORDER BY isolation_hours DESC NULLS LAST;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- **الجدول فارغ حاليًا** (0 صفوف)؛ الاستعلامات صحيحة لكنها ستعي نتائج فارغة حتى يُسجَّل أول عزل.
- `sandbox_id` يربط العزل ببيئة عزل فيزيائية (وفق ADR-009: العزل الفيزيائي لطبقة الحوكمة).
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
