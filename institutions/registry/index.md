# سجل المؤسسات — Institutions Registry

> الفهرس الرسمي لكل مؤسسات الدولة. مرتبط بجدول `institutions` في Supabase.

## نظرة عامة

| البيان | القيمة |
|---|---|
| إجمالي المؤسسات | 8 |
| المؤسسات النشطة | 8 |
| المؤسسات المغلقة | 0 |

## سجل المؤسسات

| # | المعرف | الاسم | النوع | الولاية | الحالة | تاريخ التأسيس |
|---:|---|---|---|---|---|---|
| 1 | `federal-executive` | السلطة التنفيذية الفدرالية | executive | federal | active | 2026-08-15 |
| 2 | `federal-legislative` | المجلس التشريعي الفدرالي | legislative | federal | active | 2026-08-15 |
| 3 | `federal-judicial` | المحكمة العليا الفدرالية | judicial | federal | active | 2026-08-15 |
| 4 | `federal-treasury` | الخزانة الفدرالية | treasury | federal | active | 2026-08-15 |
| 5 | `federal-oversight` | هيئة الرقابة العليا | oversight | federal | active | 2026-08-15 |
| 6 | `royal-guard` | الحرس الملكي | security | federal | active | 2026-08-15 |
| 7 | `school-federal` | المدرسة الفدرالية | education | federal | active | 2026-08-15 |
| 8 | `university-federal` | الجامعة الفدرالية | education | federal | active | 2026-08-15 |

## التصنيف حسب النوع

| النوع | العدد | المؤسسات |
|---|---:|---|
| executive | 1 | السلطة التنفيذية |
| legislative | 1 | المجلس التشريعي |
| judicial | 1 | المحكمة العليا |
| treasury | 1 | الخزانة |
| oversight | 1 | هيئة الرقابة |
| security | 1 | الحرس الملكي |
| education | 2 | المدرسة + الجامعة |

## الأقسام الفرعية للمؤسسات

| القسم | الدور | الحالة |
|---|---|---|
| [`bank/`](../bank/NUCLEUS.md) | البنك الفدرالي | stub |
| [`university/`](../university/NUCLEUS.md) | الجامعة | stub |
| [`court/`](../court/NUCLEUS.md) | المحكمة | stub |
| [`factory/`](../factory/NUCLEUS.md) | مصنع الأدوات | stub |
| [`registry/`](registry/NUCLEUS.md) | السجل (هذا الملف) | active |

## قاعدة البيانات

- **الجدول:** `institutions` (8 صفوف)
- **الأعمدة:** `institution_id`, `name`, `type`, `state`, `status`, `head_agent_id`, `budget`, `established_at`, `closed_at`, `metadata`
- **Supabase Project:** `mqcfmwtdaymrmwvthqyw`

## الخطوات التالية

- [ ] تعيين وكلاء لرئاسة كل مؤسسة (`head_agent_id`)
- [ ] تخصيص ميزانيات (`budget`)
- [ ] إنشاء مؤسسات ولائية (خارج النطاق الفدرالي)
- [ ] تفعيل مصنع الأدوات (`tool_generation_queue`)
