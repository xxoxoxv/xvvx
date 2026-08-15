# السجل — النواة

## الهدف
السجل الرسمي للوكلاء المعتمدين. من يدخل، من يخرج، من في الخدمة.

## الواجهة
- `README.md`
- `citizens.yaml`
- `generate_imported.py`
- `imported_agents_data.py`
- `imported_citizens.yaml`

## قاعدة البيانات
- `agents`

## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- ربط السجل بقاعدة البيانات
- تفعيل البحث والتصفية
- إنشاء لوحة معلومات

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "agents_registry: OK" || echo "agents_registry: FAIL"
```
