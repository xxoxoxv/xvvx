# EXECUTION_PLAN.md — خطة التنفيذ المرحلية

> **هذه هي خارطة الطريق الحية للدولة.** كل تقدم يُحدّث هنا. اقرأها لتعرف ما تم وما بقي.

## كيف تقرأ هذه الخطة

1. ابدأ من `ARCHITECTURE.md` لفهم البنية
2. اقرأ هذه الخطة لمعرفة المرحلة الحالية وما يجب عمله
3. اذهب إلى مجالك واقرأ `NUCLEUS.md` للتفاصيل
4. عند إنهاء أي مهمة، حدّث هذه الخطة في نفس الـ commit

## مفتاح الحالات

| الحالة | المعنى |
|---|---|
| DONE | مكتمل ودفع إلى main |
| DOING | قيد التنفيذ الآن |
| NEXT | جاهز للبدء |
| TODO | لم يبدأ بعد |
| BLOCKED | محظور |

---

## التقدم الإجمالي

| المجال | مكتمل | الإجمالي | الحالة |
|---|---:|---:|---|
| المراحل | 2 | 9 | DOING |
| المجالات المغطاة | 12 | 12 | DONE |
| النوى المنشأة | 96 | 96 | DONE |
| جداول قاعدة البيانات | 23 | 23 | DONE |
| اختبارات الدخان | 0 | 12 | TODO |
| السجلات (Registries) | 12 | 12 | DONE |

---

## مصفوفة المجال × المرحلة

| المجال | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 |
|---|---|---|---|---|---|---|---|---|---|---|
| core | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| royal | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| federal | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| states | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| institutions | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| agents | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| tools | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| interfaces | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| runtime | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| docs | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| ops | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| tests | DONE | DONE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

---

## المرحلة 0 — الأساس التأسيسي (DONE)

**الهدف:** بناء الهيكل العظمي للدولة.

| المهمة | الحالة | الدليل |
|---|---|---|
| مستودع Monorepo بـ 12 مجالاً | DONE | commit `73b0c3f3` |
| 96 NUCLEUS.md لكل مجلد فرعي | DONE | commit `67378945` |
| ARCHITECTURE.md (دستور البنية) | DONE | commit `73b0c3f3` |
| README.md يوجّه لـ ARCHITECTURE.md | DONE | commit `73b0c3f3` |
| قاعدة بيانات Supabase متصلة (23 جدول) | DONE | 342 وكيل، 157 حدث |
| خطة تنفيذ مرحلية (هذا الملف) | DONE | هذا الـ commit |

---

## المرحلة 1 — سجلات الحقيقة (DONE)

**الهدف:** جعل كل مجال قابلاً للاكتشاف. إنشاء سجلات وفهارس لكل مجال.

| المجال | المهمة | الملف | الحالة |
|---|---|---|---|
| core | سجل الذاكرة والمعرفة | `core/memory/index.md` | DONE |
| core | فهرس الميثاق | `core/meta/registry.md` | DONE |
| royal | فهرس المراسيم الملكية | `royal/decrees.md` | DONE |
| federal | فهرس السلطات الثلاث | `federal/index.md` | DONE |
| states | فهرس الولايات | `states/index.md` | DONE |
| institutions | سجل المؤسسات (8 موجودة) | `institutions/registry/index.md` | DONE |
| agents | سجل الوكلاء (342 موجود) | `agents/registry/index.md` | DONE |
| tools | سجل الأدوات (10 موجودة) | `tools/registry/index.md` | DONE |
| interfaces | سجل الواجهات | `interfaces/registry.md` | DONE |
| runtime | فهرس الأحداث (157 موجودة) | `runtime/events/index.md` | DONE |
| docs | فهرس الوثائق | `docs/index.md` | DONE |
| ops | فهرس العمليات | `ops/index.md` | DONE |

**تعريف الإنجاز:** كل سجل يحتوي على قائمة كاملة مرتبطة بقاعدة البيانات حيث ينطبق.

---

## المرحلة 2 — العقود والمخططات (NEXT)

**الهدف:** تعريف "العقود" بين الأجزاء قبل التنفيذ الحقيقي.

| المجال | المهمة | الحالة |
|---|---|---|
| tools | مخطط بيانات الأدوات (مدخلات/مخرجات) | TODO |
| agents | مخطط هوية الوكيل | TODO |
| institutions | مخطط المؤسسة | TODO |
| runtime | مخطط المهمة ومخطط الحدث | TODO |
| interfaces | مخطط الواجهة | TODO |
| royal | مخطط الموافقة ومخطط التدقيق | TODO |
| federal | مخطط المعاملة المالية | TODO |
| core | مخطط الذاكرة ومخطط الخبرة | TODO |
| states | مخطط السياسة الولائية | TODO |
| ops | مخطط السجل ومخطط المقياس | TODO |
| tests | مخطط اختبار الدخان | TODO |
| docs | قالب قرار العمارة (ADR) | TODO |

**تعريف الإنجاز:** كل مخطط موثق بـ JSON Schema أو ما يعادله.

---

## المرحلة 3 — نوى عاملة

**الهدف:** كل مجال رئيسي له stub قابل للتشغيل أو التحقق.

| المجال | المهمة | الحالة |
|---|---|---|
| tests | اختبارات دخان لكل 12 مجالاً | TODO |
| runtime | هيكل مهمة + هيكل حدث | TODO |
| tools | فحص سجل الأدوات | TODO |
| agents | فحص سجل الوكلاء | TODO |
| institutions | فحص سجل المؤسسات | TODO |
| royal | فحص الحرس الملكي | TODO |
| ops | فحص سجل التدقيق | TODO |
| federal | فحص الخزانة | TODO |
| core | فحص الذاكرة | TODO |

**تعريف الإنجاز:** كل stub يُرجع نتيجة حقيقية من قاعدة البيانات.

---

## المرحلة 4 — ربط قاعدة البيانات

**الهدف:** ربط بنية المستودع بجداول Supabase.

| المجال | الجداول المرتبطة | الحالة |
|---|---|---|
| agents | `agents`, `agent_population`, `school_results` | TODO |
| tools | `tools`, `tool_generation_queue` | TODO |
| runtime | `tasks`, `event_store` | TODO |
| royal | `royal_guards`, `king_decrees`, `audit_entries`, `reviews` | TODO |
| institutions | `institutions` | TODO |
| federal | `treasury_transactions`, `treasury_budgets`, `treasury_reports` | TODO |
| interfaces | `interface_registry` | TODO |
| core | `memories`, `experiences` | TODO |
| tools/models | `model_cache`, `model_cost_log` | TODO |
| states/health | `agent_health_checks`, `agent_treatments` | TODO |
| royal/security | `agent_isolations` | TODO |

**تعريف الإنجاز:** لكل مجال: وثيقة ربط + استعلامات نموذجية + لا ترحيلات مدمرة.

---

## المرحلة 5 — حلقة التشغيل الأساسية

**الهدف:** إنشاء أول حلقة كاملة: مهمة ← وكيل ← أداة ← حدث ← تدقيق ← ذاكرة.

| المهمة | المجال | الحالة |
|---|---|---|
| دورة حياة المهمة | runtime | TODO |
| مواصفات تسجيل الأحداث | runtime | TODO |
| مواصفات مسار التدقيق | royal | TODO |
| مواصفات تحديث الذاكرة | core | TODO |
| سيناريو "تنفيذ مهمة واحدة" | runtime + agents + tools | TODO |

**تعريف الإنجاز:** حلقة كاملة موثقة وقابلة للتنفيذ. أول نبضة قلب للدولة.

---

## المرحلة 6 — تفعيل المؤسسات والولايات

**الهدف:** جعل الدولة تشبه دولة، لا مجرد مجلدات.

| المؤسسة/الولاية | التدفق | الحالة |
|---|---|---|
| institutions/bank | تدفق الخزانة | TODO |
| institutions/university | تدفق تدريب الوكلاء | TODO |
| institutions/court | تدفق المراجعة والأحكام | TODO |
| institutions/factory | تدفق توليد الأدوات | TODO |
| states/health | فحوصات الوكلاء | TODO |
| states/finance | الميزانيات الولائية | TODO |
| states/science | البحث والتقييم | TODO |
| states/law | السياسات والعقود | TODO |
| states/infrastructure | خارطة الخدمات | TODO |
| states/culture | معايير الهوية | TODO |

**تعريف الإنجاز:** كل تدفق موثق برسم بياني + خطوات + جداول مرتبطة.

---

## المرحلة 7 — الواجهات

**الهدف:** نقاط دخول قابلة للاستخدام للبشر والوكلاء.

| المجال | المهمة | الحالة |
|---|---|---|
| interfaces/api | عقد API كامل | TODO |
| interfaces/cli | خريطة الأوامر | TODO |
| interfaces/web | مخطط لوحة المالك | TODO |
| interfaces/registry | ربط السجل بـ Supabase | TODO |

**تعريف الإنجاز:** كل واجهة لها مواصفة قابلة للتنفيذ.

---

## المرحلة 8 — الحوكمة والأمن والمراقبة

**الهدف:** تقوية المملكة.

| المجال | المهمة | الحالة |
|---|---|---|
| royal/governance | عتبات الموافقة | TODO |
| royal/security | فهرس الحواجز الواقية | TODO |
| royal/security | بروتوكول العزل | TODO |
| royal/security | بروتوكول المفتاح الكهربائي | TODO |
| royal/governance | تقارير التدقيق | TODO |
| ops/observability | خطة اللوحات | TODO |
| ops/continuity | كتيب التعافي من الكوارث | TODO |

**تعريف الإنجاز:** كل بروتوكول موثق وقابل للتفعيل.

---

## المرحلة 9 — النضج والفصل المستقبلي

**الهدف:** التحضير للاستخراج المستقبلي دون تقسيم مبكر.

| المهمة | الحالة |
|---|---|
| معايير جاهزية الاستخراج (amos-runtime, amos-interfaces, ...) | TODO |
| سياسة الإصدار | TODO |
| نضج CI/الاختبارات | TODO |
| نموذج الحوكمة طويل الأمد | TODO |

**تعريف الإنجاز:** معايير واضحة ل متى وكيف يُفصل أي جزء.

---

## انضباط الـ Commit

> **كل commit تنفيذي يجب أن يحدّث `EXECUTION_PLAN.md` في نفس الـ commit.**

### تعريف الإنجاز لأي مهمة

1. الملفات منشأة/محدّثة
2. `NUCLEUS.md` ذو صلة محدّث إذا تغير النطاق
3. `EXECUTION_PLAN.md` محدّث (الحالة + الدليل)
4. إضافة سجل في `docs/implementation/PROGRESS_LOG.md`
5. اختبار دخان أو تحقق نصي
6. Commit مدفوع إلى main
7. الرد يحتوي رابط الـ commit

### قاعدة التحديث

عند إنهاء مهمة:
- غيّر الحالة من TODO → DONE في المصفوفة
- أضف سطر في PROGRESS_LOG.md
- أضف رقم الـ commit كدليل

---

## سجل التقدم (مختصر)

التاريخ الكامل في `docs/implementation/PROGRESS_LOG.md`.

| التاريخ | المرحلة | ما تم | Commit |
|---|---|---|---|
| 2026-08-15 | P0 | هيكلة Monorepo بـ 12 مجالاً | `73b0c3f3` |
| 2026-08-15 | P0 | 96 NUCLEUS.md لكل مجلد فرعي | `67378945` |
| 2026-08-15 | P0 | خطة التنفيذ المرحلية | (هذا الـ commit) |
| 2026-08-15 | P1 | سجل الذاكرة والمعرفة (core/memory/index.md) | `eb0bcd61` |
| 2026-08-15 | P1 | 11 سجل وفهرس (كل المجالات) | (هذا الـ commit) |
