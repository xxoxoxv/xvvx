# سجل الذاكرة — Memory Registry

> الفهرس الرسمي لذاكرة الدولة الرقمية. مرتبط بـ Supabase.

## نظرة عامة

| الجدول | الصفوف | آخر تحديث |
|---|---:|---|
| `memories` | 2 | 2026-08-15 05:14 |
| `experiences` | 1 | 2026-08-15 05:14 |
| `event_store` | 156 | 2026-08-15 05:49 |

---

## سجل الذاكرة التشغيلية — `memories`

| المفتاح | الكلمات المفتاحية | تاريخ الإنشاء | حجم القيمة |
|---|---|---|---|
| `test-connection` | test, connection | 2026-08-15 05:14 | 25 بايت |
| `agent_context_reset:agent-a5ad24b5` | (لا يوجد) | 2026-08-15 04:18 | 64 بايت |

---

## سجل الخبرات — `experiences`

| المعرف | النوع | المهمة | الوكيل | النموذج | درجة الجودة | التاريخ |
|---|---|---|---|---|---|---|
| `exp-4d03746c` | success | `test-task` | `test-agent` | — | 0.95 | 2026-08-15 05:14 |

---

## السجل التاريخي — `event_store`

- **إجمالي الأحداث:** 156
- **أقدم حدث:** 2026-08-15 04:07:55
- **أحدث حدث:** 2026-08-15 05:49:12

### آخر 5 أحداث

| معرف الحدث | الموضوع | التاريخ |
|---|---|---|
| `evt-acfeaeee` | `amos_federation.tool.executed` | 2026-08-15 05:49 |
| `evt-f5a44164` | `amos_federation.health.agent_isolated` | 2026-08-15 04:18 |
| `evt-f8411a9a` | `amos_federation.health.treatment_completed` | 2026-08-15 04:18 |
| `evt-3890b0c0` | `amos_federation.health.check_completed` | 2026-08-15 04:18 |
| `evt-d4bc69a5` | `amos_federation.health.treatment_completed` | 2026-08-15 04:18 |

---

## الأقسام الفرعية

| القسم | الدور | الحالة |
|---|---|---|
| [`experience/`](experience/NUCLEUS.md) | الخبرات المستخلصة من المهام | stub |
| [`history/`](history/NUCLEUS.md) | السجل التاريخي للأحداث | stub |
| [`knowledge/`](knowledge/NUCLEUS.md) | القاعدة المعرفية | stub |
| [`operational/`](operational/NUCLEUS.md) | الذاكرة التشغيلية الجارية | stub |

---

## قاعدة البيانات

- **Supabase Project:** `mqcfmwtdaymrmwvthqyw`
- **PostgreSQL:** 17
- **الجداول المرتبطة:**

| الجدول | الأعمدة الرئيسية | الارتباط |
|---|---|---|
| `memories` | `key`, `value`, `keywords`, `tenant_id` | operational/ |
| `experiences` | `id`, `type`, `task_id`, `agent_id`, `model_used`, `quality_score`, `provenance` | experience/ |
| `event_store` | `event_id`, `subject`, `data`, `created_at` | history/ |

---

## الخطوات التالية

- [ ] ربط الذاكرة التشغيلية بآلية تحديث فورية
- [ ] تصنيف الخبرات حسب النوع والجودة والمجال
- [ ] إنشاء خط زمني تفاعلي للأحداث
- [ ] تفعيل البحث المعرفي عبر الكلمات المفتاحية
- [ ] ربط `event_store` بآلية Event Sourcing
