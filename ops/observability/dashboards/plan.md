# خطة اللوحات — Observability Dashboards Plan

> **المجال:** ops/observability
> **المرحلة:** P8 — الحوكمة والأمن والمراقبة
> **الحالة:** بروتوكول (Protocol)
> **تاريخ الإنشاء:** 2026-08-15
> **الجداول:** `metrics` · `logs` · `traces`

---

## 1. الهدف
تعريف لوحات المراقبة التي تعرض صحة الدولة حيًا: المهام، الوكلاء، الأحداث، التدقيق، والمالية.

## 2. اللوحات
| اللوحة | المؤشرات (KPIs) | المصدر |
|---|---|---|
| لوحة المهام | نشطة/مكتملة/فاشلة | `tasks` + `event_store` |
| لوحة الوكلاء | نشطون/معزولون/صحة | `agent_population` + `agent_health_checks` |
| لوحة الأحداث | معدل الأحداث/أنواعها | `event_store` |
| لوحة التدقيق | معلَّمة/مقبولة/مرفوضة | `audit_entries` |
| لوحة الخزانة | الرصيد/المعاملات | `treasury_*` |
| لوحة الأداء | زمن الاستجابة/الأخطاء | `metrics` + `traces` |

## 3. مصادر البيانات
- **Metrics:** مقاييس كمية (عدد، زمن، معدل).
- **Logs:** سجلات نصية من `event_store`.
- **Traces:** تتبع السلاسل السببية (correlation_id).

## 4. التحديث والتنبيه
- تحديث حي عبر الأحداث (event-driven).
- تنبيهات عند تجاوز عتبات (معدل فشل، عزل، انتهاك حاجز).
- ربط التنبيهات ببروتوكولات royal/security.

## 5. اختبار القبول
```bash
test -f ops/observability/dashboards/plan.md && grep -q "KPIs" ops/observability/dashboards/plan.md \
  && echo "dashboards_plan: OK" || echo "dashboards_plan: FAIL"
```
