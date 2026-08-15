# Runtime Specs — النواة

## الهدف
مجلد مواصفات (Specifications) محرك التشغيل: يضم مواصفات دورة حياة المهمة وتسجيل الأحداث والحلقات المرجعية.

## الملفات
- `task_lifecycle.md` — مواصفة دورة حياة المهمة (P5)
- `event_logging.md` — مواصفة تسجيل الأحداث (P5)

## الواجهة
- `../stubs/task_event_check.py` — بيانات المهام والأحداث المخزّنة
- `../tasks/` — بنية المهمة
- `../../docs/contracts/schemas/task.schema.json` + `event.schema.json` + `execution_loop.schema.json`

## الحالة
نشط — مواصفات P5 مكتملة وجاهزة للتنفيذ

## اختبار الدخان
```bash
test -f runtime/specs/task_lifecycle.md && test -f runtime/specs/event_logging.md \
  && echo "runtime/specs: OK" || echo "runtime/specs: FAIL"
```
