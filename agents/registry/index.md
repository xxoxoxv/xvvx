# سجل الوكلاء — Agents Registry

> الفهرس الرسمي لسكان الدولة (الوكلاء). مرتبط بجدول `agent_population` في Supabase.

## الهدف
الفهرس الرسمي لسكان الدولة من الوكلاء، مرتبطًا بجدول `agent_population`، ليكون مصدرًا واحدًا لمن يسكن الدولة وبأي صفة.

## نظرة عامة

| البيان | القيمة |
|---|---|
| إجمالي الوكلاء | 342 |
| نشطون | 3 |
| في التدريب | 1 |
| مسجلون (بانتظار التدريب) | 337 |

## توزيع الحالات

| الحالة | العدد | النسبة |
|---|---:|---:|
| `registered` | 337 | 98.5% |
| `active` | 3 | 0.9% |
| `training` | 1 | 0.3% |

## الأعمدة الرئيسية

| العمود | الوصف |
|---|---|
| `agent_id` | المعرف الفريد للوكيل |
| `name` | اسم الوكيل |
| `role` | الدور الوظيفي |
| `category` | التصنيف |
| `state` | الحالة (registered/active/training) |
| `permissions` | الصلاحيات |
| `allowed_tools` | الأدوات المسموح بها |
| `token_budget` | ميزانية التوكنز |
| `tokens_used` | التوكنز المستهلكة |
| `school_score` | درجة المدرسة |
| `specialization` | التخصص |
| `graduated_at` | تاريخ التخرج |

## الأقسام الفرعية

| القسم | الدور | الحالة |
|---|---|---|
| [`identities/`](../identities/NUCLEUS.md) | هويات الوكلاء | stub |
| [`capabilities/`](../capabilities/NUCLEUS.md) | قدرات الوكلاء | stub |
| [`lifecycle/`](../lifecycle/NUCLEUS.md) | دورة حياة الوكيل | stub |
| [`evolution/`](../evolution/NUCLEUS.md) | تطور الوكلاء | stub |
| [`registry/`](NUCLEUS.md) | السجل (هذا الملف) | active |

## جداول مرتبطة

| الجدول | الصفوف | الوصف |
|---|---:|---|
| `agent_population` | 342 | السكان الكاملون |
| `agents` | 0 | الوكلاء المنطقيون |
| `school_results` | 6 | نتائج اختبارات المدرسة |
| `agent_training_queue` | 0 | طابور التدريب |

## قاعدة البيانات

- **Supabase Project:** `mqcfmwtdaymrmwvthqyw`

## الخطوات التالية

- [ ] تدريب الوكلاء المسجلين (337 وكيل)
- [ ] تصنيف الوكلاء حسب الدور والتخصص
- [ ] تفعيل آلية الترقية (registered → training → active)
- [ ] ربط الوكلاء بالمؤسسات
- [ ] تفعيل طابور التدريب (`agent_training_queue`)
