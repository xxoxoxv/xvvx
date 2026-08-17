# الهويات — النواة

## الهدف
هويات الوكلاء. كل هوية لها اسم ودور وصلاحيات وشخصية وتاريخ.

## الواجهة
- `README.md`
- `agent-001.md`
- `agent-002.md`
- `agent-003.md`
- `imported/`

## قاعدة البيانات
- `agents`
- `agent_population`

## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- ربط الهويات بقاعدة البيانات (342 وكيل)
- تفعيل البحث
- إنشاء بطاقات هوية

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "agents_identities: OK" || echo "agents_identities: FAIL"
```
