<!--
File:        tools/models/db_link.md
Purpose:     ربط مجال النماذج والتخزين المؤقت بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Tools / Models — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال النماذج (تخزين مؤقت + سجل تكلفة الاستدعاء) بقاعدة بيانات Supabase.**
> يوثّق جدولَي ذاكرة النماذج وتكاليفها، أعمدتها، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي
> هجرات مدمّرة — الربط للقراءة فقط.

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

### 1. `model_cache` — التخزين المؤقت للاستجابات (2 صفان)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `cache_key` | varchar | |
| `prompt_hash` | varchar | |
| `model` | varchar | |
| `response` | text | |
| `tokens` | int | |
| `created_at` | timestamp | |

### 2. `model_cost_log` — سجل تكاليف الاستدعاء (2 صفان)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `invocation_id` | varchar | **UNIQUE** |
| `model` | varchar | |
| `tokens` | int | |
| `cost_usd` | varchar | |
| `latency_ms` | int | |
| `source` | varchar | |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- معدل إصابات الذاكرة المؤقتة (cache hit rate)
-- (عدد مرات إعادة استخدام نفس prompt_hash مقارنة بإجمالي الإدخالات)
SELECT
  COUNT(*) AS total_entries,
  COUNT(DISTINCT prompt_hash) AS unique_prompts,
  ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT prompt_hash))
        / NULLIF(COUNT(*), 0), 2) AS reuse_pct
FROM model_cache;

-- التكلفة الإجمالية (total cost)
SELECT
  COUNT(*) AS invocations,
  SUM(tokens) AS total_tokens,
  ROUND(SUM(CAST(cost_usd AS NUMERIC)), 4) AS total_cost_usd,
  AVG(latency_ms) AS avg_latency_ms
FROM model_cost_log;

-- التكلفة والاستخدام حسب النموذج (by model)
SELECT
  m.model,
  COUNT(m.id) AS cache_entries,
  SUM(m.tokens) AS cache_tokens,
  (SELECT COUNT(*) FROM model_cost_log c WHERE c.model = m.model) AS cost_entries,
  (SELECT ROUND(SUM(CAST(cost_usd AS NUMERIC)), 4)
     FROM model_cost_log c WHERE c.model = m.model) AS total_cost_usd
FROM model_cache m
GROUP BY m.model
ORDER BY total_cost_usd DESC NULLS LAST;

-- أبطأ الاستدعاءات
SELECT invocation_id, model, tokens, cost_usd, latency_ms, source, created_at
FROM model_cost_log
ORDER BY latency_ms DESC
LIMIT 20;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- `cost_usd` مخزّن كنص (`varchar`) — يُحوَّل إلى `NUMERIC` عند الحاجة للتجميع.
- `cache_key` و `prompt_hash` يُستخدمان لتحديد تطابق الاستدعاءات.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
