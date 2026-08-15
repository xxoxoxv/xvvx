# الهويات المستوردة — النواة

## الهدف
وكلاء مستوردون من أطراف خارجية. كل هوية موثقة المنشأ.

## الواجهة
- `README.md`
- `federal-executive/`
- `governance/`
- `governance-audits/`
- `memory/`
- `models/`
- `observability/`
- `security/`
- `states-culture/`
- `states-finance/`
- `states-health/`
- `states-infrastructure/`
- `states-law/`
- `states-science/`
- `tools/`


## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- توثيق مصدر كل هوية
- تفعيل فحص التوافق
- إنشاء عملية استيراد موحدة

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "agents_identities_imported: OK" || echo "agents_identities_imported: FAIL"
```
