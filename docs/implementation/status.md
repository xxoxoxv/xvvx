# حالة تنفيذ AMOS-Federation

## التعريف
سجل الحالة الهندسي لخطة التسعين يومًا — كل المراحل مكتملة.

## النطاق
يوثق المنجز وما بقي في خريطة الخدمات، API، الحاويات، والاختبارات.

## المالك
Federal Council

## تاريخ الإنشاء
2026-08-15

## المنجز

### المرحلة 0: البنية الأساسية (أسابيع 1-4)
- Docker Compose، migrations، Event Bus، CI، وفحوص الهوية.
- هياكل FastAPI للخدمات التسع، مسارات `/health` و`/ready`، ومعرّف الطلب وتتبع اختياري.
- JWT HS256، `POST/GET /v1/tasks`، و`POST /v1/plan` بخطط حتمية قابلة للاختبار.
- طبقة تخزين مهام بذاكرة داخلية للاختبارات والتطوير مع عقد جاهز لـ PostgreSQL.
- تحقق من مخططات الأحداث المسجلة مع بديل خفيف عند غياب `jsonschema`.

### المرحلة 1: MVP Agent Runtime (أسابيع 5-8)
- Tool Registry: تسجيل وعرض وحل الأدوات بالكلمات المفتاحية (Semantic Router) مع بذور من tool-index.yaml.
- Model Gateway: توجيه واستدعاء النماذج مع fallback محلي حتمي عند غياب مفتاح Claude API.
- Agent Runtime: Base Agent + Worker Agent + Tool Sandbox مع 12 أداة محاكاة.
- دورة E2E كاملة: طلب → تخطيط → تنفيذ → نتيجة → تسليم.
- 3 agent manifests (worker-researcher, worker-analyst, critic-001).

### المرحلة 2: Memory + Experience Replay (أسابيع 9-12)
- Memory Service: تخزين واسترجاع وبحث بالكلمات المفتاحية مع عزل المستأجرين.
  - `POST /v1/memory/store` + `POST /v1/memory/query` + `POST /v1/memory/search` + `GET /v1/memory/{key}`.
  - مطابقة كلمات مفتاحية حتمية (Jaccard) كبديل خفيف للـ embeddings.
  - إحصائيات الذاكرة عبر `GET /v1/memory/stats/summary`.
- Experience Replay Buffer: تسجيل الخبرات (نجاح/فشل/فجوة/إصلاح) مع تتبع المصدر.
  - `POST /v1/experiences` + `GET /v1/experiences` مع فلترة (نوع، وكيل، حد أدنى للجودة).
  - `GET /v1/experiences/{id}` لاسترجاع خبرة محددة.
  - `POST /v1/evaluations/run` لتشغيل تقييم أساسي.
  - provenance tracking تلقائي لكل خبرة.
- 74 اختبار: 55 من المرحلة 0-1 + 19 جديد (memory-service, experience).

### المرحلة 3: Evaluation + Critic (أسابيع 13-16)
- Critic Service: مراجعة نتائج المهام مع درجة جودة (0-1) وتغذية راجعة.
  - `POST /v1/reviews` بمعايير قابلة للقياس (اكتمال، نتيجة، معرّفات، جودة).
  - `GET /v1/reviews` مع فلترة (مهمة، حد أدنى للدرجة) + `GET /v1/reviews/{id}`.
  - `GET /v1/reviews/stats/summary` لإحصائيات المراجعات.
  - تقييم حتمي: نسبة الإكمال (40%)، وجود نتيجة (30%)، معرّفات (20%)، جودة الخطوات (10%).
- Evaluation Harness: مجموعة 20 مهمة قياسية مغطية 4 أنواع و5 مجالات.
  - `POST /v1/evaluations/benchmark` لتشغيل المعيار.
  - `GET /v1/evaluations/gaps` لاكتشاف الفجوات المعرفية حسب المجال.
  - `POST /v1/evaluations/run` محدّث ليشمل نتائج المعيار.
  - Gap Analyzer: يكتشف المجالات ذات معدل الفشل > 30%.
- 94 اختبار: 74 من المراحل 0-2 + 20 جديد (critic, benchmark).

### المرحلة 4: Alpha/Beta Shadow (أسابيع 17-22)
- Model Gateway محدّث: دعم نموذجين (alpha + beta) + تتبع التكلفة.
  - `POST /v1/models/invoke` يسجل التكلفة لكل استدعاء.
  - `GET /v1/cost/summary` ملخص التكاليف مصنّف حسب النموذج.
- Shadow Testing Framework: تشغيل ألفا وبيتا بالتوازي مع مقارنة.
  - `POST /v1/shadow/test` يوجّه الطلب لكلا النموذجين ويسجّل المقارنة.
  - `GET /v1/shadow/results` + `GET /v1/shadow/results/{id}` لعرض النتائج.
  - `GET /v1/shadow/stats` ملخص إحصائي (تشابه متوسط، فرق زمن الاستجابة).
  - مقارنة حتمية: تشابه نصي (Jaccard)، فرق latency، فرق tokens، فرق تكلفة.
- 104 اختبار: 94 من المراحل 0-3 + 10 جديد (shadow, cost tracking).

### المرحلة 5: LoRA Factory (أسابيع 23-28)
- Data Collection Pipeline: استخراج وتنظيف وتوازن بيانات التدريب من سجل الخبرات.
  - `POST /v1/datasets` ينشئ مجموعة بيانات: استخراج → تنظيف → موازنة → Data BOM.
  - `GET /v1/datasets` + `GET /v1/datasets/{id}` لعرض واسترجاع البيانات.
  - deduplication بـ SHA-256، موازنة حسب النوع، Data BOM مع hash.
- Model Registry: تسجيل النماذج مع Model Cards وحالة كاملة.
  - `POST /v1/models/train` محاكاة حتمية لتدريب LoRA مع مقاييس (accuracy, loss).
  - `GET /v1/models` + `GET /v1/models/{id}` لعرض واسترجاع النماذج.
  - `PATCH /v1/models/{id}/status` لتحديث الحالة (registered → trained → evaluated → promoted).
  - `GET /v1/models/{id}/card` لاسترجاع Model Card.
  - knowledge injection (anti-forgetting) ممكّن في كل Model Card.
- 119 اختبار: 104 من المراحل 0-4 + 15 جديد (data pipeline, model registry).

### المرحلة 6: Governance + Canary (أسابيع 29-36)
- Policy-as-Code: ثلاث سياسات قابلة للتنفيذ.
  - `GET /v1/policies` عرض كل السياسات.
  - `POST /v1/policies/check` فحص سياسة ضد سياق قرار.
  - سياسة الترقية: 5 بوابات + درجة جودة ≥ 0.7 + معيار ≥ 0.8.
  - سياسة الوصول: أدوات خطيرة تتطلب دور admin.
  - سياسة الميزانية: حد يومي + تنبيه عند 80%.
- Kill Switch متعدد المستويات: normal → alert → degraded → halt.
  - `GET /v1/system/status` + `POST /v1/system/kill-switch` + `POST /v1/system/kill-switch/reset`.
- Promotion Gates: 5 بوابات (evaluation → shadow → canary → human_approval → activation).
  - `POST /v1/promotions` + `POST /v1/promotions/{id}/gates` + `GET /v1/promotions/{id}`.
  - فشل بوابة يوقف الترقية، اجتياز الكل يرقى النموذج.
- Canary Deployment: نسبة مرور + مقاييس + تراجع تلقائي.
  - `POST /v1/canary` + `GET /v1/canary/{id}` + `PATCH /v1/canary/{id}/metrics`.
  - تراجع تلقائي عند error_rate > 10% أو quality < 0.5.
  - `POST /v1/canary/{id}/rollback` للتراجع اليدوي.
- Audit Log: سجل غير قابل للتعديل بسلسلة hash (SHA-256).
  - `GET /v1/audit` عرض السجل + `GET /v1/audit/verify` التحقق من سلامة السلسلة.
- 146 اختبار: 119 من المراحل 0-5 + 27 جديد (policy, kill switch, promotion, canary, audit).

## المؤجل
- الأسبوعان 11-13: Redis/Qdrant الفعليان، عزل المستأجرين على مستوى قاعدة البيانات، hardening، restore drills، واختبارات الحمل.
- واجهة control-console ليست خدمة Python ضمن هذا التنفيذ، وتبقى ضمن واجهة الويب المخطط لها.
