# الخزانة الفدرالية — النواة

## الهدف
إدارة الميزانية والمعاملات المالية. كل دينار موثق ومحاسب.

## الواجهة
- `README.md`
- `accounting/`
- `budgets/`
- `resource-allocation/`
- `token-issuance/`

## قاعدة البيانات
- `treasury_transactions`
- `treasury_budgets`
- `treasury_reports`

## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- ربط الخزانة بقاعدة البيانات
- تفعيل الميزانيات
- إنشاء التقارير المالية الدورية

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "federal_treasury: OK" || echo "federal_treasury: FAIL"
```
