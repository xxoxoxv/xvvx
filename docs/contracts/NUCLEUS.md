# docs/contracts — العقود والمخططات (NUCLEUS)

## الهدف
تعريف العقود الرسمية بين أجزاء الدولة الرقمية. كل مخطط يحدد بنية البيانات بدقة قبل التنفيذ.

## الواجهة
- `schemas/*.schema.json` — 12 مخطط JSON Schema مواءم مع جداول Supabase
- `README.md` — فهرس العقود والجداول المرتبطة

## الحالة
stub — المخططات منشأة ومتحقق منها، جاهزة للربط الفعلي في P4

## الخطوات التالية
- ربط كل مخطط بجدوله الفعلي في Supabase (P4)
- إنشاء stubs ترجع بيانات حقيقية مطابقة للمخططات (P3)
- إضافة اختبارات تحقق ضد المخططات

## اختبار الدخان
```bash
test -d schemas && test -f README.md && python3 -c "import json; json.load(open('schemas/tools.schema.json'))" && echo "contracts: OK" || echo "contracts: FAIL"
```
