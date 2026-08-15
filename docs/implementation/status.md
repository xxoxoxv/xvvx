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
| **Governance** | MVP/Persistent | Policy Engine كود مُدمج (لا OPA)، Kill Switch، Audit Log دائم بـ SQLAlchemy + hash chain |
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

## الحالة الحقيقية
البيانات دائمة بـ SQLite عبر SQLAlchemy. الأحداث منشورة ومخزَّنة فعليًا. تبقى بعد إعادة التشغيل. لا يزال البنية التحتية الخارجية (PostgreSQL/Redis/Qdrant/NATS/MinIO/Docker) غير مفعّلة. الخارطة الجديدة (v1.0) تنقل كل مكوّن من "محاكاة" إلى "حقيقي".

## المؤجل (حسب الخارطة الجديدة v1.0)
- Phase 3: الحوكمة التأسيسية (OPA/Rego + Kill Switch حقيقي)
- Phase 4: الأدوات الحقيقية (100 أداة في Sandbox حقيقي)
- Phase 5: النماذج الحقيقية (Claude + vLLM)
- Phase 6-17: السكان، المؤسسات، الفيدرالية، المصانع، التعلم، الإطلاق
