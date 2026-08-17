# فهرس الأحداث — Events Index

> الفهرس الرسمي لسجل أحداث الدولة. مرتبط بجدول `event_store` في Supabase.

## الهدف
الفهرس الرسمي لسجل أحداث الدولة ونظرة عامة على حجمه وأنواعه، فلا يقع حدث في الدولة بلا سجل يُراجَع.

## نظرة عامة

| البيان | القيمة |
|---|---|
| إجمالي الأحداث | 157 |
| أقدم حدث | 2026-08-15 04:07:55 |
| أحدث حدث | 2026-08-15 05:49:12 |
| المهام | 1 |

## توزيع الأحداث حسب الموضوع

| الموضوع | العدد | النسبة |
|---|---:|---:|
| `amos_federation.health.check_completed` | 151 | 96.2% |
| `amos_federation.health.treatment_completed` | 3 | 1.9% |
| `amos_federation.tool.executed` | 1 | 0.6% |
| `amos_federation.health.agent_isolated` | 1 | 0.6% |

## المهام (tasks)

| المعرف | النوع | الوصف | الحالة | الأولوية | المجال |
|---|---|---|---|---|---|
| `task-492d0c0f120e` | event_chain_test | مهمة اختبار المرحلة 2 | assigned | normal | general |

## الأقسام الفرعية

| القسم | الدور | الحالة |
|---|---|---|
| [`engine/`](../engine/NUCLEUS.md) | محرك التنفيذ | stub |
| [`scheduler/`](../scheduler/NUCLEUS.md) | المجدول | stub |
| [`events/`](NUCLEUS.md) | الأحداث (هذا الملف) | active |
| [`tasks/`](../tasks/NUCLEUS.md) | المهام | stub |

## قاعدة البيانات

- **الجداول:** `event_store` (157), `tasks` (1)
- **Supabase Project:** `mqcfmwtdaymrmwvthqyw`

## الخطوات التالية

- [ ] تفعيل Event Sourcing الكامل
- [ ] ربط الأحداث بآلية التدقيق
- [ ] إنشاء خط زمني تفاعلي
- [ ] تفعيل دورة حياة المهام الكاملة
