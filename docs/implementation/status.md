# حالة تنفيذ AMOS-Federation

## التعريف
سجل الحالة الهندسي لخطة التسعين يومًا بعد إنجاز مرحلة التأسيس وSprint الخدمات الأساسية.

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
- 55 اختبار: 35 أساسي + 20 جديد (tool-registry, model-gateway, agent-runtime, E2E).

## المؤجل
- الأسبوعان 9-10 (المرحلة 2): Memory Service + Experience Replay Buffer.
- الأسبوعان 11-13: Redis/Qdrant الفعليان، Experience Replay، عزل المستأجرين، hardening، restore drills، واختبارات الحمل.
- واجهة control-console ليست خدمة Python ضمن هذا التنفيذ، وتبقى ضمن واجهة الويب المخطط لها.
