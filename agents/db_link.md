<!--
File:        agents/db_link.md
Purpose:     ربط مجال الوكلاء بقاعدة بيانات Supabase — وثيقة الربط بين المستودع وقاعدة الحقيقة (P4)
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Agents — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط المجال بقاعدة بيانات Supabase.** يوثّق هذا الملف الجداول المرتبطة بمجال
> الوكلاء، أعمدتها، أنواعها، واستعلامات نموذجية تعمل فعليًا على الجداول. لا تُنفّذ أي هجرات
> مدمّرة (No destructive migrations) — الربط للقراءة فقط.

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

### 1. `agents` — الهويات الأساسية للوكلاء (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `name` | varchar | |
| `role` | varchar | |
| `status` | varchar | |
| `permissions` | json | |
| `allowed_tools` | json | |
| `token_budget` | int | |
| `tenant_id` | varchar | |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### 2. `agent_population` — السكان الكامل للوكلاء (342 صفًا)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `agent_id` | varchar | |
| `name` | varchar | |
| `role` | varchar | |
| `category` | varchar | |
| `state` | varchar | |
| `permissions` | text | |
| `allowed_tools` | text | |
| `token_budget` | int | |
| `tokens_used` | int | |
| `school_score` | numeric | |
| `specialization` | varchar | |
| `created_at` | timestamp | |
| `graduated_at` | timestamp | |

### 3. `school_results` — نتائج اختبارات المدرسة (6 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `agent_id` | varchar | |
| `step` | varchar | |
| `passed` | boolean | |
| `score` | int | |
| `notes` | text | |
| `taken_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- عدد الوكلاء حسب الحالة (state)
SELECT state, COUNT(*) AS count
FROM agent_population
GROUP BY state
ORDER BY count DESC;

-- قائمة الوكلاء حسب الفئة (category)
SELECT id, agent_id, name, role, category, specialization
FROM agent_population
WHERE category = :category
ORDER BY created_at;

-- معدل نجاح المدرسة (school pass rate)
SELECT
  COUNT(*)                                                       AS total_attempts,
  SUM(CASE WHEN passed THEN 1 ELSE 0 END)                         AS passed_count,
  ROUND(100.0 * SUM(CASE WHEN passed THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2)                                AS pass_rate_pct,
  AVG(score)                                                     AS avg_score
FROM school_results;

-- نتيجة كل وكيل في المدرسة
SELECT agent_id, step, passed, score, taken_at
FROM school_results
ORDER BY taken_at DESC;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- الجداول مرتبطة عبر `agent_id` و `agent_population.id`/`agent_population.agent_id`.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
