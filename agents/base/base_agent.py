"""
AMOS Federal State - Base Agent Implementation
التنفيذ الأساسي للوكيل الذي يرث منه جميع الوكلاء

السمات الأساسية:
- هوية فريدة (citizen_id)
- اسم ووصف
- حالة ودورة حياة
- سجل أداء ومهام
- اتصال بقاعدة البيانات
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import uuid
from pathlib import Path


class BaseAgent(ABC):
    """
    الفئة الأساسية لجميع وكلاء الدولة الفدرالية
    
    جميع الوكلاء يرثون من هذه الفئة ويضيفون وظائفهم الخاصة
    """
    
    def __init__(self, citizen_id: str, name: str, 
                 description: Optional[str] = None,
                 data_dir: str = "data/agents"):
        self.citizen_id = citizen_id
        self.name = name
        self.description = description or f"Agent {name}"
        self.created_at = datetime.now()
        self.status = "ACTIVE"  # ACTIVE, INACTIVE, RETIRED, TERMINATED
        
        self.data_dir = Path(data_dir) / citizen_id
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # سجل الأداء
        self.performance_log: List[Dict[str, Any]] = []
        self.tasks_completed = 0
        self.tasks_failed = 0
        
        # الاتصال بقاعدة البيانات
        self.db_connection = None
        
        self._load_state()
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        تنفيذ مهمة (يجب تنفيذه من قبل الفئات الوراثية)
        
        Args:
            task: قاموس يحتوي على تفاصيل المهمة
            
        Returns:
            قاموس يحتوي على نتيجة التنفيذ
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        الحصول على قائمة القدرات المتاحة للوكيل
        
        Returns:
            قائمة من النصوص تمثل القدرات
        """
        pass
    
    def assign_task(self, task: Dict[str, Any]) -> bool:
        """
        تعيين مهمة للوكيل
        
        Args:
            task: تفاصيل المهمة
            
        Returns:
            True إذا تم التعيين بنجاح
        """
        # يمكن تطوير هذا ليتم تخزين المهام في قاعدة البيانات
        self._log_action("TASK_ASSIGNED", task)
        return True
    
    def complete_task(self, task_id: str, result: Any, success: bool = True):
        """
        إكمال مهمة وتسجيل النتيجة
        
        Args:
            task_id: معرف المهمة
            result: نتيجة التنفيذ
            success: هل نجحت المهمة
        """
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        log_entry = {
            "task_id": task_id,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.performance_log.append(log_entry)
        self._save_state()
    
    def _log_action(self, action: str, details: Any):
        """تسجيل إجراء في سجل الوكيل"""
        log_entry = {
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.performance_log.append(log_entry)
        
        # الاحتفاظ بآخر 1000 إدخال فقط
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-1000:]
    
    def _save_state(self):
        """حفظ حالة الوكيل في ملف JSON"""
        state_file = self.data_dir / "state.json"
        state = {
            "citizen_id": self.citizen_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "performance_log": self.performance_log[-100:]  # آخر 100 إدخال فقط
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def _load_state(self):
        """تحميل حالة الوكيل من ملف JSON"""
        state_file = self.data_dir / "state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.status = state.get("status", "ACTIVE")
                self.tasks_completed = state.get("tasks_completed", 0)
                self.tasks_failed = state.get("tasks_failed", 0)
                self.performance_log = state.get("performance_log", [])
    
    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة الوكيل الحالية"""
        return {
            "citizen_id": self.citizen_id,
            "name": self.name,
            "status": self.status,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self._calculate_success_rate(),
            "capabilities": self.get_capabilities()
        }
    
    def _calculate_success_rate(self) -> float:
        """حساب نسبة النجاح"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 1.0
        return self.tasks_completed / total
    
    def deactivate(self):
        """تعطيل الوكيل"""
        self.status = "INACTIVE"
        self._log_action("DEACTIVATED", {})
        self._save_state()
    
    def activate(self):
        """تفعيل الوكيل"""
        self.status = "ACTIVE"
        self._log_action("ACTIVATED", {})
        self._save_state()
    
    def retire(self):
        """تقاعد الوكيل"""
        self.status = "RETIRED"
        self._log_action("RETIRED", {})
        self._save_state()
    
    def terminate(self):
        """إنهاء الوكيل نهائياً"""
        self.status = "TERMINATED"
        self._log_action("TERMINATED", {})
        self._save_state()
    
    def log_event(self, level: str, message: str):
        """تسجيل حدث في سجل الوكيل"""
        self._log_action(f"EVENT_{level.upper()}", {"message": message})
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self.citizen_id})>"
