# Royal Specs — النواة

## الهدف
مجلد مواصفات الحوكمة والأمن الملكي: يضم مواصفات مسار التدقيق والعتبات والبروتوكولات الأمنية.

## الملفات
- `audit_trail.md` — مواصفة مسار التدقيق (P5)

## الواجهة
- `../stubs/guard_check.py` — حراس ملكيون + مراسيم
- `../../docs/contracts/schemas/approval.schema.json`
- `../governance/` — عتبات الموافقة (يُوسَّع في P8)
- `../security/` — بروتوكولات العزل (تُوسَّع في P8)

## الحالة
نشط — مواصفة التدقيق مكتملة، البروتوكولات الأمنية في P8

## اختبار الدخان
```bash
test -f royal/specs/audit_trail.md && echo "royal/specs: OK" \
  || echo "royal/specs: FAIL"
```
