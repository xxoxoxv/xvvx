# تدفق المالية الولائية — الميزانيات

> **المجال:** states/finance
> **المرحلة:** P6 — تفعيل المؤسسات والولايات
> **الحالة:** مواصفة تدفق (Flow Spec)
> **تاريخ الإنشاء:** 2026-08-15
> **الجداول:** `treasury_budgets` · `treasury_transactions` · `legislations`

---

## 1. الهدف
تفعيل ولاية المالية: إعداد الميزانيات الولائية، اعتمادها، ومتابعة الصرف مقابل الاعتمادات.

## 2. مخطط التدفق (Mermaid)
```mermaid
graph LR
    P[اقتراح ميزانية ولائية] -->|legislate| L[legislations: قانون الميزانية]
    L -->|approve| B[treasury_budgets]
    B -->|spend against| T[treasury_transactions]
    T -->|report| R[treasury_reports]
    R -.->|review| G[governance]
```

## 3. الخطوات
1. **الاقتراح** — تجهيز ميزانية الولاية لكل قطاع.
2. **التقنين** — إصدار قانون ميزانية في `legislations`.
3. **الاعتماد** — تخصيص الميزانية في `treasury_budgets`.
4. **الصرف** — كل صرف يُسجَّل في `treasury_transactions` مقابل البند.
5. **التقرير** — تجميع المصروفات في `treasury_reports`.
6. **المراجعة** — مراجعة الحوكمة لاستخدام الميزانية.

## 4. الجداول المرتبطة
| الجدول | الدور |
|---|---|
| `legislations` | القانون المالي الولائي |
| `treasury_budgets` | اعتمادات الميزانية |
| `treasury_transactions` | الصرف الفعلي |
| `treasury_reports` | التقارير المالية |

## 5. اختبار القبول
```bash
test -f states/finance/flow.md && grep -q "treasury_budgets" states/finance/flow.md \
  && echo "finance_flow: OK" || echo "finance_flow: FAIL"
```
