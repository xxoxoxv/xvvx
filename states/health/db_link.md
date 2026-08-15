<!--
File:        states/health/db_link.md
Purpose:     ربط ولاية الصحة بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# States / Health — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط ولاية الصحة (الفحوصات والعلاجات) بقاعدة بيانات Supabase.**
> يوثّق جدولَي فحوصات الوكلاء وعلاجاتهم، أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي
> هجرات مدمّرة — الربط للقراءة فقط. **جميع الجداول فارغة حاليًا.**

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

### 1. `agent_health_checks` — فحوصات صحة الوكلاء (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `agent_id` | varchar | |
| `check_date` | timestamp | |
| `status` | varchar | |
| `performance_score` | float | |
| `resource_usage` | json | |
| `policy_compliance` | float | |
| `tool_success_rate` | float | |
| `error_rate` | float | |
| `findings` | json | |
| `recommendations` | json | |
| `prev_hash` | varchar | |
| `hash` | varchar | |
| `created_at` | timestamp | |

### 2. `agent_treatments` — علاجات الوكلاء (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `agent_id` | varchar | |
| `treatment_type` | varchar | |
| `started_at` | timestamp | |
| `completed_at` | timestamp | |
| `status` | varchar | |
| `details` | json | |
| `result` | json | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- أحدث فحص لكل وكيل (latest health check)
SELECT DISTINCT ON (agent_id)
  agent_id, check_date, status, performance_score, policy_compliance,
  tool_success_rate, error_rate
FROM agent_health_checks
ORDER BY agent_id, check_date DESC;

-- العلاجات حسب الحالة (treatments by status)
SELECT status, COUNT(*) AS count
FROM agent_treatments
GROUP BY status
ORDER BY count DESC;

-- سجل صحة وكيل (agent health history)
SELECT agent_id, check_date, status, performance_score, error_rate, findings
FROM agent_health_checks
WHERE agent_id = :agent_id
ORDER BY check_date DESC;

-- الوكلاء ذوو الأداء المنخفض
SELECT agent_id, MAX(check_date) AS last_check,
       AVG(performance_score) AS avg_perf, AVG(error_rate) AS avg_error
FROM agent_health_checks
GROUP BY agent_id
HAVING AVG(performance_score) < 0.6
ORDER BY avg_perf ASC;

-- التحقق من سلسلة الفحوصات (hash chain)
SELECT
  id, agent_id, check_date, prev_hash, hash,
  (prev_hash = LAG(hash) OVER (PARTITION BY agent_id ORDER BY check_date)) AS chain_ok
FROM agent_health_checks
ORDER BY agent_id, check_date;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- **جميع الجداول فارغة حاليًا** (0 صفوف)؛ الاستعلامات صحيحة لكنها ستعي نتائج فارغة حتى يبدأ الفحص.
- `agent_health_checks` يستخدم Hash Chain (ADR-010) متسلسلًا لكل وكيل على حدة.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
