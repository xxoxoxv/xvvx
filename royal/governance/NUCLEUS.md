# الحوكمة — النواة

## الهدف
إدارة الالتزام بالسياسات. الموافقات، التدقيق، السياسات، سجل المخططات.

## الواجهة
- `README.md`
- `approvals/`
- `audits/`
- `policies/`
- `schema-registry/`

## قاعدة البيانات
- `audit_entries`
- `reviews`

## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- ربط التدقيق بقاعدة البيانات (10 سجلات)
- تفعيل المراجعات
- ربط الموافقات بالصلاحيات

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "royal_governance: OK" || echo "royal_governance: FAIL"
```
