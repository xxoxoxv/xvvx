# Tools — النواة

## الهدف
الأدوات والنماذج: توليدها، تسجيلها، إتاحتها للوكلاء، وإدارة التبعيات والترخيص.

## الواجهة
- `registry/` — سجل الأدوات (Supabase: tools — 10 أدوات موجودة)
- `schemas/` — مخططات الأدوات
- `governance/` — حوكمة الأدوات
- `dependencies/` — التبعيات
- `licenses/` — التراخيص
- `models/` — سجل النماذج (alpha, beta, gamma, external) + (Supabase: model_cache, model_cost_log)

## الحالة
stub — الهيكل موجود + models منقول

## الخطوات التالية
- ربط طابور توليد الأدوات (Supabase: tool_generation_queue)
- تفعيل آلية البحث عن الأدوات للوكلاء
- ربط سجل النماذج والتكلفة

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "tools: OK" || echo "tools: FAIL"
```
