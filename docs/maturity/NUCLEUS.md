# Maturity — النواة

## الهدف
مجلد معايير النضج والفصل المستقبلي: متى وكيف تُفصل أجزاء الدولة إلى وحدات مستقلة، وسياسات الإصدار والحوكمة طويلة الأمد.

## الملفات
- `extraction_criteria.md` — معايير جاهزية الاستخراج (P9)
- `versioning_policy.md` — سياسة الإصدار Semantic (P9)
- `ci_maturity.md` — نضج CI والاختبارات (P9)
- `long_term_governance.md` — نموذج الحوكمة طويل الأمد (P9)

## الواجهة
- `../implementation/PROGRESS_LOG.md` — سجل التقدم
- `../adr/template.md` — قالب قرارات العمارة
- `../../.github/workflows` — خط أنابيب CI

## الحالة
نشط — معايير P9 مكتملة

## اختبار الدخان
```bash
ls docs/maturity/*.md >/dev/null 2>&1 && echo "docs/maturity: OK" || echo "docs/maturity: FAIL"
```
