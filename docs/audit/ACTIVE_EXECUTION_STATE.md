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
| 10 | جولة استرداد الحالة وبداية E2.2-G |
| 11 | إصلاح توافق PostgreSQL (E2.2-G) |
| 12 | قرار المرجعية: مخطَّط tasks والسجل القانوني للتدقيق (E2.2-G) |

---

## 1. الحالة الراهنة

| الحقل | القيمة |
|---|---|
| Current Phase | E2.2 — Crown Root of Trust & Protection |
| Current Subphase | E2.2-G — Full relevant suite across systems |
| Current Objective | تشغيل الحِزَم الكاملة عبر الأنظمة (تاج + سيادة + دستور + حكامة + خدمات فدرالية) مع ruff والفحوص الساكنة ومسح الأسرار، وأي ارتداد = BLOCK |
| Status | E2.2-A..F = VERIFIED · E2.2-G = IN_PROGRESS — عيب توافق PostgreSQL **أُصلح في مصدره وأُثبت تنفيذيًّا** (§11)، وبوابة `ruff format` **صارت خضراء** بعد تنسيق تنسيقي بحت مُثبَت بتطابق AST (§11.6). لم تُشاهَد جولة CI فعلية بعد |
| Current Commit SHA | `7fef2e1` (إصلاح توافق PostgreSQL — مدفوع ومؤكَّد على `origin/main`) |
| Last Verified Commit | `7fef2e1` — مؤكَّد على `origin/main` بـ`git ls-remote` |
| Previous Checkpoint SHA | `b4deb5a` (E2.2-F) · `24cae55` (تثبيت حالة E2.2-E) · `891f6fe` (E2.2-E) · `3fed334` (E2.2-D) · `dae73f6` (E2.2-C) · `b13cd87` (E2.2-B) · `fb5ce9d` (E2.2-A) · `098beb3` (ما قبل التاج) |
| Remote Confirmed | نعم — `origin/main = 7fef2e1` مؤكَّد بـ`git ls-remote` (وقت كتابة §11.6) |
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

### نقطة تفتيش E2.2-F (مغلقة)

```
CHECKPOINT E2.2-F
-----------------
Objective:      إثبات الاستمرارية السيادية من الطرف إلى الطرف عبر مسار **منفَّذ**،
                لا عبر سلسلة يُركّبها الاختبار
Completed:      core/crown/sovereign_session.py (بوابات متسلسلة بلا سلطة) ·
                tests/crown/test_sovereign_continuity_e2e.py (11 اختبارًا) ·
                tools/crown/prove_sovereign_continuity.py (إثبات تنفيذي خارج pytest) ·
                خطوة CI «بوابة 6ب» · مدخل sovereign_session.py في مولِّد المصفوفة
Tests:          332 اختبار تاج ناجح · تغطية فروع 94.48% · sovereign_session.py 95.0%
                729 ناجحًا في (crown + sovereignty + constitutional + governance)
Security:       أداة الإثبات 18 ادّعاءً برمز 0 · ثلاثة حقن فشل أخرجت BLOCKED برمز 1:
                (1) حذف بوابة المرساة (2) حارس يقبل النقض (3) قبول الأوامر في كل حال
Real defect:    test_grand_crown_lifecycle_end_to_end كان **يدّعي** بقاء D1 قابلًا
                للتحقق بعد الاختراق، والاستدعاء لم يفحص النتيجة أصلًا. والقاعدة
                المنفَّذة في was_valid_at عكس ذلك عمدًا: الاختراق يُبطل الماضي
                والإحالة لا تُبطله. صُحِّح الاختبار والوثيقة إلى القاعدة المنفَّذة،
                وأُضيف اختبار للفرق بين التدوير والاختراق.
Truth audit:    ارتفع إلى 108 من عمل هذه الوحدة (استثناءان يُبتلعان) ثم أُصلح في
                مصدره وعاد إلى 106 — لا تخفيف عتبة ولا استثناء في الماسح
Documentation:  مصفوفة الحقيقة مولَّدة من جديد · sovereign_session.py مُسقَط إلى
                TESTED لأن لا وحدة إنتاج تستوردها — والإسقاط أُبقي ولم يُزيَّف
Commit:         b4deb5a
Remote:         مؤكَّد — origin/main = b4deb5a بـgit ls-remote
Remaining:      E2.2-G · E2.3-A · E2.3-B
Next Action:    E2.2-G — الحِزَم الكاملة عبر الأنظمة
Status:         VERIFIED محليًّا · CI لم تُشغَّل بعد على GitHub
```

**ما لا يُدَّعى في E2.2-F:** السلسلة K1→K2 كانت مُختبَرة قبل هذه الوحدة في
`test_crown_grand_tests.py`، فليست جديدة. الجديد ثلاثة: أن السلسلة صارت **مسارًا
منفَّذًا** يسقط إن حُذفت منه بوابة (وقد أُثبت بالحقن)، وأن الإثبات صار يُشغَّل خارج
pytest برمز خروج، وأن حالات لم تكن مغطّاة صارت مغطّاة (الأمر قبل المرساة، ونقض خفيّ،
ومفتاح نشط ثانٍ، واستئناف الأوامر بلا إعلان حضور، والتدوير مقابل الاختراق).

**ولا يُدَّعى الاندماج:** `sovereign_session.py` لا تستوردها وحدة إنتاج بعد، ولذلك
حالتها `TESTED` لا `INTEGRATED` في المصفوفة. ولم تُلفَّق لها استيرادة من `cli.py`
لترقية الحالة، لأن ترقية بلا استعمال حقيقي كذبٌ على المصفوفة نفسها.

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

### جولة E2.2-F (2026-08-16)

| الأمر | النتيجة |
|---|---|
| `python tools/crown/prove_sovereign_continuity.py` | PASS — 18 ادّعاءً، رمز 0 · وثلاثة حقن أخرجت BLOCKED برمز 1 |
| `python -m pytest tests/crown -q --cov=core.crown --cov-branch --cov-fail-under=90` | 332 passed · تغطية فروع 94.48% |
| `python -m pytest tests/crown tests/sovereignty tests/constitutional tests/governance -q` | 729 passed |
| `python -m ruff check .` | All checks passed |
| `python tools/governance/truth_audit.py . --ratchet` | 108 ← 106 بعد الإصلاح في المصدر · ثابت عند 106 |
| `crown-check` · `verify_crown_root_of_trust` · `verify_secret_boundaries` · `--check` للمصفوفة والوثيقة · بوابات الهوية | كلها رمز 0 |

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
- **وضع Postgres في حزمة خدمات الاتحاد معطوب** — `AMOS_RUN_POSTGRES_TESTS=1` يُسقِط
  اختبارات قائمة تفترض sqlite. التفصيل والتصنيف في §10.4 — ولا يُدّعى أنه محلول.
- **بيانة اعتماد نافذة في `.env.example` المُلتزَم** — التدوير واجب، انظر §10.4.

## 6. ما تبقّى وترتيبه

| الوحدة | الموضوع | الحال |
|---|---|---|
| E2.2-A | توثيق نطاق التاج ونواته | **VERIFIED** (`cda68d5`، البعيد مؤكَّد) |
| E2.2-B | بوابة CI `crown-root-of-trust` | **VERIFIED** (11 فحصًا + 8 خطوات CI، وحالات الفشل مُجرَّبة) |
| E2.2-C | خارطة المرحلة ومصفوفة الحقيقة | **VERIFIED** (مصفوفة مولَّدة تُسقِط الادّعاء إلى دليله) |
| E2.2-D | بوابات الهوية | **VERIFIED** (`3fed334`، البعيد مؤكَّد) — عيبان حقيقيان في الحُرّاس أنفسهم |
| E2.2-E | تحقق الأسرار وحدود الثقة | **VERIFIED** (`891f6fe`، البعيد مؤكَّد) — 11 بوابة، وثلاثة حقن، وسرّ الملك خرج من الكود |
| E2.2-F | إثبات الاستمرارية السيادية من الطرف إلى الطرف | **VERIFIED محليًّا** — مسار منفَّذ + إثبات تنفيذي + ثلاثة حقن · وعيب ادّعاء في اختبار قائم صُحِّح |
| E2.2-G | الحِزَم الكاملة عبر الأنظمة | **IN_PROGRESS** — بوابة تغطية نواة الدستور **حمراء** (87.91% مقابل 90%) وهي حمراء قبل هذا العمل (§12.9)، وبقية البوابات خضراء، وعيب توافق PostgreSQL أُصلح وأُثبت بـ158/158 على قاعدة حقيقية (§11)، وبوابة `ruff format` صارت خضراء (§11.6). وبَندا §11.5 المفتوحان أُصلحا بقرار مالك وأُثبتا بـ191/191 على قاعدة حقيقية (§12). يبقى: مشاهدة جولة CI فعلية |
| E2.3-A | التحقق النهائي العابر للأنظمة | PENDING |
| E2.3-B | تقرير الإثبات وإغلاق المرحلة | PENDING |

## 7. الأمر التالي حرفيًّا

E2.2-G — شغّل الحِزَم الكاملة عبر الأنظمة، وأي ارتداد = BLOCK يُصلَح في مصدره:

```bash
python -m pytest tests/crown tests/sovereignty tests/constitutional tests/governance -q
cd federal/executive/services && PYTHONPATH=src python -m pytest tests -q && cd -
python -m ruff check .
python tools/crown/verify_crown_root_of_trust.py && python tools/crown/verify_secret_boundaries.py
python tools/crown/prove_sovereign_continuity.py
python tools/governance/truth_audit.py . --ratchet
git commit -m "test(crown): verify cross-system sovereignty integrity"
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
| E2.2-E | حدود الأسرار والثقة | `891f6fe` ثم `24cae55` | مؤكَّد بـ`ls-remote` | VERIFIED |
| E2.2-F | الاستمرارية السيادية عبر مسار منفَّذ (وتصحيح ادّعاء في اختبار قائم) | `b4deb5a` | مؤكَّد بـ`ls-remote` | VERIFIED |

## 10. جولة استرداد الحالة وبداية E2.2-G (2026-08-16)

وكيل جديد استلم المستودع من نسخة نقية (`git clone`)، ولم يعتمد على ذاكرة محادثة
ولا على عمل محلي سابق. ما يلي مخرجات أوامر شُغِّلت فعلًا في هذه الجولة.

### 10.1 حالة المستودع عند الاستلام

| الفحص | النتيجة |
|---|---|
| `git rev-parse HEAD` | `dd1f60c462752a74aad8775b538609d1770cae3b` |
| `git ls-remote origin main` | `dd1f60c` — **مطابق تمامًا لـHEAD** |
| `git status --porcelain -uall` | فارغ — لا تغيير محلي ولا ملف غير متتبَع |
| `git branch --show-current` | `main` |
| عمل محلي غير مدفوع | **لا شيء** — لا مرحلة جزئية مفقودة، ولا شيء حُرِف أو أُعيد ضبطه |

الـcommit الأخير `dd1f60c` هو توثيق لا كود، والجوهر التنفيذي لـE2.2-F في `b4deb5a`.

### 10.2 إعادة التحقق من E2.2-F — بالتشغيل لا بالوثيقة

| الدليل | المقاس الآن | الموثَّق سابقًا | مطابق |
|---|---|---|---|
| `core/crown/sovereign_session.py` | موجود (310 أسطر، داخل `b4deb5a`) | موجود | ✓ |
| `tests/crown/test_sovereign_continuity_e2e.py` | موجود (326 سطرًا) | موجود | ✓ |
| `tools/crown/prove_sovereign_continuity.py` | موجود (319 سطرًا) | موجود | ✓ |
| خطوة CI «بوابة 6ب» | `ci.yml:320-323` تُشغِّل أداة الإثبات | موجودة | ✓ |
| `python tools/crown/prove_sovereign_continuity.py` | **PASS — رمز 0** | PASS · 18 ادّعاءً | ✓ |
| `pytest tests/crown --cov-branch --cov-fail-under=90` | **332 passed · 94.48%** · `sovereign_session.py` 95% | 332 · 94.48% · 95.0% | ✓ |
| `pytest tests/crown tests/sovereignty tests/constitutional tests/governance` | **729 passed** | 729 passed | ✓ |

**حكم E2.2-F:** موجودة فعلًا على `origin/main`، وأرقامها أُعيد قياسها فطابقت الموثَّق
حرفًا بحرف. لا ارتداد، ولا ادّعاء غير مسند.

### 10.3 بوابات E2.2-G التي مرّت فعلًا

| الأمر | النتيجة |
|---|---|
| `python -m ruff check .` | All checks passed — رمز 0 |
| `tools/crown/verify_crown_root_of_trust.py` | 11/11 — رمز 0 |
| `tools/crown/verify_secret_boundaries.py` | 11/11 — رمز 0 |
| `python -m core.crown.cli crown-check` | `"passed": true` — رمز 0 |
| `tools/crown/generate_crown_truth_matrix.py --check` | مطابقة للدليل — رمز 0 |
| `tools/governance/generate_crown_threat_doc.py --check` | مطابقة للتنفيذ — رمز 0 |
| بوابات الهوية الأربع | كلها رمز 0 · 45 إقليمًا مسجّلًا · صفر مخالفة |
| `tools/governance/truth_audit.py . --ratchet` | **ثابت عند 106** — لا ارتداد |
| `PYTHONPATH=src pytest tests` (خدمات الاتحاد، التركيب المدعوم) | **694 passed · 8 skipped** |
| حالة الشجرة بعد كل البوابات | نقية — لا انحراف مولَّد |

### 10.4 أول تشغيل حقيقي لـPostgres — وما كشفه

الثمانية المتخطّاة في `tests/test_phase1_postgres.py` لم تُشغَّل قطّ من قبل — لا محليًا ولا في CI.
وملاحظة `.env.example` تقول إن المضيف المباشر غير قابل للوصول. **وهي متقادمة جزئيًا:**
`db.mqcfmwtdaymrmwvthqyw.supabase.co` لا يحمل سجل A إطلاقًا (IPv6 وحده)، لكن مجمّع الاتصال
`aws-0-ap-northeast-1.pooler.supabase.com` يعمل على 5432 وعلى 6543 بمستخدم `postgres.<project_ref>`.

| الأمر | النتيجة |
|---|---|
| اتصال `psycopg2` عبر المجمّع (5432 و 6543) | نجح — PostgreSQL 17.6، 36 جدولًا في `public`، RLS مُفعّل على كلّها |
| `AMOS_RUN_POSTGRES_TESTS=1 pytest tests/test_phase1_postgres.py` | **8 passed** — أول إثبات تنفيذي لمسار الاستمرارية على Postgres حقيقي |
| الحزمة الكاملة في وضع Postgres | **FAIL — عيب حقيقي، والقياس الكلي لم يُكمل بعد** |

#### عيب حقيقي مكشوف (EXISTING — يسبق E2.2)

`tests/conftest.py:21-25` يُحوّل **الحزمة بأكملها** إلى Postgres حين تُفعّل
`AMOS_RUN_POSTGRES_TESTS=1`، بإسناد `AMOS_DATABASE_URL` إلى `AMOS_TEST_DATABASE_URL`. وسبعة
اختبارات في `tests/test_common_branches.py` **تفترض أن الرابط sqlite دائمًا** فتسقط حتمًا:

```
test_get_database_url_uses_env       assert 'postgresql://...' .startswith('sqlite')
test_is_postgres_false_for_sqlite    assert _is_postgres() is False   ← صار True
test_pg_connect_args_sqlite_branch   {'sslmode':'require','connect_timeout':15} != {'check_same_thread': False}
test_get_engine_returns_sqlite_engine  'sqlite' not in engine.url
TestEventPublisher × 3               تكتب SQL بلهجة sqlite (علامة ?) على Postgres
```

ورُصدت أيضًا إخفاقات وأخطاء جماعية في `test_edge_branches.py` و`test_event_bus.py` و
`test_expansion.py` و`test_federation.py` في الوضع نفسه — **وعددها النهائي غير
مقاس بعد، ولا يُدّعى رقم لها**؛ الجولة تتجاوز الساعة لأن كل دورة تعبر الشبكة إلى طوكيو.

**التصنيف:** `EXISTING` — ليس ارتدادًا من E2.2-F ولا من E2.2-G. التركيب المدعوم
(Postgres معطّل) ما زال أخضر بـ694/8. لكن وضع Postgres المُعلَن في `conftest.py`
**معطوب بنيوًّا**، ووجود مفتاح تشغيل لمسار لم يُجرَّب قطّ هو نفسه ثقة كاذبة.

**ما لم يُفعل قصدًا:** لم تُعدّل ولا تُسكت ولا تُتخطّى أي من الاختبارات الساقطة، ولم
يُرفع أي استثناء في `conftest.py`. الإصلاح في المصدر يحتاج قرارًا من مالك المشروع.

#### خطر أمني مُعلَن (لا يُخفى)

`.env.example` المُلتزَم يحمل **كلمة مرور postgres حقيقية نصًّا** لمشروع Supabase قائم،
ومفتاح `sb_publishable_...`. المالك يعدّها قاعدة تجريبية، و`verify_secret_boundaries.py`
يمرّ لأن `.env.example` ملف قالب. **ومع ذلك هي بيانة اعتماد نافذة في تاريخ عام،
وتدويرها واجب قبل أي استخدام إنتاجي.** لم تُحذف هنا لأن حذفها لا يمحوها من التاريخ،
والمعالجة الصادقة هي التدوير لا الإخفاء.

### 10.5 الأمر التالي والمعوّقات

| الحقل | القيمة |
|---|---|
| NEXT EXACT ACTION | ~~قرار المالك في عيب وضع Postgres~~ → **حُسم: اختار المالك المسار (أ) وأُنجز، انظر §11.** الأمر التالي في §11.7 |
| BLOCKERS | ~~وضع Postgres يُسقِط اختبارات قائمة~~ → مُصلَح (§11.3) · ~~القياس الكلي غير مكتمل~~ → قيس (§11.4) |
| ممنوع | إغلاق E2.2-G وادّعاء PASS قبل حل ما سبق · E3 ما زالت مقفلة |

## 11. إصلاح توافق PostgreSQL (E2.2-G · 2026-08-16)

اختار مالك المشروع صراحةً **المسار (أ): إصلاح المصدر والاختبارات، لا تجميد PostgreSQL.**
كل رقم في هذا القسم مخرج أمر شُغِّل فعلًا على قاعدة Supabase الحقيقية عبر المجمّع
`aws-0-ap-northeast-1.pooler.supabase.com`، لا تقدير ولا استنتاج.

### 11.1 خط الأساس قبل الإصلاح (مقاس، لا مقدَّر)

الملفات السبعة المستهدفة في وضع PostgreSQL، قبل أي تعديل:

```
17 failed, 93 passed, 30 errors in 1120.96s (0:18:40)   [140 مجموعة]
```

### 11.2 الأسباب الجذرية الأربعة (لا الأعراض)

| # | السبب الجذري | الموضع | الأثر الحقيقي |
|---|---|---|---|
| ج1 | `db_cursor()` كان يسرّب paramstyle الخاص بالمحرك إلى مستدعيه؛ فكُتب SQL الإنتاج بلهجة psycopg2 (`%s`) والاختبارات بلهجة sqlite (`?`) | `common/database.py` · `common/events.py` · `api_gateway/store.py` | مسار الأحداث كان **لا يعمل أبدًا على SQLite** والفشل يُبتلَع في `except Exception` فيُسجَّل تحذيرًا فقط — سجل تدقيق لا يُثبت شيئًا |
| ج2 | ترتيب سلسلة البصمات كان `ORDER BY id`، و`audit_log.id` في PostgreSQL هو `UUID DEFAULT gen_random_uuid()` | `common/events.py` · `migrations/001_init.sql` | ترتيب **عشوائي** على PostgreSQL: «آخر بصمة» كانت صفًّا غير مُعرَّف، أي كسر صامت لسلسلة الكتل |
| ج3 | `AMOS_RUN_POSTGRES_TESTS=1` كان يحوّل **الحزمة كلها** إلى PostgreSQL، بما فيها اختبارات مكتوبة لدلالات SQLite | `tests/conftest.py` | 7 إخفاقات زائفة + إرهاق تجمّع اتصالات المزوّد (`EMAXCONNSESSION: max clients … pool_size: 15`) وهو مصدر الأخطاء الثلاثين كلها |
| ج4 | حجم تجمّع الاتصالات مثبَّت في الكود (`pool_size=5, max_overflow=10`) بلا أي مَخرج ضبط، ومنطق معاملات الاتصال مكرَّر في موضعين | `common/database.py` | تشغيل مستحيل مقابل أي وسيط مُجمَّع محدود العملاء |

**عيب خامس مكشوف ومُصلَح:** التجهيزة `_set_pg_url` في `tests/test_phase1_postgres.py` كانت
تكتب `os.environ` مباشرة ولا تردّ القيمة، فتُسرِّب لهجة PostgreSQL إلى الملفات التالية
في نفس الجلسة. صارت تستخدم `monkeypatch` فتُعزل.

### 11.3 ما نُفِّذ فعلًا

**طبقة SQL محايدة اللهجة — في مسار الإنتاج، لا في الاختبارات:**
- `db_dialect()` صار المصدر الوحيد لتحديد اللهجة؛ لا مقارنات نصية متفرقة.
- `PortableCursor` + `translate_placeholders()`: كل الكود يكتب المحاجيز بالشكل
  القانوني `?` فقط، والمغلّف يترجمها إلى `%s` على psycopg2، يتجاهل ما داخل السلاسل
  النصية، ويضاعف `%` الحرفي. السجلات تعود قواميس في اللهجتين.
- `events.py` و`api_gateway/store.py` صارا بلا SQL خاص بلهجة واحدة.
- `audit_log_ddl()` / `ensure_audit_log_table()` / `drop_audit_log_table()`: تعريف
  **واحد** للجدول في اللهجتين، يُستخدم في الإنتاج والاختبار معًا. حُذف تعريف
  SQLite المكرر من `tests/test_common_branches.py`.
- عمود `seq` متزايد رتيب (`AUTOINCREMENT` / `GENERATED BY DEFAULT AS IDENTITY`) صار
  الأساس الوحيد للترتيب، و`events.py` يستخدم `ORDER BY seq`. للنشرات القائمة:
  هجرة جديدة `migrations/003_audit_log_seq.sql`.
- `_pg_connect_args()` صارت المصدر الوحيد لمعاملات الاتصال ويستدعيها `get_engine()`؛
  وحجم التجمّع صار قابلًا للضبط بـ`AMOS_DB_POOL_SIZE` / `AMOS_DB_MAX_OVERFLOW`
  (الافتراضيات كما كانت: 5 و10 — **لم يُخفَّض أي حدّ**).
- أُزيلت أربع تعليقات `# pragma: no branch` كانت تدّعي أن فروع PostgreSQL
  «إنتاجية فقط»؛ صارت الفروع مقيسة فعلًا.

**عزل الاختبارات (بلا حذف ولا تخطٍّ ولا خفض حدّ):**
- `conftest.py`: `AMOS_RUN_POSTGRES_TESTS=1` **لم يعد** يحوّل الحزمة كلها. قاعدة
  الاختبار الافتراضية SQLite دائمًا. من يريد PostgreSQL يطلبه صراحةً.
- تجهيزتان جديدتان: `sqlite_url` (تثبيت لهجة SQLite صراحةً) و`postgres_url`
  (تحويل اختبار واحد إلى PostgreSQL الحقيقي ثم إعادة البيئة).
- الاختبارات السبعة التي كانت تؤكّد دلالات SQLite صارت تطلب `sqlite_url`، فنتيجتها
  مستقلة عن أي متغيّر بيئة خارجي. **لم يُحذف ولا يُتخطَّ أي اختبار منها.**
- دعم SQLite الخفيف محفوظ كما هو: الحزمة الافتراضية لا تحتاج شبكة ولا خدمة.

**اختبارات جديدة هي الدليل الوحيد على عبارة «PostgreSQL مدعوم»:**
`tests/test_phase1_postgres_events.py` — 11 اختبارًا على قاعدة حقيقية تُثبت: لهجة
المؤشر، ودورة المحاجيز `?` كاملةً، وشكل السجل قاموسًا، ووجود `seq` ورتابته،
وأن `get_last_chain_hash()` يعيد **آخر صف إدراجًا** لا صفًّا عشوائيًّا، وأن
`publish()` **يُثبِت الصف فعلًا** في `audit_log` بلا رجوع صامت، وأن الحدث الثاني
يربط ببصمة الأول، وأن `verify_chain()` يميّز السليم من المتلاعب به ومن غياب الجدول.
وأُضيفت 7 اختبارات فروع في `test_common_branches.py` لطبقة الترجمة والفرع المقابل
لـ`_is_postgres` / `_pg_connect_args`.

### 11.4 النتيجة بعد الإصلاح (مقاسة)

| ما شُغِّل | النتيجة |
|---|---|
| الملفات السبعة على **PostgreSQL الحقيقي** | **158 passed, 0 failed, 0 errors, 0 skipped** in 241.12s |
| الحزمة الكاملة `federal/executive/services/tests` على SQLite | **701 passed, 19 skipped** in 90.59s |
| `tests/crown tests/sovereignty tests/constitutional tests/governance` | **729 passed** |
| بوابة تغطية التاج `--cov-branch --cov-fail-under=90` | **332 passed · 94.48%** — الحدّ 90% كما هو |
| `ruff check .` (المستودع كله) | All checks passed |
| `ruff check src/ tests/` بـruff 0.6.9 المثبَّت في CI | All checks passed |
| `truth_audit.py . --ratchet` | **ثابت عند 106** — لم يزد |
| 13 بوابة حكامة/دستور/سيادة/تاج (نفس أوامر `ci.yml`) | 13/13 PASS |

المقارنة الصريحة: من `17 failed · 93 passed · 30 errors` في 1120 ثانية، إلى
`158 passed · 0 failed · 0 errors` في 241 ثانية. والزيادة في الحزمة الافتراضية
`694 → 701` ناجحًا و`8 → 19` متخطّىً هي الاختبارات الجديدة نفسها (7 تعمل على
SQLite، و11 تُطلَب صراحةً على PostgreSQL).

### 11.5 ما لم يُدَّع

- **لا يُقال إن PostgreSQL مدعوم في كل المستودع.** المُثبَت تنفيذيًّا: طبقة
  `db_cursor` وطبقة الأحداث وسجل التدقيق ونماذج ORM السبعة والاستمرارية عبر إعادة
  التشغيل. ما لم يُشغَّل على PostgreSQL لا يُوصف بأنه مُثبَت.
- ~~**عيب قائم لم يُصلَح:** مخطَّطان متضاربان لجدول `tasks`~~ → **أُصلح بقرار مالك
  في §12.** كان `PostgresTaskStore` يخاطب `tasks.task_id` وهو عمود غير موجود في
  نموذج ORM ولا في القاعدة الفعلية، ثم **يرجع صامتًا إلى الذاكرة**. صار `TaskModel`
  المرجع الوحيد، وأُزيل مسار SQL الخام والرجوع الصامت. التفصيل والأدلة في §12.2–12.3.
- ~~**عيب قائم ثانٍ لم يُصلَح:** اختلاف الشكل المهشّم بين `publish` و`verify_chain`~~
  → **أُصلح بقرار مالك في §12.** صار للطرفين سجل قانوني واحد
  (`canonical_audit_record`) بلا تغيير الخوارزمية. التفصيل والأدلة في §12.4–12.6.

### 11.6 بوابة `ruff format --check` — كانت حمراء، وصارت خضراء

`ci.yml:29` يشغّل `ruff format --check src/ tests/` بـ`ruff==0.6.9`. تشغيلها على
`origin/main` (`b7c4089`) في شجرة عمل نظيفة عبر `git worktree`:

```
6 files would be reformatted, 111 files already formatted
```

الملفات: `common/config.py` · `common/database.py` · `common/durable_event_bus.py` ·
`tests/test_common_branches.py` · `tests/test_inmemory_stores.py` ·
`tests/test_king_login_boundary.py`.

**هذا كان سابقًا لهذا العمل تمامًا.** ولأن مهمة `test` معلَّقة بـ`needs: lint`، فقد كانت
مهام CI التالية لا تُنفَّذ على `main` أصلًا. بعد إصلاح توافق PostgreSQL صار العدد **5**
(تنسَّق `database.py` ضمنًا، وملفي الجديد نظيف).

**ثم أمر المالك صراحةً بتنسيق الملفات الخمسة، فنُفِّذ:**

| الحقل | القيمة |
|---|---|
| الأداة | `ruff==0.6.9` — **نفس النسخة المثبَّتة في `ci.yml`**، لا نسخة أحدث |
| الأمر | `ruff format` على الملفات الخمسة بأسمائها، لا على المستودع |
| النتيجة | `5 files reformatted` ثم `118 files already formatted` → **البوابة خضراء** |
| حجم التغيير | 5 ملفات · +17 / −23 سطرًا |

**إثبات أن التغيير تنسيقي بحت:** قُوبل تمثيل `ast.dump(ast.parse(...))` لكل ملف قبل
التنسيق (من `git show HEAD:<path>`) وبعده:

```
AST IDENTICAL   common/config.py
AST IDENTICAL   common/durable_event_bus.py
AST IDENTICAL   tests/test_common_branches.py
AST IDENTICAL   tests/test_inmemory_stores.py
AST IDENTICAL   tests/test_king_login_boundary.py
ALL FORMATTING-ONLY: True
```

أي لا تغيّر سلوكي ممكن: الشجرة النحوية متطابقة حرفيًّا في الملفات الخمسة.

**ما أُعيد تشغيله بعد التنسيق (لا يُكتفى بالبوابة وحدها):**

| ما شُغِّل | النتيجة |
|---|---|
| `ruff format --check src/ tests/` بـ0.6.9 (`ci.yml:29`) | **118 files already formatted** — أخضر |
| `ruff check src/ tests/` بـ0.6.9 (`ci.yml:28`) | All checks passed |
| `ruff check .` — بوابة المستودع كله (`ci.yml:35`) | All checks passed |
| الحزمة الكاملة للخدمات (SQLite) | **701 passed · 19 skipped** |
| الملفات السبعة على **PostgreSQL الحقيقي** | **158 passed · 0 failed · 0 errors** |
| التاج + السيادة + الدستور + الحكامة | **729 passed** |
| بوابة تغطية التاج | **332 passed · 94.48%** — الحدّ 90% كما هو |
| `tests/smoke/run_smoke_tests.py` | PASS |
| 13 بوابة حكامة/دستور/سيادة/تاج | **13/13 PASS** |
| `truth_audit.py . --ratchet` | **ثابت عند 106** — لم يزد |

تغيّر `truth_matrix.json` هو انزياح أرقام أسطر وعدّ سطور فقط (19891 → 19886)؛
عدد المخالفات لم يتغيّر.

**ما يبقى غير مزعوم:** البوابتان خضراوان محليًّا على نفس نسخة الأداة ونفس الأوامر،
لكن **لم يُشاهَد تشغيل CI فعلي على GitHub بعد هذا الدفع**. خُضرة CI الفعلية تُثبت
بمشاهدة الجولة، لا بالاستنتاج المحلي.

### 11.7 الأمر التالي والمعوّقات

| الحقل | القيمة |
|---|---|
| NEXT EXACT ACTION | ~~(1) تنسيق الملفات الخمسة~~ → **أُنجز (§11.6)**. يبقى قرار المالك في بندين: (2) توحيد مخطَّط `tasks` المتضارب · (3) توحيد شكل حساب البصمة بين `publish` و`verify_chain`. ثم مشاهدة جولة CI فعلية على GitHub قبل أي حديث عن إغلاق E2.2-G |
| BLOCKERS | ~~بوابة `ruff format --check` حمراء~~ → خضراء محليًّا بنفس نسخة الأداة (§11.6) · يبقى أن جولة CI الفعلية لم تُشاهَد بعد |
| ممنوع | إعلان E2.2-G = PASS قبل مشاهدة جولة CI فعلية خضراء · إعلان «PostgreSQL مدعوم» خارج ما شُغِّل · E3 ما زالت مقفلة |
| بيانة الاعتماد | كلمة مرور `.env.example` **تُركت كما هي بقرار المالك الصريح**. الخطر المُعلَن في §10.4 قائم ولا يُعدّ مُعالَجًا. |

## 12. قرار المرجعية: مخطَّط tasks والسجل القانوني للتدقيق (E2.2-G · 2026-08-16)

هذا القسم يوثّق **قرار مالك** صريحًا في البندين المفتوحين في §11.5، ثم ما نُفِّذ
وما قيس. الأرقام كلها مخارج أوامر شُغِّلت، وقاعدة PostgreSQL هي قاعدة Supabase
الحقيقية عبر المجمّع، لا محاكاة.

### 12.1 نص القرار كما ورد

**(1) المهام:** طبقة قاعدة البيانات / PostgreSQL هي مصدر الحقيقة الدائم للمهام.
`TaskModel` هو النموذج الدائم الأساسي. مخزن الذاكرة **ليس** مصدر حقيقة. يجوز
للـruntime استخدام DTO خاص به بشرط وجود mapping واضح إلى `TaskModel`، ولا يجوز
وجود نموذجين متنافسين كمصدر حقيقة. **لا إعادة تصميم لنظام المهام الآن** — توحيد
المرجعية فقط مع الحفاظ على بنية المرحلة.

**(2) بصمة التدقيق:** سجل قانوني واحد (canonical audit record). `publish` و
`verify_chain` يعيدان بناء **نفس** التمثيل حرفيًّا. الترتيب الأساسي للسلسلة هو
`seq`. `prev_hash` جزء من المادة الداخلة في البصمة. `chain_hash` يُحسب بـSHA-256
من نفس التمثيل القانوني في الإنشاء والتحقق. **لا تغيير للخوارزمية الآن.** ويُضاف
اختبار يثبت أن تغيير أي حقل جوهري أو ترتيب السلسلة يكسر التحقق.

### 12.2 البند الأول — ما كان العيب بالضبط

| # | الحقيقة قبل الإصلاح | الدليل |
|---|---|---|
| 1 | **مخطَّطان متنافسان لنفس الجدول:** `migrations/001_init.sql` يعرّف `tasks` بمفتاح `id UUID` **و**عمود `task_id VARCHAR UNIQUE`، بينما نموذج ORM `TaskModel` يعرّف `id` كمعرّف المهمة **ولا يعرّف `task_id` إطلاقًا** | `001_init.sql:63-65` مقابل `common/database.py:74-92` |
| 2 | `PostgresTaskStore` في `api_gateway/store.py` كان يكتب SQL خامًا إلى `tasks (task_id, …)` — عمود غير موجود في أي قاعدة أُنشئت من ORM، وهي القواعد الفعلية | تحقّق على قاعدة الاختبار: `information_schema.columns` لا يحوي `task_id` |
| 3 | ذلك الفشل كان يُبتلَع في `except Exception: return self._fallback.create(task)` فيرجع صامتًا إلى الذاكرة — فتبدو الكتابة ناجحة والمهمة **غير محفوظة** | `store.py` القديم، سطرا 66-67 و81-82 |
| 4 | `PersistentTaskStoreAdapter` في `main.py` كان يحوّل الحقول **يدويًّا** ويبتلع الاستثناء بنفس الطريقة، فله بديل ذاكرة صامت ثانٍ | `main.py` القديم، `except Exception: return self._fallback...` |
| 5 | اختباران في `test_common_branches.py` كانا **يثبّتان** سلوك الرجوع الصامت كعقد مقبول (`test_create_falls_back_to_memory`) | نفس الملف قبل التعديل |

### 12.3 البند الأول — ما نُفِّذ

- **`TaskModel` صار المرجع الوحيد.** أُزيل مسار SQL الخام كليًّا، ومعه العمود
  الوهمي `task_id`. لا يوجد الآن نموذجان يتنافسان على جدول `tasks`.
- **mapping صريح ومسمّى** في `store.py`: الثابت `TASK_DTO_TO_MODEL_FIELDS`
  يوثّق كل حقل من DTO إلى عموده الدائم، وأبرز سطر فيه `"task_id": "id"` — أي أن
  `task_id` مفهوم DTO فقط، ومفتاح النموذج الدائم هو `id`. والدالتان
  `task_details_to_model()` و`task_model_to_details()` هما الطريقان الوحيدان
  للتحويل؛ لا تحويل حقول يدوي في `main.py` بعد اليوم.
- **`DatabaseTaskStore`** هو المخزن الوحيد المربوط بالبوابة، يعمل على PostgreSQL
  في الإنتاج وعلى SQLite في الاختبارات الخفيفة **بنفس النموذج ونفس التحويل**.
- **لا رجوع صامت:** عند تعذّر القاعدة يُرفع `TaskStoreUnavailableError` صراحةً.
  `InMemoryTaskStore` بقي **بديلًا اختباريًّا صريحًا** موسومًا في docstring بأنه
  ليس مصدر حقيقة، ولا يُستخدم كرجوع تلقائي.
- **هجرة `004_unify_tasks_schema.sql`** للنشرات التي طُبِّق عليها `001_init.sql`:
  تنقل معرّف المهمة إلى `id`، تُسقط `task_id`، وتضيف `plan`/`updated_at`. مكتوبة
  متعادية (idempotent) ومحمية بشرط وجود العمود، ومعها تحذير نسخ احتياطي.
- **`001_init.sql` وُسِم في موضعه** بأن تعريفه لجدول `tasks` **مُتجاوَز** وأن
  المرجع هو `TaskModel`، حتى لا يُقرأ لاحقًا كعقد.
- **الاختباران اللذان كانا يثبّتان الرجوع الصامت** لم يُحذفا بل **قُلبا إلى العقد
  الجديد**: صارا يثبتان أن الاستثناء يُرفع ولا يُخفى
  (`test_create_raises_instead_of_silent_memory_fallback` ونظيره للقراءة). وأُضيف
  صف اختبارات `TestTaskModelMapping` يثبت أن الـmapping يغطي كل حقل دائم وأن
  `task_id` ليس عمودًا في النموذج.
- **ما لم يُفعل بقصد:** لم يُعَد تصميم نظام المهام. `PersistentTaskStore` في
  `common/persistent.py` بقي كما هو لأنه يخاطب **نفس** `TaskModel` — فهو مسار
  وصول آخر لنفس النموذج، لا نموذج منافس. توحيد مسارات الوصول خارج نطاق هذا الأمر.

### 12.4 البند الثاني — ما كان العيب بالضبط

`publish()` كان يهشّم `{event_id, timestamp, event_type, source, data}`، أما
`verify_chain()` فيعيد الحساب على `{event_id, metadata}` فقط. الشكلان مختلفان،
فأي سلسلة يكتبها `publish` **لا يمكن أن تجتاز** `verify_chain` — وهذا عيب مستقل
عن اللهجة يظهر على SQLite وPostgreSQL معًا. وكان `source` داخلًا في البصمة وهو
غير محفوظ في الجدول، أي أن التحقق كان **مستحيلًا بنيويًّا** لا مجرد مختلف الشكل.

### 12.5 البند الثاني — ما نُفِّذ

- **`canonical_audit_record()`** صارت المصدر الوحيد للشكل المهشّم، ويستدعيها
  الإنشاء والتحقق معًا. و`canonical_audit_record_from_row()` تبني **نفس** التمثيل
  من صف محفوظ.
- **المواد الداخلة في البصمة** معلنة في الثابت `CANONICAL_AUDIT_FIELDS`:
  `event_id, timestamp, event_type, actor_type, actor_id, action, metadata` —
  وكلها أعمدة موجودة في `audit_log`، فالتحقق قادر على استردادها حرفيًّا.
- **`prev_hash` جزء من المادة المهشّمة** كبادئة، كما نص القرار، وزيادةً على ذلك
  يتحقق `verify_chain` من أن `prev_hash` المحفوظ يطابق بصمة الصف السابق فعلًا —
  فتبديل الترتيب يُكشف حتى لو كانت كل بصمة سليمة في ذاتها.
- **الترتيب الأساسي `seq`** في القراءة والتحقق (`ORDER BY seq ASC`).
- **الخوارزمية لم تُغيَّر:** `SHA-256` على `f"{prev_hash}:{canonical_json}"` مع
  `sort_keys=True` و`ensure_ascii=False` — نفس ما كان.
- **توحيد اللهجتين:** `metadata` يعود قاموسًا من `JSONB` ونصًّا من `TEXT`؛
  `_canonical_metadata` يوحّدهما. و`_canonical_timestamp` يوحّد النص والـ
  `datetime` إلى ISO بتوقيت UTC. بلا هذا التوحيد لانكسر التحقق على PostgreSQL وحده.
- **`source` خارج البصمة صراحةً وبتعليق في الكود:** ليس عمودًا في `audit_log`،
  فلا يمكن استرداده عند التحقق — ولأنه غير محفوظ فلا محل للتلاعب به. تغطيته
  تقتضي تغيير المخطَّط، وهو خارج «لا تغيّر الخوارزمية الآن».

### 12.6 الاختبارات المطلوبة في القرار — أُضيفت وشُغِّلت

ملف جديد `tests/test_audit_canonical_record.py` (**18 اختبارًا**، SQLite):

| ما يُثبَت | الاختبار |
|---|---|
| التمثيل من الصف = التمثيل المباشر حرفيًّا | `test_from_row_equals_direct_construction` |
| المواد المهشّمة هي بالضبط الحقول السبعة | `test_canonical_fields_are_exactly_the_hashed_material` |
| القاموس والنص يعطيان نفس التمثيل | `test_metadata_string_and_dict_canonicalize_identically` |
| الوقت نصًّا أو `datetime` يعطي نفس التمثيل | `test_timestamp_string_and_datetime_canonicalize_identically` |
| دورة كاملة: `publish` ×3 ثم `verify_chain` = True، والربط عبر `prev_hash` صحيح | `test_published_chain_verifies` |
| **تغيير أي حقل جوهري يكسر التحقق** — مُعامَل على الحقول السبعة كلها | `test_tampering_any_canonical_field_breaks_verification[7 حالات]` |
| تغيير `prev_hash` يكسر التحقق | `test_tampering_prev_hash_breaks_verification` |
| تغيير `chain_hash` يكسر التحقق | `test_tampering_chain_hash_breaks_verification` |
| **تبديل ترتيب السلسلة (`seq`) يكسر التحقق** بلا تغيير أي حقل آخر | `test_swapping_seq_of_two_rows_breaks_verification` |
| حذف صف من وسط السلسلة يكسر التحقق | `test_deleting_a_middle_row_breaks_verification` |
| إلحاق صف مزوَّر يكسر التحقق | `test_appending_a_forged_row_breaks_verification` |

وأُضيفت النظائر على **PostgreSQL الحقيقي** في `test_phase1_postgres_events.py`:
دورة `publish`/`verify` كاملة، وأن `JSONB` يوحَّد كالنص، وأن تغيير `metadata`
يكسر التحقق، وأن تبديل `seq` يكسر التحقق، وأن `tasks` بلا عمود `task_id`، وأن
`DatabaseTaskStore` يكتب ويقرأ من PostgreSQL فعلًا.

### 12.7 الأرقام المقاسة

| ما شُغِّل | النتيجة |
|---|---|
| الحزمة الكاملة للخدمات (SQLite) | **725 passed · 19 skipped** (كانت 701/19) |
| 9 ملفات (مجموعة PostgreSQL + الملفات المتأثرة) على **قاعدة Supabase الحقيقية** | **191 passed · 0 failed · 0 errors** · 343.86s |
| منها اختباران كانا يستوردان `PersistentTaskStoreAdapter` المُزال | لم يُحذفا — حُدِّثا إلى `DatabaseTaskStore` ونجحا على PostgreSQL |
| `ruff format --check src/ tests/` بـ0.6.9 | **119 files already formatted** — أخضر |
| `ruff check src/ tests/` + `ruff check .` | All checks passed |
| مدقّق الحقيقة `truth_audit.py . --ratchet` | **106 → 100 مخالفة** (تقدّم حقيقي: IN_MEMORY_STORE 64→60، SILENT_FALLBACK 31→29) وثُبّت خط أساس أضيق عند 100 |
| بوابات الحكم والتاج والسيادة العشر (سكربتات) | **10/10 PASS** |
| `tests/crown` + `tests/sovereignty` + `tests/constitutional` + `tests/governance` | **729 passed** |
| بوابة تغطية التاج `--cov-fail-under=90` | 332 passed · **94.48%** |
| بوابة تغطية السيادة `--cov-fail-under=90` | 267 passed · **94.20%** |
| بوابة تغطية الدستور `--cov-fail-under=90` | **حمراء: 87.91%** — انظر §12.9 |
| `tests/smoke/run_smoke_tests.py` | PASS |

### 12.9 بوابة حمراء رُصدت ولم تُخفَ ولم تُخفَّض: تغطية نواة الدستور

`ci.yml:153-157` يشغّل تغطية فروع لا تقل عن **90%** على
`core.constitutional_engine`. التشغيل الفعلي الآن:

```
TOTAL  616 stmts  59 miss  178 branch  23 brpart  88%
FAIL Required test coverage of 90% not reached. Total coverage: 87.91%
99 passed
```

النقص موزّع لا محصور: `rules.py` 85% · `model.py` 86% · `engine.py` 88% ·
`cli.py` 89% · `articles.py` 90% · `ledger.py` 94%.

**ليست ارتدادًا من هذا العمل، والدليل تنفيذي:**

1. `git status` لهذا العمل لا يمسّ `core/` إطلاقًا — التغييرات في
   `federal/executive/services/` و`docs/` و`migrations/` فقط.
2. شُغِّلت البوابة على `HEAD` (`bc9ad98`) في **شجرة عمل نظيفة** عبر
   `git worktree add`، فأعطت **87.91% نفسها حرفيًّا**. أي أنها كانت حمراء قبل
   هذا العمل.

**ما لم يُفعل، بقصد:** لم يُخفَّض `--cov-fail-under`، ولم يُستثنَ ملف، ولم يُعلَّم
اختبار بالتخطي، ولم يُكتب اختبار صوري لرفع الرقم. رفع التغطية الحقيقي لنواة
الدستور **وحدة عمل مستقلة** خارج نطاق هذا الأمر (الذي يخص مرجعية المهام والسجل
القانوني للتدقيق)، ولا يجوز حشره فيه. وسُجِّل هنا لأن ادّعاء «كل البوابات خضراء»
صار **غير صحيح** بعد هذا الرصد، فوجب تصحيحه.

**أثره على الحالة:** E2.2-G يبقى `IN_PROGRESS`. لا يُعلَن PASS، ولا يُفتح E3.

### 12.8 ما يبقى غير مزعوم

- لم يُشاهَد تشغيل CI فعلي على GitHub؛ البوابات خضراء محليًّا بنفس نسخة الأداة.
- هجرة `004` **لم تُطبَّق** على قاعدة الاختبار لأن تلك القاعدة أُنشئت من ORM
  وهي متوافقة أصلًا. تطبيقها على نشرة قديمة لم يُجرَّب هنا، ولا يُدّعى.
- توحيد مسارات الوصول إلى `TaskModel` (`DatabaseTaskStore` مقابل
  `PersistentTaskStore`) لم يُنجَز — نموذج واحد، ومسارا وصول. خارج نطاق الأمر.
- السجلات التي كُتبت قبل هذا التغيير بالشكل القديم لن تجتاز `verify_chain`، وهي
  أصلًا لم تكن تجتازه لأن الشكلين كانا مختلفين. لا ارتداد، ولا هجرة بيانات مطلوبة.

## المراجع
- خارطة المرحلة: [`PHASE_E_ROADMAP.md`](PHASE_E_ROADMAP.md)
- مصفوفة الحقيقة: [`TRUTH_MATRIX.md`](TRUTH_MATRIX.md)
- تعريف الإنجاز: [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md)
- معمار الحماية: [`../security/CROWN_SOVEREIGNTY_PROTECTION.md`](../security/CROWN_SOVEREIGNTY_PROTECTION.md)
