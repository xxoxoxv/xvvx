"""
AMOS Federal State - Supervisor Agent Framework
الوكلاء المشرفون - الطبقة العليا من هرمية الوكلاء

المشرفون يديرون الفرق، يوزعون المهام، ويراقبون الأداء.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
import os

from ..base.base_agent import BaseAgent


class SupervisorAgent(BaseAgent):
    """
    وكيل مشرف - يدير فريق من Worker Agents
    
    المسؤوليات:
    - توزيع المهام على العمال
    - مراقبة التقدم والأداء
    - حل التعارضات والتنسيق
    - رفع التقارير للوكلاء المنسقين
    """
    
    def __init__(
        self,
        citizen_id: str,
        name: str,
        role: str = "SUPERVISOR",
        department: Optional[str] = None,
        team_size: int = 5,
        **kwargs
    ):
        super().__init__(citizen_id, name, role, **kwargs)
        
        self.department = department or "GENERAL"
        self.team_size = team_size
        self.workers: Dict[str, str] = {}  # worker_id -> worker_name
        self.active_tasks: Dict[str, dict] = {}
        self.completed_tasks: List[dict] = []
        self.performance_metrics: Dict[str, Any] = {
            "tasks_assigned": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_completion_time": 0.0,
            "team_efficiency": 1.0
        }
        
        self._load_team()
    
    def _load_team(self):
        """تحميل فريق العمال من التخزين"""
        workers_file = self.data_dir / f"supervisor_{self.citizen_id}_team.json"
        if workers_file.exists():
            with open(workers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workers = data.get("workers", {})
                self.performance_metrics = data.get("metrics", self.performance_metrics)
    
    def _save_team(self):
        """حفظ حالة الفريق"""
        workers_file = self.data_dir / f"supervisor_{self.citizen_id}_team.json"
        data = {
            "workers": self.workers,
            "metrics": self.performance_metrics,
            "updated_at": datetime.now().isoformat()
        }
        with open(workers_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def assign_worker(self, worker_id: str, worker_name: str) -> bool:
        """إضافة عامل للفريق"""
        if len(self.workers) >= self.team_size:
            self.log_event("warning", f"فريق كامل - لا يمكن إضافة {worker_name}")
            return False
        
        self.workers[worker_id] = worker_name
        self._save_team()
        self.log_event("info", f"تم إضافة العامل {worker_name} ({worker_id}) للفريق")
        return True
    
    def remove_worker(self, worker_id: str) -> bool:
        """إزالة عامل من الفريق"""
        if worker_id not in self.workers:
            return False
        
        worker_name = self.workers.pop(worker_id)
        self._save_team()
        self.log_event("info", f"تم إزالة العامل {worker_name} ({worker_id}) من الفريق")
        return True
    
    def distribute_task(self, task: dict, worker_id: Optional[str] = None) -> Optional[str]:
        """
        توزيع مهمة على عامل
        
        Args:
            task: تعريف المهمة
            worker_id: معرف العامل المحدد (اختياري - يتم الاختيار التلقائي إذا لم يُحدد)
        
        Returns:
            معرف العامل الذي تم تعيينه أو None إذا فشل
        """
        if not self.workers:
            self.log_event("error", "لا يوجد عمال في الفريق لتوزيع المهمة")
            return None
        
        # اختيار العامل الأنسب
        if worker_id is None:
            worker_id = self._select_best_worker(task)
        
        if worker_id not in self.workers:
            self.log_event("error", f"العامل {worker_id} غير موجود في الفريق")
            return None
        
        # تسجيل المهمة النشطة
        task_id = task.get("id", str(uuid.uuid4()))
        self.active_tasks[task_id] = {
            "task": task,
            "assigned_to": worker_id,
            "assigned_at": datetime.now().isoformat(),
            "status": "IN_PROGRESS"
        }
        
        self.performance_metrics["tasks_assigned"] += 1
        self._save_team()
        
        self.log_event("info", f"تم توزيع المهمة {task_id} على العامل {self.workers[worker_id]}")
        return worker_id
    
    def _select_best_worker(self, task: dict) -> str:
        """اختيار أفضل عامل للمهمة بناءً على الحمل والمهارات"""
        if not self.workers:
            raise ValueError("لا يوجد عمال متاحين")
        
        # استراتيجية بسيطة: اختيار العامل بأقل مهام نشطة
        # يمكن تطويرها لتشمل المهارات والتخصصات
        return list(self.workers.keys())[0]  # مؤقتاً نختار الأول
    
    def complete_task(self, task_id: str, result: dict, success: bool = True):
        """إكمال مهمة"""
        if task_id not in self.active_tasks:
            self.log_event("warning", f"المهمة {task_id} غير موجودة في المهام النشطة")
            return
        
        task_info = self.active_tasks.pop(task_id)
        assigned_at = datetime.fromisoformat(task_info["assigned_at"])
        completion_time = (datetime.now() - assigned_at).total_seconds()
        
        self.completed_tasks.append({
            "task_id": task_id,
            "result": result,
            "success": success,
            "completion_time": completion_time,
            "completed_at": datetime.now().isoformat()
        })
        
        # تحديث المقاييس
        if success:
            self.performance_metrics["tasks_completed"] += 1
        else:
            self.performance_metrics["tasks_failed"] += 1
        
        # حساب متوسط وقت الإكمال
        total_time = sum(t["completion_time"] for t in self.completed_tasks[-10:])  # آخر 10 مهام
        self.performance_metrics["avg_completion_time"] = total_time / min(len(self.completed_tasks), 10)
        
        # حساب كفاءة الفريق
        total = self.performance_metrics["tasks_assigned"]
        if total > 0:
            self.performance_metrics["team_efficiency"] = self.performance_metrics["tasks_completed"] / total
        
        self._save_team()
        self.log_event("info", f"اكتملت المهمة {task_id} - ناجحة: {success}")
    
    def get_team_status(self) -> dict:
        """الحصول على حالة الفريق"""
        return {
            "supervisor_id": self.citizen_id,
            "supervisor_name": self.name,
            "department": self.department,
            "team_size": len(self.workers),
            "workers": self.workers,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "metrics": self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_report(self, period: str = "daily") -> dict:
        """إنشاء تقرير أداء"""
        return {
            "report_type": f"{period}_supervisor_report",
            "supervisor": self.get_team_status(),
            "recent_completions": self.completed_tasks[-20:],
            "generated_at": datetime.now().isoformat()
        }
    
    async def execute(self, instruction: str) -> dict:
        """تنفيذ تعليمات الإشراف"""
        self.log_event("info", f"مشرف يتلقى تعليمات: {instruction[:50]}...")
        
        # تحليل التعليمات وتنفيذ الإجراء المناسب
        instruction_lower = instruction.lower()
        
        if "تقرير" in instruction_lower or "report" in instruction_lower:
            return self.generate_report()
        elif "حالة" in instruction_lower or "status" in instruction_lower:
            return self.get_team_status()
        elif "توزيع" in instruction_lower or "assign" in instruction_lower:
            # مثال: توزيع مهمة جديدة
            task = {"id": str(uuid.uuid4()), "description": instruction, "type": "manual"}
            worker_id = self.distribute_task(task)
            return {"action": "task_distributed", "worker_id": worker_id, "task_id": task["id"]}
        else:
            # تنفيذ افتراضي
            return await super().execute(instruction)


class DepartmentSupervisor(SupervisorAgent):
    """مشرف قسم - يدير قسماً محدداً"""
    
    def __init__(self, citizen_id: str, name: str, department: str, **kwargs):
        super().__init__(citizen_id, name, role="DEPT_SUPERVISOR", department=department, **kwargs)
        self.specialization = self._get_department_specialization(department)
    
    def _get_department_specialization(self, dept: str) -> List[str]:
        """الحصول على تخصصات القسم"""
        specializations = {
            "FINANCE": ["accounting", "budgeting", "auditing"],
            "HEALTH": ["medical", "emergency", "public_health"],
            "EDUCATION": ["curriculum", "training", "certification"],
            "SECURITY": ["surveillance", "emergency_response", "risk_assessment"],
            "INFRASTRUCTURE": ["construction", "maintenance", "planning"],
            "JUSTICE": ["legal_review", "compliance", "investigation"]
        }
        return specializations.get(dept, ["general"])


class RegionalSupervisor(SupervisorAgent):
    """مشرف إقليمي - يدير منطقة جغرافية"""
    
    def __init__(self, citizen_id: str, name: str, region: str, **kwargs):
        super().__init__(citizen_id, name, role="REGIONAL_SUPERVISOR", **kwargs)
        self.region = region
        self.sub_regions: List[str] = []
    
    def add_sub_region(self, region_name: str):
        """إضافة منطقة فرعية"""
        if region_name not in self.sub_regions:
            self.sub_regions.append(region_name)
            self.log_event("info", f"تم إضافة المنطقة {region_name}")
    
    def get_regional_status(self) -> dict:
        """الحصول على حالة المنطقة"""
        status = self.get_team_status()
        status["region"] = self.region
        status["sub_regions"] = self.sub_regions
        return status
