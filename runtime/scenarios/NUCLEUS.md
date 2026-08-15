# Runtime Scenarios — النواة

## الهدف
سيناريوهات مرجعية تُوضّح حلقات التشغيل الكاملة لتكون وحدة قياس للتدفقات اللاحقة.

## الملفات
- `single_task_execution.md` — سيناريو "تنفيذ مهمة واحدة" (P5) — أول نبضة قلب للدولة

## الواجهة
- `../specs/task_lifecycle.md` + `../specs/event_logging.md`
- `../../core/specs/memory_update.md` + `../../royal/specs/audit_trail.md`

## الحالة
نشط — السيناريو المرجعي الأول مكتمل

## اختبار الدخان
```bash
test -f runtime/scenarios/single_task_execution.md && echo "runtime/scenarios: OK" \
  || echo "runtime/scenarios: FAIL"
```
