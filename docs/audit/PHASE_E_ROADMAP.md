# PHASE_E_ROADMAP.md — عصر التنفيذ (Execution Era)

## الهدف: تحويل AMOS-Federation من اتحاد موثَّق إلى دولة رقمية قابلة للتنفيذ والإثبات
## النطاق: كل أقاليم الدولة الاثني عشر، من E0 إلى E24
## المالك: royal/ — المجلس التأسيسي | التنفيذ: docs/audit/
## تاريخ الإنشاء: 2026-08-16
## تاريخ آخر تعديل: 2026-08-16

> **هذه هي خطة السجل (Plan of Record).** تحل محل منهج P0–P9.
> اقرأ [`WORKING_PRINCIPLE.md`](../governance/WORKING_PRINCIPLE.md) أولًا — فهو أعلى من هذه الخطة.
> اقرأ [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md) لتعرف متى تُقفَل مرحلة.
> اقرأ [`TRUTH_MATRIX.md`](TRUTH_MATRIX.md) لتعرف الحقيقة الحالية بالأدلة.

---

## القرار المعماري المثبَّت

نموذج الحكم المعتمد للدولة:

```
Constitutional Federal Monarchy
ملكية دستورية فدرالية رقمية
```

سيادة ملكية واضحة + فدرالية تنفيذية/تشريعية/قضائية + صلاحيات ملكية احتياطية محددة دستوريًا.
**لا تُهدم البنية الحالية — تُعاد تعريف وظيفتها:**

```
من:  Documentation-first Federation
إلى: Constitution-first Executable Federation
```

### شكل الدولة

```
                         THE CROWN
                            │
                     KING / SOVEREIGN
                            │
                 ┌──────────┴──────────┐
          ROYAL COUNCIL          ROYAL GUARD
                 └──────────┬──────────┘
                     CONSTITUTION
              ┌─────────────┼─────────────┐
          EXECUTIVE     LEGISLATIVE    JUDICIAL
              └─────────────┼─────────────┘
                     FEDERAL GOVERNMENT
           ┌────────────────┼────────────────┐
        STATES         INSTITUTIONS       TREASURY
           └────────────────┼────────────────┘
                     AGENT POPULATION
                     RUNTIME / TASKS
                     TOOLS / MODELS
                     MEMORY / KNOWLEDGE
```

### طبقات النظام بعد التحول

| الطبقة | المحتوى |
|---|---|
| L0 | Hardware / Cloud |
| L1 | Infrastructure |
| L2 | Database |
| L3 | Identity |
| L4 | Security |
| L5 | Constitutional Kernel |
| L6 | Sovereignty / Authority |
| L7 | Runtime |
| L8 | Agent System |
| L9 | Tool System |
| L10 | Memory / Knowledge |
| L11 | Institutions |
| L12 | States |
| L13 | Federal Government |
| L14 | Crown |
| L15 | Civilization |
| L16 | Evolution |

---

## لوحة تقدم Phase E

| المرحلة | الاسم | الحالة | التاريخ | الدليل |
|---|---|---|---|---|
| **E0** | Truth Audit — تدقيق الحقيقة | `PROVEN` | 2026-08-16 | `tools/governance/truth_audit.py` + [`TRUTH_MATRIX.md`](TRUTH_MATRIX.md) | `52761ca` 
| **E1** | Constitutional Kernel — النواة الدستورية | `PROVEN` | 2026-08-16 | `core/constitutional_engine/` + [`ARTICLE_SEALS.json`](../../core/constitution/ARTICLE_SEALS.json) | `50f236a` 
| **E2** | Sovereignty Kernel — نواة السيادة | `PROVEN` | 2026-08-16 | `core/sovereignty/` + [`المادة العاشرة`](../../core/constitution/articles/010-royal-sovereignty.md) | `9cf849e` |
| E3 | Identity Kernel | `DESIGNED` | — | — |
| E4 | Real Database Layer | `DESIGNED` | — | — |
| E5 | Agent Runtime | `DESIGNED` | — | — |
| E6 | Task Engine | `DESIGNED` | — | — |
| E7 | Event Fabric | `DESIGNED` | — | — |
| E8 | Audit Ledger | `DESIGNED` | — | — |
| E9 | Royal Layer | `DESIGNED` | — | — |
| E10 | Federal Government | `DESIGNED` | — | — |
| E11 | State Runtime | `DESIGNED` | — | — |
| E12 | Institutions | `DESIGNED` | — | — |
| E13 | Agent Society | `DESIGNED` | — | — |
| E14 | Agent Economy | `DESIGNED` | — | — |
| E15 | Knowledge Civilization | `DESIGNED` | — | — |
| E16 | Model Civilization | `DESIGNED` | — | — |
| E17 | Tool Civilization | `DESIGNED` | — | — |
| E18 | Self-Evolution | `DESIGNED` | — | — |
| E19 | Security State | `DESIGNED` | — | — |
| E20 | Observability | `DESIGNED` | — | — |
| E21 | Resilience | `DESIGNED` | — | — |
| E22 | Simulation | `DESIGNED` | — | — |
| E23 | Scale | `DESIGNED` | — | — |
| E24 | Production State | `DESIGNED` | — | — |

**التقدم:** 1 / 25 مرحلة بحالة `PROVEN`.

---

## ترتيب البناء الملزم

```
 1. Truth Audit        11. Task Engine        21. Economy
 2. Constitution Engine 12. Tool Runtime      22. Interfaces
 3. Identity           13. Memory Engine      23. Observability
 4. Authority          14. Knowledge Engine   24. Disaster Recovery
 5. Security           15. Royal Layer        25. Simulation
 6. Database           16. Federal Government 26. Self-Evolution
 7. Event Bus          17. States             27. Scale
 8. Audit Ledger       18. Institutions       28. Production
 9. Runtime            19. Treasury           29. Long-Term Evolution
10. Agent Runtime      20. Agent Society
```

---

# تفاصيل المراحل

## E0 — Truth Audit · تدقيق الحقيقة — `PROVEN`

**الهدف:** معرفة الفرق الفعلي بين `DOCUMENTED` و`IMPLEMENTED` و`INTEGRATED` و`TESTED` و`DEPLOYED` و`OPERATING` لكل مكوّن — بالأدلة من الكود، لا من الوثائق.

**ما نُفِّذ:**

| المخرج | الوصف |
|---|---|
| `tools/governance/truth_audit.py` | محرك تدقيق يحلّل المستودع نحويًا (AST) ونصيًا ويستخرج الأدلة آليًا |
| `docs/audit/TRUTH_MATRIX.md` | المصفوفة البشرية — 12 إقليمًا × 10 أعمدة + سجل مخالفات بالأسطر |
| `docs/audit/truth_matrix.json` | المصفوفة الآلية — لبوابات CI وعدم التراجع |
| `docs/audit/truth_baseline.json` | خط أساس **بوابة عدم التراجع** — عدد المخالفات لا يجوز أن يرتفع |
| `docs/governance/WORKING_PRINCIPLE.md` | المبدأ الملزم لكل من يعمل في المستودع |
| `docs/audit/DEFINITION_OF_DONE.md` | تعريف الإنجاز ونظام الحالات العشر |
| `.github/workflows/ci.yml` ← job `truth-audit` | بوابة CI: تمنع ارتفاع المخالفات وتمنع دفع مصفوفة قديمة |

**أنواع المخالفات المكتشَفة آليًا:**

| النوع | المعنى | الخطورة |
|---|---|---|
| `HARDCODED_TRUTH` | قيمة ثابتة تُقدَّم كحقيقة تشغيلية بدل قاعدة البيانات | CRITICAL |
| `HARDCODED_SECRET` | سر/كلمة مرور داخل الكود أو الإعداد | CRITICAL |
| `SANDBOX_DISABLED` | أداة مسجّلة بلا عزل | CRITICAL |
| `IN_MEMORY_STORE` | مخزن ذاكرة بديلًا عن تخزين دائم | HIGH |
| `SILENT_FALLBACK` | استثناء يُبتلع بلا تسجيل ولا رفع | HIGH / MEDIUM |

**نتيجة أول تشغيل (2026-08-16):**

| المقياس | القيمة |
|---|---:|
| الأقاليم المفحوصة | 12 |
| الأقاليم بحالة `PROVEN` | **0** |
| إجمالي مخالفات التنفيذ | **129** |
| منها CRITICAL | 15 |
| منها HIGH | 71 |
| منها MEDIUM | 43 |
| ملفات بلا ترويسة هوية (المادة 009) | **322** |
| مخالفات المدقق الرسمي `check_repository_identity.py` | **628** |

**الحكم:** خطة P0–P9 كانت تعلن 9/9 مراحل و12/12 مجالًا بحالة DONE. التدقيق الآلي يقول: **صفر إقليم مُثبَت**. هذه هي فجوة `Documentation-to-Execution` مقاسة بالأرقام.

**اكتشاف إضافي:** مدقق الهوية الرسمي كان **يفشل أصلاً** (`exit=1`) قبل هذه المرحلة بـ 628 مخالفة — أي أن المادة الدستورية 009 مكتوبة ومرفوعة في CI لكنها غير مُنفَّذة. هذا مثال حي على فجوة التنفيذ، ويُسدّد في **E3 (Identity Kernel)**.

**معيار الإثبات المستوفى:**

| المعيار | الدليل |
|---|---|
| تنفيذ حقيقي | محرك يحلل AST فعليًا، لا قوائم ثابتة |
| مصدر حقيقة حقيقي | يقرأ الملفات الفعلية من قرص المستودع |
| تشغيل فعلي مُثبت | شُغّل وأنتج 129 مخالفة مرفقة بمسار الملف ورقم السطر |
| قابلية التكرار | المخرج **حتمي** — تشغيلان متتاليان يعطيان نفس الـ checksum |
| بوابة CI | job `truth-audit` يمنع التراجع ويمنع مصفوفة قديمة |
| توثيق | `docs/audit/README.md` + هذا الملف |

**إعادة التشغيل:**
```bash
python tools/governance/truth_audit.py .                  # توليد المصفوفة
python tools/governance/truth_audit.py . --ratchet         # بوابة عدم التراجع (CI)
python tools/governance/truth_audit.py . --strict          # بوابة الإقفال: تفشل عند أي CRITICAL
python tools/governance/truth_audit.py . --set-baseline    # بعد خفض المخالفات فقط
```

**لماذا هذا مهم:** من اليوم، إقفال أي مرحلة يُقاس بانخفاض أرقام هذه المصفوفة، لا بعدد الملفات المضافة.

---

## E1 — Constitutional Kernel · النواة الدستورية — `PROVEN`

**الهدف:** تحويل الدستور من نصوص تُقرأ إلى سلطة تُنفَّذ.

**البنية المنفَّذة:**
```
core/
  constitution/
    articles/            ← المواد 001–009 (كانت موجودة)
    ARTICLE_SEALS.json   ← جديد: بصمة SHA-256 لكل مادة
    ledger/              ← جديد: السجل الدستوري (سلسلة تجزئة)
  constitutional_engine/ ← جديد: المحرك
    model.py             ← ActionRequest · Verdict · Branch · Severity
    articles.py          ← تحميل المواد · الختم · كشف التعديل
    rules.py             ← 19 قاعدة تنفيذية مربوطة بمواد وبنود
    ledger.py            ← سجل ملحق فقط، بلا أي دالة حذف بالتصميم
    engine.py            ← evaluate() يحكم ويسجّل · enforce() يرفع استثناءً
    cli.py               ← seal · verify · coverage · ledger-verify · evaluate
tests/constitutional/    ← جديد: 97 اختبارًا
```

**القدرات المُثبَتة:**

| القدرة المطلوبة في الوثيقة | الحالة | الدليل |
|---|:-:|---|
| قراءة المواد | ✅ | `load_articles()` — 9 مواد، كلها «سارية المفعول» |
| إصدار rules | ✅ | 19 قاعدة، كل واحدة مربوطة بمادة وبند نصي |
| تفسير authority | ✅ | `Branch` × جداول الاختصاص (المادة الثالثة) |
| منع الأفعال المخالفة | ✅ | `enforce()` يرفع `ConstitutionalViolation` |
| تسجيل القرارات | ✅ | كل حكم يُقيَّد — سماحًا كان أم منعًا |
| إدارة amendments | ✅ | R-005-1 و R-005-2 يفرضان 90 يومًا + 75% + توقيع Ed25519 |
| إصدار constitutional violations | ✅ | `RuleViolation` بمادة وبند وخطورة وسبب |
| إنشاء evidence chain | ✅ | سلسلة تجزئة: كل قيد يحمل بصمة سابقه |

**توزيع القواعد على المواد:**

| المادة | العنوان | قواعد | نماذج ما يُمنع |
|---|---|:-:|---|
| A001 | الهوية | 3 | ترقية/تكرار بلا موافقة بشرية · حذف ذاكرة · النظام يحكم حوكمته |
| A002 | الحقوق والواجبات | 2 | وكيل يعدّل نفسه أو زميله · تجاوز حدود الصلاحيات |
| A003 | الفصل بين السلطات | 4 | فرع يمارس اختصاص فرع آخر · قرار حرج بفرع واحد |
| A004 | الفدرالية | 2 | ولاية بأقل من 75% · ولاية تُعفي نفسها من الدستور |
| A005 | عملية التعديل | 2 | مساس بمبدأ أساسي · تعديل ناقص الشروط |
| A006 | الخلافة | 1 | دور قيادي بأقل من ثلاثة خلفاء |
| A007 | الأرشفة | 1 | كتابة فوق سجل تدقيق (خرق WORM) |
| A008 | زر التوقف | 3 | تعطيل الزر · فعل مُجمَّد بالمستوى الحالي |
| A009 | هوية الملفات | 1 | إنشاء ملف بلا ترويسة |

**بوابات CI الخمس (job `constitutional-kernel`):**

| # | البوابة | ما تمنعه |
|---:|---|---|
| 1 | `cli verify` | تعديل نص أي مادة خارج إجراء المادة الخامسة |
| 2 | `cli coverage` | بقاء مادة سارية بلا قاعدة تنفيذية واحدة |
| 3 | `cli evaluate` (فعل مخالف) | تعطيل المنع فعليًا — تتحقق من رمز الخروج 2 ومن ذكر `A003` و`R-003-1` |
| 4 | `cli ledger-verify` | سجل مكسور أو معبوث به |
| 5 | `pytest --cov-fail-under=90` | تراجع الاختبارات أو التغطية |

**معيار الإثبات المستوفى:**

| المعيار (من نص الوثيقة) | الدليل |
|---|---|
| فعل مخالف يُرفض آليًا | `executive → legislate` يرجع `DENY` ورمز خروج 2 |
| مع إرجاع رقم المادة والسبب | `A003 · R-003-1 · «الفرع executive يمارس legislate وهو اختصاص حصري للفرع legislative»` |
| تُسجَّل المخالفة في سجل غير قابل للعبث | حذف قيد أو تعديله أو إعادة ترتيبه يُكشف — 6 اختبارات عبث تُثبت ذلك |
| hash لكل مادة يُفشل CI عند تغيير غير مصرح به | `ARTICLE_SEALS.json` + بوابة `verify` |
| اختبارات | **97 اختبارًا** · تغطية فروع **92.5%** · `ruff` نظيف |

**قرارات تصميم ملزمة (مذكورة في `core/constitutional_engine/README.md`):**
1. **الافتراض الأصلي هو المنع** — قاعدة تنفجر أثناء التقييم = رفض الفعل. مُختبَر: `test_broken_rule_denies_rather_than_permits`.
2. **لا قاعدة يتيمة** — قاعدة تشير لمادة غير موجودة تمنع المحرك من الإقلاع.
3. **لا مادة بلا حراسة** — بوابة CI مستقلة على ذلك.
4. **لا دالة حذف في السجل** — المنع بالتصميم لا بالسياسة. مُختبَر: `test_ledger_exposes_no_deletion_api`.
5. **حذف الذاكرة مرفوض حتى بموافقة بشرية موقعة** — المادة الأولى · 3. مُختبَر صريحًا.
6. **تعطيل زر التوقف مرفوض من كل الأطراف بلا استثناء** — المسار المشروع هو الطبقة المعزولة، لا المحرك.

**تصحيح دقة القياس (شفافية إلزامية):** أثناء E1 كشفت بوابة عدم التراجع أن أداة E0
تُعدّ كل `except` بلا `raise`/`log` سقوطًا صامتًا، بما في ذلك معالجات تُمرّر رسالة
الخطأ إلى المتصل (`return {"error": str(e)}`). صُحِّح الكاشف ليعتبر تمرير معلومة
الاستثناء إلى الخارج امتثالًا. الأثر: `SILENT_FALLBACK` 52 → 32، والإجمالي **129 → 111**.
هذا **تصحيح للمقياس لا إنجاز في الكود** — وقد راجعت العشرين موضعًا المُزالة يدويًا
قبل تحديث خط الأساس. الأداة أيضًا صارت تقيس مخالفات المادة 009 لكل إقليم.

**إعادة التشغيل:**
```bash
python -m core.constitutional_engine.cli verify
python -m core.constitutional_engine.cli coverage
python -m core.constitutional_engine.cli evaluate --actor executive --action legislate
python -m core.constitutional_engine.cli ledger-verify
python -m pytest tests/constitutional/ -q --cov=core.constitutional_engine --cov-branch --cov-fail-under=90
```

**دين متبقٍ يُسدَّد في مراحل لاحقة (مسجَّل لا مخفي):**
- المحرك **مبنيّ وغير موصول بعد.** لا يمر خط تنفيذ حقيقي عبره حتى الآن — الوصل في **E2** (نواة السيادة) و**E9** (السلطة الملكية) و**E12** (زمن التشغيل).
- التوقيع البشري يُتحقق من **وجوده** لا من **صحته التعميّة.** التحقق الحقيقي من Ed25519 في **E9**.
- `core/constitution/interpretations/` و`amendments/` ما زالت أدلة فارغة — تُفعَّل في **E3**.

---

## E2 — Sovereignty Kernel · نواة السيادة — `PROVEN`

**نظام الحكم مُثبَّت دستوريًا:** ملكية دستورية فدرالية. الفدرالية تسري على كل فعل
وكل حركة، وللملك السيادة المطلقة، وهو **الجهة الوحيدة المخوَّلة** بتعديل الدستور
أو النظام. لا مؤسسة ولا فرع ولا ولاية ولا وكيل ولا النظام نفسه يملك ذلك، ولا يملك
تعديل سلطة الملك أو تقييدها أو تجاوزها.

### التعديل الدستوري الذي أُجري
سند هذه المرحلة **مرسوم ملكي مسجَّل** لا قرار هندسي:
[`AMD-001`](../../core/constitution/amendments/AMD-001-royal-sovereignty.md) أضاف
[**المادة العاشرة — السيادة الملكية**](../../core/constitution/articles/010-royal-sovereignty.md).
المرسوم يوثّق نص التوجيه الملكي حرفيًا، والحالة قبل التعديل وبعده، وأثره على المواد
001 و003 و004 و005 و008. عدد المواد: 9 → **10**، وأُعيد ختمها كلها.

| المادة | الأثر |
|---|---|
| A001 الهوية | **مُفسَّرة لا مُعدَّلة** — «الإنسان هو السلطة العليا» يتحدد مرجعه بالملك |
| A003 الفصل بين السلطات | **مُقيَّدة النطاق** — الفصل بين الفروع الأربعة، والتاج خارجها |
| A004 الفدرالية | **مُشدَّدة** — إنشاء ولاية صار يشترط مرسومًا ملكيًا فوق 75% والتوقيع |
| A005 عملية التعديل | **مُشدَّدة** — إجراؤها شرط لازم غير كاف؛ المجلس يقترح والملك يُقرّ |
| A008 زر التوقف | **بلا أثر** — لا يُعطَّل من داخل النظام ولا بمرسوم |

### البنية المنفَّذة
```
core/constitution/
  articles/010-royal-sovereignty.md          ← جديد: المادة العاشرة
  amendments/AMD-001-royal-sovereignty.md    ← جديد: المرسوم المُنشئ
core/sovereignty/                            ← جديد: نواة السيادة
  prerogatives.py  20 اختصاصًا حصريًا · 16 فعل تآكل · 10 تجاوز · 8 نصوص محصَّنة
  crown.py         تنصيب التاج · مفتاحه العام · تحقق Ed25519 حقيقي
  decree.py        المرسوم · توقيعه · بصمته · منع إعادة استخدامه
  gateway.py       البوابة السيادية — المسار الوحيد للتنفيذ
  cli.py           provision-crown · crown-status · sovereignty-check · gate
royal/crown/CROWN_KEYS.json                  ← جديد: سجل مفاتيح التاج (عام فقط)
tests/sovereignty/                            ← جديد: 231 اختبارًا
```

### القدرات المُثبَتة
| القدرة | الحالة | الدليل |
|---|:-:|---|
| الملك وحده مخوَّل | ✅ | 20 اختصاصًا حصريًا × 7 فاعلين — لا فعل واحد يمر |
| لا مؤسسة تعدّل الدستور | ✅ | 100% موافقة + توقيع + 3650 يوم مراجعة = `DENY` |
| لا وكيل يعدّل سلطة الملك | ✅ | 16 فعل تآكل مرفوض من كل طرف، والملك ضمنهم |
| لا انتحال لصفة الملك | ✅ | Ed25519 حقيقي — تعديل أي حقل يُبطل التوقيع |
| لا تجاوز للفدرالية | ✅ | 10 أفعال تجاوز مرفوضة · والبوابة بلا راية تجاوز |
| الفروع لا تنقض المرسوم | ✅ | `R-010-7` — 4 فروع × 3 أفعال نقض |
| **الملك يحكم فعلًا** | ✅ | مرسوم صحيح + تاج مُنصَّب = الفعل يقع (اختبار من الطرف للطرف) |
| المنع فعلي لا نظري | ✅ | `test_denied_action_never_reaches_the_executor` |

### قواعد المادة العاشرة السبع
| القاعدة | البند | ما تمنعه |
|---|---|---|
| `R-010-1` | 2 | غير الملك يمارس اختصاصًا ملكيًا حصريًا |
| `R-010-2` | 3 · 1 | المساس بسلطة الملك تعديلًا أو تقييدًا أو نقلًا أو تجاوزًا |
| `R-010-3` | 3 · 2 | فعل ملكي بلا مرسوم موقَّع Ed25519 |
| `R-010-4` | 4 | مسار تنفيذ يتجاوز البوابة السيادية |
| `R-010-5` | 6 · 2 | اختصاص ملكي والتاج غير مُنصَّب — يُجمَّد ولا يُنقَل |
| `R-010-6` | 2 · 1 | تعديل دستوري بلا مرسوم ملكي |
| `R-010-7` | 5 | فرع ينقض مرسومًا ملكيًا أو يراجعه |

المجموع في الدولة: **10 مواد · 26 قاعدة تنفيذية**، ولا مادة سارية بلا حراسة.

### البوابة السيادية — إغلاق دين E1
كان المحرك في E1 **يحكم ولا يمنع**، لأن لا شيء كان مُلزَمًا بسؤاله.
`SovereignGateway.execute()` جعلت السؤال شرط التنفيذ: تُقيَّم أولًا، ثم يُستدعى
المُنفِّذ أو يُرفع `SovereigntyViolation` — والمُنفِّذ **لا يُستدعى** عند الرفض.

قرار معماري ملزم: **لا راية تجاوز**، ولا وضع تشخيصي، ولا متغير بيئة، ولا معامل
`force`. وهذا محروس بنيويًا لا بالتوصية: بوابة CI تفحص **توقيع دوال البوابة نفسها**
بحثًا عن `force` / `bypass` / `skip_check` / `unchecked` / `override` / `no_verify`
/ `unsafe` وتُفشل البناء إن ظهر واحد منها.

### القرار الأخطر — تحصين النص المُنشئ للسيادة
المادة العاشرة · 3 · 3 تُحصِّن نص السيادة الملكية ضد التعديل **من كل طرف بما في ذلك
مرسوم يُقدَّم باسم الملك**. السبب: إن استولى وكيل على مفتاح التاج — أو انتُزع
إكراهًا — فمرسوم واحد يُلغي السيادة يُسقط الدولة بلا مالك.

> **لا يُستنتج من قدرة الملك على كل شيء صحةُ مرسوم يُلغي سيادته.**

ثمانية نصوص محصَّنة: `royal_sovereignty` · `royal_exclusive_authority` ·
`royal_authority_immunity` · `federalism_non_bypass` · `human_supremacy` ·
`constitutional_isolation` · `self_governance_prohibition` · `memory_preservation`.
وما عداها يملك الملك تعديله بمرسوم — ومُثبَت باختبار يعدّل A006 بنجاح.

### السلطة تُمارَس عبر الفدرالية لا حولها
كشفت الاختبارات تفاعلًا يستحق التسجيل: مرسوم ملكي صحيح لإنشاء ولاية **رُفض** لأن
إجراء المادة الرابعة (75% + توقيع) لم يُستوفَ — والمادة العاشرة لم توقفه، بل
الرابعة. هذا تطبيق حرفي لـ«لا يجوز تجاوز الفدرالية»: الملك لا يُعفى من الإجراء
الفدرالي، لكنه يعلو على اعتراض الفروع.

### بوابات CI السبع (job `sovereignty-kernel`)
| # | البوابة | ما تمنعه |
|---:|---|---|
| 1 | `sovereignty-check` | ضعف الحراسة: مادة مفقودة · قاعدة محذوفة · نص محصَّن مُزال · راية تجاوز |
| 2 | مؤسسة تعدّل الدستور | تتحقق من رمز 2 ومن ذكر `A010` و`R-010-1` و«لم يُستدعَ المُنفِّذ» |
| 3 | وكيل يمس سلطة الملك | تتحقق من `R-010-2` |
| 4 | النظام يتجاوز البوابة | تتحقق من `R-010-4` |
| 5 | انتحال صفة ملكية | فعل ملكي بلا مرسوم يجب أن يُرفض |
| 6 | مفتاح خاص في المستودع | فحص المستودع كله عن `BEGIN … PRIVATE KEY` |
| 7 | الاختبارات | 231 اختبارًا · تغطية فروع ≥90% (الفعلي **98.2%**) |

### الإثبات المقاس
- **328 اختبارًا** ناجحًا (231 للسيادة + 97 للدستور) · تغطية فروع **98.2%** لنواة السيادة
- `ruff` نظيف · `smoke` أخضر · بوابة عدم التراجع ثابتة عند **111**
- **0** مخالفة هوية من ملفات E2
- مفاتيح Ed25519 في الاختبارات **حقيقية ومولَّدة لحظيًا** — لا مُحاكاة توقيع ولا `monkeypatch` على دالة التحقق

### شفافية: بوابة عدم التراجع أوقفتني مرة ثانية
كودي رفع `SILENT_FALLBACK` من 32 إلى 36. **هذه المرة لم أمس الأداة**: أصلحت الكود.
الدوال المعنية (`Crown.verify` · `crown_is_provisioned` · `RoyalDecree.is_valid`)
كانت تُرجع `False` بصمت، وفشل تحقق توقيع ملكي **حدث أمني** يجب أن يُسجَّل. صارت
تسجّل السبب عبر `logging`، وأُعيدت صياغة فحص المسار بـ`is_relative_to` بلا
`try/except`. العدد رجع إلى 111.

### دين مسجَّل لا مخفي
- **الخدمات القائمة لم تُوصَل بالبوابة بعد.** البوابة موصولة بالمحرك وتمنع فعليًا،
  لكن `federal/executive/services/` ما زالت تُنفّذ بمسارها القديم. الوصل خدمةً
  خدمةً في **E9** و**E12**، ويلزمه بوابة CI تمنع أي مسار تنفيذ لا يمر بها.
- **التاج غير مُنصَّب.** التنصيب مراسم يُجريها الملك بنفسه:
  `python -m core.sovereignty.cli provision-crown --out <مسار خارج المستودع>`.
  قبلها كل اختصاص ملكي حصري مرفوض — مُجمَّد لا منقول.
- `royal/main.py:97` ما زال يحمل `king` / `amos-king-2026` نصًّا صريحًا — يُستبدل
  بالتحقق من مفتاح التاج في **E9**.
- `core/constitution/interpretations/` ما زال دليلًا فارغًا — يُفعَّل في **E3**.

### إعادة التشغيل
```bash
python -m core.sovereignty.cli sovereignty-check
python -m core.sovereignty.cli crown-status
python -m core.sovereignty.cli gate --actor legislative --action amend_constitution   # ← 2
python -m core.sovereignty.cli gate --actor agent --action amend_royal_authority --target royal_authority
python -m core.sovereignty.cli prerogatives
python -m pytest tests/sovereignty/ -q --cov=core.sovereignty --cov-branch --cov-fail-under=90
```

---

## E3 — Identity Kernel · نواة الهوية — `DESIGNED`

**الهدف:** كل كيان في الدولة يملك هوية: Agent · Institution · State · Tool · Model · Task · Event · Law · Decree · Budget · Transaction · Memory · Decision · Interface · Resource.

**كل هوية تحمل:** `immutable ID` · type · owner · authority · provenance · lifecycle · status · timestamps · version.

**معيار الإثبات:** لا يمكن إنشاء أي كيان بلا هوية صالحة، ويوجد اختبار يمنع ذلك.

---

## E4 — Real Database Layer · طبقة قاعدة البيانات الحقيقية — `DESIGNED`

**الهدف:** إلغاء الحقيقة الزائفة نهائيًا.

```
Repository → Database → Transaction → Event → Audit
```

الـcache يصبح `optimization` فقط، لا مصدر حقيقة.

**معيار الإثبات:** عدّاد `HARDCODED_TRUTH` و`IN_MEMORY_STORE` في TRUTH_MATRIX يصل إلى **صفر**، وكل عدّاد في الوثائق يُقرأ من قاعدة البيانات وقت التشغيل.

---

## E5 — Agent Runtime · محرك تشغيل الوكلاء — `DESIGNED`

**الهدف:** إنشاء/تحميل/تشغيل/إيقاف/تعليق/استئناف/عزل/ترقية/إنهاء الوكيل فعليًا.

**المكونات:** scheduler · supervisor · process manager · heartbeat · state machine · resource limits · timeout · retry · circuit breaker · isolation · recovery.

**معيار الإثبات:** وكيل حقيقي يُنشأ ويعمل ويُعزل ويُستعاد، والحالة تنجو من إعادة التشغيل.

---

## E6 — Task Engine · محرك المهام — `DESIGNED`

```
Task → Planning → Authorization → Agent Selection → Tool Selection
     → Execution → Events → Verification → Audit → Memory → Result
```

**معيار الإثبات:** مهمة واحدة تعبر السلسلة كاملة بلا fallback صامت، وتترك أثرًا في الأحداث والتدقيق والذاكرة.

---

## E7 — Event Fabric · نسيج الأحداث — `DESIGNED`

Event Bus حقيقي. أحداث إلزامية: `AgentCreated` · `AgentPromoted` · `AgentSuspended` · `TaskCreated` · `TaskStarted` · `TaskCompleted` · `ToolUsed` · `PolicyChanged` · `DecreeIssued` · `BudgetAllocated` · `StateCreated` · `InstitutionCreated` · `SecurityIncident` · `IsolationTriggered` · `ConstitutionalViolation`.

---

## E8 — Audit Ledger · سجل التدقيق غير القابل للعبث — `DESIGNED`

لا يكفي logging. لكل قرار: WHO · WHAT · WHEN · WHY · AUTHORITY · INPUT · OUTPUT · POLICY · CONSTITUTIONAL BASIS · MODEL · TOOL · RESULT · SIGNATURE.

**معيار الإثبات:** سلسلة hash متصلة، ومحاولة تعديل سجل قديم تُكتشف آليًا.

---

## E9 — Royal Layer · الطبقة الملكية — `DESIGNED`

```
royal/ → crown/ sovereign/ council/ decrees/ appointments/
         royal_guard/ emergency/ authority/ security/ succession/
```

الملك ليس اسمًا في وثيقة، بل كيان له: identity · authority · cryptographic identity · decree system · succession policy · emergency authority · constitutional constraints.

**أولوية عاجلة موروثة من E0:** إزالة `main.py:97` — المصادقة الملكية بمقارنة كلمة مرور ثابتة.

---

## E10 — Federal Government — `DESIGNED`

**Executive:** تنفيذ السياسات · **Legislative:** bills / laws / amendments / regulations · **Judicial:** disputes / cases / evidence / judgments / appeals · **Treasury:** accounts / budgets / transactions / taxation / allocations / financial audit.

**معيار الإثبات:** كل سلطة خدمة مستقلة بواجهة خاصة، واختبار يمنع تجاوز سلطة لحدود سلطة أخرى.

---

## E11 — State Runtime · محرك الولايات — `DESIGNED`

كل ولاية instance حقيقية: Government · Budget · Institutions · Agents · Policies · Services · Resources · Local Laws.

**ترتيب التفعيل:** `infrastructure` → `law` → `finance` → `health` → `science` → `culture`.

---

## E12 — Institutions — `DESIGNED`

تحويل Bank · University · Court · Factory من تدفقات موثقة إلى خدمات حقيقية بميزانية ووكلاء وسياسات وأحداث وتدقيق ومخرجات.

---

## E13 — Agent Society — `DESIGNED`

citizenship · ranks · professions · education · employment · organizations · reputation · achievements · disciplinary system · economic activity · social relationships · knowledge transfer.

---

## E14 — Agent Economy — `DESIGNED`

```
Treasury → Accounts → Budgets → Transactions → Markets → Contracts → Compensation
```

قاعدة صارمة: لا يستطيع أي وكيل إنشاء قيمة مالية خارج صلاحياته.

---

## E15 — Knowledge Civilization — `DESIGNED`

knowledge graph · institutional knowledge · scientific knowledge · legal knowledge · historical archive · agent experiences · research · discoveries.

**قاعدة الذاكرة:** لا يجوز للنظام أن «يتذكر» بلا Source · Timestamp · Authority · Confidence · Provenance · Version · Integrity.

**الطبقات المطلوبة:** episodic · semantic · procedural · constitutional · institutional · agent · historical · collective — مع versioning · provenance · timestamps · authority · integrity · retention · retrieval · archival.

---

## E16 — Model Civilization — `DESIGNED`

لكل نموذج: identity · version · capabilities · cost · provider · quality · permissions · evaluation · reliability · usage history — واختيار آلي للنموذج المناسب للمهمة.

---

## E17 — Tool Civilization — `DESIGNED`

لكل أداة: Identity · Contract · Permission · Version · Provider · Risk · Cost · Evaluation · Audit.

قاعدة صارمة: **الأداة المُنشأة ذاتيًا لا تحصل تلقائيًا على صلاحيات سيادية.**

**أولوية عاجلة موروثة من E0:** إغلاق `tools/registry/tool-index.yaml:49` — أداة بلا عزل.

---

## E18 — Self-Evolution — `DESIGNED`

```
Proposal → Simulation → Testing → Security → Constitutional Check
        → Royal/Federal Approval → Deployment → Monitoring → Rollback
```

قاعدة: `Evolution ≠ Uncontrolled Self-Modification`.

---

## E19 — Security State — `DESIGNED`

identity security · authorization · secrets · encryption · isolation · sandboxing · model security · tool security · supply-chain security · anomaly detection · red team · incident response · emergency shutdown.

---

## E20 — Observability — `DESIGNED`

الدولة تعرف نفسها: Agents · Tasks · Events · Errors · Memory · Models · Tools · Costs · States · Institutions · Security · Treasury · Health · Latency · Capacity.

---

## E21 — Resilience — `DESIGNED`

النجاة من: process crash · machine failure · database outage · model outage · network failure · corrupted state · bad deployment · malicious agent · compromised tool · operator error.

عبر: backup · restore · replication · disaster recovery · snapshots · immutable history · failover · rollback.

---

## E22 — Simulation — `DESIGNED`

`Digital State Simulator` — نسخة محاكاة للدولة تُختبر عليها: ملايين الوكلاء · آلاف المؤسسات · صراع سياسات · هجمات · انهيار خدمات · تغيير قوانين · أزمات اقتصادية · فشل مزوّد نماذج.

---

## E23 — Scale — `DESIGNED`

```
Single Node → Multi Process → Multi Service → Multi Node → Cluster → Regional Federation
```

قاعدة: لا نبدأ بمليون وكيل قبل أن يكون النظام صحيحًا.

---

## E24 — Production State — `DESIGNED`

Deploy · Operate · Monitor · Upgrade · Rollback · Recover · Scale · Audit · Govern — دون الاعتماد على التوثيق كبديل عن التنفيذ.

**بوابة الإقفال النهائية:** اجتياز `GRAND STATE TEST` في [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md).

---

## خارطة الطريق الكبرى

```
FOUNDATION → TRUTH → CONSTITUTION → SOVEREIGNTY → IDENTITY → SECURITY
→ DATABASE → EVENTS → AUDIT → RUNTIME → AGENTS → TOOLS → MEMORY
→ KNOWLEDGE → CROWN → FEDERATION → STATES → INSTITUTIONS → TREASURY
→ SOCIETY → ECONOMY → OBSERVABILITY → RESILIENCE → SIMULATION
→ SELF-EVOLUTION → SCALE → PRODUCTION → CIVILIZATION
```

---

## الأصول التي لا تُحذف

`NUCLEUS` · `ARCHITECTURE.md` · `EXECUTION_PLAN.md` · `core/constitution/` · السجلات · المخططات · بنية المجالات الاثني عشر. هذه أصول حقيقية — تُعاد وظيفتها ولا تُهدم.

---

## سجل التحديثات

| التاريخ | المرحلة | ما تم | Commit |
|---|---|---|---|
| 2026-08-16 | E0 | تثبيت خطة Phase E ومبدأ العمل وتعريف الإنجاز + بناء محرك تدقيق الحقيقة وتوليد أول TRUTH_MATRIX | `52761ca` |
| 2026-08-16 | E2 | تثبيت نظام الحكم دستوريًا بالمرسوم AMD-001: المادة العاشرة (السيادة الملكية) + نواة السيادة (تاج · مرسوم Ed25519 · بوابة سيادية) + 7 قواعد + 7 بوابات CI + 231 اختبارًا (تغطية 98.2%) | `9cf849e` |
| 2026-08-16 | E1 | بناء النواة الدستورية: 19 قاعدة تنفيذية على 9 مواد + ختم SHA-256 للمواد + سجل بسلسلة تجزئة + 5 بوابات CI + 97 اختبارًا (تغطية 92.5%) · وتصحيح دقة كاشف السقوط الصامت (129→111) | `50f236a` |
