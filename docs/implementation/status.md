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
| **Agent Runtime** | MVP | Base/Worker Agent يعمل، Tool Sandbox محاكاة (12 أداة Mock) — لا Docker ولا عزل حقيقي |
| **Tool Registry** | Persistent | تسجيل وعرض وحل بالكلمات المفتاحية، تخزين SQLAlchemy/SQLite دائم، بذور من YAML |
| **Model Gateway** | MVP | مسار Claude موجود لكن غير مُختبَر بمفتاح حقيقي، fallback محلي حتمي — لا vLLM، لا نموذج محلي |
| **Memory Service** | Persistent | تخزين SQLAlchemy/SQLite دائم، بحث Jaccard بكلمات مفتاحية — لا Redis، لا Qdrant |
| **Evaluation** | Persistent | تسجيل خبرات SQLAlchemy/SQLite دائم، benchmark هيكلي، gap analyzer — بيانات تبقى بعد إعادة التشغيل |
| **Critic** | Persistent | تقييم حتمي بقواعد ثابتة، تخزين SQLAlchemy/SQLite دائم |
| **Governance** | Persistent/Real | Policy Engine Rego-like حقيقي (7 قواعد)، Kill Switch حقيقي بمستوياته الأربعة، Audit Log دائم INSERT-only بـ SHA-256 hash chain + كشف تلاعب |
| **Training/LoRA** | Mock | محاكاة حتمية للتدريب — لا PEFT، لا transformers، لا MinIO، لا artifacts حقيقية |
| **Shadow Testing** | Mock | ألفا وبيتا محاكاة بـ functions — لا نماذج حقيقية، لا مقارنة فعلية |
| **Control Console** | غير موجود | لا واجهة React — لم تُبنَ بعد |
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

## الحالة الحقيقية
البيانات دائمة بـ SQLite عبر SQLAlchemy. الأحداث منشورة ومخزَّنة فعليًا. الحوكمة تعمل فعليًا: Policy Engine يقيّم القرارات، Kill Switch يوقف التنفيذ، Audit Chain يكشف التلاعب. لا يزال البنية التحتية الخارجية (PostgreSQL/Redis/Qdrant/NATS/MinIO/Docker) غير مفعّلة. الخارطة الجديدة (v1.0) تنقل كل مكوّن من "محاكاة" إلى "حقيقي".

## المؤجل (حسب الخارطة الجديدة v1.0)
- Phase 4: الأدوات الحقيقية (100 أداة في Sandbox حقيقي)
- Phase 5: النماذج الحقيقية (Claude + vLLM)
- Phase 6-17: السكان، المؤسسات، الفيدرالية، المصانع، التعلم، الإطلاق
