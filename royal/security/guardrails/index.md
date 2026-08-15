# فهرس الحواجز الواقية — Guardrails Index

> **المجال:** royal/security
> **المرحلة:** P8 — الحوكمة والأمن والمراقبة
> **الحالة:** بروتوكول (Protocol)
> **تاريخ الإنشاء:** 2026-08-15
> **الجداول:** `agent_isolations` · `audit_entries`

---

## 1. الهدف
فهرسة الحواجز الواقية (guardrails) التي تمنع الوكلاء من تجاوز حدود صلاحياتهم أو إلحاق الضرر.

## 2. فهرس الحواجز
| الحاجز | النطاق | آلية الإنفاذ |
|---|---|---|
| حد المعدل (rate limit) | استدعاء الأدوات | واجهة API (P7) |
| عزل المستأجرين (tenant isolation) | كل البيانات | `tenant_id` إلزامي |
| نطاق الأدوات المسموح (tool scope) | الوكيل | قائمة `tools` المسموح بها لكل وكيل |
| حد الإنفاق المالي | الخزانة | عتبة الموافقة (approvals) |
| منع الترحيلات المدمرة | قاعدة البيانات | append-only + ALTER ADD فقط |
| عزل الوكيل | صحة الوكيل | `agent_isolations` |
| kill-switch | النظام كله | royal/security/kill-switch |

## 3. رصد الانتهاكات
كل تجاوز لحاجز يُصدِر حدث `amos_federation.royal.guardrail_violated` ويُسجَّل في `audit_entries` مع التصعيد حسب الخطورة.

## 4. اختبار القبول
```bash
test -f royal/security/guardrails/index.md && grep -q "guardrail" royal/security/guardrails/index.md \
  && echo "guardrails_index: OK" || echo "guardrails_index: FAIL"
```
