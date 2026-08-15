# مواصفة دورة حياة المهمة — Task Lifecycle Specification

> **المجال:** runtime
> **المرحلة:** P5 — حلقة التشغيل الأساسية
> **الحالة:** مواصفة (Spec) — جاهزة للتنفيذ
> **تاريخ الإنشاء:** 2026-08-15
> **المادة الدستورية:** 009 (الشفافية والمراجعة المستمرة)
> **المواءمة:** `tasks` Supabase table + `docs/contracts/schemas/task.schema.json`

---

## 1. الهدف

تعريف الحالات والانتقالات التي تمر بها أي مهمة (Task) داخل محرك التشغيل، من لحظة إنشائها حتى انتهائها (نجاحًا أو فشلًا)، مع ضمان أن كل انتقال قابل للمراجعة والتدقيق.

> هذه هي "نبضة قلب" الدولة: المهمة هي الوحدة الأساسية للعمل، ودورة حياتها تحكم تدفّق: مهمة ← وكيل ← أداة ← حدث ← تدقيق ← ذاكرة.

---

## 2. الحالات (States)

توسيع لحقل `status` المعرف في `task.schema.json`:

| الحالة | المعنى | قابلية الخروج |
|---|---|---|
| `pending` | المهمة منشأة، غير مُسندة بعد | → `assigned`, `cancelled` |
| `assigned` | سُندت إلى وكيل، لم يبدأ التنفيذ | → `in_progress`, `cancelled` |
| `in_progress` | الوكيل ينفذ المهمة الآن | → `completed`, `failed`, `pending` (إعادة جدولة) |
| `completed` | انتهت بنجاح، النتيجة محفوظة | → (نهائية) |
| `failed` | انتهت بفشل، السبب مُسجّل | → `pending` (إعادة محاولة), (نهائية) |
| `cancelled` | أُلغيت بطلب من الحوكمة أو المالك | → (نهائية) |

> القاعدة الذهبية: لا يوجد انتقال إلى حالة سابقة إلا عبر `pending` (إعادة جدولة/إعادة محاولة)، ويُسجَّل كل انتقال كحدث في `event_store`.

---

## 3. الانتقالات (Transitions)

مخطط الانتقال الحالة (State Transition):

```
        ┌─────────┐   assign    ┌──────────┐   start   ┌────────────┐
 create→ │ pending │ ─────────→ │ assigned │ ────────→ │ in_progress │
        └─────────┘             └──────────┘           └────────────┘
           │   │                     │ cancel              │  │  │
        cancel  │                  ┌───┘            complete │  │ fail
           │    │                  ▼                          ▼  ▼
        ┌──▼────▼──┐        ┌──────────┐            ┌──────────┐ ┌────────┐
        │ cancelled │        │ cancelled │            │ completed │ │ failed │
        └───────────┘        └──────────┘            └──────────┘ └────────┘
                                                                  │ retry
                                                                  └──→ pending
```

قواعد الانتقال:

1. **`create`** — ينشئ المهمة بحالة `pending`، يُسجّل حدث `amos_federation.task.created`.
2. **`assign`** — يربط `assigned_agent`، ينتقل إلى `assigned`، حدث `amos_federation.task.assigned`.
3. **`start`** — ينتقل إلى `in_progress`، حدث `amos_federation.task.started`.
4. **`complete`** — يكتب `result`، ينتقل إلى `completed`، حدث `amos_federation.task.completed`.
5. **`fail`** — يكتب `error` في `result`، ينتقل إلى `failed`، حدث `amos_federation.task.failed`.
6. **`retry`** — يعيد المهمة من `failed` إلى `pending` مع زيادة عدّاد المحاولات، حدث `amos_federation.task.retried`.
7. **`cancel`** — انتقال مباح من `pending`/`assigned`/`in_progress` إلى `cancelled`، حدث `amos_federation.task.cancelled`.

---

## 4. البنية القانونية لكل انتقال

كل انتقال هو معاملة (Transaction) تحمل:

- `task_id` — معرّف المهمة.
- `from_status` → `to_status`.
- `agent_id` — الوكيل المنفّذ (إن وُجد).
- `event_id` — معرّف الحدث المرتبط في `event_store`.
- `timestamp` — وقت الانتقال (UTC).
- `triggered_by` — `orchestrator` | `agent` | `governance` | `owner`.

> لا انتقال بدون حدث: التزامًا بالمادة 009 (الشفافية) والمادة الخاصة بالتدقيق (انظر `royal/specs/audit_trail.md`).

---

## 5. عدّادات وقيود

| العنصر | القيمة الافتراضية | الحد الأقصى |
|---|---|---|
| محاولات إعادة التنفيذ (`retry_count`) | 0 | 3 |
| مهلة التنفيذ (`timeout`) | 300 ثانية | 1800 ثانية |
| أولوية الجدولة (`priority`) | `normal` | `critical` |

عند بلوغ `retry_count` الحد الأقصى، تنتقل المهمة إلى `failed` نهائيًا وتُرفع إلى `royal/governance` للمراجعة.

---

## 6. ربط قاعدة البيانات

| الحقل | عمود Supabase | الجدول |
|---|---|---|
| `id` | `id` | `tasks` |
| `status` | `status` | `tasks` |
| `assigned_agent` | `assigned_agent` | `tasks` |
| `priority` | `priority` | `tasks` |
| `result` | `result` (JSONB) | `tasks` |
| `created_at` / `updated_at` | `created_at` / `updated_at` | `tasks` |
| الانتقالات | — | `event_store` |

> لا ترحيلات مدمرة: تُضاف الأعمدة الجديدة عبر `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` فقط.

---

## 7. اختبار القبول (Acceptance Test)

```bash
# تحقق نصي أن المواصفة موجودة ومكتملة
test -f runtime/specs/task_lifecycle.md && grep -q "in_progress" runtime/specs/task_lifecycle.md \
  && echo "task_lifecycle: OK" || echo "task_lifecycle: FAIL"
```

تعريف الإنجاز: مخطط انتقالات مكتمل + قواعد مرتبطة بـ `event_store` + ربط بأعمدة `tasks`.
