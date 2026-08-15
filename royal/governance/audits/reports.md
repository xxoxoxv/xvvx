# تقارير التدقيق — Audit Reports

> **المجال:** royal/governance
> **المرحلة:** P8 — الحوكمة والأمن والمراقبة
> **الحالة:** بروتوكول (Protocol)
> **تاريخ الإنشاء:** 2026-08-15
> **الجداول:** `audit_entries` · `reviews` · `event_store`

---

## 1. الهدف
تعريف كيف تُولَّد تقارير التدقيق الدورية من سجل الأحداث والتدقيقات، لتقديمها للحوكمة والمالك.

## 2. أنواع التقارير
| التقرير | الدورية | المصدر |
|---|---|---|
| ملخص المهام المكتملة | يومي | `tasks` + `event_store` |
| التدقيقات المعلَّمة | فوري | `audit_entries` (flagged) |
| الانتهاكات والحواجز | أسبوعي | guardrails + `audit_entries` |
| التدقيق المالي | شهري | `treasury_reports` |
| حالة الدولة الشاملة | عند الطلب | تجميع كلي |

## 3. آلية التوليد
1. **جمع** — استعلام `audit_entries` + `event_store` بالفترة.
2. **تجميع** — تجميع حسب المجال/النوع.
3. **التصعيد** — إبراز `flagged`/`rejected`.
4. **التوثيق** — حفظ التقرير في `reviews` (سجل قابل للمراجعة).
5. **الإصدار** — حدث `amos_federation.royal.audit_report_generated`.

## 4. ضمانات
1. التقارير مشتقة من `event_store` (append-only) — لا يمكن تزويرها.
2. كل تقرير يحمل نطاق الفترة ومنشئه.
3. التقارير المعلَّمة تدخل طابور مراجعة الحوكمة.

## 5. اختبار القبول
```bash
test -f royal/governance/audits/reports.md && grep -q "audit_entries" royal/governance/audits/reports.md \
  && echo "audit_reports: OK" || echo "audit_reports: FAIL"
```
