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
| **E0** | Truth Audit — تدقيق الحقيقة | `PROVEN` | 2026-08-16 | `tools/governance/truth_audit.py` + [`TRUTH_MATRIX.md`](TRUTH_MATRIX.md) |
| E1 | Constitutional Kernel | `DESIGNED` | — | — |
| E2 | Sovereignty Kernel | `DESIGNED` | — | — |
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

## E1 — Constitutional Kernel · النواة الدستورية — `DESIGNED`

**الهدف:** تحويل الدستور من نصوص إلى محرك قابل للتنفيذ.

**البنية المستهدفة:**
```
core/
  constitution/          ← المواد (موجودة)
  constitutional_engine/ ← المحرك (جديد)
  authority/
  principles/
  amendments/
  interpretation/
  enforcement/
```

**قدرات المحرك المطلوبة:** قراءة المواد · إصدار rules · تفسير authority · منع الأفعال المخالفة · تسجيل القرارات · إدارة amendments · إصدار constitutional violations · إنشاء evidence chain.

**معيار الإثبات:** فعل مخالف للمادة يُرفض آليًا مع إرجاع رقم المادة والسبب، وتُسجَّل المخالفة في سجل غير قابل للعبث، ويوجد hash لكل مادة يُفشل CI عند تغيير غير مصرح به.

---

## E2 — Sovereignty Kernel · نواة السيادة — `DESIGNED`

**الهدف:** تعريف السلطة تعريفًا تنفيذيًا: Sovereign · Crown · Royal · Federal · State · Institutional · Agent · Delegated · Emergency · Revoked.

**الأهم:** `Authority Resolution Engine` — عند تعارض أمرين، يعرف النظام مَن يملك السلطة.

**معيار الإثبات:** اختبار يصدر أمرين متعارضين من سلطتين مختلفتين، والمحرك يحسم النزاع ويعلل الحسم دستوريًا.

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
| 2026-08-16 | E0 | تثبيت خطة Phase E ومبدأ العمل وتعريف الإنجاز + بناء محرك تدقيق الحقيقة وتوليد أول TRUTH_MATRIX | `(هذا الـcommit)` |
