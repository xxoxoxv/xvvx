# مواصفة تسجيل الأحداث — Event Logging Specification

> **المجال:** runtime
> **المرحلة:** P5 — حلقة التشغيل الأساسية
> **الحالة:** مواصفة (Spec) — جاهزة للتنفيذ
> **تاريخ الإنشاء:** 2026-08-15
> **المادة الدستورية:** 009 (الشفافية والمراجعة المستمرة)
> **المواءمة:** `event_store` Supabase table + `docs/contracts/schemas/event.schema.json`

---

## 1. الهدف

تعريف كيفية تسجيل كل فعل يحدث داخل الدولة كحدث (Event) غير قابل للحذف (append-only)، بحيث يُعاد بناء أي حالة سابقة من سجل الأحداث وحده (Event Sourcing).

> الذاكرة المؤسسية للدولة هي سجل أحداثها. لا فعل بلا أثر.

---

## 2. بنية الحدث

كل حدث في `event_store` يلتزم بـ `event.schema.json` ويحتوي:

| الحقل | النوع | الوصف |
|---|---|---|
| `id` | string | معرّف فريد (مثل `evt-acfeaeee`) |
| `type` | string | نمط مُسمّى: `amos_federation.<domain>.<action>` |
| `aggregate_id` | string | معرّف الكائن الذي ينتمي إليه الحدث (مهمة/وكيل/أداة) |
| `payload` | JSONB | بيانات الحدث الفعلية |
| `actor` | string | من نفّذ الفعل (`agent_id` | `orchestrator` | `owner`) |
| `tenant_id` | string | عزل متعدد المستأجرين |
| `timestamp` | datetime (UTC) | وقت الحدث |
| `causation_id` | string? | معرّف الحدث الذي سببه (للتتبع السببي) |
| `correlation_id` | string? | معرّف السلسلة الكاملة (للمهمة الواحدة) |

> `causation_id` و`correlation_id` يجعلان سلسلة "مهمة ← وكيل ← أداة ← حدث ← تدقيق" قابلة لإعادة التتبع.

---

## 3. نمط التسمية — Event Type Naming

الصيغة الإلزامية:

```
amos_federation.<domain>.<action>[_<subject>]
```

أمثلة (موائمة مع الأحداث الموجودة في `task_event_check.py`):

| نوع الحدث | المعنى | المجال |
|---|---|---|
| `amos_federation.task.created` | إنشاء مهمة | runtime |
| `amos_federation.task.assigned` | إسناد مهمة | runtime |
| `amos_federation.task.started` | بدء تنفيذ | runtime |
| `amos_federation.task.completed` | إكمال مهمة | runtime |
| `amos_federation.task.failed` | فشل مهمة | runtime |
| `amos_federation.tool.executed` | تنفيذ أداة | tools |
| `amos_federation.agent.activated` | تفعيل وكيل | agents |
| `amos_federation.health.agent_isolated` | عزل وكيل صحيًا | states/health |
| `amos_federation.health.treatment_completed` | إكمال علاج | states/health |
| `amos_federation.royal.audit_logged` | تسجيل تدقيق | royal |

> قاعدة: `<domain>` يطابق أحد مجالات الـ 12. لا أفعال مخصصة خارج النمط.

---

## 4. ضمانات التسجيل (Logging Guarantees)

1. **Append-only:** لا UPDATE ولا DELETE على `event_store`. التصحيح يتم بحدث معكوس (compensating event) وليس بالحذف.
2. **Atomic with state change:** كتابة الحدث وكتابة الحالة الجديدة تتم في معاملة واحدة (Supabase transaction)، فلا توجد حالة بلا حدث ولا حدث بلا حالة.
3. **Ordered:** الأحداث مرتبة زمنيًا بـ `timestamp` + تسلسل في قاعدة البيانات.
4. **Causal chain:** كل حدث يحمل `causation_id` للحدث الأب، و`correlation_id` للمهمة الجذرية.

---

## 5. سلسلة الحدث للمهمة الواحدة

التسلسل القياسي لأحداث المهمة (correlation chain):

```
task.created ─→ task.assigned ─→ task.started ─→ tool.executed*
                                            └→ task.completed | task.failed
                                                              └→ (retry) task.retried ─→ task.started ...
```

كلها تتشارك `correlation_id` واحد = `task.id`.

---

## 6. ربط قاعدة البيانات

| الحقل | عمود Supabase | الجدول |
|---|---|---|
| `id` | `id` | `event_store` |
| `type` | `type` | `event_store` |
| `payload` | `payload` (JSONB) | `event_store` |
| `timestamp` | `timestamp` | `event_store` |
| `aggregate_id` | `aggregate_id` | `event_store` |

الأعمدة الجديدة المطلوبة (تُضاف دون تدمير): `causation_id`, `correlation_id`, `actor`, `tenant_id`.

> توجد حاليًا 157 حدثًا في `event_store` (وفق `task_event_check.py`). المواصفة لا تتطلب ترحيل البيانات القديمة، بل تُكمّلها بالحقول الجديدة بقيم `NULL` رجعية.

---

## 7. اختبار القبول

```bash
test -f runtime/specs/event_logging.md && grep -q "correlation_id" runtime/specs/event_logging.md \
  && echo "event_logging: OK" || echo "event_logging: FAIL"
```

تعريف الإنجاز: بنية حدث مكتملة + نمط تسمية + ضمانات append-only + سلسلة سببية موثقة.
