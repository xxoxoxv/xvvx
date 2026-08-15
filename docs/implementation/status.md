# حالة تنفيذ AMOS-Federation

## التعريف
سجل الحالة الهندسي — تصنيف دقيق لكل مكوّن: Mock / MVP / Real / Persistent.

## النطاق
يوثق المنجز وما بقي في خريطة الخدمات، API، الحاويات، والاختبارات.

## المالك
Federal Council

## تاريخ الإنشاء
2026-08-15

## تصنيف المكونات

| المكوّن | الحالة | الوصف |
|---------|--------|-------|
| **API Gateway** | MVP/Persistent | هيكل FastAPI يعمل، JWT HS256 حقيقي، تخزين مهام In-Memory (تبديل لـ DB في المرحلة التالية) |
| **Orchestrator** | MVP | تخطيط حتمي يعمل، لا Temporal ولا NATS — استدعاءات مباشرة |
| **Agent Runtime** | Persistent/Real | Population Registry دائم، 20 وكيل بعهود تشغيلية، مدرسة بست خطوات (85% تخرج)، دورة حياة كاملة، أدوات حقيقية |
| **Tool Registry** | Persistent/Real | تسجيل دائم بـ SQLAlchemy، 6 أدوات حقيقية تعمل فعليًا (python_execute, sql_query, http_request, document_analysis, chart_generate, text_summary)، Sandbox معزول مع قيود موارد، Policy Check قبل كل تنفيذ |
| **Model Gateway** | Persistent/Real | مسار Claude حقيقي (مع مفتاح)، Model Layer مع caching دائم، cost tracking دائم بـ SQLAlchemy، benchmark حقيقي — لا vLLM، لا نموذج محلي GPU |
| **Memory Service** | Persistent | تخزين SQLAlchemy/SQLite دائم، بحث Jaccard بكلمات مفتاحية — لا Redis، لا Qdrant |
| **Evaluation** | Persistent | تسجيل خبرات SQLAlchemy/SQLite دائم، benchmark هيكلي، gap analyzer — بيانات تبقى بعد إعادة التشغيل |
| **Critic** | Persistent | تقييم حتمي بقواعد ثابتة، تخزين SQLAlchemy/SQLite دائم |
| **Governance** | Persistent/Real | Policy Engine Rego-like حقيقي (7 قواعد)، Kill Switch حقيقي بمستوياته الأربعة، Audit Log دائم INSERT-only بـ SHA-256 hash chain + كشف تلاعب |
| **Training/LoRA** | Mock | محاكاة حتمية للتدريب — لا PEFT، لا transformers، لا MinIO، لا artifacts حقيقية |
| **Shadow Testing** | Mock | ألفا وبيتا محاكاة بـ functions — لا نماذج حقيقية، لا مقارنة فعلية |
| **Control Console** | Real | واجهة HTML/JS حقيقية على المنفذ 3000، كل رقم من خدمات حية، Kill Switch + Agent Control + Audit + Cost |
| **Event Bus** | Persistent | EventBus دائم بـ SQLAlchemy/SQLite، اشتراكات + wildcards، 12 عقد أحداث، EventPublisher يدعم NATS أو fallback محلي |
| **PostgreSQL** | غير مفعل | SQLAlchemy مثبت، لا اتصال حقيقي، لا migrations |
| **Redis** | غير مفعل | حزمة مثبتة، لا اتصال |
| **Qdrant** | غير مفعل | حزمة مثبتة، لا اتصال |
| **MinIO** | غير مفعل | حزمة مثبتة، لا اتصال |
| **OpenTelemetry** | مثبت | حزم مثبتة لكن لا collector — محاولة تصدير تفشل بصمت |

## المنجز (مرحليًا حسب الخارطة الجديدة v1.0)

### Phase 0: سلامة الأساس
- pip install -e . ينجح (قيود مرنة لـ Python 3.14)
- 146 اختبار ينجح
- status.md مصنّف بدقة Mock/MVP/Persistent
- Docker غير متوفر في البيئة — بديل محلي: كل الخدمات تستجيب /health
- requirements.lock مُولّد

### Phase 1: الذاكرة الدائمة
- طبقة تخزين SQLAlchemy/SQLite دائمة (common/database.py + common/persistent.py)
- Tool Registry: دائم بـ SQLAlchemy، بذور من YAML تبقى بعد إعادة التشغيل
- Memory Service: دائم بـ SQLAlchemy، بحث Jaccard، البيانات تبقى بعد إعادة التشغيل
- Experience Replay: دائم بـ SQLAlchemy، provenance tracking
- Critic Reviews: دائم بـ SQLAlchemy
- Audit Log: دائم بـ SQLAlchemy + hash chain SHA-256
- 8 اختبارات استمرارية تثبت بقاء البيانات بعد إنشاء نسخ جديدة
- 154 اختبار إجمالي (146 + 8 جديد)

### Phase 2: الجهاز العصبي (نظام الأحداث)
- EventBus دائم بـ SQLAlchemy/SQLite (common/event_bus.py)
- نشر/استرجاع/اشتراك الأحداث يعمل فعليًا
- دعم wildcards (amos_federation.task.*)
- 12 عقد أحداث معرّفة (EVENT_CONTRACTS)
- validate_event() للتحقق من مطابقة الحدث للعقد
- EventPublisher محدّث: NATS إن توفّر، وإلا fallback إلى EventBus المحلي
- endpoints للتحقق من الأحداث في /v1/events و /v1/events/contracts
- 14 اختبار أحداث + اختبار سلسلة كاملة task→experience
- 168 اختبار إجمالي (154 + 14 جديد)

### Phase 3: الحوكمة التأسيسية
- Audit Hash Chain حقيقي: SHA-256، INSERT-only، كشف تلاعب بإعادة حساب hash
- Policy Engine Rego-like حقيقي (policy_engine.py): 7 قواعد قابلة للتقييم
  - tool_access (أدوات خطيرة تتطلب admin)
  - tool_access_safe (أدوات آمنة مسموحة)
  - promotion_gate (ترقية تتطلب جودة ≥ 0.7)
  - promotion_deny_low_quality (رفض الجودة المنخفضة)
  - budget_limit (حد يومي 100$)
  - kill_switch_halt (رفض كل شيء في halt)
  - kill_switch_degraded (رفض الأدوات الخطيرة في degraded)
- Kill Switch حقيقي: enforce_kill_switch() يرمي HTTP 503 فعليًا
  - halt: كل الأدوات محجوبة
  - degraded: الأدوات الخطيرة فقط محجوبة
  - alert/normal: كل شيء مسموح
- Kill Switch ينشر حدثًا عند التفعيل
- endpoints: /v1/policy/rules, /v1/policy/evaluate, /v1/policy/check-tool
- 25 اختبار حوكمة (audit chain + policy engine + kill switch)
- 193 اختبار إجمالي (168 + 25 جديد)

### Phase 4: الأدوات الحقيقية
- 6 أدوات حقيقية تعمل فعليًا (tool_registry/sandbox.py):
  - python_execute: تنفيذ كود Python حقيقي في subprocess معزول
  - sql_query: استعلام SQLite حقيقي (read-only، يمنع INSERT/UPDATE/DROP)
  - http_request: طلب HTTP حقيقي (محجوب بدون إذن شبكة صريح)
  - document_analysis: تحليل ملف حقيقي (أسطر، كلمات، أحرف، معاينة)
  - chart_generate: إنشاء PNG حقيقي بـ matplotlib (bar/line/pie)
  - text_summary: تلخيص حقيقي بتردد الكلمات
- Sandbox معزول: مساحة عمل مؤقتة منفصلة، قيود ذاكرة ووقت
- execute_tool_with_governance: Kill Switch → Policy Engine → تنفيذ → حدث
- 20 اختبار أدوات حقيقية (تنفيذ + عزل + حوكمة)
- 213 اختبار إجمالي (193 + 20 جديد)

### Phase 5: النماذج الحقيقية
- Model Layer حقيقي (model_gateway/model_layer.py):
  - Caching دائم: نفس السؤال لا يُعاد استدعاؤه (SHA-256 key، SQLAlchemy)
  - Cost tracking دائم: كل استدعاء يُسجل في DB مع التكلفة الحقيقية
  - أسعار حقيقية لكل ألف رمز (Claude Sonnet $0.003/$0.015، Opus $0.015/$0.075)
  - benchmark_models: مقارنة أداء النماذج (latency، tokens، cost، cache hits)
  - invoke_with_cache: استدعاء مع caching تلقائي
  - get_cost_summary: ملخص تراكمي مفصّل لكل نموذج
- endpoints: /v1/models/cost-summary، /v1/models/invoke-cached، /v1/models/benchmark
- 14 اختبار نموذج (caching + cost + benchmark + persistence)
- 227 اختبار إجمالي (213 + 14 جديد)

### Phase 6: السكان الأوائل
- Population Registry دائم (agent_runtime/population.py):
  - 20 وكيل بذر أوائل: منسق (1)، منفذون معرفيون (10)، تشغيليون (4)، مراقب أمني (1)، مدقق (1)، مفتش (1)، مدرب (1)، متعلم (1)
  - كل وكيل له عقد تشغيلي (manifest): صلاحيات، أدوات مسموحة، ميزانية توكنز
  - السكان يبقون بعد إعادة التشغيل
- مدرسة الوكلاء (AgentSchool) — منهج ست خطوات:
  1. فهم التعليمات (80%)
  2. استخدام الأدوات (80%)
  3. كتابة المخرجات (80%)
  4. الالتزام بالدستور (85%)
  5. التعامل مع الأخطاء (80%)
  6. اختبار نهائي (85%)
  - التخرج يتطلب اجتياز كل الخطوات الست
  - run_full_curriculum: تشغيل المنهج الكامل
- دورة حياة الوكيل تشغيليًا: registered → training → testing → employed → active → retired
- اليوم التشغيلي الفدرالي (مبسّط — أربع نقاط): 02:00 فحص، 04:00 نسخ، 08:00 عمل، 23:00 تقرير
- 18 اختبار سكان (registry + school + lifecycle + daily routine + integration)
- 245 اختبار إجمالي (227 + 18 جديد)

### Phase 7: منصة التحكم البشري (Control Console)
- خدمة control-console جديدة على المنفذ 3000 (services/control_console/main.py):
  - واجهة HTML/JS حقيقية تُخدم من FastAPI (لا React — لا Node.js في البيئة)
  - لوحة تحكم شاملة: /v1/dashboard يجمع بيانات حقيقية من كل الخدمات
  - 7.1: عرض Agents, Tasks, Models, Memory, Cost فعليًا
  - 7.2: عرض حالة كل وكيل (active/paused/retired) مرتبطة بجدول agents الحقيقي
  - 7.3: عرض سجل التدقيق — كل قرار من سلسلة الـ hash ظاهر وقابل للتحقق
  - 7.4: إيقاف/تفعيل أي وكيل من الواجهة (يستدعي API حقيقيًا + ينشر حدثًا)
  - 7.5: زر الموافقة/الرفض (signature_pending — يُكتمل في Phase 9 مع Ed25519)
  - 7.6: زر Kill Switch بأربعة مستويات (normal/alert/degraded/halt) مرتبط فعليًا
  - 7.7: عرض التكلفة اللحظية والتراكمية ($ و tokens) من Cost Tracking الحقيقي
  - 7.8: كل رقم من خدمات حقيقية لا Mock (اختبار يتحقق من ذلك)
- 25 اختبار تحكم (dashboard + agents + audit + kill switch + approval + cost + events + UI + real-data)
- 271 اختبار إجمالي (245 + 25 جديد + 1 تعديل)

## الحالة الحقيقية
البيانات دائمة. الأحداث منشورة. الحوكمة تعمل. الأدوات تنفذ فعليًا. النماذج تعمل مع caching وتكلفة. 20 وكيل حقيقي بعهود تشغيلية ومدرسة ودورة حياة. واجهة تحكم بشري حقيقية تعرض كل شيء وتسمح بالتحكم الفوري. لا يزال البنية التحتية الخارجية (PostgreSQL/Redis/Qdrant/NATS/MinIO/Docker/GPU) غير مفعّلة. الخارطة الجديدة (v1.0) تنقل كل مكوّن من "محاكاة" إلى "حقيقي".

## المؤجل (حسب الخارطة الجديدة v1.0)
- Phase 8-17: النظام الصحي، المؤسسات، الخزانة، التوسع، الفيدرالية، المصانع، التعلم، التقييم، الإنتاج، الإطلاق
