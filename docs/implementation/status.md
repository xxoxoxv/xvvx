# حالة تنفيذ AMOS-Federation

## التعريف
سجل الحالة الهندسي لخطة التسعين يومًا بعد إنجاز المرحلتين الأولى والثانية.

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

## المؤجل
- الأسبوعان 11-13: Redis/Qdrant الفعليان، عزل المستأجرين على مستوى قاعدة البيانات، hardening، restore drills، واختبارات الحمل.
- المرحلة 3: Critic Agents + تقييم آلي + Regression Suite.
- واجهة control-console ليست خدمة Python ضمن هذا التنفيذ، وتبقى ضمن واجهة الويب المخطط لها.
