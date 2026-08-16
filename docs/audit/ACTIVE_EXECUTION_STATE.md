# حالة التنفيذ النشطة — ذاكرة التسليم الرسمية بين الوكلاء

## الهدف
أن يفتح أي وكيل جديد هذا المستودع فيعرف **بالضبط** أين توقف من قبله، وما ثبت
تنفيذيًّا، وما لم يثبت، وما الأمر التالي حرفيًّا — دون الرجوع إلى أي محادثة خارجية.
ولا يُكتَب في هذا الملف ادّعاء غير مثبت: كل سطر هنا إما مخرج أمر شُغِّل فعلًا، أو
موسوم صريحًا بأنه غير محقَّق.

## النطاق
حالة تنفيذ المرحلة E2.2/E2.3 (حماية سيادة التاج) ونقاط التفتيش وتسليمها.
**لا يدخل:** التوثيق المعماري (`docs/security/`)، ولا مصفوفة الحقيقة
(`docs/audit/TRUTH_MATRIX.md`)، ولا خارطة المرحلة.

## المالك
ديوان التدقيق، بتفويض التحديث إلى الوكيل المنفِّذ عند كل نقطة تفتيش.

## تاريخ الإنشاء
2026-08-16

## تاريخ آخر تعديل
2026-08-16

## المحتويات
| القسم | الموضوع |
|---|---|
| 1 | الحالة الراهنة |
| 2 | ما أُنجز |
| 3 | ما شُغِّل من اختبارات وبوابات |
| 4 | الملفات |
| 5 | الأخطاء والمخاطر المعروفة |
| 6 | ما تبقّى وترتيبه |
| 7 | الأمر التالي حرفيًّا |
| 8 | ما لا يُفعَل بعد |
| 9 | سجل نقاط التفتيش |

---

## 1. الحالة الراهنة

| الحقل | القيمة |
|---|---|
| Current Phase | E2.2 — Crown Root of Trust & Protection |
| Current Subphase | E2.2-F — End-to-end sovereign continuity proof |
| Current Objective | إثبات الاستمرارية السيادية من الطرف إلى الطرف: K1 نشط ← مرساة محقَّقة ← أمر D1 ← لا نقض من تابع ← تنفيذ ← سجل ← إبطال K1 ← بقاء D1 التاريخي قابلًا للتحقق ← تفعيل K2 ← تنفيذ D2 ← رفض أمر K1 جديد ← حدث أمني ← لا تاج زائف |
| Status | E2.2-A/B/C/D/E = VERIFIED ومدفوعة · E2.2-F = NOT_STARTED |
| Current Commit SHA | `891f6fe` (E2.2-E — مدفوع ومؤكَّد) |
| Last Verified Commit | `891f6fe` — مؤكَّد على `origin/main` بـ`git ls-remote` |
| Previous Checkpoint SHA | `891f6fe` (E2.2-E) · `3fed334` (E2.2-D) · `dae73f6` (E2.2-C) · `b13cd87` (E2.2-B) · `fb5ce9d` (E2.2-A) · `098beb3` (ما قبل التاج) |
| Remote Confirmed | نعم — `origin/main = 891f6fe` وقت كتابة هذه النقطة |
| Last Updated | 2026-08-16 |

## 2. ما أُنجز (مثبَت تنفيذيًّا)

- `core/crown/` — 12 وحدة منفَّذة: الهويات، وسجل المفاتيح، ومرساة الثقة، وبيئات
  التوقيع، ومدقق الأوامر، والسجل، والاستمرارية، والخلافة، والاسترداد، ومكتبة
  التهديدات (38 تهديدًا)، والحارس (11 طبقة)، وواجهة سطر الأوامر.
- `tests/crown/` — 10 ملفات اختبار + `conftest.py`، بمفاتيح Ed25519 حقيقية عابرة في
  الذاكرة، بلا مادة مفتاح في المستودع.
- `docs/security/` — المعمار، ونموذج التهديد (**مولَّد** من الكود)، وحدّ البشر
  والبرمجية، وخارطة الأمن المستقبلي.
- `tools/governance/generate_crown_threat_doc.py` — يولّد وثيقة التهديد من
  `core/crown/threats.py` ويتحقق من تطابقها بـ`--check`، فلا تنفصل الوثيقة عن
  التنفيذ.
- `core/crown/README.md` و`core/crown/NUCLEUS.md` و`tests/crown/README.md`.

### نقطة تفتيش E2.2-A (مغلقة)

```
CHECKPOINT E2.2-A
-----------------
Objective:      توثيق نطاق التاج ونواته + إنشاء ذاكرة التسليم
Completed:      core/crown/README.md · core/crown/NUCLEUS.md · tests/crown/README.md ·
                docs/audit/ACTIVE_EXECUTION_STATE.md
Tests:          299 passed / 0 failed · تغطية فروع 94% على core.crown
Security:       crown-check 9/9 (رمز خروج 0) · لا مادة مفتاح في المستودع
Documentation:  مطابقة للتنفيذ · وثيقة التهديد مولَّدة ومتحقَّق من تطابقها
Commit:         e3d0c8a (أساس التنفيذ) + cda68d5 (توثيق E2.2-A)
Remote:         origin/main = cda68d5 — مؤكَّد بـgit ls-remote
Remaining:      E2.2-B .. E2.3-B
Next Action:    بوابة CI crown-root-of-trust
Status:         VERIFIED
```

### نقطة تفتيش E2.2-B (مغلقة)

```
CHECKPOINT E2.2-B
-----------------
Objective:      بوابة CI crown-root-of-trust غير شكلية
Completed:      tools/crown/verify_crown_root_of_trust.py (11 فحصًا) ·
                tools/crown/README.md · وظيفة crown-root-of-trust بثماني خطوات في ci.yml
Tests:          البوابة محليًّا 11/11 · الاختبارات الكبرى 14/14 · اختبارات الحارس 32/32
Security:       فحص مادة المفاتيح وحصص الاسترداد ورايات التجاوز وادّعاء الأمن المطلق
Failure cases:  4 حقن مُجرَّبة أسقطت البوابات 2 و3 و4 و11 برمز 1، ثم استُعيد المستودع
Real defect:    الفحص التاسع كان يبتلع AttributeError فيمرّ زائفًا — صُحِّح إلى
                التقاط GuardAuthorityError وحده
Documentation:  tools/crown/README.md يوثّق حالات الفشل المُجرَّبة
Commit:         (يُثبَت بعد الالتزام في هذه النقطة)
Remote:         (يُثبَت بعد الدفع)
Remaining:      E2.2-C .. E2.3-B
Next Action:    خارطة المرحلة ومصفوفة الحقيقة
Status:         VERIFIED محليًّا · CI لم تُشغَّل بعد على GitHub
```

### نقطة تفتيش E2.2-C (مغلقة)

```
CHECKPOINT E2.2-C
-----------------
Objective:      حالة المرحلة في الخارطة ومصفوفة حقيقة للنطاق بلا كلمة COMPLETE
Completed:      tools/crown/generate_crown_truth_matrix.py (مولِّد يمتحن الادّعاء) ·
                docs/audit/CROWN_TRUTH_MATRIX.md (مولَّدة) ·
                قسم E2.2 وصفّان في لوحة التقدم وسجل التحديثات في PHASE_E_ROADMAP.md ·
                خطوة CI «بوابة 4ب» · tests/crown/test_crown_truth_matrix.py (12 اختبارًا)
Tests:          311 اختبار تاج ناجح · تغطية فروع 94.39% · 390 اختبار أساس ناجح
Security:       جذر الثقة 11/11 · crown-check 9/9 · هوية المستودع: صفر مخالفة
Truth audit:    ثابت عند 110 — صفر مخالفة جديدة (كانت 122 قبل الإصلاح)
Real defects:   (1) اسمان يُقرآن سرًّا مضمَّنًا → أُعيدت تسميتهما إلى ..._ACCESS_GRANT
                (2) 10 استثناءات مبتلعة في cli.py و guard.py وأداة التحقق → صار سبب
                    الرفض يُنقَل إلى المخرَج، و audit_chain_error معلَن في التقرير
                (3) اختبار المولِّد كان يُشغِّل pytest داخل pytest فتوالد التشغيل →
                    أُضيف حارس CROWN_TRUTH_MATRIX_MEASURING وبيانات ثابتة في الاختبار
Known gap:      command.py و continuity.py لا تستوردهما وحدة أخرى → المصفوفة تُسقِطهما
                إلى TESTED؛ الدمج شرطٌ في E2.2-F ولم يُدَّعَ إنجازه
Documentation:  CROWN_TRUTH_MATRIX.md + قسم E2.2 في الخارطة
Commit:         (يُثبَت بعد الالتزام)
Remote:         (يُثبَت بعد الدفع)
Remaining:      E2.2-D .. E2.3-B
Next Action:    بوابات الهوية — تشغيل السبع ومصالحة المخالفات بالتصنيف
Status:         VERIFIED محليًّا
```

### نقطة تفتيش E2.2-D (مغلقة)

```
CHECKPOINT E2.2-D
-----------------
Objective:      تشغيل بوابات الهوية ومصالحة كل مخالفة بتصنيفها، بلا رفع عتبة ولا
                تضييق نطاق ولا حذف مدقّق ولا تعطيل بوابة
Completed:      توسيع سجل الأقاليم بثلاثة نطاقات (core/crown · tools/crown ·
                docs/security) → 45 إقليمًا مسجَّلًا ·
                سدّ ثغرة الحاشية في check_repository_identity.py و
                stamp_readme_identity.py (strip_boilerplate) ·
                إضافة فحص صدق التاريخ (date_drift) إلى الخاتم ومسار تصحيحه ·
                ختم 43 بطاقة كان حقل «المحتويات» فيها فارغًا + تصحيح 109 تاريخًا متقادمًا
Tests:          tests/governance/ 31 ناجحًا (كانت 24؛ +7 تحرس المنطق الجديد) ·
                677 اختبار تاج/سيادة/دستور ناجح · ruff نظيف
Security:       truth_audit --ratchet ثابت عند 110 — صفر مخالفة جديدة
Gates:          check_repository_identity=0 · generate_identity_cards --check=0 ·
                write_domain_readmes --check=0 · stamp_readme_identity --check=0
Injections:     حذف tools/crown/README.md → خروج 1 (MISSING_README) ثم 0 بعد الإعادة ·
                استبدال «الهدف:» بـ«الشرح:» في core/crown/threats.py → خروج 1
                (MISSING_PURPOSE) ثم 0 بعد الإعادة · تاريخ 2020-01-01 و2099-12-31 في
                بطاقة اختبارية → date_drift يرصدهما (اختباران)
Documentation:  هذه النقطة + توصيف العيوب أدناه
Commit:         (يُثبَت بعد الالتزام)
Remote:         (يُثبَت بعد الدفع)
Remaining:      E2.2-E .. E2.3-B
Next Action:    E2.2-E — تحقق الأسرار وحدود الثقة (الحجب عند أي خطر)
Status:         VERIFIED محليًّا · CI لم تُشغَّل بعد على GitHub
```

### تصنيف مخالفات الهوية في E2.2-D

| المخالفة | العدد | التصنيف | التصرّف |
|---|---|---|---|
| نطاقات التاج الثلاثة خارج سجل الأقاليم | 3 | **NEW** (من عمل هذه المرحلة) | سُجِّلت في `SCOPES` — لا تضييق نطاق |
| حقل «المحتويات» فارغ فوق حاشية البطاقة | 43 | **REAL DEFECT** في المدقّق نفسه (مخالفات **EXISTING** كانت مستورة) | سُدَّت الثغرة ثم خُتِمت البطاقات |
| تاريخ آخر تعديل يناقض سجل git | 109 | **REAL DEFECT** في الخاتم (كان يسأل «أموجود؟» لا «أصادق؟») | أُضيف `date_drift` وصُحِّحت البطاقات |
| بطاقات مولَّدة تغيّر محتواها بعد الختم | 152 ملفًا | **EXPECTED_GENERATED** | مُلتزَمة كما ولّدتها الأداة |
| ارتداد في أي بوابة قائمة | 0 | **REGRESSION** — لا شيء | — |

**عيبان حقيقيان في الحُرّاس أنفسهم** (لا في المستودع المفحوص)، وهذا أخطر ما وُجد في
E2.2-D: بوابة تمرّ لأنها تسأل السؤال الخطأ أسوأ من بوابة غائبة، لأنها تُنتج ثقة
كاذبة. الأولى: القسم الأخير في البطاقة كانت حاشية الذيل تقع تحته فتُحتسب مضمونًا
له — فمرّ 43 حقلًا فارغًا. الثانية: فحص التاريخ كان يتثبّت من **وجود** الحقل لا من
**صدقه** — فبطاقة تُعلن 2020-01-01 وسجلّها 2026-08-15 كانت تمرّ. البوابتان الآن
تسألان عن المضمون والمطابقة، وسبعة اختبارات في `tests/governance/` تحرسهما.

قاعدة صدق التاريخ المعتمَدة: يُرفض المُعلَن إن كان **أقدم** من آخر تعديل فعلي
(تقادم) أو **بعد اليوم** (مستقبل). ولا تُشترَط المطابقة الحرفية حين تُعلن البطاقة
تاريخ اليوم وسجلّها أمس، لأن التصحيح نفسه يُعدِّل الملف فيغيّر ما يُتوقَّع منه —
واشتراطها يُنتج تذبذبًا لا ينتهي، وهو ما رُصِد تنفيذيًّا في 7 بطاقات قبل اعتماد
القاعدة.

### عيوب حقيقية وُجدت في التنفيذ وأُصلحت (لا تُعَد إلى ما كانت)

1. `identity.py::assert_not_key_material` — مدخلات مركَّبة كانت غير قابلة للوصول؛
   صارت مطابقةً بالرموز وبالعبارة.
2. `audit or CrownAudit()` في أربع وحدات كان يُهمل سجلًّا فارغًا مُمرَّرًا؛ صار
   `audit if audit is not None else CrownAudit()`.
3. `succession.py::register_successor_key` كان يعدّل سجل المفاتيح **قبل** التحقق من
   المرحلة؛ صار الفحص خالصًا وسابقًا للأثر.
4. `key_registry.py::rotate` كان يستلزم مفتاحًا نشطًا، فيجمّد التاج بعد إعلان
   الاختراق؛ صار يقبل سلفًا مُسمّى.
5. `identity.py::IdentityGraph.register` كان يستبدل هوية مسجَّلة صامتًا (إبدال
   هوية)؛ صار يرفع `IdentityConflationError`.
6. `recovery.py::ShareHolderDescriptor` كان يقبل حصةً بلا حرز بارد؛ صار يرفض.

### نقطة تفتيش E2.2-E (مغلقة)

```
CHECKPOINT E2.2-E
-----------------
Objective:      التحقق من حدود الأسرار والثقة والحجب عند أي خطر: لا مفتاح خاص في
                الشجرة ولا في التاريخ، ولا سرّ إنتاج مضمَّن، ولا سلطة فوق الملك
Completed:      tools/crown/verify_secret_boundaries.py — 11 بوابة تنفيذية ·
                إخراج سرّ دخول الملك من royal/main.py إلى الإعدادات، بمقارنة
                hmac.compare_digest ورفض 503 عند غيابه أو كونه قيمة نائبة ·
                SECRET_FIELDS و secret_violations() و assert_secrets_configured()
                في common/config.py، وكل حقل سرّي بلا قيمة افتراضية ·
                _signing_secret() في common/auth.py يرفض سرًّا أقصر من 32 محرفًا ·
                توسيع FORBIDDEN_KEY_MATERIAL بالعربية وبتركيب biometric_key ·
                docs/security/SECRET_BOUNDARIES.md · خطوتا CI جديدتان (2ب و2ج)
Tests:          federal/.../tests/test_king_login_boundary.py — 22 اختبارًا جديدًا ·
                tests/crown 321 ناجحًا (كانت 311؛ +10 تحرس معجم السمة الحيوية)
                بتغطية فروع 94.39% · 718 اختبار تاج/سيادة/دستور/حوكمة ناجح ·
                حزمة خدمات الاتحاد 694 ناجحًا و8 متخطّاة · ruff نظيف
Security:       verify_secret_boundaries=0 (11/11) · verify_crown_root_of_trust=0 ·
                crown-check=0 · truth-matrix --check=0 · threat-doc --check=0 ·
                بوابات الهوية الأربع=0 · truth_audit: 110 ← 106 مخالفة، وخط
                الأساس شُدَّ إلى 106 (تشديد لا تخفيف)
Injections:     إعادة سرّ الملك نصًّا إلى royal/main.py ← خروج 1 ·
                كتلة مفتاح خاص في docs/audit/ ← خروج 1 ·
                قيمة افتراضية لـjwt_secret في الإعدادات ← خروج 1 ·
                وعاد الخروج إلى 0 بعد كل استعادة
Documentation:  docs/security/SECRET_BOUNDARIES.md · tools/crown/README.md ·
                هذه النقطة + تصنيف المخالفات أدناه
Commit:         891f6fe
Remote:         مؤكَّد — origin/main = 891f6fe بـgit ls-remote
Remaining:      E2.2-F .. E2.3-B
Next Action:    E2.2-F — إثبات الاستمرارية السيادية من الطرف إلى الطرف
Status:         VERIFIED محليًّا · CI لم تُشغَّل بعد على GitHub
```

### تصنيف مخالفات الأسرار في E2.2-E

| المخالفة | العدد | التصنيف | التصرّف |
|---|---|---|---|
| `amos-king-2026` مكتوب في `royal/main.py` | 1 | **EXISTING** (سبقت هذه المرحلة) | أُخرج إلى الإعدادات، ومقارنة بزمن ثابت، ورفض 503 |
| قيم افتراضية لأسرار الإنتاج في `config.py` | 3 | **EXISTING** | الافتراضي صار فارغًا، والإنتاج يرفض الإقلاع بسرّ ناقص |
| معجم السمة الحيوية إنجليزي وحده في مستودع عربي | 1 | **REAL DEFECT** في الحارس نفسه | وُسِّع المعجم، مع إبقاء `biometric_reader` و«بصمة sha256» مقبولين |
| استثناءان يُبتلعان في الأداة الجديدة | 2 | **NEW** (من عمل هذه الوحدة) | أُصلحا في مصدرهما: تُقرأ الملفات بايتات فتُفحَص الثنائيات أيضًا، وما تعذّر يُعلَن |
| ثابت اختباري باسم يحمل لفظ «سرّ» | 1 | **NEW** | أُعيدت تسميته — ولا استثناء يُضاف إلى الماسح |
| مفتاح خاص في الشجرة أو في 67 التزامًا من التاريخ | 0 | — | لا شيء |
| ارتداد في أي بوابة قائمة | 0 | **REGRESSION** — لا شيء | — |

**ما لم يُنجَز، ويجب ألّا يُدّعى:** كلمة مرور الملك ليست إثبات سيادة. سدادُ دين E9
هنا **جزئي**: أُخرج السرّ من الكود، ولم يُستبدَل بتوقيع بمفتاح الملك بعد. وادّعاء
غير ذلك ادّعاءُ حمايةٍ غير موجودة، وهو أخطر من غيابها.

**ولا تُدّعى حصانة تاريخية مطلقة:** فحص التاريخ يمسح 67 التزامًا في هذا المستودع،
وهو دليلُ نظافةٍ هنا لا برهانٌ على أن سرًّا لم يوجد يومًا في نسخة أخرى.

## 3. ما شُغِّل من اختبارات وبوابات

| الأمر | النتيجة | متى |
|---|---|---|
| `python -m pytest tests/crown/ -q --cov=core.crown --cov-branch` | **299 passed / 0 failed**، تغطية فروع **94%** (2356 عبارة، 486 فرعًا، 64 جزئيًّا)، وأدنى وحدة 92% | 2026-08-16 |
| `python -m ruff check .` | All checks passed | 2026-08-16 |
| `python -m core.crown.cli crown-check` | 9/9 — رمز خروج 0 | 2026-08-16 |
| `python tools/governance/generate_crown_threat_doc.py --check` | مطابقة للتنفيذ | 2026-08-16 |
| `python -m pytest tests/sovereignty tests/constitutional tests/governance -q` | 390 passed (خط الأساس قبل عمل التاج) | 2026-08-16 |
| `python -m core.sovereignty.cli sovereignty-check` | 9/9 (خط الأساس) | 2026-08-16 |

| `python tools/crown/verify_crown_root_of_trust.py` | 11/11 — رمز خروج 0 · وحالات الفشل الأربع تُخرِج 1 | 2026-08-16 |

| `python tools/crown/generate_crown_truth_matrix.py --check` | مطابقة للدليل — رمز 0 | 2026-08-16 |
| `python tools/governance/check_repository_identity.py` | صفر مخالفة هوية | 2026-08-16 |
| `python tools/governance/truth_audit.py . --ratchet` | ثابت عند 110 — لا ارتداد | 2026-08-16 |

### جولة E2.2-E (2026-08-16)

| الأمر | النتيجة |
|---|---|
| `python tools/crown/verify_secret_boundaries.py` | 11/11 — رمز 0 · وثلاثة حقن تُخرِج 1 |
| `python -m pytest tests/crown -q --cov=core.crown --cov-branch` | 321 passed · تغطية فروع 94.39% |
| `python -m pytest tests/crown tests/sovereignty tests/constitutional tests/governance -q` | 718 passed |
| `PYTHONPATH=src pytest tests -q` (federal/executive/services) | 694 passed · 8 skipped |
| `python tools/governance/truth_audit.py . --ratchet` | 110 ← 106، وخط الأساس شُدَّ إلى 106 |
| بوابات الهوية الأربع + `crown-check` + `verify_crown_root_of_trust` + `--check` للمصفوفة والوثيقة | كلها رمز 0 |

**لم يُشغَّل بعد:** CI على GitHub (لا يملك الوكيل تشغيلها)، وإثبات الاستمرارية
السيادية من الطرف إلى الطرف (E2.2-F)، والتحقق العابر للأنظمة (E2.3-A).

## 4. الملفات

**مُضافة:** `core/crown/` (12 وحدة + `README.md` + `NUCLEUS.md`)، `tests/crown/`
(10 ملفات + `conftest.py` + `README.md`)، `docs/security/` (5 ملفات)،
`tools/governance/generate_crown_threat_doc.py`، `docs/audit/ACTIVE_EXECUTION_STATE.md`.

**مُعدَّلة:** لا شيء — لم تُمَسّ `core/sovereignty/` ولا الدستور ولا الفدرالية، ودلالات
E2.1 باقية كما هي.

**مولَّدة:** `docs/security/CROWN_THREAT_MODEL.md` (من `core/crown/threats.py`).

## 5. الأخطاء والمخاطر المعروفة

**Known Failures:** لا فشل معروف في اختبارات التاج حاليًّا.

**Known Risks:**
- بوابات الهوية والتدقيق **لم تُشغَّل** على الملفات الجديدة؛ قد تظهر مخالفات هوية
  (بطاقات، أو مؤشر هدف، أو README مجلد) أو ملاحظات مسح أسرار. تُصنَّف وتُصلَح في
  E2.2-D/E — ولا تُخفى ولا تُعطَّل بوابة.
- قصّ ذيل سلسلة السجل لا يُكشَف من داخل الملف وحده (حدّ مُعلَن، لا عيب مخفي).
- العتاد الإنتاجي والإجراءات البشرية غير منفَّذة بحكم طبيعتها.

## 6. ما تبقّى وترتيبه

| الوحدة | الموضوع | الحال |
|---|---|---|
| E2.2-A | توثيق نطاق التاج ونواته | **VERIFIED** (`cda68d5`، البعيد مؤكَّد) |
| E2.2-B | بوابة CI `crown-root-of-trust` | **VERIFIED** (11 فحصًا + 8 خطوات CI، وحالات الفشل مُجرَّبة) |
| E2.2-C | خارطة المرحلة ومصفوفة الحقيقة | **VERIFIED** (مصفوفة مولَّدة تُسقِط الادّعاء إلى دليله) |
| E2.2-D | بوابات الهوية | **VERIFIED** (`3fed334`، البعيد مؤكَّد) — عيبان حقيقيان في الحُرّاس أنفسهم |
| E2.2-E | تحقق الأسرار وحدود الثقة | **VERIFIED** (`891f6fe`، البعيد مؤكَّد) — 11 بوابة، وثلاثة حقن، وسرّ الملك خرج من الكود |
| E2.2-F | إثبات الاستمرارية السيادية من الطرف إلى الطرف | PENDING |
| E2.2-G | الحِزَم الكاملة عبر الأنظمة | PENDING |
| E2.3-A | التحقق النهائي العابر للأنظمة | PENDING |
| E2.3-B | تقرير الإثبات وإغلاق المرحلة | PENDING |

## 7. الأمر التالي حرفيًّا

E2.2-F: اكتب `tests/crown/test_sovereign_continuity_e2e.py` يُثبت السلسلة كاملةً في
اختبار واحد متصل، لا في اختبارات متفرقة:

```
K1 ACTIVE ← مرساة محقَّقة خارج القناة ← أمر D1 موقَّع ← لا نقض من تابع ←
تنفيذ ← قيد في السجل ← إعلان اختراق K1 وإبطاله ← D1 التاريخي ما يزال قابلًا
للتحقق ← تفعيل K2 ← تنفيذ D2 ← رفض أمر جديد بـK1 ← حدث أمني مسجَّل ←
لا تاج زائف ولا خلافة ذاتية
```

ثم قائمة الخصم: استبدال مرساة، وإرجاع نسخة، وتخفيض إصدار، وحارس يدّعي سيادة،
وخليفة يُفعِّل نفسه. ثم:

```bash
python -m pytest tests/crown -q --cov=core.crown --cov-branch --cov-fail-under=90
python tools/crown/verify_secret_boundaries.py && python tools/crown/verify_crown_root_of_trust.py
git commit -m "test(crown): prove sovereign continuity and adversarial resilience"
git push origin main && git ls-remote origin main   # وتحقق من التطابق
```

## 8. ما لا يُفعَل بعد (Do NOT Do Yet)

- **E3 مقفلة.** لا تبدأ حتى يصدر `docs/audit/E2_2_E2_3_PROOF_REPORT.md` بحال PASS،
  وتُثبَت كل البوابات، ويُتحقَّق من البعيد، ويقول هذا الملف صريحًا: `E3 UNBLOCKED`.
- لا `force-push`، ولا إعادة كتابة تاريخ منشور، ولا دمج نقاط التفتيش بعد دفعها.
- لا رفع حال أي تهديد إلى «منفَّذ» بلا اختبار قائم يُشير إليه بالاسم.
- لا تعطيل بوابة ولا تخفيض عتبة تغطية ولا تقليل نطاق فحص لتمرير بوابة.

## 9. سجل نقاط التفتيش

| # | الوحدة | الالتزام | البعيد | الحال |
|---|---|---|---|---|
| 0 | أساس التنفيذ (كود + اختبارات + توثيق أمني) | `e3d0c8a` | مؤكَّد | VERIFIED |
| E2.2-A | توثيق نطاق التاج ونواته وذاكرة التسليم | `cda68d5` ثم `fb5ce9d` | مؤكَّد بـ`ls-remote` | VERIFIED |
| E2.2-B | بوابة CI `crown-root-of-trust` (وكشف بوابة زائفة) | `b13cd87` | مؤكَّد بـ`ls-remote` | VERIFIED |
| E2.2-C | خارطة المرحلة ومصفوفة الحقيقة المولَّدة | `dae73f6` | مؤكَّد بـ`ls-remote` | VERIFIED |
| E2.2-D | بوابات الهوية (وعيبان في الحُرّاس أنفسهم) | `3fed334` | مؤكَّد بـ`ls-remote` | VERIFIED |
| E2.2-E | حدود الأسرار والثقة | `891f6fe` | مؤكَّد بـ`ls-remote` | VERIFIED |

## المراجع
- خارطة المرحلة: [`PHASE_E_ROADMAP.md`](PHASE_E_ROADMAP.md)
- مصفوفة الحقيقة: [`TRUTH_MATRIX.md`](TRUTH_MATRIX.md)
- تعريف الإنجاز: [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md)
- معمار الحماية: [`../security/CROWN_SOVEREIGNTY_PROTECTION.md`](../security/CROWN_SOVEREIGNTY_PROTECTION.md)
