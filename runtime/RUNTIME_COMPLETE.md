# 🏛️ AMOS Federation Runtime - دليل كامل

## نظرة عامة

تم إكمال محرك Runtime الكامل للدولة الفدرالية AMOS، والذي يمثل القلب النابض لتنفيذ المهام وإدارة الوكلاء.

## المكونات المكتملة

### 1. محرك التنفيذ (Runtime Engine) 📦
**الملف**: `runtime/engine/__init__.py`

#### المميزات:
- **إدارة دورة حياة المهام**: من الإنشاء إلى الإكمال
- **نظام الأولويات**: LOW, NORMAL, HIGH, CRITICAL
- **الاعتماديات بين المهام**: تنفيذ متسلسل حسب الاعتماديات
- **إعادة المحاولة التلقائية**: حتى 3 محاولات افتراضياً
- **Callbacks**: استدعاء دوال عند اكتمال المهام
- **الأحداث**: نظام شامل للأحداث (submit, start, complete, fail)
- **العمال المتعددين**: تشغيل متوازٍ للمهام

#### الاستخدام:
```python
from runtime.engine import RuntimeEngine, create_task, TaskPriority

engine = RuntimeEngine(config={"max_workers": 4})
await engine.initialize()

task = create_task(
    name="Process Data",
    description="معالجة البيانات",
    priority=TaskPriority.HIGH,
    data={"input": "value"}
)

await engine.submit_task(task)
```

### 2. الجدول الذكي (Task Scheduler) ⏰
**الملف**: `runtime/scheduler/__init__.py`

#### المميزات:
- **استراتيجيات جدولة متعددة**:
  - FIFO: أول وارد أول صادر
  - PRIORITY: حسب الأولوية
  - DEADLINE: حسب الموعد النهائي
  - FAIR: توزيع عادل
- **المهام المتكررة**: دعم التكرار اليومي/الأسبوعي/الساعي
- **الإلغاء**: إلغاء المهام المجدولة
- **التنفيذ الفوري والمتأخر**

#### الاستخدام:
```python
from runtime.scheduler import TaskScheduler, ScheduleStrategy
from datetime import datetime, timedelta

scheduler = TaskScheduler(strategy=ScheduleStrategy.PRIORITY)
await scheduler.start()

# جدولة فورية
await scheduler.schedule_now("task1", priority=5, data={"key": "value"})

# جدولة متأخرة
await scheduler.schedule_delayed("task2", delay_seconds=60)

# جدولة بوقت محدد
scheduled_time = datetime.utcnow() + timedelta(hours=1)
await scheduler.schedule("task3", scheduled_time=scheduled_time)
```

### 3. نظام الأحداث (Event System) 📢
**الملف**: `runtime/events/__init__.py`

#### المكونات:
- **EventBus**: ناقل الأحداث
- **EventLogger**: مسجل الأحداث
- **MetricsCollector**: مجمع المقاييس

#### أنواع الأحداث:
- دورة حياة المهمة (submitted, started, completed, failed)
- دورة حياة الوكيل (registered, unregistered, status_changed)
- النظام (startup, shutdown, error, metrics)
- الأمان (alert, audit)

#### المقاييس:
- **Counters**: عدادات قابلة للزيادة
- **Gauges**: مقاييس لحظية
- **Histograms**: توزيعات إحصائية (min, max, avg, p50, p95, p99)

#### الاستخدام:
```python
from runtime.events import EventBus, Event, EventType, MetricsCollector

event_bus = EventBus()
metrics = MetricsCollector(event_bus)

# نشر حدث
event = Event.create(
    event_type=EventType.TASK_COMPLETED,
    source="runtime_engine",
    data={"task_id": "123", "duration_ms": 150}
)
await event_bus.publish(event)

# تسجيل مقياس
metrics.increment_counter("tasks.completed", tags={"priority": "high"})
metrics.set_gauge("active_tasks", 15)
metrics.record_histogram("task_duration", 250.5)
```

### 4. الصندوق المعزول (Sandbox) 🔒
**الملف**: `runtime/sandbox/__init__.py`

#### المميزات:
- **عزل الكود**: تنفيذ آمن للكود غير الموثوق
- **سياسة الأمان**:
  - منع الوصول للشبكة
  - منع الوصول لنظام الملفات
  - قائمة بيضاء للوحدات المسموحة
  - تقييد وقت التنفيذ
  - تقييد حجم المخرجات
- **بيئات متعددة**: إنشاء بيئات معزولة مختلفة
- **سجل التنفيذ**: تتبع جميع عمليات التنفيذ

#### الوحدات المسموحة افتراضياً:
`math`, `random`, `datetime`, `time`, `re`, `json`, `collections`

#### الاستخدام:
```python
from runtime.sandbox import CodeExecutor, SecurityPolicy

policy = SecurityPolicy(
    allow_network=False,
    allow_file_system=False,
    max_execution_time_ms=5000
)

executor = CodeExecutor(policy)
env_id = executor.create_environment("safe_env")

code = """
def calculate(x, y):
    return x * y

result = calculate(10, 5)
print(f"Result: {result}")
"""

result = await executor.execute_async(env_id, code)
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

### 5. محرك السياسات (Policy Engine) 📜
**الملف**: `runtime/policy/__init__.py`

#### المميزات:
- **قواعد مرنة**: تعريف سياسات وصول معقدة
- **أنواع السياسات**:
  - ACCESS_CONTROL: التحكم بالوصول
  - RATE_LIMITING: تحديد المعدل
  - RESOURCE_QUOTA: حصص الموارد
  - DATA_VALIDATION: التحقق من البيانات
  - WORKFLOW: سير العمل
  - COMPLIANCE: الامتثال

- **التأثيرات**:
  - ALLOW: السماح
  - DENY: المنع (أولوية عالية)
  - CONDITIONAL: مشروط

- **الشروط**: مقارنة، أنماط، تعبيرات نمطية
- **سجل التدقيق**: تسجيل جميع قرارات الوصول

#### الاستخدام:
```python
from runtime.policy import PolicyEngine, create_allow_rule, create_deny_rule

engine = PolicyEngine()

# قاعدة سماح
allow_rule = create_allow_rule(
    rule_id="admin_access",
    name="Admin Full Access",
    subjects=["admin", "superuser"],
    actions=["read", "write", "delete"],
    resources=["*"],
    priority=10
)

# قاعدة منع
deny_rule = create_deny_rule(
    rule_id="no_delete_production",
    name="No Delete Production",
    subjects=["*"],
    actions=["delete"],
    resources=["production/*"],
    priority=100
)

engine.add_rule(allow_rule)
engine.add_rule(deny_rule)

# التحقق من الوصول
result = await engine.check_access(
    subject="admin",
    action="delete",
    resource="production/db"
)

print(result["allowed"])  # False (DENY له أولوية)
```

## التكامل بين المكونات

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Policy Engine                          │
│              (التحقق من الصلاحيات)                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Task Scheduler                          │
│              (جدولة المهام)                              │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Runtime Engine                          │
│              (تنفيذ المهام)                              │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│      Sandbox         │        │     Event Bus        │
│  (تنفيذ الكود الآمن) │        │   (نشر الأحداث)      │
└──────────────────────┘        └──────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │   Metrics Collector  │
                              │  (جمع المقاييس)      │
                              └──────────────────────┘
```

## أمثلة متكاملة

### مثال 1: تنفيذ مهمة مع سياسة أمان
```python
from runtime.engine import RuntimeEngine, create_task
from runtime.policy import PolicyEngine, create_allow_rule
from runtime.events import EventBus

# تهيئة المكونات
engine = RuntimeEngine()
policy_engine = PolicyEngine()
event_bus = EventBus()

# إضافة سياسة
rule = create_allow_rule(
    rule_id="task_exec",
    name="Allow Task Execution",
    subjects=["worker_agent"],
    actions=["execute"],
    resources=["tasks/*"]
)
policy_engine.add_rule(rule)

# بدء المحرك
await engine.initialize()

# إنشاء مهمة
task = create_task(
    name="Data Processing",
    description="معالجة بيانات المواطنين",
    agent_id="worker_001",
    data={"citizens": [...]}
)

# التحقق من السياسة ثم التنفيذ
access = await policy_engine.check_access(
    subject="worker_agent",
    action="execute",
    resource="tasks/data_processing"
)

if access["allowed"]:
    await engine.submit_task(task)
```

### مثال 2: جدولة مهام متكررة
```python
from runtime.scheduler import TaskScheduler, ScheduleStrategy
from datetime import datetime, timedelta

scheduler = TaskScheduler(strategy=ScheduleStrategy.PRIORITY)
await scheduler.start()

# مهمة يومية
await scheduler.schedule(
    task_id="daily_backup",
    scheduled_time=datetime.utcnow() + timedelta(hours=1),
    priority=5,
    recurrence={"interval": "days", "value": 1},
    data={"type": "full"}
)

# مهمة أسبوعية
await scheduler.schedule(
    task_id="weekly_report",
    scheduled_time=datetime.utcnow() + timedelta(days=1),
    priority=3,
    recurrence={"interval": "weeks", "value": 1}
)
```

## المقاييس والأداء

### مقاييس الأداء:
- عدد المهام المنفذة في الثانية
- متوسط وقت التنفيذ
- نسبة النجاح/الفشل
- استخدام الذاكرة
- استخدام المعالج

### مقاييس النظام:
- عدد الوكلاء النشطين
- حجم قائمة الانتظار
- زمن استجابة الأحداث

## الأمان

### طبقات الأمان:
1. **Policy Engine**: التحقق من الصلاحيات قبل التنفيذ
2. **Sandbox**: عزل تنفيذ الكود غير الموثوق
3. **Event Audit**: سجل تدقيق شامل لجميع العمليات
4. **Access Control**: قواعد وصول دقيقة

## التوسع المستقبلي

### مكونات مخطط لها:
- [ ] تكامل مع Redis للتخزين المؤقت
- [ ] تكامل مع Qdrant للذاكرة المتجهة
- [ ] Experience Replay للوكلاء
- [ ] Distributed Runtime للتشغيل الموزع
- [ ] WebSocket للبث المباشر للأحداث

## الحالة الحالية

✅ Runtime Engine - مكتمل 100%
✅ Task Scheduler - مكتمل 100%
✅ Event System - مكتمل 100%
✅ Sandbox - مكتمل 100%
✅ Policy Engine - مكتمل 100%

**الإجمالي: 100%** 🎉
