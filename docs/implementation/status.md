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
| **API Gateway** | MVP | هيكل FastAPI يعمل، JWT HS256 حقيقي، تخزين مهام In-Memory (غير دائم) |
| **Orchestrator** | MVP | تخطيط حتمي يعمل، لا Temporal ولا NATS — استدعاءات مباشرة |
| **Agent Runtime** | MVP | Base/Worker Agent يعمل، Tool Sandbox محاكاة (12 أداة Mock) — لا Docker ولا عزل حقيقي |
| **Tool Registry** | MVP | تسجيل وعرض وحل بالكلمات المفتاحية، تخزين In-Memory، بذور من YAML — لا PostgreSQL |
| **Model Gateway** | MVP | مسار Claude موجود لكن غير مُختبَر بمفتاح حقيقي، fallback محلي حتمي — لا vLLM، لا نموذج محلي |
| **Memory Service** | Mock | تخزين In-Memory، بحث Jaccard وهمي — لا Redis، لا Qdrant، لا embeddings |
| **Evaluation** | Mock/MVP | تسجيل خبرات In-Memory، benchmark هيكلي (20 مهمة)، gap analyzer بسيط — لا DB دائم |
| **Critic** | Mock | تقييم حتمي بقواعد ثابتة — لا نموذج فعلي، لا DB |
| **Governance** | MVP/Mock | Policy Engine كود مُدمج (لا OPA)، Kill Switch يغيّر قيمة فقط (لا يوقف خدمات)، Audit Log In-Memory بـ hash chain — لا PostgreSQL، لا Rego |
| **Training/LoRA** | Mock | محاكاة حتمية للتدريب — لا PEFT، لا transformers، لا MinIO، لا artifacts حقيقية |
| **Shadow Testing** | Mock | ألفا وبيتا محاكاة بـ functions — لا نماذج حقيقية، لا مقارنة فعلية |
| **Control Console** | غير موجود | لا واجهة React — لم تُبنَ بعد |
| **Event Bus** | غير موجود | لا NATS، لا JetStream — استدعاءات مباشرة فقط |
| **PostgreSQL** | غير مفعل | SQLAlchemy مثبت، لا اتصال حقيقي، لا migrations |
| **Redis** | غير مفعل | حزمة مثبتة، لا اتصال |
| **Qdrant** | غير مفعل | حزمة مثبتة، لا اتصال |
| **MinIO** | غير مفعل | حزمة مثبتة، لا اتصال |
| **OpenTelemetry** | مثبت | حزم مثبتة لكن لا collector — محاولة تصدير تفشل بصمت |

## المنجز (مرحليًا حسب الخطة السابقة)

### Phase 0-2 (الخطة القديمة): البنية الأساسية + MVP
- 9 هياكل FastAPI تعمل على /health و /ready
- JWT HS256، تخطيط حتمي، تنفيذ وكلاء، حل أدوات
- Memory Service (Mock)، Experience Replay (Mock)
- 146 اختبار ينجح

### Phase 3 (الخطة القديمة): Critic + Evaluation
- Critic Service: تقييم حتمي بـ 5 معايير (Mock — لا نموذج)
- Benchmark Suite: 20 مهمة قياسية (هيكلي — لا تنفيذ فعلي)
- Gap Analyzer: اكتشاف فجوات بناءً على نوع الخبرة (Mock)

### Phase 4 (الخطة القديمة): Shadow + Cost
- Shadow Testing: محاكاة ألفا/بيتا (Mock — functions)
- Cost Tracking: تتبع تكلفة بأسعار ثابتة (MVP — لا تكلفة حقيقية)

### Phase 5 (الخطة القديمة): LoRA Factory
- Data Pipeline: استخراج/تنظيف/موازنة (MVP — In-Memory)
- Model Registry: Model Cards + lifecycle (Mock — لا تدريب حقيقي)

### Phase 6 (الخطة القديمة): Governance
- Policy Engine: 3 سياسات كود مُدمج (Mock — لا OPA)
- Kill Switch: 4 مستويات (Mock — لا إيقاف خدمات فعلية)
- Promotion Gates: 5 بوابات (MVP — منطق يعمل In-Memory)
- Canary: تراجع تلقائي (Mock — لا deployment حقيقي)
- Audit Log: hash chain SHA-256 (MVP — In-Memory، لا DB)

## الحالة الحقيقية
كل الخدمات تعمل بـ In-Memory stores. لا persistence حقيقي. لا بنية تحتية (Docker/PostgreSQL/Redis/Qdrant/NATS/MinIO). الخارطة الجديدة (v1.0) تنقل كل مكوّن من "محاكاة" إلى "حقيقي".

## المؤجل (حسب الخارطة الجديدة v1.0)
- Phase 0: سلامة الأساس (هذا المستند)
- Phase 1: الذاكرة الدائمة (PostgreSQL/Redis/Qdrant/MinIO)
- Phase 2: الجهاز العصبي (NATS JetStream)
- Phase 3: الحوكمة التأسيسية (Audit Hash Chain + OPA + Kill Switch حقيقي)
- Phase 4: الأدوات الحقيقية (100 أداة في Sandbox حقيقي)
- Phase 5: النماذج الحقيقية (Claude + vLLM)
- Phase 6-17: السكان، المؤسسات، الفيدرالية، المصانع، التعلم، الإطلاق
