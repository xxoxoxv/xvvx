"""
AMOS Federation Runtime Engine
المحرك الرئيسي لتنفيذ المهام وإدارة دورة حياة الوكلاء
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio
import uuid
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """حالات المهمة"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """أولويات المهام"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Task:
    """تمثيل المهمة"""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        agent_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = task_id
        self.name = name
        self.description = description
        self.agent_id = agent_id
        self.priority = priority
        self.data = data or {}
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.callback = callback
        self.created_at = created_at or datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = TaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        self.max_retries = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "priority": self.priority.value,
            "data": self.data,
            "timeout": self.timeout,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        task = cls(
            task_id=data["id"],
            name=data["name"],
            description=data["description"],
            agent_id=data.get("agent_id"),
            priority=TaskPriority(data.get("priority", 2)),
            data=data.get("data", {}),
            timeout=data.get("timeout"),
            dependencies=data.get("dependencies", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
        task.status = TaskStatus(data.get("status", "pending"))
        task.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        task.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        task.result = data.get("result")
        task.error = data.get("error")
        task.retry_count = data.get("retry_count", 0)
        return task


class ExecutionContext:
    """سياق التنفيذ للمهمة"""
    
    def __init__(self, task: Task, environment: Optional[Dict[str, Any]] = None):
        self.task = task
        self.environment = environment or {}
        self.logs: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "duration_ms": 0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0
        }
        self.state: Dict[str, Any] = {}
    
    def log(self, level: str, message: str, **kwargs):
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "data": kwargs
        })
    
    def update_metric(self, key: str, value: Any):
        self.metrics[key] = value


class RuntimeEngine:
    """محرك Runtime الرئيسي"""
    
    def __init__(self, db_connection=None, redis_client=None, config: Optional[Dict] = None):
        self.config = config or {}
        self.db = db_connection
        self.redis = redis_client
        self.tasks: Dict[str, Task] = {}
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        self.agents: Dict[str, Any] = {}
        self.running = False
        self._task_queue: asyncio.Queue = None
        self._workers: List[asyncio.Task] = []
        self._max_workers = self.config.get("max_workers", 4)
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    async def initialize(self):
        """تهيئة المحرك"""
        logger.info("Initializing Runtime Engine...")
        self._task_queue = asyncio.Queue()
        self.running = True
        
        # تحميل المهام المعلقة من قاعدة البيانات
        if self.db:
            await self._load_pending_tasks()
        
        # بدء العمال
        for i in range(self._max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        
        logger.info(f"Runtime Engine initialized with {self._max_workers} workers")
    
    async def shutdown(self):
        """إيقاف المحرك"""
        logger.info("Shutting down Runtime Engine...")
        self.running = False
        
        # انتظار انتهاء المهام الحالية
        if self._task_queue:
            await self._task_queue.join()
        
        # إيقاف العمال
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("Runtime Engine shut down complete")
    
    async def _load_pending_tasks(self):
        """تحميل المهام المعلقة من قاعدة البيانات"""
        try:
            if hasattr(self.db, 'get_pending_tasks'):
                pending = await self.db.get_pending_tasks()
                for task_data in pending:
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task
                    logger.info(f"Loaded pending task: {task.id}")
        except Exception as e:
            logger.error(f"Error loading pending tasks: {e}")
    
    async def submit_task(self, task: Task) -> str:
        """إ提交 مهمة جديدة"""
        self.tasks[task.id] = task
        await self._task_queue.put(task)
        
        # حفظ في قاعدة البيانات
        if self.db and hasattr(self.db, 'save_task'):
            await self.db.save_task(task.to_dict())
        
        self._emit_event("task_submitted", task)
        logger.info(f"Task submitted: {task.id} - {task.name}")
        return task.id
    
    async def execute_task(self, task: Task) -> Any:
        """تنفيذ مهمة محددة"""
        context = ExecutionContext(task)
        self.execution_contexts[task.id] = context
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        context.update_metric("start_time", task.started_at.isoformat())
        
        try:
            # التحقق من الاعتماديات
            if not await self._check_dependencies(task):
                task.status = TaskStatus.PAUSED
                context.log("WARNING", "Task paused due to unmet dependencies")
                return None
            
            # الحصول على الوكيل المنفذ
            agent = self._get_agent_for_task(task)
            if not agent:
                raise ValueError(f"No agent available for task: {task.id}")
            
            # تنفيذ المهمة عبر الوكيل
            context.log("INFO", f"Executing task with agent: {agent.id if hasattr(agent, 'id') else 'unknown'}")
            
            # محاكاة تنفيذ المهمة (سيتم استبدالها بالوكيل الفعلي)
            result = await self._execute_with_agent(agent, task, context)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            context.update_metric("end_time", task.completed_at.isoformat())
            context.update_metric("duration_ms", (task.completed_at - task.started_at).total_seconds() * 1000)
            
            context.log("INFO", "Task completed successfully", result=result)
            
            # استدعاء الـ callback إذا وجد
            if task.callback:
                await self._invoke_callback(task.callback, result)
            
            self._emit_event("task_completed", task)
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {task.id} - {str(e)}")
            context.log("ERROR", f"Task failed: {str(e)}")
            
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                context.log("INFO", f"Retrying task ({task.retry_count}/{task.max_retries})")
                await self._task_queue.put(task)
            else:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.utcnow()
                self._emit_event("task_failed", task)
            
            raise
    
    async def _execute_with_agent(self, agent, task: Task, context: ExecutionContext) -> Any:
        """تنفيذ المهمة عبر الوكيل"""
        if hasattr(agent, 'execute'):
            return await agent.execute(task.data, context)
        elif hasattr(agent, 'process'):
            return await agent.process(task.data)
        else:
            # تنفيذ افتراضي
            await asyncio.sleep(0.1)  # محاكاة وقت التنفيذ
            return {"status": "success", "task_id": task.id}
    
    async def _check_dependencies(self, task: Task) -> bool:
        """التحقق من اعتماديات المهمة"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _get_agent_for_task(self, task: Task):
        """الحصول على الوكيل المناسب للمهمة"""
        if task.agent_id and task.agent_id in self.agents:
            return self.agents[task.agent_id]
        
        # اختيار وكيل متاح (منطق مبسط)
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'is_available') and agent.is_available():
                return agent
        
        return None
    
    async def _invoke_callback(self, callback: Callable, result: Any):
        """استدعاء الـ callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(result)
            else:
                callback(result)
        except Exception as e:
            logger.error(f"Callback execution failed: {e}")
    
    async def _worker(self, worker_name: str):
        """عامل معالجة المهام"""
        logger.info(f"Worker {worker_name} started")
        
        while self.running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                
                # التحقق من الاعتماديات قبل التنفيذ
                if task.dependencies and not await self._check_dependencies(task):
                    # إعادة الجدولة
                    await asyncio.sleep(0.5)
                    await self._task_queue.put(task)
                    continue
                
                await self.execute_task(task)
                self._task_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
        
        logger.info(f"Worker {worker_name} stopped")
    
    def register_agent(self, agent_id: str, agent: Any):
        """تسجيل وكيل"""
        self.agents[agent_id] = agent
        logger.info(f"Agent registered: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """إلغاء تسجيل وكيل"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
    
    def on_event(self, event_type: str, handler: Callable):
        """تسجيل معالج أحداث"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, data: Any):
        """إصدار حدث"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """الحصول على حالة المهمة"""
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    def get_all_tasks(self) -> List[Task]:
        """الحصول على جميع المهام"""
        return list(self.tasks.values())
    
    def get_execution_context(self, task_id: str) -> Optional[ExecutionContext]:
        """الحصول على سياق التنفيذ"""
        return self.execution_contexts.get(task_id)


# دالة مساعدة لإنشاء مهمة جديدة
def create_task(
    name: str,
    description: str,
    agent_id: Optional[str] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    dependencies: Optional[List[str]] = None,
    callback: Optional[Callable] = None
) -> Task:
    return Task(
        task_id=str(uuid.uuid4()),
        name=name,
        description=description,
        agent_id=agent_id,
        priority=priority,
        data=data,
        timeout=timeout,
        dependencies=dependencies,
        callback=callback
    )
