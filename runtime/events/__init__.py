"""
AMOS Federation Event System
نظام الأحداث والتسجيل
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio
import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    """أنواع الأحداث"""
    # دورة حياة المهمة
    TASK_SUBMITTED = "task.submitted"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    
    # دورة حياة الوكيل
    AGENT_REGISTERED = "agent.registered"
    AGENT_UNREGISTERED = "agent.unregistered"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    AGENT_ERROR = "agent.error"
    
    # النظام
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_METRICS = "system.metrics"
    
    # الأمان
    SECURITY_ALERT = "security.alert"
    SECURITY_AUDIT = "security.audit"
    
    # مخصص
    CUSTOM = "custom"


@dataclass
class Event:
    """تمثيل الحدث"""
    event_type: str
    event_id: str
    timestamp: str
    source: str
    data: Dict[str, Any]
    severity: str = "info"  # debug, info, warning, error, critical
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def create(
        cls,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        severity: str = "info",
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> "Event":
        import uuid
        return cls(
            event_type=event_type.value if isinstance(event_type, EventType) else event_type,
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            source=source,
            data=data,
            severity=severity,
            correlation_id=correlation_id,
            causation_id=causation_id
        )


class EventBus:
    """ناقل الأحداث"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_store: List[Event] = []
        self._max_store_size = 10000
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type: str, handler: Callable):
        """اشتراك معالج في حدث"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscriber added for event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """إلغاء اشتراك معالج"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
    
    async def publish(self, event: Event):
        """نشر حدث"""
        # تخزين الحدث
        async with self._lock:
            self._event_store.append(event)
            if len(self._event_store) > self._max_store_size:
                self._event_store = self._event_store[-self._max_store_size:]
        
        # إشراك المشتركين
        handlers = self._subscribers.get(event.event_type, [])
        handlers.extend(self._subscribers.get("*", []))  # المشتركين العاميين
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
        
        # تسجيل للأحداث الهامة
        if event.severity in ["error", "critical"]:
            logger.error(f"Event [{event.event_type}]: {json.dumps(event.data)}")
        elif event.severity == "warning":
            logger.warning(f"Event [{event.event_type}]: {json.dumps(event.data)}")
        else:
            logger.debug(f"Event [{event.event_type}]: {json.dumps(event.data)}")
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """الحصول على الأحداث"""
        filtered = self._event_store
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        
        if source:
            filtered = [e for e in filtered if e.source == source]
        
        if start_time:
            filtered = [e for e in filtered if datetime.fromisoformat(e.timestamp) >= start_time]
        
        if end_time:
            filtered = [e for e in filtered if datetime.fromisoformat(e.timestamp) <= end_time]
        
        return filtered[-limit:]
    
    def clear(self):
        """مسح مخزن الأحداث"""
        self._event_store.clear()


class EventLogger:
    """مسجل الأحداث"""
    
    def __init__(self, event_bus: EventBus, log_file: Optional[str] = None):
        self.event_bus = event_bus
        self.log_file = log_file
        self._async_lock = asyncio.Lock()
    
    async def log_event(self, event: Event):
        """تسجيل حدث"""
        # نشر الحدث
        await self.event_bus.publish(event)
        
        # كتابة للملف إذا وجد
        if self.log_file:
            await self._write_to_file(event)
    
    async def _write_to_file(self, event: Event):
        """كتابة الحدث للملف"""
        async with self._async_lock:
            try:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(event.to_dict()) + "\n")
            except Exception as e:
                logger.error(f"Error writing event to file: {e}")
    
    def log_sync(self, event: Event):
        """تسجيل متزامن (للاستخدام في الكود غير المتزامن)"""
        # نشر متزامن (قد لا يعمل مع المعالجات غير المتزامنة)
        handlers = self.event_bus._subscribers.get(event.event_type, [])
        for handler in handlers:
            if not asyncio.iscoroutinefunction(handler):
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Sync event handler error: {e}")
        
        # كتابة للملف
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(event.to_dict()) + "\n")
            except Exception as e:
                logger.error(f"Error writing event to file: {e}")


class MetricsCollector:
    """مجمع المقاييس"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """زيادة عداد"""
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value
        
        # نشر حدث
        event = Event.create(
            event_type=EventType.SYSTEM_METRICS,
            source="metrics_collector",
            data={
                "metric_type": "counter",
                "name": name,
                "key": key,
                "value": self._counters[key],
                "tags": tags or {}
            }
        )
        self.event_bus.publish(event)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """تعيين مقياس"""
        key = self._make_key(name, tags)
        self._gauges[key] = value
        
        event = Event.create(
            event_type=EventType.SYSTEM_METRICS,
            source="metrics_collector",
            data={
                "metric_type": "gauge",
                "name": name,
                "key": key,
                "value": value,
                "tags": tags or {}
            }
        )
        self.event_bus.publish(event)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """تسجيل قيمة هيستوجرام"""
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        
        # حساب إحصائيات
        values = self._histograms[key]
        stats = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": self._percentile(values, 50),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }
        
        event = Event.create(
            event_type=EventType.SYSTEM_METRICS,
            source="metrics_collector",
            data={
                "metric_type": "histogram",
                "name": name,
                "key": key,
                "stats": stats,
                "tags": tags or {}
            }
        )
        self.event_bus.publish(event)
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """إنشاء مفتاح فريد"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """حساب النسبة المئوية"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[-1]
        
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def get_metrics(self) -> Dict[str, Any]:
        """الحصول على جميع المقاييس"""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v),
                    "max": max(v),
                    "avg": sum(v) / len(v),
                    "p50": self._percentile(v, 50),
                    "p95": self._percentile(v, 95),
                    "p99": self._percentile(v, 99)
                }
                for k, v in self._histograms.items() if v
            }
        }
    
    def reset(self):
        """إعادة تعيين جميع المقاييس"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
