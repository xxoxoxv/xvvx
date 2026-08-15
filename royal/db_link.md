<!--
File:        royal/db_link.md
Purpose:     ربط مجال الحوكمة الملكية بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Royal — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال الحوكمة الملكية (الأمن، المراسيم، التدقيق) بقاعدة بيانات Supabase.**
> يوثّق الجداول المرتبطة بالمجال، أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات
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

### 1. `royal_guards` — الحرس الملكي (7 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `guard_id` | varchar | **UNIQUE** |
| `codename` | varchar | |
| `cover_role` | varchar | |
| `cover_institution` | varchar | |
| `mission` | text | DEFAULT `'monitor'` |
| `loyalty_level` | int | DEFAULT `100` |
| `status` | varchar | DEFAULT `'active'` |
| `last_report` | timestamp | |
| `findings` | json | |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### 2. `king_decrees` — المراسيم الملكية (1 صف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `decree_id` | varchar | **UNIQUE** |
| `title` | varchar | |
| `decree_text` | text | |
| `decree_type` | varchar | DEFAULT `'royal'` |
| `affected_entity` | varchar | |
| `status` | varchar | DEFAULT `'enacted'` |
| `signed_by` | varchar | DEFAULT `'king'` |
| `enacted_at` | timestamp | |
| `metadata` | json | |

### 3. `audit_entries` — سجل التدقيق (10 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `action` | varchar | |
| `actor` | varchar | |
| `details` | json | |
| `prev_hash` | varchar | |
| `hash` | varchar | |
| `created_at` | timestamp | |

### 4. `reviews` — المراجعات (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `task_id` | varchar | |
| `agent_id` | varchar | |
| `quality_score` | float | |
| `feedback` | text | |
| `approved` | bool | |
| `criteria` | json | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- الحرس النشط (active guards)
SELECT guard_id, codename, cover_role, cover_institution, mission, loyalty_level, last_report
FROM royal_guards
WHERE status = 'active'
ORDER BY loyalty_level DESC, created_at;

-- أحدث المراسيم (recent decrees)
SELECT decree_id, title, decree_type, affected_entity, status, signed_by, enacted_at
FROM king_decrees
ORDER BY enacted_at DESC
LIMIT 20;

-- المراجعات حسب درجة الجودة
SELECT task_id, agent_id, quality_score, approved, created_at
FROM reviews
ORDER BY quality_score DESC NULLS LAST;

-- التحقق من سلسلة التدقيق (audit chain verification)
SELECT
  id,
  action,
  actor,
  prev_hash,
  hash,
  created_at,
  (prev_hash = LAG(hash) OVER (ORDER BY created_at)) AS chain_ok
FROM audit_entries
ORDER BY created_at;

-- عدد إجراءات التدقيق لكل فاعل
SELECT actor, COUNT(*) AS count
FROM audit_entries
GROUP BY actor
ORDER BY count DESC;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- `audit_entries` يستخدم Hash Chain (ADR-010): يجب أن يطابق `prev_hash` في صفٍ ما قيمة `hash`
  في الصف السابق حسب الترتيب الزمني للتحقق من سلامة السلسلة.
- جداول العزل الصحي موثّقة في `royal/security/db_link.md`.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
