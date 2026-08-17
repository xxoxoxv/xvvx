# سجل مخططات الأحداث — النواة

## الهدف
دليل مخططات JSON (Draft-07) الخاصة بأحداث الحوكمة. كل حدث له مخطط يتحقق منه
`common/event_schemas.validate_event` قبل النشر.

## الملفات
- `task.created.schema.json` — عقد حدث إنشاء المهمة (P9)

## الواجهة
- `../../common/event_schemas.py::load_event_schema(event_type)` — تحميل المخطط
- `../../common/event_schemas.py::validate_event(event_type, payload)` — التحقق

## الحالة
نشط — `task.created` مكتمل ويمرّ به `test_event_schemas`

## اختبار الدخان
```bash
test -f governance/schema-registry/task.created.schema.json && echo "schema_registry: OK" || echo "schema_registry: FAIL"
```
