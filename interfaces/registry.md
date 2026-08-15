# سجل الواجهات — Interfaces Registry

> الفهرس الرسمي لنقاط دخول الدولة. مرتبط بجدول `interface_registry` في Supabase.

## نظرة عامة

| البيان | القيمة |
|---|---|
| إجمالي الواجهات | 3 |
| الواجهات المسجلة | api, cli, web |
| جدول Supabase | `interface_registry` |
| حالة الربط | مُفعّل (P7) |

> جدول `interface_registry` مُفعّل الآن (المرحلة 7) — كل واجهة جديدة تُسجَّل تلقائيًا.

## الأقسام الفرعية

| القسم | الدور | الحالة |
|---|---|---|
| [`web/`](web/NUCLEUS.md) | لوحة المالك على الويب | stub |
| [`api/`](api/NUCLEUS.md) | عقد API | stub |
| [`cli/`](cli/NUCLEUS.md) | واجهة سطر الأوامر | stub |

## قاعدة البيانات

- **الجدول:** `interface_registry` (0 صفوف)
- **Supabase Project:** `mqcfmwtdaymrmwvthqyw`

## الخطوات التالية

- [x] تعريف عقد API (المرحلة 7) — `api/contract.md`
- [x] تصميم لوحة المالك على الويب (المرحلة 7) — `web/owner_dashboard.md`
- [x] إنشاء خريطة أوامر CLI (المرحلة 7) — `cli/command_map.md`
- [x] ربط الواجهات بـ Supabase (المرحلة 7) — هذا الملف

## تدفق تسجيل واجهة جديدة

1. **اكتشاف** — تعريف واجهة جديدة (api/cli/web).
2. **التسجيل** — إدراجها في `interface_registry` مع المعرّف والنوع ونقطة الدخول.
3. **الربط** — ربط الواجهة بالأدوات/المجالات المعنية.
4. **التفعيل** — إصدار حدث `amos_federation.interface.registered`.
5. **الرصد** — تتبّع الاستدعاءات في `event_store`.
