"""
AMOS Federal State - Coordinator Agent Framework
الوكلاء المنسقون - الطبقة العليا من الهرمية

المنسقون يديرون المشرفين، يضعون الاستراتيجيات، ويتخذون القرارات الاستراتيجية.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

from ..base.base_agent import BaseAgent


class CoordinatorAgent(BaseAgent):
    """
    وكيل منسق - يدير فريق من Supervisor Agents
    
    المسؤوليات:
    - وضع الاستراتيجيات والخطط
    - تنسيق بين الأقسام/المناطق
    - اتخاذ القرارات الاستراتيجية
    - رفع التقارير للإدارة العليا
    """
    
    def __init__(
        self,
        citizen_id: str,
        name: str,
        role: str = "COORDINATOR",
        scope: str = "NATIONAL",
        **kwargs
    ):
        super().__init__(citizen_id, name, role, **kwargs)
        
        self.scope = scope  # NATIONAL, REGIONAL, DEPARTMENTAL
        self.supervisors: Dict[str, dict] = {}  # supervisor_id -> info
        self.strategic_plans: Dict[str, dict] = {}
        self.active_initiatives: Dict[str, dict] = {}
        self.decisions_log: List[dict] = []
        
        self._load_coordination_data()
    
    def _load_coordination_data(self):
        """تحميل بيانات التنسيق"""
        coord_file = self.data_dir / f"coordinator_{self.citizen_id}_data.json"
        if coord_file.exists():
            with open(coord_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.supervisors = data.get("supervisors", {})
                self.strategic_plans = data.get("plans", {})
                self.active_initiatives = data.get("initiatives", {})
                self.decisions_log = data.get("decisions", [])
    
    def _save_coordination_data(self):
        """حفظ بيانات التنسيق"""
        coord_file = self.data_dir / f"coordinator_{self.citizen_id}_data.json"
        data = {
            "supervisors": self.supervisors,
            "plans": self.strategic_plans,
            "initiatives": self.active_initiatives,
            "decisions": self.decisions_log,
            "updated_at": datetime.now().isoformat()
        }
        with open(coord_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_supervisor(self, supervisor_id: str, supervisor_info: dict) -> bool:
        """إضافة مشرف للفريق"""
        if supervisor_id in self.supervisors:
            self.log_event("warning", f"المشرف {supervisor_id} موجود بالفعل")
            return False
        
        self.supervisors[supervisor_id] = {
            **supervisor_info,
            "added_at": datetime.now().isoformat(),
            "status": "active"
        }
        self._save_coordination_data()
        self.log_event("info", f"تم إضافة المشرف {supervisor_info.get('name', 'Unknown')}")
        return True
    
    def remove_supervisor(self, supervisor_id: str) -> bool:
        """إزالة مشرف من الفريق"""
        if supervisor_id not in self.supervisors:
            return False
        
        removed = self.supervisors.pop(supervisor_id)
        self._save_coordination_data()
        self.log_event("info", f"تم إزالة المشرف {removed.get('name', 'Unknown')}")
        return True
    
    def create_strategic_plan(self, plan_name: str, objectives: List[str], timeline: dict) -> str:
        """إنشاء خطة استراتيجية"""
        plan_id = str(uuid.uuid4())
        
        self.strategic_plans[plan_id] = {
            "name": plan_name,
            "objectives": objectives,
            "timeline": timeline,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "kpi_targets": {},
            "progress": 0.0
        }
        
        self._save_coordination_data()
        self.log_event("info", f"تم إنشاء الخطة الاستراتيجية: {plan_name}")
        return plan_id
    
    def launch_initiative(self, initiative_name: str, plan_id: str, assigned_supervisors: List[str]) -> str:
        """إطلاق مبادرة ضمن خطة استراتيجية"""
        if plan_id not in self.strategic_plans:
            raise ValueError(f"الخطة {plan_id} غير موجودة")
        
        initiative_id = str(uuid.uuid4())
        
        self.active_initiatives[initiative_id] = {
            "name": initiative_name,
            "plan_id": plan_id,
            "assigned_supervisors": assigned_supervisors,
            "status": "active",
            "launched_at": datetime.now().isoformat(),
            "milestones": [],
            "resources_allocated": {}
        }
        
        # تحديث الخطة الأم
        self.strategic_plans[plan_id]["initiatives"] = self.strategic_plans[plan_id].get("initiatives", [])
        self.strategic_plans[plan_id]["initiatives"].append(initiative_id)
        
        self._save_coordination_data()
        self.log_event("info", f"تم إطلاق المبادرة: {initiative_name}")
        return initiative_id
    
    def make_decision(self, decision_type: str, description: str, impact: str, stakeholders: List[str]) -> dict:
        """اتخاذ قرار استراتيجي"""
        decision_id = str(uuid.uuid4())
        
        decision = {
            "id": decision_id,
            "type": decision_type,
            "description": description,
            "impact": impact,
            "stakeholders": stakeholders,
            "made_at": datetime.now().isoformat(),
            "status": "implemented",
            "review_date": None
        }
        
        self.decisions_log.append(decision)
        self._save_coordination_data()
        self.log_event("info", f"تم اتخاذ القرار: {decision_type} - {description[:50]}...")
        
        return decision
    
    def get_coordination_status(self) -> dict:
        """الحصول على حالة التنسيق"""
        return {
            "coordinator_id": self.citizen_id,
            "coordinator_name": self.name,
            "scope": self.scope,
            "supervisors_count": len(self.supervisors),
            "active_plans": len([p for p in self.strategic_plans.values() if p["status"] == "active"]),
            "active_initiatives": len([i for i in self.active_initiatives.values() if i["status"] == "active"]),
            "total_decisions": len(self.decisions_log),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_strategic_report(self) -> dict:
        """إنشاء تقرير استراتيجي شامل"""
        return {
            "report_type": "strategic_coordination_report",
            "coordinator": self.get_coordination_status(),
            "strategic_plans": list(self.strategic_plans.values()),
            "active_initiatives": list(self.active_initiatives.values()),
            "recent_decisions": self.decisions_log[-10:],
            "generated_at": datetime.now().isoformat()
        }
    
    async def execute(self, instruction: str) -> dict:
        """تنفيذ تعليمات التنسيق"""
        self.log_event("info", f"منسق يتلقى تعليمات: {instruction[:50]}...")
        
        instruction_lower = instruction.lower()
        
        if "تقرير" in instruction_lower or "report" in instruction_lower:
            return self.generate_strategic_report()
        elif "حالة" in instruction_lower or "status" in instruction_lower:
            return self.get_coordination_status()
        elif "خطة" in instruction_lower or "plan" in instruction_lower:
            # مثال: إنشاء خطة جديدة
            plan_id = self.create_strategic_plan(
                plan_name="خطة طارئة",
                objectives=["تحسين الكفاءة", "تقليل التكاليف"],
                timeline={"start": "2025-01-01", "end": "2025-12-31"}
            )
            return {"action": "plan_created", "plan_id": plan_id}
        elif "قرار" in instruction_lower or "decision" in instruction_lower:
            decision = self.make_decision(
                decision_type="استراتيجي",
                description=instruction,
                impact="عالي",
                stakeholders=["all_departments"]
            )
            return {"action": "decision_made", "decision": decision}
        else:
            return await super().execute(instruction)


class NationalCoordinator(CoordinatorAgent):
    """منسق وطني - أعلى مستوى تنسيقي"""
    
    def __init__(self, citizen_id: str, name: str, **kwargs):
        super().__init__(citizen_id, name, role="NATIONAL_COORDINATOR", scope="NATIONAL", **kwargs)
        self.priority_areas: List[str] = []
    
    def set_priority(self, area: str, priority_level: int):
        """تحديد أولوية وطنية"""
        self.priority_areas.append({"area": area, "level": priority_level})
        self.priority_areas.sort(key=lambda x: x["level"], reverse=True)
        self._save_coordination_data()
        self.log_event("info", f"تم تحديد الأولوية الوطنية: {area} (مستوى {priority_level})")


class DepartmentalCoordinator(CoordinatorAgent):
    """منسق قطاعي - يدير قطاعاً محدداً"""
    
    def __init__(self, citizen_id: str, name: str, department: str, **kwargs):
        super().__init__(citizen_id, name, role="DEPT_COORDINATOR", scope="DEPARTMENTAL", **kwargs)
        self.department = department
        self.sub_departments: List[str] = []
    
    def add_sub_department(self, dept_name: str):
        """إضافة قسم فرعي"""
        if dept_name not in self.sub_departments:
            self.sub_departments.append(dept_name)
            self._save_coordination_data()
