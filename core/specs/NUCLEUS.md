# Core Specs — النواة

## الهدف
مجلد مواصفات النواة (الذاكرة والمعرفة والميثاق): يضم مواصفات تحديث الذاكرة والخبرة.

## الملفات
- `memory_update.md` — مواصفة تحديث الذاكرة (P5)

## الواجهة
- `../stubs/memory_check.py` — بيانات الذاكرة المخزّنة
- `../memory/` — فهرس الذاكرة والمعرفة
- `../../docs/contracts/schemas/memory.schema.json`

## الحالة
نشط — مواصفة تحديث الذاكرة مكتملة

## اختبار الدخان
```bash
test -f core/specs/memory_update.md && echo "core/specs: OK" \
  || echo "core/specs: FAIL"
```
