"""
AMOS Federation Scheduler
جدول المهام الذكي وإدارة الأولويات
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import heapq
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ScheduleStrategy(Enum):
    """استراتيجيات الجدولة"""
    FIFO = "fifo"  # أول وارد أول صادر
    LIFO = "lifo"  # آخر وارد أول صادر
    PRIORITY = "priority"  # حسب الأولوية
    DEADLINE = "deadline"  # حسب الموعد النهائي
    FAIR = "fair"  # توزيع عادل


class ScheduledTask:
    """مهمة مجدولة"""
    
    def __init__(
        self,
        task_id: str,
        scheduled_time: datetime,
        priority: int = 0,
        deadline: Optional[datetime] = None,
        recurrence: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.scheduled_time = scheduled_time
        self.priority = priority
        self.deadline = deadline
        self.recurrence = recurrence
        self.data = data or {}
        self.created_at = datetime.utcnow()
        self.executed = False
        self.retry_count = 0
    
    def __lt__(self, other):
        # للمقارنة في الـ heap
        if self.scheduled_time != other.scheduled_time:
            return self.scheduled_time < other.scheduled_time
        return self.priority > other.priority  # الأولوية الأعلى أولاً
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "scheduled_time": self.scheduled_time.isoformat(),
            "priority": self.priority,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "recurrence": self.recurrence,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "executed": self.executed,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        task = cls(
            task_id=data["task_id"],
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            priority=data.get("priority", 0),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            recurrence=data.get("recurrence"),
            data=data.get("data", {})
        )
        task.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        task.executed = data.get("executed", False)
        task.retry_count = data.get("retry_count", 0)
        return task
    
    def should_execute(self) -> bool:
        """هل يجب تنفيذ المهمة الآن؟"""
        return datetime.utcnow() >= self.scheduled_time and not self.executed
    
    def is_overdue(self) -> bool:
        """هل تجاوزت المهمة موعدنها النهائي؟"""
        if self.deadline:
            return datetime.utcnow() > self.deadline and not self.executed
        return False
    
    def next_recurrence(self) -> Optional[datetime]:
        """حساب وقت التكرار التالي"""
        if not self.recurrence:
            return None
        
        interval = self.recurrence.get("interval")
        value = self.recurrence.get("value", 1)
        
        if interval == "seconds":
            return self.scheduled_time + timedelta(seconds=value)
        elif interval == "minutes":
            return self.scheduled_time + timedelta(minutes=value)
        elif interval == "hours":
            return self.scheduled_time + timedelta(hours=value)
        elif interval == "days":
            return self.scheduled_time + timedelta(days=value)
        elif interval == "weeks":
            return self.scheduled_time + timedelta(weeks=value)
        
        return None


class TaskScheduler:
    """جدول المهام"""
    
    def __init__(self, strategy: ScheduleStrategy = ScheduleStrategy.PRIORITY):
        self.strategy = strategy
        self._queue: List[ScheduledTask] = []
        self._task_map: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._callbacks: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def start(self):
        """بدء الجدول"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("Task scheduler started")
    
    async def stop(self):
        """إيقاف الجدول"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Task scheduler stopped")
    
    async def schedule(
        self,
        task_id: str,
        scheduled_time: datetime,
        priority: int = 0,
        deadline: Optional[datetime] = None,
        recurrence: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        callback: Optional[Any] = None
    ) -> str:
        """جدولة مهمة"""
        async with self._lock:
            task = ScheduledTask(
                task_id=task_id,
                scheduled_time=scheduled_time,
                priority=priority,
                deadline=deadline,
                recurrence=recurrence,
                data=data
            )
            
            heapq.heappush(self._queue, task)
            self._task_map[task_id] = task
            
            if callback:
                self._callbacks[task_id] = callback
            
            logger.info(f"Task scheduled: {task_id} at {scheduled_time}")
            return task_id
    
    async def schedule_now(
        self,
        task_id: str,
        priority: int = 0,
        data: Optional[Dict[str, Any]] = None,
        callback: Optional[Any] = None
    ) -> str:
        """جدولة مهمة للتنفيذ الفوري"""
        return await self.schedule(
            task_id=task_id,
            scheduled_time=datetime.utcnow(),
            priority=priority,
            data=data,
            callback=callback
        )
    
    async def schedule_delayed(
        self,
        task_id: str,
        delay_seconds: int,
        priority: int = 0,
        data: Optional[Dict[str, Any]] = None,
        callback: Optional[Any] = None
    ) -> str:
        """جدولة مهمة بتنفيذ متأخر"""
        scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        return await self.schedule(
            task_id=task_id,
            scheduled_time=scheduled_time,
            priority=priority,
            data=data,
            callback=callback
        )
    
    async def cancel(self, task_id: str) -> bool:
        """إلغاء مهمة مجدولة"""
        async with self._lock:
            if task_id not in self._task_map:
                return False
            
            task = self._task_map.pop(task_id)
            task.executed = True  # منع التنفيذ
            
            # إعادة بناء الـ queue بدون المهمة الملغاة
            self._queue = [t for t in self._queue if t.task_id != task_id]
            heapq.heapify(self._queue)
            
            if task_id in self._callbacks:
                del self._callbacks[task_id]
            
            logger.info(f"Task cancelled: {task_id}")
            return True
    
    async def get_pending_tasks(self) -> List[ScheduledTask]:
        """الحصول على المهام المعلقة"""
        async with self._lock:
            now = datetime.utcnow()
            pending = [t for t in self._queue if not t.executed]
            
            if self.strategy == ScheduleStrategy.PRIORITY:
                pending.sort(key=lambda t: (-t.priority, t.scheduled_time))
            elif self.strategy == ScheduleStrategy.DEADLINE:
                pending.sort(key=lambda t: (t.deadline or datetime.max, t.scheduled_time))
            elif self.strategy == ScheduleStrategy.FAIR:
                pending.sort(key=lambda t: t.created_at)
            
            return pending
    
    async def _run_scheduler(self):
        """تشغيل حلقة الجدولة"""
        while self._running:
            try:
                await self._process_due_tasks()
                await asyncio.sleep(0.1)  # فحص كل 100ms
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(1)
    
    async def _process_due_tasks(self):
        """معالجة المهام المستحقة"""
        async with self._lock:
            now = datetime.utcnow()
            executed_tasks = []
            
            while self._queue and self._queue[0].should_execute():
                task = heapq.heappop(self._queue)
                
                if task.executed:
                    continue
                
                task.executed = True
                executed_tasks.append(task)
                
                # جدولة التكرار التالي إذا وجد
                if task.recurrence:
                    next_time = task.next_recurrence()
                    if next_time:
                        new_task = ScheduledTask(
                            task_id=f"{task.task_id}_run_{task.retry_count + 1}",
                            scheduled_time=next_time,
                            priority=task.priority,
                            deadline=task.deadline,
                            recurrence=task.recurrence,
                            data=task.data
                        )
                        heapq.heappush(self._queue, new_task)
                        self._task_map[new_task.task_id] = new_task
                
                # إزالة من الخريطة
                if task.task_id in self._task_map:
                    del self._task_map[task.task_id]
            
            # إطلاق الأحداث للمهام المنفذة
            for task in executed_tasks:
                await self._on_task_due(task)
    
    async def _on_task_due(self, task: ScheduledTask):
        """عند استحقاق مهمة"""
        logger.info(f"Task due: {task.task_id}")
        
        callback = self._callbacks.get(task.task_id)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"Callback error for task {task.task_id}: {e}")
    
    def get_queue_size(self) -> int:
        """حجم قائمة الانتظار"""
        return len(self._queue)
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """الحصول على مهمة محددة"""
        return self._task_map.get(task_id)
    
    def clear(self):
        """مسح جميع المهام"""
        self._queue.clear()
        self._task_map.clear()
        self._callbacks.clear()
        logger.info("Scheduler queue cleared")
