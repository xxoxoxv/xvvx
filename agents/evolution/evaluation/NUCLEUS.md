# التقييم — النواة

## الهدف
تقييم أداء الوكلاء. كل تقييم موثق بالنتائج والمعايير والمقارنات.

## الواجهة
- `README.md`
- `benchmarks/`
- `promotion-gates.yaml`
- `regression/`
- `safety/`

## قاعدة البيانات
- `school_results`
- `reviews`

## الحالة
stub — النواة جاهزة، المحتوى ينتظر البناء

## الخطوات التالية
- ربط التقييم بقاعدة البيانات
- تفعيل التقييم الآلي
- إنشاء تقارير الأداء

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "agents_evolution_evaluation: OK" || echo "agents_evolution_evaluation: FAIL"
```
