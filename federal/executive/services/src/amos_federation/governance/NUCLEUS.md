# سجل مخططات الأحداث — النواة

## الهدف
سجل مركزي لمخططات JSON (Draft-07) الخاصة بأحداث الحوكمة. يُستخدم من قبل
`common/event_schemas.validate_event` للتحقق من امتثال الحمولات قبل النشر.

## الملفات
- `task.created.schema.json` — عقد حدث إنشاء المهمة (P9)

## الواجهة
- `../../../common/event_schemas.py::load_event_schema(event_type)` — يحمّل المخطط
- `../../../common/event_schemas.py::validate_event(event_type, payload)` — يتحقق

## الاصطلاحات
- Draft-07، `$id`، `x-amos` (domain/created/phase/status/owner)
- `additionalProperties: false` لكل كائن

## الحالة
نشط — عقد task.created مكتمل ويمرّ به اختبارات `test_event_schemas`

## اختبار الدخان
```bash
test -f governance/schema-registry/task.created.schema.json && echo "schema_registry: OK" || echo "schema_registry: FAIL"
```
