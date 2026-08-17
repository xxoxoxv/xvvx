<!--
File:        federal/db_link.md
Purpose:     ربط مجال الحكومة المركزية والخزانة بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Federal — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال الحكومة المركزية (الخزانة الفدرالية) بقاعدة بيانات Supabase.**
> يوثّق جداول الخزانة، أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات مدمّرة —
> الربط للقراءة فقط. **جميع الجداول فارغة حاليًا.**

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

### 1. `treasury_transactions` — معاملات الخزانة (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `tx_type` | varchar | |
| `source` | varchar | |
| `agent_id` | varchar | |
| `amount` | float | |
| `description` | text | |
| `linked_event` | varchar | |
| `linked_ref` | varchar | |
| `prev_hash` | varchar | |
| `hash` | varchar | |
| `created_at` | timestamp | |

### 2. `treasury_budgets` — ميزانيات الخزانة (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `holder_type` | varchar | |
| `holder_id` | varchar | |
| `allocated` | float | |
| `spent` | float | |
| `period` | varchar | |
| `created_at` | timestamp | |

### 3. `treasury_reports` — تقارير الخزانة الدورية (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | varchar | **PK** |
| `period` | varchar | |
| `report_type` | varchar | |
| `total_income` | float | |
| `total_expense` | float | |
| `net_balance` | float | |
| `transactions_count` | int | |
| `breakdown` | json | |
| `chain_verified` | bool | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- المعاملات حسب النوع (transactions by type)
SELECT tx_type, COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total_amount
FROM treasury_transactions
GROUP BY tx_type
ORDER BY total_amount DESC;

-- استغلال الميزانية (budget utilization)
SELECT
  holder_type,
  holder_id,
  allocated,
  spent,
  ROUND(100.0 * COALESCE(spent, 0) / NULLIF(allocated, 0), 2) AS utilization_pct,
  period
FROM treasury_budgets
ORDER BY utilization_pct DESC NULLS LAST;

-- تقارير فترة معينة (period reports)
SELECT period, report_type, total_income, total_expense, net_balance,
       transactions_count, chain_verified, created_at
FROM treasury_reports
ORDER BY period DESC;

-- التحقق من سلسلة المعاملات (hash chain)
SELECT
  id,
  tx_type,
  amount,
  prev_hash,
  hash,
  created_at,
  (prev_hash = LAG(hash) OVER (ORDER BY created_at)) AS chain_ok
FROM treasury_transactions
ORDER BY created_at;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- **جميع الجداول فارغة حاليًا** (0 صفوف)؛ الاستعلامات صحيحة لكنها ستعيد نتائج فارغة حتى يبدأ التشغيل.
- تستخدم المعاملات Hash Chain (ADR-010) وترتبط بالأحداث عبر `linked_event`/`linked_ref`.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
