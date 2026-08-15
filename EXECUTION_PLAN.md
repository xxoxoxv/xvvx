# EXECUTION_PLAN.md — خطة التنفيذ المرحلية

> ## ⚠️ إشعار سيادي — 2026-08-16
>
> **هذه الخطة (P0–P9) لم تعد خطة السجل.** قياسها لـ«الإنجاز» كان يعتمد على وجود الملفات، لا على إثبات القدرات.
> تدقيق الحقيقة الآلي (E0) أظهر: **0 من 12 إقليمًا** بحالة `PROVEN`، و**129 مخالفة تنفيذ**، و**628 مخالفة هوية**.
>
> خطة السجل الجديدة: [`docs/audit/PHASE_E_ROADMAP.md`](docs/audit/PHASE_E_ROADMAP.md) — عصر التنفيذ (E0–E24).
> المبدأ الملزم: [`docs/governance/WORKING_PRINCIPLE.md`](docs/governance/WORKING_PRINCIPLE.md).
> الحقيقة المقاسة: [`docs/audit/TRUTH_MATRIX.md`](docs/audit/TRUTH_MATRIX.md).
>
> **يُحتفظ بما يلي كسجل تاريخي فقط.** كل حالة `DONE` أدناه تُقرأ على أنها `DESIGNED` أو `SPECIFIED` حتى يثبت التدقيق غير ذلك.

## الهدف
حفظ خطة التنفيذ الأولى (P0–P9) كسجل تاريخي بعد أن حلّت محلها خطة Phase E. تُقرأ للمرجع لا للعمل — قياسها للإنجاز كان وجود الملفات لا إثبات القدرة.

---

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
| المراحل | 9 | 9 | DONE |
| المجالات المغطاة | 12 | 12 | DONE |
| النوى المنشأة | 105 | 105 | DONE |
| جداول قاعدة البيانات | 23 | 23 | DONE |
| اختبارات الدخان | 12 | 12 | DONE |
| تغطية الاختبارات | 80% | 87.8% | DONE |
| السجلات (Registries) | 12 | 12 | DONE |

---

## مصفوفة المجال × المرحلة

| المجال | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 |
|---|---|---|---|---|---|---|---|---|---|---|
| core | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | TODO |
| royal | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | DONE | TODO |
| federal | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | TODO | TODO |
| states | DONE | DONE | DONE | DONE | DONE | TODO | DONE | TODO | TODO | TODO |
| institutions | DONE | DONE | DONE | DONE | DONE | TODO | DONE | TODO | TODO | TODO |
| agents | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | TODO |
| tools | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | TODO |
| interfaces | DONE | DONE | DONE | DONE | DONE | TODO | DONE | TODO | TODO | TODO |
| runtime | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | TODO |
| docs | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | DONE | DONE |
| ops | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | DONE | TODO |
| tests | DONE | DONE | DONE | DONE | DONE | DONE | TODO | TODO | TODO | TODO |

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

## المرحلة 2 — العقود والمخططات (DONE)

**الهدف:** تعريف "العقود" بين الأجزاء قبل التنفيذ الحقيقي.

| المجال | المهمة | الحالة |
|---|---|---|
| tools | مخطط بيانات الأدوات (مدخلات/مخرجات) | DONE |
| agents | مخطط هوية الوكيل | DONE |
| institutions | مخطط المؤسسة | DONE |
| runtime | مخطط المهمة ومخطط الحدث | DONE |
| interfaces | مخطط الواجهة | DONE |
| royal | مخطط الموافقة ومخطط التدقيق | DONE |
| federal | مخطط المعاملة المالية | DONE |
| core | مخطط الذاكرة ومخطط الخبرة | DONE |
| states | مخطط السياسة الولائية | DONE |
| ops | مخطط السجل ومخطط المقياس | DONE |
| tests | مخطط اختبار الدخان | DONE |
| docs | قالب قرار العمارة (ADR) | DONE |

**تعريف الإنجاز:** كل مخطط موثق بـ JSON Schema أو ما يعادله. ✓ مكتمل — 12 مخطط + قالب ADR

---

## المرحلة 3 — نوى عاملة (DONE)

**الهدف:** كل مجال رئيسي له stub قابل للتشغيل أو التحقق.

| المجال | المهمة | الحالة |
|---|---|---|
| tests | اختبارات دخان لكل 12 مجالاً | DONE |
| runtime | هيكل مهمة + هيكل حدث | DONE |
| tools | فحص سجل الأدوات | DONE |
| agents | فحص سجل الوكلاء | DONE |
| institutions | فحص سجل المؤسسات | DONE |
| royal | فحص الحرس الملكي | DONE |
| ops | فحص سجل التدقيق | DONE |
| federal | فحص الخزانة | DONE |
| core | فحص الذاكرة | DONE |

**تعريف الإنجاز:** كل stub يُرجع نتيجة حقيقية من قاعدة البيانات. ✓ مكتمل — 11/11 stubs تُرجع بيانات حقيقية، اختبارات دخان 11/11 PASS

---

## المرحلة 4 — ربط قاعدة البيانات (DONE)

**الهدف:** ربط بنية المستودع بجداول Supabase.

| المجال | الجداول المرتبطة | الحالة |
|---|---|---|
| agents | `agents`, `agent_population`, `school_results` | DONE |
| tools | `tools`, `tool_generation_queue` | DONE |
| runtime | `tasks`, `event_store` | DONE |
| royal | `royal_guards`, `king_decrees`, `audit_entries`, `reviews` | DONE |
| institutions | `institutions` | DONE |
| federal | `treasury_transactions`, `treasury_budgets`, `treasury_reports` | DONE |
| interfaces | `interface_registry` | DONE |
| core | `memories`, `experiences` | DONE |
| tools/models | `model_cache`, `model_cost_log` | DONE |
| states/health | `agent_health_checks`, `agent_treatments` | DONE |
| royal/security | `agent_isolations` | DONE |

**تعريف الإنجاز:** لكل مجال: وثيقة ربط + استعلامات نموذجية + لا ترحيلات مدمرة. ✓ مكتمل — 11 وثيقة ربط + ملخص، 23+ جدول، 0 ترحيلات مدمرة

---

## المرحلة 5 — حلقة التشغيل الأساسية (DONE)

**الهدف:** إنشاء أول حلقة كاملة: مهمة ← وكيل ← أداة ← حدث ← تدقيق ← ذاكرة.

| المهمة | المجال | الحالة |
|---|---|---|
| دورة حياة المهمة | runtime | DONE |
| مواصفات تسجيل الأحداث | runtime | DONE |
| مواصفات مسار التدقيق | royal | DONE |
| مواصفات تحديث الذاكرة | core | DONE |
| سيناريو "تنفيذ مهمة واحدة" | runtime + agents + tools | DONE |

**تعريف الإنجاز:** حلقة كاملة موثقة وقابلة للتنفيذ. أول نبضة قلب للدولة.

---

## المرحلة 6 — تفعيل المؤسسات والولايات (DONE)

**الهدف:** جعل الدولة تشبه دولة، لا مجرد مجلدات.

| المؤسسة/الولاية | التدفق | الحالة |
|---|---|---|
| institutions/bank | تدفق الخزانة | DONE |
| institutions/university | تدفق تدريب الوكلاء | DONE |
| institutions/court | تدفق المراجعة والأحكام | DONE |
| institutions/factory | تدفق توليد الأدوات | DONE |
| states/health | فحوصات الوكلاء | DONE |
| states/finance | الميزانيات الولائية | DONE |
| states/science | البحث والتقييم | DONE |
| states/law | السياسات والعقود | DONE |
| states/infrastructure | خارطة الخدمات | DONE |
| states/culture | معايير الهوية | DONE |

**تعريف الإنجاز:** كل تدفق موثق برسم بياني + خطوات + جداول مرتبطة.

---

## المرحلة 7 — الواجهات (DONE)

**الهدف:** نقاط دخول قابلة للاستخدام للبشر والوكلاء.

| المجال | المهمة | الحالة |
|---|---|---|
| interfaces/api | عقد API كامل | DONE |
| interfaces/cli | خريطة الأوامر | DONE |
| interfaces/web | مخطط لوحة المالك | DONE |
| interfaces/registry | ربط السجل بـ Supabase | DONE |

**تعريف الإنجاز:** كل واجهة لها مواصفة قابلة للتنفيذ.

---

## المرحلة 8 — الحوكمة والأمن والمراقبة (DONE)

**الهدف:** تقوية المملكة.

| المجال | المهمة | الحالة |
|---|---|---|
| royal/governance | عتبات الموافقة | DONE |
| royal/security | فهرس الحواجز الواقية | DONE |
| royal/security | بروتوكول العزل | DONE |
| royal/security | بروتوكول المفتاح الكهربائي | DONE |
| royal/governance | تقارير التدقيق | DONE |
| ops/observability | خطة اللوحات | DONE |
| ops/continuity | كتيب التعافي من الكوارث | DONE |

**تعريف الإنجاز:** كل بروتوكول موثق وقابل للتفعيل.

---

## المرحلة 9 — النضج والفصل المستقبلي (DONE)

**الهدف:** التحضير للاستخراج المستقبلي دون تقسيم مبكر.

| المهمة | الحالة |
|---|---|
| معايير جاهزية الاستخراج (amos-runtime, amos-interfaces, ...) | DONE |
| سياسة الإصدار | DONE |
| نضج CI/الاختبارات | DONE |
| نموذج الحوكمة طويل الأمد | DONE |

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
| 2026-08-15 | P2 | 12 مخطط JSON Schema + قالب ADR | (هذا الـ commit) |
| 2026-08-15 | P3 | 11 stub + اختبارات دخان 11/11 PASS | (هذا الـ commit) |
| 2026-08-15 | P4 | 11 وثيقة ربط قاعدة بيانات + ملخص | (هذا الـ commit) |
| 2026-08-15 | P5 | حلقة التشغيل الأساسية: 5 مواصفات + مخطط + سيناريو | (هذا الـ commit) |
| 2026-08-15 | P6 | تفعيل المؤسسات والولايات: 10 تدفقات موثقة | (هذا الـ commit) |
| 2026-08-15 | P7 | الواجهات: 4 مواصفات واجهة | (هذا الـ commit) |
| 2026-08-15 | P8 | الحوكمة والأمن والمراقبة: 7 بروتوكولات | (هذا الـ commit) |
| 2026-08-15 | P9 | النضج والفصل المستقبلي: 4 معايير | (هذا الـ commit) |
| 2026-08-15 | P9 | رفع تغطية الأفرع فوق 80% (80.3%) + بوابة CI للأفرع | (هذا الـ commit) |
