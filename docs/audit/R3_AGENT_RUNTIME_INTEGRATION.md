# R3 — دمج بيئة تشغيل الوكلاء في مسار التنفيذ القانوني

**الهدف:** ربط `agent_runtime` القائم بدورة التنفيذ القانونية دون إنشاء مسار تنفيذ ثانٍ
**النطاق:** `federal/executive/services` — `executive_core` + `agent_runtime`
**المالك:** federal/executive/services
**تاريخ الإنشاء:** 2026-08-16
**نقطة الانطلاق:** `0363d56` (R2)

---

## 1. خريطة بيئة التشغيل كما وُجدت (R3-A)

قياس من الشِفرة، لا من التوثيق. الموقع:
`federal/executive/services/src/amos_federation/services/agent_runtime/`

| الملف | الأسطر | ما فيه فعلًا |
|---|---|---|
| `main.py` | 142 | FastAPI. `POST /v1/execute` يفوّض إلى `core.run`؛ يردّ 403 `EXECUTION_BYPASS_FORBIDDEN` على `task`/`plan` خام. `GET /v1/agents/available` يقرأ `CapabilityDispatcher().available_agents()`. `GET /v1/tools/available` يقرأ `WorkerAgent().sandbox.available_tools()` |
| `base_agent.py` | 46 | `BaseAgent` ABC: `agent_id, agent_type, domain, permissions, sandbox=ToolSandbox()`؛ `can_use_tool(tool_id)` = الأداة في الصندوق **و** (`*` في الصلاحيات أو الأداة فيها) |
| `worker.py` | 99 | `WorkerAgent(BaseAgent)`؛ `async execute(task, plan)` يمرّ على الخطوات، يتخطّى ما لا صلاحية له بـ`status: "skipped"`، وإلا `sandbox.execute`. **يُرجع `status: "completed"` دائمًا** |
| `sandbox.py` | 124 | `ToolSandbox`: 12 معالجًا كلها `_mock_*`. أداة مجهولة تُرجع `{"error": ...}` (لا استثناء). `_mock_critic_review` يُرجع `quality_score: 0.85` ثابتًا |
| `population.py` | 470 | سجل سكّان مستقلّ بقاعدة ومحرّك خاصّين (`PopulationBase`) |
| `health.py` | 717 | صحّة/عزل/علاج بجداول خاصّة |

استنتاج: بيئة التشغيل **موجودة وقابلة للربط**. فلم تُنشأ بيئة جديدة في R3 — رُبط
`WorkerAgent` و`ToolSandbox` القائمان كما هما.

## 2. الخلل المقيس قبل R3 — القدرة كانت تُمنَح لا تُتحقَّق

في `executive_core/engine.py`، كان `_dispatch_step` يبني `AgentAssignment` حقيقيًّا من
جدول `agents` ثم **يُلقيه**: لا يُحفَظ منه إلا `assigned_agent`. وحين يحين التنفيذ كان
`_execute_step` يُلفّق تعيينًا آخر:

```python
assignment = AgentAssignment(
    agent_id=agent_id,
    agent_role="worker",                                   # ثابت مكتوب في الشِفرة
    permissions=(),                                        # فارغة
    allowed_tools=tuple(step.get("tool", "") for step in task["plan"]),   # أدوات الخطة
    required_tools=tuple(step.get("tool", "") for step in task["plan"]),  # نفسها
)
agent = self._agent_for(assignment)   # WorkerAgent(permissions=list(allowed_tools))
```

`allowed_tools == required_tools` بحكم البناء ⇒ `can_use_tool` في `BaseAgent` صحيح
دائمًا. فحصُ قدرةٍ جوابه «نعم» دائمًا ليس فحصًا. وجدول `agents` لم يكن يُقرأ لحظة
التنفيذ إطلاقًا: وكيل حُذف أو عُزل أو ضُيِّقت أدواته بعد التوزيع كان ينفّذ كأن شيئًا لم يكن.

ولم يكن هناك: `execution_id`، ولا سياق تنفيذ، ولا دورة حياة وكيل مُعلَنة، ولا فصل بين
صدق بيئة التشغيل وصدق الأداة.

## 3. ما بُني (R3-B/C/D/E/F/G/H)

### 3.1 حدّ واحد: `executive_core/agent_runtime_gateway.py` (جديد)

`AgentRuntimeGateway` هو الطريق الوحيد من النواة إلى بيئة التشغيل:

- `available_tools()` — من `ToolSandbox` نفسه، لا قائمة موازية.
- `verify_capabilities(assignment)` — fail-closed، ترفع `CapabilityDeniedError`.
- `build_context(...) → ExecutionContext` — يُبنى **بعد** فحص القدرة لا قبله.
- `record_lifecycle(context, phase, detail)` — تدقيق ثم حدث دائم.
- `dispatch(task, assignment, ...) → AgentExecutionResult` — قدرة ← سياق ← دورة حياة ← نتيجة.

**ما لا يفعله الحدّ (R3-B، ويحرسه اختبار ساكن):** لا `compare_and_set`، لا `TaskModel`،
لا `TaskState`، لا `_guarded_transition`، لا إنشاء مهمّة، لا قرار سيادي، لا مسار تنفيذ ثانٍ.
النواة تبقى صاحبة القرار وحاملة القلم.

### 3.2 التعيين يُعاد قراءته من السجل: `dispatcher.assignment_for()` (جديد)

يقرأ صفّ الوكيل من `agents` بالمعرّف والمستأجر، ويرفع `NoEligibleAgentError` إن كان
غير مُسجَّل أو خرج من `EMPLOYABLE_STATUSES`. **لا يختار بديلًا ولا يخفّض متطلَّبًا.**
الأدوات المسموحة والصلاحيات والدور تأتي من القاعدة **كما هي الآن**.

### 3.3 المحرّك بعد التعديل

- `_dispatch_step` يحفظ لقطة تعيين التوزيع في `result["dispatch"]` (أثر نسب، لا مصدر صلاحية).
- `_execute_step` صار: `assignment_for` → `runtime.dispatch` → كتابة النتيجة ونقل الحالة.
- `AgentAssignment` و`WorkerAgent` لم يبقَ لهما ذكر في `engine.py` (يحرسه اختبار ساكن).
- `agent_factory` يُمرَّر إلى الحدّ كما هو، فالحقن للاختبار يعبر المسار القانوني ولا يتجاوزه.

### 3.4 سياق التنفيذ (R3-F)

`ExecutionContext` (frozen): `task_id, agent_id, execution_id, correlation_id, tenant_id,
agent_role, authorization, capabilities_granted, capabilities_required`. بلا أسرار.
و**ليس** بديلًا عن الحفظ: مصدر الحقيقة لحالة المهمّة يبقى جدول `tasks`.

### 3.5 دورة حياة الوكيل (R3-D)

`AgentLifecycle`: `resolved → started → executing → completed|failed → idle`.
تُقيَّد في التدقيق وتُنشَر على `amos_federation.executive.agent_lifecycle` (عقد حدث جديد
في `common/event_bus.py`) بحقل صريح `task_state_effect: False`.

**النموذجان لم يُدمَجا:** دورة حياة الوكيل منفصلة عن آلة حالات المهمّة، ولا يكتب الوكيل
ولا الحدّ في `TaskModel`.

### 3.6 نسب النتيجة (R3-G)

`AgentExecutionResult` يحمل: `task_id, agent_id, execution_id, agent_role, status, steps,
tools_invoked, capabilities_granted, result_summary, started_at, completed_at,
agent_lifecycle`، ويضيف المحرّك `dispatch_assignment` و`execution_assignment`.

- `tools_invoked` = أدوات خطوات **مكتملة** فقط، بلا تكرار — لا قائمة أماني.
- ما لا يُعرف يُقال: دور غائب في السجل ⇒ `UNKNOWN`، ولا يُملأ بـ`"worker"` مُلفَّقة.
- **الحالة تُحسَب من الخطوات لا تُنقل عن الوكيل:** `WorkerAgent` يُعلن `completed` دائمًا،
  فيُصحَّح إلى `failed` (كل الخطوات متخطّاة) أو `partial` (خلط) أو `unreported` (خطوات لا
  تُعلن حالتها — لا تُحسَب نجاحًا ولا فشلًا) أو `empty`. و`failed`/`empty` تُسقط المهمّة.

### 3.7 حدّ المحاكاة (R3-H)

حقلان منفصلان بقصد، كي لا يُقرأ صدق البيئة صدقًا للأداة:

| الحقل | القيمة | المعنى المقيس |
|---|---|---|
| `runtime_fidelity` | `REAL` | الوكيل يُستدعى فعلًا وينفّذ خطواته داخل العملية |
| `tool_execution_fidelity` | `SIMULATION` | كل معالجات `ToolSandbox` دوالّ `_mock_*` |
| `tool_fidelity_reason` | `tool_sandbox_handlers_are_mocks` | السبب مُسمّى إلزامًا |
| `execution_fidelity` (المهمّة) | `SIMULATION` | يبقى كما في R2 — المخرَج النهائي محاكاة |

## 4. الاختبارات المستهدفة (R3-J)

`federal/executive/services/tests/test_r3_agent_runtime_integration.py` — **13 اختبارًا،
كلها ناجحة** بأمر `python -m pytest tests/test_r3_agent_runtime_integration.py -q`:

| # | الاختبار | ما يُثبته |
|---|---|---|
| 1 | `..._runs_the_real_worker_agent_through_one_gateway` | الصنف المبنيّ هو `agent_runtime.worker.WorkerAgent` نفسه، مرّة واحدة |
| 2 | `..._capabilities_come_from_the_registry_not_from_the_plan` | المنحة أوسع من الخطة ⇒ ليست مشتقّة منها |
| 3 | `..._capability_gap_fails_closed_before_any_step_runs` | نقص أداة ⇒ `CapabilityDeniedError`، لا تنفيذ جزئي |
| 4 | `..._tool_absent_from_runtime_inventory_fails_closed` | منح السجل لا يخلق أداة |
| 5 | `..._agent_that_left_employable_status_cannot_execute` | عزل بعد التوزيع ⇒ `agent_not_employable` |
| 6 | `..._execution_context_carries_identity_and_authorization` | المعرّفات والإذن حاضرة، بلا أسرار، والسياق ليس مخزنًا |
| 7 | `..._agent_lifecycle_is_published_and_does_not_move_task_state` | صفوف أحداث في القاعدة، `task_state_effect: False`، `execution_id` واحد |
| 8 | `..._result_provenance_is_complete_and_unknowns_are_declared` | نسب كامل و`UNKNOWN` مُعلَن |
| 9 | `..._status_is_computed_from_steps_not_taken_from_the_agent` | الوكيل يكتب النجاح حرفيًّا؛ الحدّ يحسبه |
| 10 | `..._all_steps_skipped_fails_the_task_instead_of_declaring_success` | لا نجاح على عمل لم يقع |
| 11 | `..._runtime_and_tool_fidelity_are_recorded_separately` | الحقلان منفصلان ومُسجَّلان |
| 12 | `..._gateway_never_writes_task_state_and_engine_no_longer_fabricates_assignment` | حرس ساكن للتجاوز |
| 13 | `..._dispatch_does_not_raise_on_runtime_failure_silently` | الفشل يُرفع ويُسجَّل ولا يُقلب نجاحًا |

## 5. حالة الصدق

| البند | الحال |
|---|---|
| استدعاء الوكيل وتنفيذ الخطوات | **REAL** — داخل العملية |
| قراءة سجل الوكلاء لحظة التنفيذ | **REAL** — PostgreSQL/SQLite حسب التهيئة |
| دورة حياة الوكيل (تدقيق + حدث دائم) | **REAL** — صفوف في `durable_events` |
| تنفيذ الأدوات | **SIMULATION** — كل المعالجات `_mock_*` |
| صحّة الوكلاء وسكّانهم (`health.py`, `population.py`) | **UNCONNECTED** — لم تُربط بالمسار القانوني في R3 بقصد |
| CI على GitHub | **UNOBSERVED** — لا وصول إلى `api.github.com` من هذه البيئة |

## 6. ما لم يُبنَ بقصد (R3-L)

لا Treasury ولا Courts ولا States ولا External World ولا Marketplace ولا Physical World.
ولم تُوسَّع R3 إلى منظومة أدوات حقيقية: `ToolSandbox` بقي كما هو، وصِدقه مُعلَن لا مُخفى.
كذلك لم يُدمَج سجلّا الوكلاء (`agents` مقابل `agent_population`) — بقيا كما هما،
وهذا **دين موثَّق** لا إصلاح مُدَّعى.

## 7. الدين المعروف

1. **سجلّان للوكلاء:** `agents` (مصدر حقيقة التوزيع والتنفيذ) و`agent_population`
   (بقاعدة ومحرّك خاصّين، يُقرأ بـSQL خام من `services/royal/main.py`). غير مدموجين.
2. **`ToolSandbox` محاكاة كاملة** — أداة مجهولة تُرجع `{"error": ...}` بلا استثناء،
   و`_mock_critic_review` يُرجع `quality_score` ثابتًا. النتيجة تُعلَن `SIMULATION`.
3. **`health.py` و`population.py` غير مربوطين** بدورة حياة الوكيل الجديدة.
4. **تشغيل الحزم بالتوازي يُفسد** `core/constitution/ledger/constitutional_ledger.jsonl`.
5. **CI غير مُشاهَد** — لا يُدَّعى نجاحه.
