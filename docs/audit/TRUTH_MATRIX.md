# TRUTH_MATRIX.md — مصفوفة الحقيقة

## الهدف: قياس الفجوة بين ما تقوله وثائق الدولة وما ينفذه الكود فعليًا
## النطاق: كل أقاليم المستودع الاثني عشر
## المالك: docs/audit/ — ديوان تدقيق الدولة
## تاريخ الإنشاء: 2026-08-16
## تاريخ آخر تعديل: يُحدَّد بـ commit التوليد (المخرج حتمي بلا طابع زمني)

> **هذا الملف مُولَّد آليًا. لا تحرّره يدويًا.**
> يُعاد توليده بالأمر: `python tools/governance/truth_audit.py`

> **القاعدة الذهبية:** لا تُقبل عبارة DONE لأن الملف موجود. `DONE = Capability Proven`.

---

## 1. الحكم الإجمالي

| المقياس | القيمة |
|---|---:|
| الأقاليم المفحوصة | 12 |
| الأقاليم بحالة PROVEN | 0 |
| إجمالي المخالفات | 110 |
| ملفات بلا ترويسة هوية (المادة 009) | 25 |
| منها CRITICAL | 15 |
| منها HIGH | 68 |
| منها MEDIUM | 27 |

### توزيع المخالفات حسب النوع

| النوع | العدد | المعنى |
|---|---:|---|
| IN_MEMORY_STORE | 64 | مخزن ذاكرة يُستخدم بديلًا عن تخزين دائم |
| SILENT_FALLBACK | 31 | استثناء يُبتلع بلا تسجيل ولا رفع |
| HARDCODED_TRUTH | 10 | قيمة ثابتة تُقدَّم كحقيقة تشغيلية بدل قاعدة البيانات |
| HARDCODED_SECRET | 4 | سر/كلمة مرور مكتوبة داخل الكود أو الإعداد |
| SANDBOX_DISABLED | 1 | أداة خطرة مسجّلة بلا عزل |

---

## 2. مصفوفة الأقاليم

| الإقليم | موثّق | منفّذ | مصدر حقيقي | زائف/مخبأ | مدمج | مختبَر | مؤمَّن | مُراقَب | منشور | **مُثبَت** | الحالة |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| `core/` | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | **❌** | `DEPLOYED` |
| `royal/` | ✅ | ✅ | ✅ | — | ❌ | ✅ | ✅ | ❌ | ✅ | **❌** | `DEPLOYED` |
| `federal/` | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ✅ | ✅ | **❌** | `UNIT_TESTED` |
| `states/` | ✅ | ❌ | ❌ | — | ❌ | ✅ | ✅ | ❌ | ✅ | **❌** | `DEPLOYED` |
| `institutions/` | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ | ✅ | ❌ | ❌ | **❌** | `UNIT_TESTED` |
| `agents/` | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❌ | ✅ | **❌** | `DEPLOYED` |
| `tools/` | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | **❌** | `DEPLOYED` |
| `interfaces/` | ✅ | ❌ | ❌ | — | ❌ | ✅ | ✅ | ❌ | ❌ | **❌** | `SPECIFIED` |
| `runtime/` | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ | ✅ | ❌ | ✅ | **❌** | `DEPLOYED` |
| `docs/` | ✅ | ❌ | ❌ | — | ❌ | ✅ | ✅ | ❌ | ✅ | **❌** | `DEPLOYED` |
| `ops/` | ✅ | ✅ | ✅ | — | ❌ | ✅ | ✅ | ❌ | ❌ | **❌** | `INTEGRATED` |
| `tests/` | ✅ | ✅ | ❌ | — | ❌ | ✅ | ✅ | ❌ | ✅ | **❌** | `DEPLOYED` |

> `⚠️` في عمود «زائف/مخبأ» يعني وجود قيم ثابتة أو مخازن ذاكرة تُستخدم بديلًا عن مصدر الحقيقة. أي إقليم يحمل `⚠️` **لا يمكن** أن يصل PROVEN.

---

## 3. الحجم الفعلي لكل إقليم

| الإقليم | md | py | yaml | أسطر كود | نوى | بلا ترويسة هوية | حالات النوى |
|---|---:|---:|---:|---:|---:|---:|---|
| `core/` | 63 | 18 | 0 | 2816 | 13 | 2 | unspecified=13 |
| `royal/` | 51 | 2 | 1 | 92 | 14 | 3 | unspecified=14 |
| `federal/` | 51 | 121 | 3 | 19370 | 7 | 2 | unspecified=7 |
| `states/` | 47 | 2 | 0 | 32 | 7 | 2 | unspecified=7 |
| `institutions/` | 19 | 2 | 0 | 89 | 6 | 2 | unspecified=6 |
| `agents/` | 601 | 4 | 283 | 549 | 11 | 3 | unspecified=11 |
| `tools/` | 37 | 8 | 2 | 1660 | 12 | 3 | unspecified=12 |
| `interfaces/` | 14 | 2 | 0 | 30 | 4 | 2 | unspecified=4 |
| `runtime/` | 20 | 2 | 0 | 71 | 7 | 2 | unspecified=7 |
| `docs/` | 39 | 2 | 0 | 47 | 7 | 2 | unspecified=7 |
| `ops/` | 38 | 2 | 0 | 93 | 12 | 1 | unspecified=12 |
| `tests/` | 13 | 9 | 0 | 2132 | 5 | 1 | unspecified=5 |

---

## 4. سجل المخالفات بالأدلة

### CRITICAL (15)

| الموقع | النوع | الخطورة | التفصيل |
|---|---|---|---|
| `agents/registry/imported_agents_data.py:15` | HARDCODED_TRUTH | CRITICAL | `AGENTS` بيانات ثابتة بديلة عن قاعدة البيانات |
| `agents/stubs/registry_check.py:18` | HARDCODED_TRUTH | CRITICAL | `AGENT_COUNT = 342` عدّاد ثابت يُقدَّم كحقيقة تشغيلية |
| `agents/stubs/registry_check.py:21` | HARDCODED_TRUTH | CRITICAL | `AGENTS_SAMPLE` بيانات ثابتة بديلة عن قاعدة البيانات |
| `core/stubs/memory_check.py:19` | HARDCODED_TRUTH | CRITICAL | `MEMORIES` بيانات ثابتة بديلة عن قاعدة البيانات |
| `core/stubs/memory_check.py:34` | HARDCODED_TRUTH | CRITICAL | `EXPERIENCES` بيانات ثابتة بديلة عن قاعدة البيانات |
| `federal/executive/services/src/amos_federation/common/config.py:25` | HARDCODED_SECRET | CRITICAL | `postgres_password` قيمة سرية افتراضية مكتوبة داخل الكود |
| `federal/executive/services/src/amos_federation/common/config.py:44` | HARDCODED_SECRET | CRITICAL | `minio_secret_key` قيمة سرية افتراضية مكتوبة داخل الكود |
| `federal/executive/services/src/amos_federation/common/config.py:48` | HARDCODED_SECRET | CRITICAL | `jwt_secret` قيمة سرية افتراضية مكتوبة داخل الكود |
| `federal/executive/services/src/amos_federation/services/governance/expansion.py:108` | HARDCODED_TRUTH | CRITICAL | `FULL_POPULATION_CATEGORIES` بيانات ثابتة بديلة عن قاعدة البيانات |
| `federal/executive/services/src/amos_federation/services/royal/main.py:97` | HARDCODED_SECRET | CRITICAL | مصادقة بمقارنة `password` مع قيمة ثابتة في الكود |
| `institutions/stubs/registry_check.py:18` | HARDCODED_TRUTH | CRITICAL | `INSTITUTIONS` بيانات ثابتة بديلة عن قاعدة البيانات |
| `runtime/stubs/task_event_check.py:31` | HARDCODED_TRUTH | CRITICAL | `EVENT_COUNT = 156` عدّاد ثابت يُقدَّم كحقيقة تشغيلية |
| `runtime/stubs/task_event_check.py:34` | HARDCODED_TRUTH | CRITICAL | `EVENTS_SAMPLE` بيانات ثابتة بديلة عن قاعدة البيانات |
| `tools/registry/tool-index.yaml:49` | SANDBOX_DISABLED | CRITICAL | أداة مسجّلة بلا عزل (sandbox=false) |
| `tools/stubs/registry_check.py:18` | HARDCODED_TRUTH | CRITICAL | `TOOLS` بيانات ثابتة بديلة عن قاعدة البيانات |

### HIGH (68)

| الموقع | النوع | الخطورة | التفصيل |
|---|---|---|---|
| `federal/executive/services/src/amos_federation/common/events.py:20` | SILENT_FALLBACK | HIGH | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/main.py:27` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/main.py:37` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/store.py:26` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/store.py:44` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/critic/store.py:32` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/evaluation/benchmark.py:170` | SILENT_FALLBACK | HIGH | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/evaluation/store.py:33` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/governance/federation.py:250` | SILENT_FALLBACK | HIGH | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/memory_service/store.py:50` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/model_gateway/main.py:22` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryShadowStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/model_gateway/main.py:40` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryShadowStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/model_gateway/main.py:139` | SILENT_FALLBACK | HIGH | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/model_gateway/shadow.py:28` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryShadowStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/model_gateway/shadow.py:142` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryShadowStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/tool_registry/store.py:31` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryToolStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/training/data_pipeline.py:31` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/training/main.py:15` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/training/main.py:16` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/training/main.py:29` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/training/main.py:30` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/src/amos_federation/services/training/model_registry.py:30` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_common_branches.py:32` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_common_branches.py:207` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_common_branches.py:216` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_common_branches.py:223` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryTaskStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_edge_branches.py:13` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryShadowStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_edge_branches.py:17` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_edge_branches.py:22` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryShadowStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_edge_branches.py:43` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_edge_branches.py:47` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_edge_branches.py:55` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryModelRegistry` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:12` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:13` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:15` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:25` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryToolStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:33` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:41` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:46` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:52` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:58` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:64` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:71` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:77` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:83` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryCriticStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:97` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:104` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:112` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:118` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:124` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:130` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:136` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:143` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryExperienceStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:167` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:173` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:181` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:188` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:198` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryVectorStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:239` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryToolStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:246` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryToolStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:252` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryToolStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_inmemory_stores.py:266` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryToolStore` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_training.py:12` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_training.py:68` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_training.py:77` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_training.py:86` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_training.py:98` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |
| `federal/executive/services/tests/test_training.py:110` | IN_MEMORY_STORE | HIGH | مخزن ذاكرة `InMemoryDataPipeline` يُستخدم كمصدر حقيقة |

### MEDIUM (27)

| الموقع | النوع | الخطورة | التفصيل |
|---|---|---|---|
| `federal/executive/services/src/amos_federation/common/event_schemas.py:53` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/event_schemas.py:57` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/event_schemas.py:61` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/persistent.py:66` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/persistent.py:285` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/persistent.py:536` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/persistent.py:649` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/persistent.py:660` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/service.py:25` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/tracing.py:22` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/common/tracing.py:36` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/main.py:51` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/main.py:70` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/store.py:66` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/api_gateway/store.py:81` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/governance/expansion.py:952` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/governance/federation.py:298` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/governance/policy_engine.py:46` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/governance/policy_engine.py:51` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/governance/policy_engine.py:56` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/governance/policy_engine.py:61` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/tool_registry/sandbox.py:117` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/tool_registry/sandbox.py:246` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `federal/executive/services/src/amos_federation/services/tool_registry/store.py:58` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `tools/governance/truth_audit.py:243` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `tools/governance/truth_audit.py:271` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |
| `tools/governance/truth_audit.py:348` | SILENT_FALLBACK | MEDIUM | استثناء يُبتلع بلا تسجيل ولا رفع — يخفي فشل مصدر الحقيقة |

---

## 5. ماذا يعني هذا

كل صف بحالة أقل من `PROVEN` هو **دَين تنفيذي** مفتوح. خطة Phase E مرتّبة لسداد هذا الدين إقليمًا إقليمًا.

راجع [`PHASE_E_ROADMAP.md`](PHASE_E_ROADMAP.md) لترتيب السداد، و[`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) لمعيار الإقفال.
