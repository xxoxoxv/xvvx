# Tests Stubs — النواة

## الهدف
مجلد stubs لمجال الاختبارات: يضم فحص اكتمال اختبارات الدخان والنوى داخل مجال tests.

## الملفات
- `tests_check.py` — فحص مجال الاختبارات (P3 — الاختبار الثاني عشر)

## الواجهة
- `../smoke/run_smoke_tests.py` — مشغّل اختبارات الدخان
- `../integration/` + `../e2e/` — نوى الاختبارات

## الحالة
نشط — فحص مجال tests مكتمل (12/12 مجال)

## اختبار الدخان
```bash
test -f tests/stubs/tests_check.py && echo "tests_stubs: OK" || echo "tests_stubs: FAIL"
```
