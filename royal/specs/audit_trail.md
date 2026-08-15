# مواصفة مسار التدقيق — Audit Trail Specification

> **المجال:** royal
> **المرحلة:** P5 — حلقة التشغيل الأساسية
> **الحالة:** مواصفة (Spec) — جاهزة للتنفيذ
> **تاريخ الإنشاء:** 2026-08-15
> **المادة الدستورية:** 009 (الشفافية والمراجعة المستمرة)
> **المواءمة:** `audit_entries` + `reviews` Supabase tables + `docs/contracts/schemas/approval.schema.json`

---

## 1. الهدف

تعريف كيف تتحوّل كل سلسلة أحداث (event chain) إلى مسار تدقيق قابل للمراجعة من قبل الحوكمة الملكية (royal/governance)، بحيث لا يمكن لأي فعل أن يمر دون أثر قابل للتتبع من المهمة حتى الذاكرة.

> الديوان الملكي لا يحكم الغياب. كل فعل له بصمة.

---

## 2. سلسلة التدقيق الكاملة

مسار التدقيق يربط الطبقات الست:

```
مهمة (task) ──→ وكيل (agent) ──→ أداة (tool) ──→ حدث (event)
                                                      │
                                                      ▼
                                               تدقيق (audit_entry)
                                                      │
                                                      ▼
                                                ذاكرة (memory)
```

كل عقدة في السلسلة تحمل مرجعًا للعقدة السابقة:

| العقدة | المرجع للسابق | الجدول |
|---|---|---|
| مهمة | `correlation_id` (الجذر) | `tasks` |
| وكيل | `task.assigned_agent` | `agents` |
| أداة | `event.aggregate_id` | `tools` |
| حدث | `causation_id` | `event_store` |
| تدقيق | `event_id` المُراجَع | `audit_entries` |
| ذاكرة | `audit_entry_id` | `memories` |

> هذا يحقق قابلية التتبع الكامل (end-to-end traceability): من أي ذاكرة، تصل إلى التدقيق، فالحدث، فالأداة، فالوكيل، فالمهمة الجذرية.

---

## 3. بنية سجل التدقيق (audit_entry)

كل سجل في `audit_entries`:

| الحقل | النوع | الوصف |
|---|---|---|
| `id` | string | معرّف التدقيق |
| `event_id` | string | الحدث المُراجَع (FK → `event_store.id`) |
| `task_id` | string | المهمة الجذرية (FK → `tasks.id`) |
| `reviewer` | string | الجهة المراجِعة (`royal_guards` | `governance` | `owner`) |
| `verdict` | enum | `approved` \| `flagged` \| `rejected` |
| `notes` | text | ملاحظات المراجعة |
| `created_at` | datetime (UTC) | وقت التدقيق |

> `verdict = rejected` يُطلق حدث `amos_federation.royal.audit_rejected` ويوقف السلسلة حتى مراجعة الحوكمة.

---

## 4. عتبات المراجعة (Review Thresholds)

متى يُنشأ سجل تدقيق تلقائيًا:

| الزناد | نوع المراجعة | المراجِع |
|---|---|---|
| كل مهمة `completed` | تدقيق قياسي | `royal_guards` |
| مهمة `failed` بعد تجاوز المحاولات | مراجعة تصعيدية | `governance` |
| تنفيذ أداة عالية الخطورة | تدقيق مسبق | `governance` |
| عزل وكيل صحيًا | مراجعة طارئة | `states/health` + `royal/security` |
| معاملة مالية | تدقيق مالي | `federal/treasury` |

> مرجع التفاصيل الكامل للعتبات: `royal/governance` (يُوسَّع في P8).

---

## 5. ضمانات التدقيق

1. **Inseparable from events:** لا يُغلق حدث `task.completed` إلا بإنشاء `audit_entry` في نفس المعاملة.
2. **Non-repudiation:** سجلات التدقيق append-only، لا تُحذف. التصحيح يكون بتدقيق لاحق يعلق على السجل الأصلي.
3. **Review queue:** السجلات بحالة `flagged` تدخل طابور مراجعة الحوكمة (`reviews`).
4. **Time-bound:** التدقيق القياسي يجب أن يتم خلال 24 ساعة من الحدث، وإلا يُرفع للتصعيد.

---

## 6. ربط قاعدة البيانات

| الحقل | عمود Supabase | الجدول |
|---|---|---|
| `id` | `id` | `audit_entries` |
| `event_id` | `event_id` | `audit_entries` |
| `task_id` | `task_id` | `audit_entries` |
| `reviewer` | `reviewer` | `audit_entries` |
| `verdict` | `verdict` | `audit_entries` |
| المراجعات المعلّقة | — | `reviews` |

> يوجد حاليًا 10 سلاسل تدقيق و7 حراس ملكيين (وفق `royal/stubs/guard_check.py`). المواصفة تُنظّم التوسع دون تدمير السلاسل القائمة.

---

## 7. اختبار القبول

```bash
test -f royal/specs/audit_trail.md && grep -q "end-to-end traceability" royal/specs/audit_trail.md \
  && echo "audit_trail: OK" || echo "audit_trail: FAIL"
```

تعريف الإنجاز: سلسلة تدقيق كاملة من المهمة إلى الذاكرة + عتبات مراجعة + ضمانات append-only.
