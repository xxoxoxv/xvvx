# سجل الأدوات — Tools Registry

> الفهرس الرسمي لكل أدوات الدولة المعتمدة. مرتبط بجدول `tools` في Supabase.

## الهدف
الفهرس الرسمي لأدوات الدولة وصلاحية كل أداة ومتطلبات عزلها، فلا تُستخدم أداة غير مسجَّلة.

## نظرة عامة

| البيان | القيمة |
|---|---|
| إجمالي الأدوات | 10 |
| طابور توليد الأدوات | 0 |
| النماذج المخزنة مؤقتاً | 2 |
| إجمالي تكاليف النماذج | $0.00 |

## سجل الأدوات

| # | المعرف | الاسم | الصلاحيات | Sandbox | تاريخ الإنشاء |
|---:|---|---|---|---|---|
| 1 | `sql_query` | SQL Query Executor | data.read | false | 2026-08-15 |
| 2 | `python_execute` | Python Code Executor | code.execute | false | 2026-08-15 |
| 3 | `chart_generate` | Chart Generator | output.generate | false | 2026-08-15 |
| 4 | `document_analysis` | Document Analyzer | document.read | false | 2026-08-15 |
| 5 | `legal_search` | Legal Search Engine | search.execute | false | 2026-08-15 |
| 6 | `research_apis` | External Research APIs | external_api.call | false | 2026-08-15 |
| 7 | `data_analysis` | Statistical Data Analysis | data.read, code.execute | false | 2026-08-15 |
| 8 | `medical_dbs` | Medical Database Query | data.read, phi.access | false | 2026-08-15 |
| 9 | `generation` | Content Generation | output.generate | false | 2026-08-15 |
| 10 | `design` | Design Tool | output.generate | false | 2026-08-15 |

## التصنيف حسب الصلاحيات

| الصلاحية | الأدوات |
|---|---|
| `data.read` | sql_query, data_analysis, medical_dbs |
| `code.execute` | python_execute, data_analysis |
| `output.generate` | chart_generate, generation, design |
| `document.read` | document_analysis |
| `search.execute` | legal_search |
| `external_api.call` | research_apis |
| `phi.access` | medical_dbs |

## النماذج (model_cache)

| النموذج | التوكنز | التاريخ |
|---|---:|---|
| `claude-sonnet` | 8 | 2026-08-15 04:18 |
| `local-model` | 7 | 2026-08-15 05:57 |

## تكاليف النماذج (model_cost_log)

| النموذج | التوكنز | التكلفة | المصدر | التاريخ |
|---|---:|---|---|---|
| `claude-sonnet` | 8 | $0.00 | external | 2026-08-15 04:18 |
| `local-model` | 7 | $0.00 | local | 2026-08-15 05:57 |

## الأقسام الفرعية

| القسم | الدور | الحالة |
|---|---|---|
| [`registry/`](NUCLEUS.md) | السجل (هذا الملف) | active |
| [`schemas/`](../schemas/NUCLEUS.md) | مخططات الأدوات | stub |
| [`models/`](../models/NUCLEUS.md) | النماذج | stub |
| [`dependencies/`](../dependencies/NUCLEUS.md) | التبعيات | stub |
| [`governance/`](../governance/NUCLEUS.md) | حوكمة الأدوات | stub |
| [`licenses/`](../licenses/NUCLEUS.md) | التراخيص | stub |

## قاعدة البيانات

- **الجداول:** `tools` (10), `model_cache` (2), `model_cost_log` (2), `tool_generation_queue` (0)
- **Supabase Project:** `mqcfmwtdaymrmwvthqyw`

## الخطوات التالية

- [ ] إنشاء مخططات JSON Schema لكل أداة
- [ ] تفعيل مصنع الأدوات (`tool_generation_queue`)
- [ ] ربط الأدوات بالوكلاء (`allowed_tools`)
- [ ] تفعيل آلية مراقبة التكاليف
