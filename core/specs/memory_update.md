# مواصفة تحديث الذاكرة — Memory Update Specification

> **المجال:** core
> **المرحلة:** P5 — حلقة التشغيل الأساسية
> **الحالة:** مواصفة (Spec) — جاهزة للتنفيذ
> **تاريخ الإنشاء:** 2026-08-15
> **المادة الدستورية:** 009 (الشفافية والمراجعة المستمرة)
> **المواءمة:** `memories` + `experiences` Supabase tables + `docs/contracts/schemas/memory.schema.json`

---

## 1. الهدف

تعريف كيف تتحوّل نتائج المهام المُكتملة إلى ذاكرة (memories) وخبرة (experiences) قابلة للاسترجاع، بحيث تتعلّم الدولة من كل مهمة تنفّذها.

> الدولة التي لا تتذكر ماضيها محكوم عليها بتكراره. الذاكرة هي الفرق بين التكرار والتطور.

---

## 2. أنواع الذاكرة

| النوع | الجدول | الغرض | دورة الحياة |
|---|---|---|---|
| ذاكرة عامة (memory) | `memories` | حقائق ومعارف مستخلصة من المهام | طويلة الأمد |
| خبرة (experience) | `experiences` | سجل ما نجح وما فشل في مواقف محددة | تراكمي |

---

## 3. آلية التحديث — When & How

### متى تُحدَّث الذاكرة

تُكتب الذاكرة حصرًا عند انتقال المهمة إلى `completed` (وفق `runtime/specs/task_lifecycle.md`)، ضمن نفس معاملة إغلاق المهمة والتدقيق.

> لا ذاكرة من مهمة لم تكتمل. هذا يمنع تلوث الذاكرة بنتائج المهام الفاشلة.

### كيف تُكتب الذاكرة

خطوات التحديث:

1. **Extract** — يستخلص المحرك "الدروس" من `task.result` (ما الذي عمل؟ ما الذي فشل؟).
2. **Classify** — يُصنَّف الدرس: حقيقة جديدة (memory) أم خبرة (experience).
3. **Link** — يُربط بالحدث (`event_id`) والتدقيق (`audit_entry_id`) والمهمة (`task_id`).
4. **Persist** — يُكتب في `memories` أو `experiences`.
5. **Emit** — يُصدِر حدث `amos_federation.core.memory_written`.

---

## 4. بنية سجل الذاكرة

| الحقل | النوع | الوصف |
|---|---|---|
| `id` | string | معرّف الذاكرة |
| `task_id` | string | المهمة التي ولّدتها (FK → `tasks.id`) |
| `event_id` | string | الحدث المرتبط (FK → `event_store.id`) |
| `audit_entry_id` | string | التدقيق المرتبط (FK → `audit_entries.id`) |
| `type` | enum | `fact` \| `lesson` \| `preference` \| `experience` |
| `content` | text | محتوى الذاكرة (لغة طبيعية) |
| `domain` | string | المجال المرتبط |
| `confidence` | float | ثقة 0.0–1.0 (تزداد بالتكرار) |
| `created_at` | datetime (UTC) | وقت الكتابة |

> `confidence` يرتفع عندما يُؤكَّد الدرس عبر مهام متعددة (تراكم الخبرة).

---

## 5. ضمانات الذاكرة

1. **Provenance-required:** لا تُكتب ذاكرة بلا `task_id` + `event_id` + `audit_entry_id`. كل ذاكرة لها أصل قابل للتتبع.
2. **Immutable origin:** الذكريات الأصلية append-only. التحديث يُنشئ ذاكرة جديدة بمرجع للأصلية، لا يعدّلها.
3. **Decay policy:** الذكريات منخفضة `confidence` وغير المسترجعة لمدة 90 يومًا تُعلَّم `stale` (لا تُحذف، تُتجاوز في الاسترجاع).
4. **No hallucination:** الذاكرة تُستخلص من `task.result` الفعلي فقط، لا تولّد من لا شيء.

---

## 6. سلسلة الاسترجاع (Recall Chain)

عند بدء مهمة جديدة، يسترجع المحرك الذكريات ذات الصلة:

```
new_task.domain ──→ query memories WHERE domain = ? AND confidence > 0.3
                              │
                              ▼
                   results injected into task.plan as context
```

> هذا يحقق حلقة التعلّم: المهمة السابقة ← ذاكرة ← سياق للمهمة التالية.

---

## 7. ربط قاعدة البيانات

| الحقل | عمود Supabase | الجدول |
|---|---|---|
| `id` | `id` | `memories` |
| `content` | `content` | `memories` |
| `task_id` | `task_id` | `memories` |
| `domain` | `domain` | `memories` |
| الخبرات | — | `experiences` |

> يوجد حاليًا 2 ذاكرة + 1 خبرة (وفق `core/stubs/memory_check.py`). المواصفة تضمن أن النمو يبقى قابلًا للتتبع.

---

## 8. اختبار القبول

```bash
test -f core/specs/memory_update.md && grep -q "Provenance-required" core/specs/memory_update.md \
  && echo "memory_update: OK" || echo "memory_update: FAIL"
```

تعريف الإنجاز: آلية تحديث مرتبطة بـ `task.completed` + بنية ذاكرة بأصل قابل للتتبع + سياسة اضمحلال + حلقة استرجاع.
