# سجل المخططات — النواة

## الهدف
سجل موحد لمخططات البيانات. كل تغيير في المخطط موثق ومتاح للمراجعة.

## الواجهة
- `README.md`
- `approval.signed.schema.json`
- `experience.recorded.schema.json`
- `task.created.schema.json`


## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- توثيق مخططات قاعدة البيانات
- تفعيل فحص التوافق
- إنشاء نسخ مرجعية

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "royal_governance_schema-registry: OK" || echo "royal_governance_schema-registry: FAIL"
```
