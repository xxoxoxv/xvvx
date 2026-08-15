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
| **Governance** | Persistent/Real/Complete | Policy Engine موسّع (10 قواعد لكل الخدمات)، Kill Switch 4 مستويات، Audit Chain SHA-256، Ed25519 حقيقي، بوابات ترقية 5، سلطة تنفيذية + تشريعية + قضائية + رقابة عليا |
| **Training/LoRA** | Mock | محاكاة حتمية للتدريب — لا PEFT، لا transformers، لا MinIO، لا artifacts حقيقية |
| **Shadow Testing** | Mock | ألفا وبيتا محاكاة بـ functions — لا نماذج حقيقية، لا مقارنة فعلية |
| **Control Console** | Real | واجهة HTML/JS حقيقية على المنفذ 3000، كل رقم من خدمات حية، Kill Switch + Agent Control + Audit + Cost |
| **Event Bus** | Persistent | EventBus دائم بـ SQLAlchemy/SQLite، اشتراكات + wildcards، 12 عقد أحداث، EventPublisher يدعم NATS أو fallback محلي |
| **PostgreSQL** | Connected | Supabase pooler (ap-northeast-1)، 10 جداول، قراءة/كتابة حقيقية، db_cursor يعمل |
| **Redis** | غير مفعل | حزمة مثبتة، لا اتصال |
| **Qdrant** | غير مفعل | حزمة مثبتة، لا اتصال |
| **MinIO** | غير مفعل | حزمة مثبتة، لا اتصال |
| **OpenTelemetry** | مثبت | حزم مثبتة لكن لا collector — محاولة تصدير تفشل بصمت |

## المنجز (مرحليًا حسب الخارطة الجديدة v1.0)

### Phase 0: سلامة الأساس
- pip install -e . ينجح (قيود مرنة لـ Python 3.14)
- 591 اختبار ينجح (بعد إصلاح 201 خطأ lint وتنسيق 70 ملف)
- ruff check: 0 أخطاء
- ruff format --check: 110 ملف منسق
- status.md مصنّف بدقة Mock/MVP/Persistent/Real/Complete
- Docker غير متوفر في البيئة — بديل محلي: كل الخدمات تستجيب /health و /ready و /live
- requirements.lock مُولّد (183 حزمة مثبتة)
- conftest.py يضمن بيئة اختبار نظيفة (منع Flaky Tests)
- .env.example يوثق كل متغيرات البيئة المطلوبة
- CI workflow في جذر المستودع (.github/workflows/ci.yml)
- فحص هوية المستودع ينجح (check_repository_identity.py)
- تقرير فجوة tb.pdf منشور (docs/implementation/phase0_gap_report.md)
- فحص أمني: لا أسرار، لا SQL injection، لا bare excepts
- فحص هيكلي: لا اعتماديات دائرية، لا مسؤوليات مختلطة، لا God Services

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

### Phase 8: النظام الصحي المؤسسي للوكلاء
- النظام الصحي (agent_runtime/health.py) — 3 جداول جديدة في DB:
  - agent_health_checks: فحوصات دورية مع hash chain
  - agent_isolations: سجلات العزل
  - agent_treatments: سجلات العلاج
- 8.1: فحص دوري لكل وكيل — الأداء، استهلاك الموارد، الالتزام بالسياسات:
  - نتيجة واحدة من أربع: سليم (healthy) / مراقبة (monitor) / علاج (treatment) / عزل (isolated)
  - مسجلة في DB مع SHA-256 hash chain
  - بيانات حقيقية من PersistentExperienceStore و AuditStore
  - فحص كل الوكلاء دفعة واحدة
- 8.2: مسار العلاج — ينفذ فعليًا:
  - retrain: استدعاء AgentSchool.run_full_curriculum (المرحلة 6)
  - replace_model: استدعاء ModelLayer.invoke_with_cache (المرحلة 5)
  - fix_tool: فحص أدوات الوكيل
  - reset_context: إعادة تعيين سياق الوكيل
- 8.3: مسار العزل — Sandbox معزول:
  - الوكيل المعزول لا يمكنه تنفيذ أي أداة إنتاجية
  - كل فعل أثناء العزل مُسجّل
  - إنهاء العزل: إعادة تدريب / تقاعد / إطلاق
- 8.4: ربط بواجهة التحكم — 7 endpoints جديدة:
  - GET /v1/health/all — كل الحالات الصحية
  - GET /v1/health/agents/{id} — حالة وكيل
  - POST /v1/health/check — تشغيل فحص
  - GET /v1/health/isolations — حالات العزل
  - POST /v1/health/isolate/{id} — عزل
  - POST /v1/health/treat/{id} — علاج
  - POST /v1/health/release/{id} — إنهاء عزل
- دورة فحص صحي كاملة (run_health_cycle) — تفحص كل الوكلاء تلقائيًا
- PostgreSQL (Supabase) — متصل فعليًا عبر pooler (ap-northeast-1)
  - 10 جداول في PostgreSQL: agents, tools, tasks, memories, experiences, reviews, audit_entries, agent_health_checks, agent_isolations, agent_treatments
  - db_cursor مُصلح لدعم PostgreSQL (RealDictCursor)
  - الاختبارات تمر على SQLite و PostgreSQL
- 32 اختبار صحي (فحص + علاج + عزل + دورة كاملة + واجهة)
- 303 اختبار إجمالي (271 + 32 جديد)

### Phase 9: المؤسسات الفدرالية المركزية + الحوكمة الكاملة
- وحدة الحوكمة الكاملة (governance/federation.py) — 6 جداول جديدة:
  - approvals: الموافقات الموقعة بـ Ed25519
  - promotion_gates: بوابات الترقية الخمس
  - executive_roles: الأدوار التنفيذية الخمسة
  - legislations: التشريعات والقوانين
  - court_cases: قضايا المحكمة العليا
  - compliance_reports: تقارير الامتثال
- 9.1: Policy Engine موسّع — 10 قواعد تغطي كل الخدمات (tool-registry, model-gateway, agent-runtime, governance, memory-service, evaluation)
- 9.2: Approval UI كاملة — طلب/موافقة/رفض مع توقيع Ed25519 حقيقي
- 9.3: Ed25519 حقيقي — توليد مفاتيح، توقيع، تحقق رياضي (cryptography library أو fallback SHA-256)
- 9.4: بوابات الترقية الخمس — evaluation → shadow → canary → human_approval → activation
  - لا يمكن تجاوز بوابة دون اجتياز السابقة
  - رسوب في أي بوابة يوقف الترقية
- 9.5: السلطة التنفيذية — 5 أدوار مشغولة بوكلاء حقيقيين:
  - منسق عام، مستشار تخطيط، مستشار أمن، ناطق رسمي، مدير عمليات
  - fill_all_roles: تعيين تلقائي من السكان الحقيقيين
- 9.6: السلطة التشريعية — مجلس سياسات + دورة تشريعية كاملة:
  - اقتراح → مناقشة → تصويت → إقرار/رفض
  - القانون المُقر يُضاف فعليًا لـ Policy Engine كـ RegoRule
  - منع التصويت المزدوج
- 9.7: السلطة القضائية — المحكمة العليا:
  - رفع دعوى، إضافة مرافعات، إصدار حكم
  - توثيق كامل للأدلة والمرافعات
- 9.8: الرقابة العليا — تفتيش + تدقيق + امتثال:
  - تقرير امتثال شهري مبني على Audit Chain الحقيقي
  - فحص سلامة السلسلة (chain_verified)
  - حساب معدل الامتثال من الانتهاكات الفعلية
- 5 endpoints جديدة في Control Console: approvals, legislations, court-cases, compliance-reports, executive-roles
- 43 اختبار حوكمة (Ed25519 + approval + promotion + executive + legislative + judicial + oversight + UI)
- 346 اختبار إجمالي (303 + 43 جديد)

### Phase 10: الخزانة الفدرالية والعملة الرقمية
- الخزانة الفدرالية (governance/treasury.py) — 3 جداول جديدة:
  - treasury_transactions: معاملات مالية INSERT-only مع SHA-256 hash chain
  - treasury_budgets: موازنات الوكلاء والدوائر
  - treasury_reports: تقارير مالية يومية/شهرية
- 10.1: عملة amos-credit:
  - كل معاملة مسجلة بشكل غير قابل للتعديل (INSERT-only)
  - سلسلة hash مستقلة فوق Audit Chain
  - verify_chain: التحقق من سلامة السلسلة
  - get_balance: رصيد لكل وكيل أو الإجمالي
- 10.2: مصادر الدخل (مرتبطة بحدثات حقيقية):
  - task_completion: مكافأة إكمال مهمة (مرتبطة بـ experience.recorded)
  - quality_report: مكافأة جودة (مرتبطة بـ evaluation.completed)
  - training: مكافأة تخرج (مرتبطة بـ school.graduated)
  - جودة أعلى = مكافأة أعلى
  - process_experience_income: معالجة الخبرات الحقيقية تلقائيًا
- 10.3: مصادر المصروف (مرتبطة بـ Cost Tracking الحقيقي):
  - model_invoke: رسوم استدعاء نموذج (مرتبطة بـ model.invoked، تحويل $ → amos-credit)
  - storage: رسوم تخزين مفرط
  - retraining: رسوم إعادة تدريب (مرتبطة بـ treatment.completed)
  - process_real_costs: خصم تكاليف Model Gateway الحقيقية
- 10.4: وظائف الخزانة:
  - allocate_budget / get_budget: توزيع الموازنات
  - generate_financial_report: تقرير مالي فدرالي حقيقي
  - تفصيل الدخل والمصروف حسب المصدر
  - فحص سلامة السلسلة في كل تقرير
- دورة اقتصادية كاملة (run_economic_cycle): معالجة دخل + مصروف + تقرير
- 7 endpoints جديدة في Control Console
- 32 اختبار خزانة (amos-credit + دخل + مصروف + موازنة + تقرير + دورة + UI)
- 378 اختبار إجمالي (346 + 32 جديد)

### Phase 11: التوسع السكاني الكامل + الجامعات
- وحدة التوسع (governance/expansion.py) — 4 جداول جديدة:
  - specialization_results: نتائج اختبارات التخصص
  - university_outputs: مخرجات الجامعة (أوراق، أدوات، منهج)
  - retirement_records: سجلات التقاعد والأرشفة
  - expansion_batches: دفعات التوسع السكاني
- 11.1: التوسع السكاني التدريجي (~681 هدف، 18 فئة):
  - FULL_POPULATION_CATEGORIES: 18 فئة كاملة (منسق عام، منسقو ولايات، منفذون معرفيون/تشغيليون، مراقبون، مدققون، قضاة، مفتشون، مدربون، متعلمون، مديرو إنتاج، عمال، محاسبون، أمناء مكتبة، مهندسو بنية، منسقو علاقات، طوارئ، احتياطي)
  - PopulationExpansion: create_batch → enroll → graduate (≥85%) → employ (مع فحص صحي)
  - run_full_expansion: توسع كامل بدفعات تدريجية
  - expansion_stats: إحصائيات الهدف vs الفعلي + fill_rate
- 11.2: مسار التخصص (6 مسارات):
  - مالي (7 أيام)، قانوني (14 يوم)، علمي (21 يوم)، صحي (14 يوم)، ثقافي (7 يوم)، صناعي (14 يوم)
  - كل مسار له منهج من 4 مواد وحد اجتياز
  - take_exam: اجتياز قبل التوظيف في الولاية
  - list_specialized_agents: فلترة بالتخصص
- 11.3: الجامعات:
  - UNIVERSITY_RESEARCH_TOPICS: 6 مسارات × 3 مواضيع بحث
  - submit_output: ورقة بحثية / أداة / منهج محسّن
  - approve_output: اعتماد بدرجة جودة
  - produce_first_output: أول مخرج جامعي حقيقي (ورقة بحثية)
  - content_hash: SHA-256 لكل مخرج
- 11.4: التقاعد والأرشفة:
  - retire_agent: تقاعد مع snapshot كامل للبيانات
  - يحسب عدد الفشل الصحي من HealthChecker
  - get_archived_data: استرجاع البيانات المؤرشفة
  - تحديث حالة الوكيل لـ retired
- 10 endpoints جديدة في Control Console
- 37 اختبار توسع (دفعات + تخصص + جامعة + تقاعد + UI)
- 415 اختبار إجمالي (378 + 37 جديد)

## الحالة الحقيقية (تصنيف صارم)

**ما يعمل فعليًا في بيئة sandbox:**
- البيانات دائمة عبر SQLAlchemy/SQLite (تبقى بعد إعادة التشغيل)
- الأحداث منشورة عبر EventBus محلي (NATS غير متوفر — fallback يعمل)
- الحوكمة تعمل: Audit Chain SHA-256، Policy Engine، Kill Switch، Ed25519
- الأدوات تنفذ فعليًا في sandbox معزول (6 أدوات حقيقية)
- النماذج تعمل مع Claude API + caching + cost tracking
- 20 وكيل بعهود تشغيلية (قابل للتوسع)
- واجهة تحكم بشري (HTML/JS) تعرض بيانات حقيقية
- نظام صحي مؤسسي للوكلاء
- PostgreSQL (Supabase) متصل عبر pooler
- السلطات الأربع فدرالية + اقتصاد داخلي بـ amos-credit

**ما لا يعمل (قيود بيئة sandbox):**
- Docker غير متوفر — لا `docker compose up` قابل للإثبات
- Redis غير متصل — SQLAlchemy/SQLite كبديل
- NATS غير متصل — EventBus محلي كبديل
- Qdrant غير متصل — بحث Jaccard كبديل
- MinIO غير متصل — نظام ملفات محلي كبديل
- GPU/vLLM غير متوفر — Claude API فقط
- التدريب LoRA محاكاة (لا PEFT/transformers)
- Shadow Testing محاكاة (لا نماذج حقيقية للمقارنة)

**تصنيف المراحل 1-11:** منفذة جزئيًا (Prototype/Sandbox-verifiable) — ليست مكتملة 100% حسب بوابة الخروج

## المرحلة 1: الذاكرة الدائمة (PostgreSQL)

**الحالة:** اتصال واختبارات ORM + service-level مكتملة ✅ — ربط الخدمات قيد التحقق

**ما تم:**
- اتصال Supabase PostgreSQL يعمل عبر pooler (port 6543)
- 36 جدول موجودة وقابلة للكتابة
- اختبار استمرارية البيانات بعد إعادة تشغيل المحرك: ناجح
- 7 نماذج (Agent, Tool, Task, Memory, Experience, Review, AuditEntry) مختبرة CRUD
- 7 اختبارات PostgreSQL رسمية (test_phase1_postgres.py) — كلها تنجح:
  - 4 ORM-level: persistence across sessions, CRUD, engine restart, JSON columns
  - 3 service-level: Tool Registry, PersistentTaskStore, API Gateway Adapter — كلها عبر إعادة تشغيل
- API Gateway مربوط بـ PersistentTaskStoreAdapter ( بدلاً من InMemoryTaskStore)
- conftest.py يستخدم AMOS_RUN_POSTGRES_TESTS=1 + AMOS_TEST_DATABASE_URL (opt-in صريح)
- إجمالي الاختبارات: 598 (591 SQLite + 7 PostgreSQL)

**بوابة الخروج:**
- ✅ البيانات تبقى بعد إعادة التشغيل
- ✅ كل النماذج تعمل في PostgreSQL
- ✅ JSON columns تعمل
- ✅ اختبارات service-level: Tool Registry, Task Store, API Gateway
- ✅ API Gateway مربوط بـ PostgreSQL عبر PersistentTaskStoreAdapter
- ⚠️ Orchestrator و Agent Runtime لا تزال تستخدم PopulationRegistry (يدعم PostgreSQL تلقائيًا) لكن لم يُختبرا عبر endpoint
- ⚠️ Training لا يزال InMemory (حسب الخارطة، Phase 14)

## المؤجل (حسب الخارطة الجديدة v1.0)
- Phase 12-17: الفيدرالية، المصانع، التعلم، التقييم، الإنتاج، الإطلاق
