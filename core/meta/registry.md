# سجل الميثاق — Meta Registry

> الفهرس الشامل لقاعدة بيانات الدولة. كل جدول، كل صف، كل علاقة.

## الهدف
الفهرس الشامل لقاعدة بيانات الدولة — كل جدول وصف وعلاقة — ليُعرف موضع كل حقيقة قبل الاستعلام عنها.

## نظرة عامة على قاعدة البيانات

- **المشروع:** `mqcfmwtdaymrmwvthqyw` (Supabase)
- **PostgreSQL:** 17
- **إجمالي الجداول:** 23
- **إجمالي الصفوف:** 545+

## فهرس الجداول

| # | الجدول | الصفوف | المجال المرتبط | الوصف |
|---:|---|---:|---|---|
| 1 | `agent_population` | 342 | agents | سكان الدولة (الوكلاء) |
| 2 | `event_store` | 157 | runtime, core/memory | سجل الأحداث (Event Store) |
| 3 | `audit_entries` | 10 | royal, ops | سجل التدقيق (سلسلة هاش) |
| 4 | `tools` | 10 | tools | سجل الأدوات المعتمدة |
| 5 | `royal_guards` | 7 | royal | الحرس الملكي |
| 6 | `institutions` | 8 | institutions | المؤسسات الفدرالية |
| 7 | `school_results` | 6 | agents/evolution | نتائج اختبارات المدرسة |
| 8 | `memories` | 2 | core/memory | الذاكرة التشغيلية |
| 9 | `experiences` | 1 | core/memory | الخبرات المستخلصة |
| 10 | `model_cache` | 2 | tools/models | ذاكرة النماذج المؤقتة |
| 11 | `model_cost_log` | 2 | tools/models | سجل تكاليف النماذج |
| 12 | `king_decrees` | 1 | royal | المراسيم الملكية |
| 13 | `tasks` | 1 | runtime | المهام |
| 14 | `agents` | 0 | agents | جدول الوكلاء (النسخة المنطقية) |
| 15 | `reviews` | 0 | royal | المراجعات |
| 16 | `interface_registry` | 0 | interfaces | سجل الواجهات |
| 17 | `tool_generation_queue` | 0 | tools/factory | طابور توليد الأدوات |
| 18 | `agent_training_queue` | 0 | agents/evolution | طابور تدريب الوكلاء |
| 19 | `treasury_transactions` | 0 | federal/treasury | معاملات الخزانة |
| 20 | `treasury_budgets` | 0 | federal/treasury | ميزانيات الخزانة |
| 21 | `treasury_reports` | 0 | federal/treasury | تقارير الخزانة |
| 22 | `agent_health_checks` | 0 | states/health | فحوصات صحة الوكلاء |
| 23 | `agent_isolations` | 0 | royal/security | حالات العزل |
| 24 | `agent_treatments` | 0 | states/health | علاجات الوكلاء |

## توزيع البيانات حسب المجال

| المجال | الجداول | الصفوف |
|---|---:|---:|
| agents | 4 | 349 |
| runtime | 2 | 158 |
| royal | 4 | 18 |
| tools | 3 | 12 |
| core/memory | 3 | 160 |
| institutions | 1 | 8 |
| federal/treasury | 3 | 0 |
| states/health | 3 | 0 |
| interfaces | 1 | 0 |

## الخطوات التالية

- [ ] ربط كل جدول بمجاله في الكود
- [ ] إنشاء استعلامات نموذجية لكل جدول
- [ ] تفعيل المراقبة المستمرة لحجم البيانات
