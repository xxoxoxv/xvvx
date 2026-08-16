# R2 — توحيد دورة حياة المهمة، الأحداث الدائمة، وخدمات التنفيذ

- **الهدف:** أن تكون دورة حياة المهمة التنفيذية الواحدة متماسكة فعلاً: REQUEST → SOVEREIGN AUTHORIZATION → TASK PERSISTENCE → STATE TRANSITION → PLANNING → DISPATCH → EXECUTION → RESULT → AUDIT → DURABLE EVENT، بحيث لا توجد دورة حياة ثانية موازية خارج Executive Core.
- **النطاق:** `executive_core` · `common/event_wiring` · `common/durable_event_bus` · `model_gateway` · `training` · `critic` · `evaluation`
- **المالك:** federal/executive/services
- **نقطة البداية:** `5e61f12` (R1)
- **تاريخ الإنشاء:** 2026-08-16

## 1. Before — الحالة قبل R2 (مقيسة من الكود)

| الموضع | ما كان يحدث فعلاً | الأثر |
| --- | --- | --- |
| `common/event_wiring.py` | يستورد `PersistentTaskStore` ويُنشئ صفّ مهمّة بنفسه (`_task_store.create`) ثم يكتب `update_status(..., "assigned")` — و`assigned` ليست حالة في آلة الحالات | **دورة حياة ثانية موازية**: مهمّة تُنشأ وتتغيّر حالتها بلا إذن سيادي وبلا انتقال ذرّي |
| `run_full_event_chain()` | سلسلة أحداث مُعلَنة كمحاكاة على `amos_federation.task.created` وما بعده، لا تمرّ بالنواة | أحداث نطاق لا يقابلها تنفيذ حقيقي — «نجاح» يُقاس على محاكاة |
| `model_gateway` `POST /v1/models/invoke` | استدعاء نموذج بلا `task_id` وبلا إذن؛ الفشل الخارجي يُلتقط ويُعاد كـfallback محلي بلا إعلان | سلطة تنفيذ نموذج مستقلة عن `SovereignGateway`، و**محاكاة تُخفي انقطاعاً** |
| `training` `POST /v1/models/train` | «تدريب» يُسجّل نموذجاً باسم الدولة؛ `accuracy`/`loss` مشتقّان من sha256 بلا إعلان في المخرَج | مسار تدريب مستقل عن النظام التنفيذي + أرقام غير مقيسة تبدو مقيسة |
| `critic` `POST /v1/reviews` | يُقيّم `steps` الواردة **من الطالب نفسه** ولو ذُكرت `task_id` قانونية | تقييم على مادة يرسلها الطالب = حكم رسمي على محتوى غير قانوني |
| `evaluation` `POST /v1/experiences` | يقبل `task_id` أيّاً كانت بلا تمييز موجود من وهمي | خبرات تُغذّي التدريب بنسب غير متحقّق منه |
| قياس الأحداث الدائمة | لا اختبار يُثبت أن التنفيذ يُنتج **صفّاً في القاعدة** لا كائناً في الذاكرة | الادّعاء بالدوام كان **UNOBSERVED** |

## 2. After — الحالة بعد R2

| الموضع | التحوّل | الحالة |
| --- | --- | --- |
| `common/event_wiring.py` | حُذف استيراد مستودع المهام كليّاً: لا `create` ولا `update_status`. صار **مُسقِطاً للقراءة** لا مالكاً للدورة | **REAL** |
| `CanonicalLifecycleProjector` | مستهلك (`legacy_domain_projection`) يشترك على `amos_federation.executive.task_transitioned` ويُشتقّ منه أحداث النطاق القديمة: `agent.assigned` عند `dispatched` (من `detail.assignment.agent_id`) و`agent.completed` عند `completed` | **REAL** |
| `run_full_event_chain()` | يستدعي `get_executive_core().submit_and_run(...)`: الانتقالات حقيقية، والحالة النهائية من آلة الحالات، والأحداث دائمة | **REAL** |
| `executive_core/fidelity.py` (جديد) | `ExecutionFidelity` = REAL · SIMULATION · UNAVAILABLE، و`declare()` **ترفع ValueError** إذا أُعلن غير REAL بلا سبب مُسمّى | **REAL** |
| `executive_core/subsystem_boundary.py` (جديد) | حدّ واحد تعبره الأنظمة المتخصّصة: تحقّق نسب (`task_provenance`) → إذن دستوري fail-closed (`review_only`) → قيد تدقيق → حدث دائم على `amos_federation.executive.subsystem_activity` بـ`execution_effect: False`. **لا يستدعي `compare_and_set` ولا يكتب في `tasks` إطلاقاً** | **REAL** |
| `model_gateway` | `task_id` اختيارية تُتحقَّق من المستودع القانوني (وهمية → 404، رفض → 403)؛ الاستجابة تحمل `execution_fidelity` و`fidelity_reason` و`activity_id` و`authority_decision`؛ غياب المفتاح أو فشل الاستدعاء صار `UNAVAILABLE` بسبب مُسمّى لا محاكاة صامتة | **REAL** (الحدّ) · **UNAVAILABLE** (الاستدعاء الخارجي بلا مفتاح) |
| `training` | يعبر الحدّ نفسه (404/403)؛ المقاييس و Model Card والاستجابة كلّها مُعلَنة `SIMULATION` مع `metrics_origin: sha256_seed` و`fidelity_reason: metrics_derived_from_hash_not_training` | **SIMULATION** مُعلَنة |
| `critic` | `task_id` قانونية → يُقرأ الخطوات والملخّص من نتيجة المستودع (`canonical_result`)؛ وإرسال `steps` مع مهمّة قانونية → **403**؛ الاستجابة تحمل `task_provenance` و`scored_material` | **REAL** (العقد) · **PARTIAL** (منطق التقييم نفسه لم يُبنَ) |
| `evaluation` | يُصنّف النسب `canonical` / `unverified` / `none` ويحفظه في `provenance` مع `activity_id`، بلا إخفاء الحالات القديمة | **REAL** (الوسم) |
| `common/event_bus.py` | عقد حدث جديد للموضوع `amos_federation.executive.subsystem_activity` | **REAL** |

## 3. Canonical execution lifecycle

المسار الوحيد المشروع لتغيير حالة مهمّة:

```
REQUEST (api_gateway / orchestrator / agent_runtime — واجهات HTTP فقط)
  → get_executive_core().submit / advance_to / run
    → SovereignGateway + ConstitutionalAuthorizer.guard      (fail-closed)
      → ExecutiveTaskRepository.compare_and_set              (انتقال ذرّي)
        → PersistentAuditStore.append                        (سلسلة hash)
          → durable_bus.publish(TRANSITION_SUBJECT)          (صفّ في durable_events)
            → CanonicalLifecycleProjector                    (أحداث النطاق القديمة — قراءة فقط)
```

`compare_and_set` و`PersistentTaskStore` و`TaskModel(` تبقى حصراً داخل `executive_core`. لا Task Model ثانٍ، ولا مستودع ثانٍ.

## 4. Event path

- **الناقل:** `common/durable_event_bus.py` وحده. **لم يُنشأ ناقل ثالث**، ولم يُنقل منطق الأحداث إلى API Gateway.
- **مالك قرار الإصدار:** `executive_core` فقط. الخدمات الحافّة لا تنشر موضوع الانتقال (يحرسه اختبار ساكن).
- **الدوام:** يُقاس بـSQL مباشر على جدول `durable_events` بعد إسقاط مفرد الناقل من الذاكرة (`bus_module._bus = None`)، ثم `replay(...)` — أي أن الحدث ليس in-memory simulation.
- **الترتيب:** `id` تصاعدي في القاعدة هو الترتيب، و`correlation_id = task_id` يربط أحداث المهمّة الواحدة.
- **الأحداث القديمة:** تُسقَط من الانتقال الحقيقي. `tool.executed` و`experience.recorded` **لا تُسقَط** — انظر §9.

## 5. Model boundary

`Model Gateway` **لم يُعَد بناؤه**. الحدّ الفاصل: التوجيه والاستدعاء وحدود الاستخدام تبقى ملكه؛ أما **ربط استدعاء بمهمّة تنفيذية** فلا يقع إلا عبر `SubsystemBoundary` بإذن `ConstitutionalAuthorizer`. فليس للبوابة سلطة مستقلة عن `SovereignGateway` في كل ما يمسّ دورة حياة مهمّة، ولا تملك تحريك حالتها.

## 6. Training boundary

- **lifecycle:** طلب → إذن → تشغيل مُعلَن محاكاة → تسجيل نموذج → قيد تدقيق + حدث دائم.
- **task provenance:** `task_id` تُتحقَّق من المستودع القانوني أو تُردّ (404).
- **authorization:** fail-closed؛ قرار غير ALLOW يمنع التشغيل.
- **result/audit:** `activity_id` + `audit_id` + حدث دائم بـ`execution_effect: False`.
- لم يُحوَّل التدريب إلى منظومة تدريب ضخمة، و**لم يُنشأ له مسار تنفيذ سرّي**.

## 7. Evaluation boundary

- الحلقة الذكية الكاملة **لم تُبنَ** — بُني عقد التكامل الحقيقي فقط.
- الناقد يُقيّم مادة قانونية أو يُعلن أنها `caller_supplied` مع نسب `unverified`؛ الخلط ممنوع بـ403.
- **لا نتائج تقييم مُخترعة:** `rules_evaluated` تأتي من المُصرِّح الفعلي، ولا تُسند درجة جودة ثابتة (يحرسه اختبار ساكن)، ومُسقِط `agent.completed` لا يُصدر `quality_score` لأنه لا يملك حكماً على الجودة.

## 8. Remaining bypasses (معروفة وموثَّقة)

1. `orchestrator` `POST /v1/plan?preview=true` — تخطيط استطلاعي بلا حفظ وبلا سلطة (`authority=None`). قراءة فقط بحكم التصميم، لا تنفيذ.
2. `evaluation` `/v1/experiences` بلا `task_id` — يبقى مقبولاً موسوماً `none`؛ لم يُمنع لئلا تُكسر مسارات قائمة.
3. `critic` بلا `task_id` قانونية — مراجعة موسومة `unverified` على مادة الطالب؛ عقد قائم، والمنع الكامل مؤجَّل.
4. `training` `/v1/datasets` — إنشاء مجموعة بيانات لا يعبر الحدّ (لا يمسّ مهمّة تنفيذية).
5. `model_gateway` بلا `task_id` — استدعاء نموذج غير منسوب لمهمّة يمرّ بلا حدّ؛ مقصود لكونه لا يخصّ دورة حياة.

## 9. الصدق: REAL · PARTIAL · SIMULATION · UNOBSERVED

| العنصر | الوسم | التبرير |
| --- | --- | --- |
| انتقالات الحالة، الإذن السيادي، سلسلة التدقيق، الأحداث الدائمة | **REAL** | مقيسة بـSQL وبإعادة تشغيل الناقل |
| حدّ الأنظمة المتخصّصة (نسب + إذن + تدقيق + حدث) | **REAL** | 25 اختباراً في `tests/test_r2_task_execution_integration.py` |
| إسقاط `agent.assigned` / `agent.completed` | **REAL** | مُشتقّة من انتقال حقيقي، والوكيل مُطابق لسجل الوكلاء |
| إسقاط `tool.executed` / `experience.recorded` | **PARTIAL** | تفصيل الانتقال لا يحمل أحداث أدوات مفصّلة؛ لم تُخترع |
| منطق تقييم الناقد | **PARTIAL** | العقد حقيقي، والحلقة الذكية خارج نطاق R2 |
| تنفيذ الأدوات (`ToolSandbox`) و`EXECUTION_FIDELITY` | **SIMULATION** | لم يتغيّر؛ ولا نزعم غير ذلك |
| مقاييس التدريب | **SIMULATION** | `metrics_origin: sha256_seed` مُعلَن في المخرَج |
| استدعاء النموذج بلا مفتاح API | **UNAVAILABLE** | سبب مُسمّى، ولا محاكاة تُغطّي الانقطاع |
| CI على GitHub Actions | **UNOBSERVED** | `api.github.com` غير مُفوَّض لهذه الجلسة — لا نزعم نجاح CI |

## 10. Known debt

1. **تلف السجل الدستوري عند التشغيل المتوازي:** كل نداء حدّ يكتب في `constitutional_ledger.jsonl` عبر `review_only`؛ تشغيل الحزم بالتوازي يُتلف الملف. الحزم تُشغَّل تسلسلياً. الحلّ (قفل ملفّي/طابور كتابة) مؤجَّل بقرار.
2. `protobuf`/`googleapis` lock resolution — مؤجَّل بقرار.
3. مواضيع النطاق القديمة تبقى مزدوجة مع موضوع الانتقال القانوني؛ الحذف يحتاج ترحيل مستهلكين.
4. المنع الكامل للمسارات غير المنسوبة (§8) يحتاج قراراً على توافق الخلف.

## 11. القياس (مُلاحَظ في هذه الجلسة، لا مُقدَّر)

| المقياس | R1 (`5e61f12`) | R2 | الحكم |
| --- | --- | --- | --- |
| `pytest tests/` (الجذر) | 757 passed | **757 passed** | لا انحدار |
| حزمة الخدمات (SQLite) | 774 passed · 25 skipped | **799 passed · 25 skipped** (+25 اختبار R2) | لا انحدار |
| حزمة الخدمات (PostgreSQL) | — | **25 passed** | أخضر |
| تغطية الفروع | 80.14% | **91%** (5431 عبارة · 1028 فرعاً) | فوق الحدّ |
| `truth_audit --ratchet` | 100 مخالفة | **100 مخالفة** (ثابت) | لم يُضَف تمويه |
| `ruff check .` | نجح | **نجح** | — |
| هوية المستودع | نجح | **نجح** | — |
| `verify_cross_system_suites.py` | نجح | **نجح** (POSTGRES, SQLITE) | — |
| GitHub Actions CI | UNOBSERVED | **UNOBSERVED** | لا نزعم نجاحاً |

ملاحظة إجرائية: أمر الحزمة الجذرية هو `python -m pytest tests/`. تشغيل `pytest` عارياً من جذر المستودع يجمع مجلدات خارج نطاق الحزمة ويفشل في الاستيراد — سلوك سابق لـR2 ولم يتغيّر به.
