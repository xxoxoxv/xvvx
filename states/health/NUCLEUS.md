# ولاية الصحة — النواة

## الهدف
إدارة صحة الوكلاء. الفحوصات الدورية، العلاج، الوقاية، الأوبئة الرقمية.

## الواجهة
- `README.md`
- `agents/`
- `knowledge/`
- `services/`
- `tools/`

## قاعدة البيانات
- `agent_health_checks`
- `agent_treatments`

## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- ربط الصحة بقاعدة البيانات
- تفعيل الفحوصات الدورية
- إنشاء نظام إنذار صحي

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "states_health: OK" || echo "states_health: FAIL"
```
