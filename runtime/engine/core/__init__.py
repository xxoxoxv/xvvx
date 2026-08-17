"""
AMOS Runtime Engine - Core Module
محرك وقت التشغيل - الوحدة الأساسية

This module provides the core runtime engine for executing agent tasks,
managing workflows, and orchestrating the federal state operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """حالة المهمة"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """أولوية المهمة"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """تمثيل المهمة"""
    id: str
    name: str
    agent_id: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل المهمة إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'agent_id': self.agent_id,
            'payload': self.payload,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


class TaskQueue:
    """طابور المهام ذو الأولوية"""
    
    def __init__(self):
        self._queues: Dict[Priority, List[Task]] = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.NORMAL: [],
            Priority.LOW: []
        }
        self._lock = asyncio.Lock()
    
    async def enqueue(self, task: Task) -> None:
        """إضافة مهمة للطابور"""
        async with self._lock:
            self._queues[task.priority].append(task)
            logger.info(f"Task {task.id} enqueued with priority {task.priority.name}")
    
    async def dequeue(self) -> Optional[Task]:
        """سحب مهمة من الطابور حسب الأولوية"""
        async with self._lock:
            for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                if self._queues[priority]:
                    task = self._queues[priority].pop(0)
                    logger.info(f"Task {task.id} dequeued")
                    return task
        return None
    
    async def size(self) -> int:
        """حجم الطابور الكلي"""
        async with self._lock:
            return sum(len(q) for q in self._queues.values())


class RuntimeEngine:
    """
    محرك وقت التشغيل الرئيسي
    Responsible for executing tasks, managing agents, and orchestrating workflows
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.task_queue = TaskQueue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.agents: Dict[str, Any] = {}
        self._running = False
        self._workers: List[asyncio.Task] = []
        self._num_workers = self.config.get('num_workers', 4)
        
        logger.info("Runtime Engine initialized")
    
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """تسجيل وكيل في المحرك"""
        self.agents[agent_id] = agent
        logger.info(f"Agent {agent_id} registered")
    
    def unregister_agent(self, agent_id: str) -> None:
        """إلغاء تسجيل وكيل"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")
    
    async def submit_task(self, task: Task) -> str:
        """إ提交 مهمة للتنفيذ"""
        await self.task_queue.enqueue(task)
        self.active_tasks[task.id] = task
        logger.info(f"Task {task.id} submitted")
        return task.id
    
    async def _execute_task(self, task: Task) -> None:
        """تنفيذ مهمة واحدة"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            if task.agent_id not in self.agents:
                raise ValueError(f"Agent {task.agent_id} not found")
            
            agent = self.agents[task.agent_id]
            
            # Execute task based on agent type
            if hasattr(agent, 'execute'):
                result = await agent.execute(task.payload)
            elif hasattr(agent, 'run'):
                result = await agent.run(task.payload)
            else:
                result = await self._default_executor(task)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                await self.task_queue.enqueue(task)
                logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task.id} failed permanently: {e}")
        
        finally:
            if task.id in self.active_tasks:
                self.completed_tasks[task.id] = self.active_tasks.pop(task.id)
    
    async def _default_executor(self, task: Task) -> Any:
        """منفذ المهام الافتراضي"""
        await asyncio.sleep(0.1)  # Simulate work
        return {'status': 'executed', 'task_id': task.id}
    
    async def _worker(self, worker_id: int) -> None:
        """عامل تنفيذ المهام"""
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            task = await self.task_queue.dequeue()
            
            if task:
                await self._execute_task(task)
            else:
                await asyncio.sleep(0.1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self) -> None:
        """بدء تشغيل المحرك"""
        if self._running:
            return
        
        self._running = True
        logger.info(f"Starting Runtime Engine with {self._num_workers} workers")
        
        for i in range(self._num_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
    
    async def stop(self) -> None:
        """إيقاف المحرك"""
        if not self._running:
            return
        
        self._running = False
        logger.info("Stopping Runtime Engine")
        
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
    
    async def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة المحرك"""
        return {
            'running': self._running,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'queue_size': await self.task_queue.size(),
            'workers': len(self._workers),
            'agents': len(self.agents)
        }


# Singleton instance
_engine_instance: Optional[RuntimeEngine] = None


def get_engine(config: Optional[Dict[str, Any]] = None) -> RuntimeEngine:
    """الحصول على مثان المحرك الوحيد"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RuntimeEngine(config)
    return _engine_instance


async def initialize_engine(config: Optional[Dict[str, Any]] = None) -> RuntimeEngine:
    """تهيئة وتشغيل المحرك"""
    engine = get_engine(config)
    await engine.start()
    return engine
