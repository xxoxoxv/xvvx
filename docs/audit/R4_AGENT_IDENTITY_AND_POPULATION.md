# R4 — توحيد هوية الوكيل والسجل والسكّان

**الهدف:** إزالة ازدواجية هوية الوكيل وسكّان النظام — مصدر حقيقة واحد للهوية،
والسكّان إسقاط عنه لا سجل ثانٍ.
**النطاق:** `executive_core` (agent_identity, dispatcher) · `agent_runtime`
(population, health) · `royal` · `control_console` · `tools/migrations`
**المالك:** federal/executive/services
**تاريخ الإنشاء:** 2026-08-16
**تاريخ آخر تعديل:** 2026-08-17 — ترحيل R4 **مُطبَّق فعلًا** على القاعدة
الحقيقية بسياسة OPTION 2 (الدليل التاريخي وحده). انظر §7.
**الأساس:** R3 (`9565713`) — بيئة تشغيل الوكلاء داخل المسار القانوني.
**قيد صريح:** لم تُلمَس أمانة التنفيذ (`EXECUTION_FIDELITY = SIMULATION`) ولا
أُعيد بناء بيئة التشغيل التي اكتملت في R3.

---

## 1. الحالة قبل R4 (مقيسة من الكود لا مفترضة)

### 1.1 سجلّان يُنشئان هوية ويحفظانها

| | `agents` (`AgentModel`، `common/database.py`) | `agent_population` (`agent_runtime/population.py`) |
|---|---|---|
| المفتاح | `id` (نصّي، يُعطى من الخارج) | `id` تسلسلي + `agent_id` فريد يُولَّد داخليًّا |
| توليد المعرّف | المتصل يحدّده | `f"agent-{uuid4().hex[:8]}"` داخل الوحدة |
| المحرِّك | `get_session_factory()` المشترك مع `tasks` | `create_engine(...)` **خاص** + `PopulationBase` خاصّة |
| الصلاحيات/الأدوات | أعمدة `JSON` | أعمدة `Text` تحمل JSON مُسلسلًا يدويًّا |
| دورة الحياة | `status` (registered/active/…) | `state` (registered/training/testing/specialized/employed/active/retired، و`paused` يكتبها نظام العزل وهي غير موثَّقة في العمود) |
| حقول لا تقابلها | — | `category`, `school_score`, `specialization`, `tokens_used`, `graduated_at` |
| من يكتب | `dispatcher.register_agent` فقط (بـ `session.merge` = كتابة صامتة فوق هوية قائمة) | `PopulationRegistry.register_agent` / `seed_initial_population` / `update_state` |
| من يقرأ | `CapabilityDispatcher.candidates/available_agents/select/assignment_for` → أي **مسار التنفيذ كلّه** | `health.py` (7 مواضع)، `control_console/main.py` (5)، `governance/expansion.py` (10)، `governance/federation.py` (2)، `governance/treasury.py` (1)، و**SQL خام** في `royal/main.py` (6 مواضع: عدّ، توزيع حالة، توزيع دور، إقصاء، إعادة، قائمة السكّان) |

### 1.2 النتائج المقيسة للازدواجية

1. **هويّتان لنفس الوكيل:** الوكيل المُنشأ عبر السكّان لا وجود له في `agents`،
   فلا يراه الموزِّع أبدًا؛ والوكيل المُنشأ عبر `register_agent` لا وجود له في
   السكّان، فلا يظهر في أي لوحة ولا يُفحَص صحيًّا.
2. **دورتا حياة:** `agents.status` و`agent_population.state` تتغيّران مستقلّتين؛
   نظام العزل كان يكتب `paused` في السكّان بينما يبقى الوكيل `active` في السجل
   الذي يقرأه الموزِّع — أي أن **عزل الوكيل لم يكن يمنع توزيعه**.
3. **عدّادان للسكّان:** `royal_dashboard` يعدّ `agent_population`، و
   `available_agents` يعدّ `agents`.
4. **قدرات قديمة:** `health.check_agent` كان يقرأ `allowed_tools` من نصّ السكّان،
   لا من الأدوات التي تُمنَح فعلًا لحظة التنفيذ.

### 1.3 حقائق تسهّل التوحيد

- **لا `ForeignKey` في المستودع كلّه** (`grep "ForeignKey(" federal/` = صفر)، فلا
  قيود مرجعية تُكسَر بالتوحيد.
- `agent_health_checks`, `agent_isolations`, `treatments`, `school_results`,
  `experiences` كلها تشير إلى `agent_id` **نصًّا** بلا قيد؛ فتوحيد المعرّف كافٍ
  للحفاظ على ارتباطها التاريخي.

---

## 2. مصدر الحقيقة المُختار (R4-B)

**`agents` هو المصدر الكانوني لهوية الوكيل.** والقرار مبنيّ على البنية القائمة:

1. هو الجدول **الوحيد** الذي يقرأه مسار التنفيذ المعتمد الذي بُني في R1–R3
   (توزيع → تعيين لحظة التنفيذ → حدّ بيئة التشغيل). اختيار السكّان كمصدر كان
   يعني إعادة كتابة المسار القانوني نفسه — وهو خارج نطاق R4.
2. يسكن نفس `get_session_factory()` الذي تسكنه `tasks`، فقراءة الهوية لحظة
   التنفيذ تجري على نفس المحرِّك؛ أما السكّان فينشئ محرِّكًا ثانيًا.
3. يحفظ الصلاحيات والأدوات في `JSON` مكتوب، لا نصًّا يُفكّ يدويًّا في كل قراءة.

**`agent_population` ليس سجل هوية بعد R4.** صار:

- **ملفًّا تدريبيًّا:** `category`, `school_score`, `specialization`,
  `tokens_used`, `graduated_at` — بيانات لا مكان لها في الهوية.
- **إسقاط قراءة:** `list_agents` / `population_stats` يُبنيان على السجل الكانوني.
- أعمدته المكرّرة (`name`, `role`, `permissions`, `allowed_tools`, `state`) تبقى
  مكتوبة كـ **مرآة توافُقية مهجورة (deprecated mirror)** لقرّاء خارج المستودع،
  ولا يُقرأ منها شيء داخله.

**لم يُنشأ سجل ثالث.** `executive_core/agent_identity.py` ليس مخزنًا: هو الطبقة
الكانونية الوحيدة للقراءة والكتابة فوق جدول `agents` نفسه.

---

## 3. نموذج الهوية (R4-C)

`executive_core/agent_identity.py`:

- `AgentIdentity` (frozen): `agent_id`, `name`, `role`, `lifecycle_state`,
  `permissions`, `allowed_tools`, `token_budget`, `tenant_id`, `created_at`،
  و`employable` محسوبة من **نفس** `EMPLOYABLE_STATUSES` التي يستعملها الموزِّع
  (لا مجموعة موازية).
- `new_agent_id()` = `agent-<uuid4[:8]>` — معرّف مستقرّ **لا يُشتقّ من الاسم**.
  الاسم ليس هوية: وكيلان بنفس الاسم هويّتان مختلفتان (مُختبَر).
- `register_identity(...)` ترفض التكرار بـ `DuplicateAgentIdentityError`.
  التحديث لا يجري ضمنًا: `update_identity(...)` صريحة. (`session.merge` الصامت لم
  يبقَ في مسار إنشاء الهوية، وحرس ساكن يمنع عودته.)
- `get_identity` / `require_identity` (`UnknownAgentIdentityError`) /
  `list_identities` / `set_lifecycle_state`.
- **دورة حياة واحدة:** `AgentLifecycleState` تجمع ما كان موزّعًا بين الحقلين:
  registered · training · testing · specialized · employed · active · promoted ·
  ready · paused · retired — وتُحفَظ في `agents.status` وحده.
  أُضيفت `employed` إلى `EMPLOYABLE_STATUSES` لأن الوكيل المتخرِّج كان — بعد
  توحيد الحقل — سيسقط من الترشيح.

---

## 4. تكامل التشغيل (R4-D)

المسار بعد R4: **مهمّة → المحرّك → `CapabilityDispatcher` (على `agents`) →
`AgentAssignment` → `AgentRuntimeGateway` → تنفيذ.**

- لا تغيير في المسار نفسه (بُني في R3) — التغيير أن كل قراءة هوية/دور/صلاحية/
  أداة صارت من السجل الكانوني، ولا شيء في هذا المسار يستورد `population`
  (حرس ساكن يفحص `dispatcher.py` و`agent_runtime_gateway.py`).
- مُختبَر: تلويث `allowed_tools`/`permissions` في صفّ السكّان لا يغيّر تعيين
  التنفيذ؛ والصفّ السكّاني بلا هوية كانونية لا يُوزَّع عليه (`NoEligibleAgentError`).
- مُختبَر: تقاعد الوكيل يمنع تعيينه لحظة التنفيذ — أي أن عزل/تقاعد صار **نافذًا**
  على التوزيع، وهو ما كان مكسورًا قبل R4.

---

## 5. نموذج السكّان (R4-E)

`population_projection()` يُشتقّ من السجل الكانوني:

| الحقل | المصدر | الصدق |
|---|---|---|
| `total`, `by_lifecycle_state`, `active`, `retired`, `paused`, `employable` | `agents` | REAL — عدّ فعلي |
| `idle` | `employable - executing` | REAL مشروط برصد النشاط |
| `executing`, `failed` | آخر طور لكل وكيل من أحداث `amos_federation.executive.agent_lifecycle` (المسجَّلة فعلًا في R3) | REAL إن رُصدت أحداث، و**`None`** مع `runtime_activity.observed = false` إن لم تُرصَد |

**لا يُختلق رقم.** الإحصاء غير المرصود يُعلَن `None` صراحةً بدل تصفيره كأنه قياس
(مُختبَر). و`PopulationRegistry.population_stats()` يعيد `total` مطابقًا لعدّاد
السجل الكانوني — لا عدّاد ثانٍ.

الصفوف السكّانية التي لا هوية كانونية لها **لا تُحذَف ولا تُخفى**: تعود من
`list_agents()`/`get_agent()` موسومة `canonical: false` و
`reconciliation_required: true` و`identity_source: "agent_population"`، وتُعدّ في
`unmigrated_profiles()`.

---

## 6. تكامل الصحّة (R4-F)

- `health.py` لم يبقَ فيه أي `get_population_registry`: الهوية والقدرات من
  `get_identity`، وقائمة من يُفحَص من `list_identities`، وتغييرات دورة الحياة
  (training/active/paused/retired) عبر `set_lifecycle_state` — أي أن العزل صار
  يكتب الحقل الذي يقرأه الموزِّع فعلًا.
- `identity_health()` و`population_health()` **مبنيّان على فحص مكوّنات فعلي**، لا
  على وجود عملية: السجل الكانوني (قابلية القراءة والعدّ)، ناقل الأحداث، تناسق
  الإسقاط (عدد الصفوف غير المُوفَّقة)، ونظام العزل (العزل النشط). كل تقرير يحمل
  `basis: "component_checks"`. أي مكوّن يفشل يُعلَن `unavailable` والحالة الكلية
  تنزل معه؛ ووجود صفّ غير مُوفَّق يُنزل الحالة إلى `degraded` (مُختبَر).
- **لم تُبنَ منصّة Observability** — لا مقاييس زمنية ولا تجميع تاريخي.

---

## 7. الترحيل والتوافُق (R4-G) — مُطبَّق على القاعدة الحقيقية

`tools/migrations/r4_unify_agent_identity.py`. القرار المعتمد:
**OPTION 2 — APPLY ONLY TO ROWS WITH ACTUAL HISTORICAL EVIDENCE.**

### 7.1 لماذا لم يُرحَّل كل صفّ سكّاني

النسخة الأولى من السكربت كانت تُنشئ هوية كانونية لكل صفّ في `agent_population`.
قياس القاعدة الحقيقية (Supabase، مشروع `mqcfmwtdaymrmwvthqyw`، PostgreSQL
17.6.1.155) أسقط هذا الخيار:

| المقياس | القيمة المقيسة |
|---|---|
| صفوف `agent_population` | **5116** |
| `agent_id` متمايزة | 5116 (لا هوية مكرّرة) |
| **أسماء** متميزة | **24** |
| أزواج (اسم، دور) متميزة | 24 |
| صفوف `agents` قبل الترحيل | 0 |

24 اسمًا في 5116 صفًّا يعني تنفيذًا متكرّرًا لـ`seed_initial_population`، أي أن
الأغلبية صفوف **بذر** لا هويّات تشغيلية. وبما أن
`EMPLOYABLE_STATUSES = {registered, active, promoted, ready, employed}`
تضمّ `registered`، وحالة 5068 صفًّا هي `registered`، فترحيلها كان سيُدخل 5068
وكيلًا **قابلًا للتوزيع** إلى مسار التنفيذ في معاملة واحدة. ولذلك: لا هوية بلا
دليل.

### 7.2 السياسة المنفَّذة

1. لا تُرحَّل 5116 صفًّا تلقائيًّا. 2. الاسم ليس هوية. 3. (الاسم، الدور) ليست
هوية. 4. لا هوية كانونية لصفوف البذر. 5. الصفوف ذات الدليل التاريخي وحدها
تتأهّل. 6. الدليل = حالة غير `registered` أو مرجع حقيقي في أحد جداول
`EVIDENCE_SOURCES` (school_results، experiences، agent_health_checks،
agent_isolations، agent_treatments، specialization_results، retirement_records،
reviews، executive_roles، treasury_transactions، university_outputs،
institutions، tasks). 7. الدليل غير الكافي ⇒ لا تُخترَع هوية. 8. لا يُحذَف صفّ
سكّاني. 9. provenance محفوظة: الهوية تأخذ **نفس** `agent_population.agent_id`.
10. لا سجل ثالث.

### 7.3 DRY-RUN على القاعدة الحقيقية (قبل الكتابة)

| البند | العدد |
|---|---|
| إجمالي السكّان | 5116 |
| صفوف ذات دليل تاريخي | **48** |
| هويّات كانونية للإنشاء | **48** |
| صفوف كانونية سابقًا | 0 |
| صفوف بذر (seed-only) | **5068** |
| مراجع غير محلولة (unresolved) | 6 معرّفات / 34 صفّ مرجعي |
| هويّات مكرّرة في السكّان | 0 |
| مراجع يتيمة (orphan) | `experiences` و`reviews` — انظر 7.7 |
| هويّات غامضة (اسم+دور مكرّر) | موجودة ومُعلَنة، **لم تُدمَج** |

توزيع الدليل على الصفوف الـ48: 12 `paused` · 12 `active` (منها 2 بنتائج مدرسة) ·
14 `employed` (كلها بنتائج مدرسة) · 7 `retired` (منها 2 بفحوص صحّة) ·
2 `specialized` (منها 1 بفحوص صحّة) · 1 `training`. لا صفّ يحمل دليل
`experiences` أو عزل أو علاج أو تقاعد أو مراجعة أو دور تنفيذي.

**نسخة احتياطية قبل الكتابة:**
`docs/audit/backups/r4_evidenced_population_backup.json` — الصفوف الـ48 كاملة
مع سبب تأهيل كلٍّ منها.

### 7.4 التطبيق الفعلي (معاملة واحدة)

نُفِّذ على القاعدة الحقيقية عبر قناة SQL لمشروع Supabase، في `BEGIN … COMMIT`
واحد، بـ`INSERT … SELECT … ON CONFLICT (id) DO NOTHING`، بلا `DELETE` وبلا
`UPDATE` على `agent_population`. مصدر العبارة: `emit_sql()` في السكربت نفسه، فلا
SQL يدويّ غير قابل للمراجعة.

> سبب استخدام قناة SQL لا `--apply`: لا `DATABASE_URL` ولا كلمة مرور Postgres
> متاحة في بيئة التشغيل هذه؛ القناة المتاحة إلى القاعدة الحقيقية هي واجهة SQL
> لمشروع Supabase وحدها. الدالّة `migrate(apply=True)` هي المسار المكافئ حين
> يتوفّر رابط قاعدة، وهي المسار المُختبَر في الحزمة.

### 7.5 التحقّق بعد التطبيق (مقيس، لا مُفترض)

| الفحص | النتيجة |
|---|---|
| صفوف `agents` | **48** (كانت 0) |
| `id` متمايزة في `agents` | 48 ⇒ تفرّد كانوني سليم |
| صفوف `agent_population` بعد الترحيل | **5116** (بلا تغيير — لا حذف) |
| صفوف ذات دليل وما زالت بلا هوية | **0** |
| صفوف بذر رُحِّلت خطأً | **0** |
| هوية كانونية بلا صفّ سكّاني مقابل | 0 |
| وكلاء قابلون للتوزيع | **26** (14 `employed` + 12 `active`) |
| هويّات كانونية بحالة `registered` | **0** ⇒ لا صفّ بذر دخل التوزيع |
| `school_results` بلا هوية كانونية | 0 (الـ16 كلها مُرحَّلة) |
| `agent_health_checks` بلا هوية كانونية | 0 |
| حقول هوية فارغة (`name`/`role`) | 0 |
| `tenant_id` غير متوقّع | 0 |
| **التكرار (idempotency)** | تشغيل ثانٍ للعبارة نفسها ⇒ **0 صفّ مُدخَل**، السكّان 5116 |

توزيع الهويّات الكانونية الـ48: `employed` 14 (قابل للتوزيع) · `active` 12
(قابل للتوزيع) · `paused` 12 · `retired` 7 · `specialized` 2 · `training` 1.

### 7.6 CANONICAL AGENTS / HISTORICAL POPULATION / LEGACY SEED / UNRESOLVED

| التصنيف | العدد | المكان | يدخل التوزيع؟ |
|---|---|---|---|
| **CANONICAL AGENTS** | 48 | `agents` (+ صفّها في `agent_population` كملفّ تدريبي) | 26 منها فقط (`active`/`employed`) |
| **HISTORICAL POPULATION** | 48 | نفس الصفوف السكّانية، بأدلّتها التاريخية | عبر هويّتها الكانونية وحدها |
| **LEGACY SEED ROWS** | **5068** | `agent_population` فقط — **بلا هوية كانونية** | **لا** |
| **UNRESOLVED ROWS** | 6 معرّفات / 34 صفّ | مراجع في `experiences` و`reviews` بلا صفّ سكّاني ولا هوية | لا |

`agent_population` لم يفقد صفًّا واحدًا: 5116 قبل، 5116 بعد.

### 7.7 UNRESOLVED ROWS — لماذا لم تُخترَع لها هوية

مراجع تاريخية إلى معرّفات لا يوجد لها صفّ سكّاني ولا هوية كانونية:

| المصدر | المعرّف | صفوف |
|---|---|---|
| `experiences` | `agent-xyz` | 1 |
| `experiences` | `test-agent` | 1 |
| `experiences` | `worker-analyst` | 1 |
| `experiences` | `worker-researcher` | 1 |
| `reviews` | `worker-analyst` | 24 |
| `reviews` | `worker-researcher` | 6 |

يُضاف إليها **7 صفوف في `experiences` بـ`agent_id = NULL`** لا تُنسَب إلى أحد.

هذه المعرّفات أسماء عاملين من مسارات اختبار/تجريب سابقة. اختراع هوية كانونية لها
كان يعني إنشاء وكيل من اسم — وهو ما تمنعه القاعدتان 2 و7 صراحةً. فتُعلَن
UNRESOLVED وتبقى بيانات الخبرات والمراجعات كما هي (لا تُحذَف ولا تُنسَب).

### 7.8 خصائص السكربت

- **idempotent:** التشغيل الثاني يُنشئ صفرًا (مُقيس على القاعدة الحقيقية وفي الحزمة).
- **غير مُدمِّر:** `rows_deleted: 0`، `columns_cleared: 0` دائمًا.
- **بلا كتابة افتراضيًّا:** `--apply` مطلوب صراحةً؛ الافتراضي فحص.
- **`--backup PATH`:** تصدير JSON للصفوف المؤهَّلة قبل أي كتابة.
- **`--emit-sql`:** العبارة المعاملاتية المكافئة، وهي المستخدَمة فعليًّا هنا.
- **جدول دليل مفقود** يُعلَن في `evidence_sources_unavailable`، ولا يُعَدّ «لا دليل» بصمت.

### 7.9 أثر على مقياس الصحّة

`unmigrated_profiles()` (كل صفّ بلا هوية) كان يجعل 5068 صفّ بذر تُبقي
`population_projection` في `degraded` أبديًّا فيفقد المقياس معناه التشخيصي. فُصِل
المقياس إلى ثلاثة أعداد مُعلَنة كلها:

| الحقل | المعنى | يُنزِل الصحّة؟ |
|---|---|---|
| `reconciliation_debt_rows` | صفّ **ذو دليل تاريخي** بلا هوية كانونية | **نعم** — خلل حقيقي |
| `legacy_seed_rows` | صفّ بذر بلا أي أثر | لا |
| `unmigrated_profile_rows` | المجموع الكلّي (كما كان) | لا (يُعلَن فقط) |

الدليل المقاس في `population.py` جزئيٌّ بقصد (`state` + `school_results` فقط،
وهما ما يملكه محرِّك السكّان)؛ المرجع الكامل للأدلّة هو سكربت الترحيل، وملفّ
الخدمة لا يستورد أداة ترحيل.

### طبقة التوافُق — بلا غموض

| المكوّن | الحالة بعد R4 |
|---|---|
| جدول `agents` + `executive_core.agent_identity` | **CANONICAL** — مصدر الهوية ودورة الحياة |
| `dispatcher.register_agent` | مسار كتابة قائم يعمل على الجدول الكانوني نفسه (يستعمل `merge` = upsert صريح للاستدعاءات القائمة) |
| أعمدة `agent_population`: `category`, `school_score`, `specialization`, `tokens_used`, `graduated_at` | **CANONICAL للملفّ التدريبي** — لا تقابلها أعمدة في الهوية |
| أعمدة `agent_population`: `name`, `role`, `permissions`, `allowed_tools`, `state` | **DEPRECATED MIRROR** — تُكتب للتوافُق، لا تُقرأ داخل المستودع |
| `PopulationRegistry.get_agent/list_agents/population_stats/update_state` | **COMPATIBILITY ADAPTER** — شكل القاموس القديم محفوظ، لكن الهوية كانونية |
| قرّاء السكّان في `expansion.py`, `federation.py`, `treasury.py`, `control_console` | تعمل كما هي عبر المُهيّئ أعلاه — لم تُلمَس |
| SQL خام في `royal/main.py` | حُوِّل إلى `agents` (عدّ، توزيع، إقصاء، إعادة) و`LEFT JOIN agent_population` للملفّ التدريبي؛ شكل الرد لم يتغيّر |

**الدَين المتبقّي:** الأعمدة المرآة لم تُحذَف (حذفها يكسر قرّاء خارج المستودع
يقرأون Supabase مباشرة)، وجداول `agent_population`/`school_results` تبقى على
`PopulationBase` ومحرِّك خاصّ. توحيد المحرِّك وإسقاط الأعمدة المرآة عمل لاحق.

---

## 8. الحرس الساكن (R4-H)

في `tests/test_r4_agent_identity_and_population.py::test_static_guards_forbid_second_identity_source`
(يفحص الكود بعد إزالة التعليقات والسلاسل، فلا يمرّ بحكم التوثيق):

1. `population.py` يستدعي `register_identity` ولا يحتوي `uuid` — أي لا توليد
   معرّف هوية محليًّا.
2. `dispatcher.py` و`agent_runtime_gateway.py` لا تحتويان `population` إطلاقًا.
3. `health.py` لا يحتوي `get_population_registry`، ويحتوي `get_identity` و
   `set_lifecycle_state`.
4. `royal/main.py` لا يحتوي `FROM agent_population` ولا `UPDATE agent_population`.
5. `agent_identity.py` لا يحتوي `merge` — لا كتابة صامتة فوق هوية قائمة.
6. لا وحدة تحت `services/` غير `population.py` تلمس `AgentPopulationModel`.

---

## 9. الاختبارات (R4-I)

`federal/executive/services/tests/test_r4_agent_identity_and_population.py` —
**16 اختبارًا، كلها ناجحة** (`16 passed`، مرصودة محليًّا):

| # | الاختبار | البند |
|---|---|---|
| 1 | تفرّد الهوية والاسم ليس هوية | C |
| 2 | القراءة الكانونية والمجهول يسقط صريحًا | B |
| 3 | الموزِّع يختار من الكانوني وحده | D |
| 4 | تعيين التنفيذ يقرأ القدرات من الكانوني لا من السكّان | D |
| 5 | السكّان إسقاط: العدّاد واحد | E |
| 6 | الإحصاء غير المرصود يُعلَن لا يُصفَّر | E/J |
| 7 | دورة حياة واحدة، والتقاعد ينفذ على التوزيع | C |
| 8 | تقرير الصحّة على مكوّنات، وينزل إلى degraded | F |
| 9 | الفحص الصحي يقرأ الهوية الكانونية | F |
| 10 | صفوف البذر تُعلَن legacy ولا تُنزِل الصحّة | F/G |
| 11 | الترحيل يطبَّق على ذوات الدليل وحدها، متكرِّر وغير مُدمِّر | G |
| 12 | نتائج المدرسة دليل ولو بقيت الحالة `registered` | G |
| 13 | مرجع تاريخي يتيم لا يخترع هوية | G |
| 14 | (الاسم، الدور) ليست هوية في الترحيل — لا دمج | C/G |
| 15 | SQL المُصدَر معاملاتي، idempotent، غير مُدمِّر | G |
| 16 | الحرس الساكن ضدّ العودة للازدواجية | H |

**الحزم المتأثّرة، مُشغَّلة بعد التعديل:** `test_phase6_population.py` ·
`test_health_system.py` · `test_phase7_health.py` · `test_control_console.py`
(81 نجحت) · `test_expansion.py` · `test_federation.py` · `test_treasury.py` ·
`test_r3_agent_runtime_integration.py` (125 نجحت).

**إصلاح جانبي:** `pytest.ini` في الجذر (`pythonpath = .`) — كان `pytest` من
الجذر يسقط في **الجمع** بـ `ModuleNotFoundError: No module named 'tests.crown'`
لأن `python -m pytest` يضيف مجلّد العمل إلى `sys.path` و`pytest` المباشر لا
يضيفه. الآن الأمران متساويان وحزمة `tests/crown` تُجمَع.

---

## 10. تصنيف الصدق (R4-J)

| المكوّن | التصنيف | الأساس |
|---|---|---|
| الهوية الكانونية (إنشاء/قراءة/دورة حياة/تفرّد) | **REAL** | كتابة وقراءة فعلية في PostgreSQL/SQLite، ومقيسة باختبارات |
| قراءة الموزِّع وتعيين التنفيذ من الكانوني | **REAL** | كان REAL في R1–R3، ولم يُلمَس إلا بتوسيع `EMPLOYABLE_STATUSES` |
| الإسقاط السكّاني: `total`/دورة الحياة/`employable`/`retired` | **REAL** | عدّ فعلي من `agents` |
| الإسقاط السكّاني: `executing`/`failed` | **PARTIAL** | مشتقّة من أحداث دورة الحياة المسجَّلة؛ تُعلَن `None` + `observed=false` إن لم تُرصَد أحداث |
| صحّة طبقة الهوية والسكّان | **PARTIAL** | فحص مكوّنات حقيقي (سجل، ناقل، تناسق، عزل) لكنه ليس Observability: بلا مقاييس زمنية ولا تاريخ تجميعي |
| `HealthChecker.check_agent` (الأداء من الخبرات) | **PARTIAL** | كما كان قبل R4 — يقرأ خبرات حقيقية، لكن الخبرات نفسها تأتي من مسار تنفيذ فيه أدوات محاكاة |
| تنفيذ الأدوات | **SIMULATION** | `ToolSandbox` معالِجات `_mock_*` — لم تُلمَس في R4 |
| `EXECUTION_FIDELITY` | **SIMULATION** (كما في R3) | لم تُغيَّر |
| ترحيل R4 على القاعدة الحقيقية (Supabase، 5116 صفًّا) | **REAL** | نُفِّذ فعلًا في معاملة واحدة: 48 هوية كانونية أُنشئت، 5068 صفّ بذر لم يُلمَس، السكّان 5116 قبل وبعد، والتشغيل الثاني أدخل 0 — كلها مقيسة بعد التطبيق (§7.5) |
| الهويّات الكانونية الـ48 كبيانات تشغيلية | **PARTIAL** | الهوية والحالة والصلاحيات مأخوذة من سجلّ حقيقي، لكن `school_score` لبعضها من درجات مدرسة افتراضية محاكاة |
| المعرّفات الستة UNRESOLVED | **UNRESOLVED (مُعلَن)** | مراجع في `experiences`/`reviews` بلا صفّ سكّاني — لم تُخترَع لها هوية ولم تُحذَف بياناتها |
| CI | **UNOBSERVED** | `api.github.com` غير مغطّى بالاعتماد المتاح — لا يُدّعى PASS |

---

## 11. الدَين المتبقّي بعد R4

1. **5068 صفّ بذر (LEGACY SEED ROWS)** باقية في `agent_population` بلا هوية
   كانونية — بقرار سياسة لا بخلل. تُعلَن في `legacy_seed_rows` ولا تدخل التوزيع
   ولا تُنزِل الصحّة. تنظيفها (أو تعليمها بعمود `origin='seed'`) عمل لاحق يحتاج
   قرار مالك البيانات، لأن الحذف يمسّ سجلًّا قائمًا.
   **1أ. 6 معرّفات UNRESOLVED** في `experiences`/`reviews` + 7 صفوف
   `experiences` بـ`agent_id = NULL` — لا تُنسَب ولا تُحذَف حتى يثبت أصلها.
   **1ب. لا قيد `UNIQUE` على `agent_population.agent_id` في القاعدة الحقيقية**
   ولا FOREIGN KEY واحد في المخطّط كلّه؛ التفرّد مضمون بالنموذج لا بالقاعدة.
2. **الأعمدة المرآة المهجورة** لم تُحذَف، ومحرِّك `PopulationBase` ما زال ثانيًا.
3. **`school_results` و`AgentSchool`** ما زالا يفترضان `agent_id` بلا قيد مرجعي.
4. **`dispatcher.register_agent`** يبقى مسار upsert صامت للاستدعاءات القائمة؛
   الطريق الذي يرفض التكرار هو `register_identity`.
5. **درجات المدرسة الافتراضية** (`[85, 85, 85, 90, 85, 90]`) ما زالت محاكاة —
   خارج نطاق R4.
6. **تشغيل الحزم بالتوازي يُفسد** `constitutional_ledger.jsonl` (دَين موثَّق سابقًا).
7. **`ruff format --check src/ tests/` يفشل** على 4 ملفّات (`dispatcher.py`،
   `royal/main.py`، `test_r3_agent_runtime_integration.py`،
   `test_r4_agent_identity_and_population.py`) بـ`ruff 0.6.9` المثبَّت في CI.
   **قياس أساس:** الفشل قائم على `f4df92e` قبل أي تعديل في هذه الجولة، أي أنه
   دَين سابق لا انحدار. `ruff check .` (بوابة E3) يمرّ نظيفًا قبل وبعد.

---

## 12. المراجع

- R3: `docs/audit/R3_AGENT_RUNTIME_INTEGRATION.md`
- الحالة التنفيذية: `docs/audit/ACTIVE_EXECUTION_STATE.md`
- الكود: `federal/executive/services/src/amos_federation/services/executive_core/agent_identity.py`
- الترحيل: `tools/migrations/r4_unify_agent_identity.py`
- نسخة ما قبل الترحيل: `docs/audit/backups/r4_evidenced_population_backup.json`
- المزوّدات المتعدّدة للصندوق الرملي (R5): `docs/audit/R5_MULTI_PROVIDER_SANDBOX.md`
- الاختبارات: `federal/executive/services/tests/test_r4_agent_identity_and_population.py`
