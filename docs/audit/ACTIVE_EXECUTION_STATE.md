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
| Current Subphase | E2.2-A — Crown documentation + NUCLEUS |
| Current Objective | توثيق نطاق التاج ونواته توثيقًا مطابقًا للتنفيذ، ثم الالتزام والدفع والتحقق من البعيد |
| Status | IN_PROGRESS |
| Current Commit SHA | (يُحدَّث بعد الالتزام في هذه النقطة) |
| Last Verified Commit | `098beb317e142066956577cbdbc541fc6725b9a9` (قبل عمل التاج) |
| Previous Checkpoint SHA | لا يوجد — هذه أول نقطة تفتيش في E2.2 |
| Remote Confirmed | لا — لم يُدفَع بعد |
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

## 3. ما شُغِّل من اختبارات وبوابات

| الأمر | النتيجة | متى |
|---|---|---|
| `python -m pytest tests/crown/ -q --cov=core.crown --cov-branch` | **299 passed / 0 failed**، تغطية فروع **94%** (2356 عبارة، 486 فرعًا، 64 جزئيًّا)، وأدنى وحدة 92% | 2026-08-16 |
| `python -m ruff check .` | All checks passed | 2026-08-16 |
| `python -m core.crown.cli crown-check` | 9/9 — رمز خروج 0 | 2026-08-16 |
| `python tools/governance/generate_crown_threat_doc.py --check` | مطابقة للتنفيذ | 2026-08-16 |
| `python -m pytest tests/sovereignty tests/constitutional tests/governance -q` | 390 passed (خط الأساس قبل عمل التاج) | 2026-08-16 |
| `python -m core.sovereignty.cli sovereignty-check` | 9/9 (خط الأساس) | 2026-08-16 |

**لم يُشغَّل بعد:** بوابات الهوية (`stamp_readme_identity`,
`check_repository_identity`, `generate_identity_cards`, `write_domain_readmes`)،
و`truth_audit . --ratchet`، والحِزَم الكاملة بعد إضافة ملفات التاج، وبوابة CI
`crown-root-of-trust` (غير موجودة بعد).

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
| E2.2-A | توثيق نطاق التاج ونواته | IN_PROGRESS |
| E2.2-B | بوابة CI `crown-root-of-trust` | PENDING |
| E2.2-C | خارطة المرحلة ومصفوفة الحقيقة | PENDING |
| E2.2-D | بوابات الهوية | PENDING |
| E2.2-E | تحقق الأسرار وحدود الثقة | PENDING |
| E2.2-F | إثبات الاستمرارية السيادية من الطرف إلى الطرف | PENDING |
| E2.2-G | الحِزَم الكاملة عبر الأنظمة | PENDING |
| E2.3-A | التحقق النهائي العابر للأنظمة | PENDING |
| E2.3-B | تقرير الإثبات وإغلاق المرحلة | PENDING |

## 7. الأمر التالي حرفيًّا

```bash
cd /home/user/workspace/AMOS-Fedration
git add core/crown tests/crown docs/security tools/governance/generate_crown_threat_doc.py docs/audit/ACTIVE_EXECUTION_STATE.md
# التزام أساس التنفيذ برسالة البند 50، ثم التزام التوثيق (E2.2-A)، ثم الدفع والتحقق:
git ls-remote origin main   # تأكيد أن البعيد يحتوي الالتزام فعلًا
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
| 0 | أساس التنفيذ (كود + اختبارات + توثيق أمني) | (قيد الالتزام) | — | IN_PROGRESS |

## المراجع
- خارطة المرحلة: [`PHASE_E_ROADMAP.md`](PHASE_E_ROADMAP.md)
- مصفوفة الحقيقة: [`TRUTH_MATRIX.md`](TRUTH_MATRIX.md)
- تعريف الإنجاز: [`DEFINITION_OF_DONE.md`](DEFINITION_OF_DONE.md)
- معمار الحماية: [`../security/CROWN_SOVEREIGNTY_PROTECTION.md`](../security/CROWN_SOVEREIGNTY_PROTECTION.md)
