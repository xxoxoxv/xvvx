"""
AMOS Federal State - Agent Hierarchy Management
إدارة هرمية الوكلاء

الهرمية الكاملة:
1. Sovereign (zoorooz) - السيادة المطلقة
2. National Coordinators - المنسقون الوطنيون
3. Departmental/Regional Coordinators - منسقو القطاعات/المناطق
4. Supervisors (Department/Regional) - المشرفون
5. Worker Agents - وكلاء العمال التنفيذيين
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid

from agents.base.base_agent import BaseAgent
from agents.workers.worker_agent import WorkerAgent
from agents.supervisors.supervisor_agent import SupervisorAgent, DepartmentSupervisor, RegionalSupervisor
from agents.coordinators.coordinator_agent import CoordinatorAgent, NationalCoordinator, DepartmentalCoordinator


class AgentHierarchy:
    """
    إدارة هرمية الوكلاء الكاملة للدولة الفدرالية
    """
    
    def __init__(self, data_dir: str = "data/agents"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.sovereign: Optional[str] = None  # citizen_id of sovereign
        self.national_coordinators: Dict[str, NationalCoordinator] = {}
        self.departmental_coordinators: Dict[str, DepartmentalCoordinator] = {}
        self.supervisors: Dict[str, SupervisorAgent] = {}
        self.workers: Dict[str, WorkerAgent] = {}
        
        self._load_hierarchy()
    
    def _load_hierarchy(self):
        """تحميل حالة الهرمية"""
        hierarchy_file = self.data_dir / "hierarchy_state.json"
        if hierarchy_file.exists():
            with open(hierarchy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sovereign = data.get("sovereign")
                # يمكن تحميل الوكلاء الحاليين هنا
    
    def _save_hierarchy(self):
        """حفظ حالة الهرمية"""
        hierarchy_file = self.data_dir / "hierarchy_state.json"
        data = {
            "sovereign": self.sovereign,
            "national_coordinators_count": len(self.national_coordinators),
            "departmental_coordinators_count": len(self.departmental_coordinators),
            "supervisors_count": len(self.supervisors),
            "workers_count": len(self.workers),
            "updated_at": datetime.now().isoformat()
        }
        with open(hierarchy_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def set_sovereign(self, citizen_id: str, name: str) -> bool:
        """تعيين السيادي (فقط مرة واحدة)"""
        if self.sovereign is not None:
            return False
        
        self.sovereign = citizen_id
        self._save_hierarchy()
        return True
    
    def create_worker(self, citizen_id: str, name: str, specialization: Optional[str] = None) -> WorkerAgent:
        """إنشاء وكيل عامل"""
        worker = WorkerAgent(citizen_id, name, specialization=specialization)
        self.workers[citizen_id] = worker
        self._save_hierarchy()
        return worker
    
    def create_supervisor(self, citizen_id: str, name: str, 
                         supervisor_type: str = "GENERAL",
                         department: Optional[str] = None,
                         region: Optional[str] = None) -> SupervisorAgent:
        """إنشاء وكيل مشرف"""
        if supervisor_type == "DEPARTMENT":
            supervisor = DepartmentSupervisor(citizen_id, name, department or "GENERAL")
        elif supervisor_type == "REGIONAL":
            supervisor = RegionalSupervisor(citizen_id, name, region or "UNKNOWN")
        else:
            supervisor = SupervisorAgent(citizen_id, name)
        
        self.supervisors[citizen_id] = supervisor
        self._save_hierarchy()
        return supervisor
    
    def create_coordinator(self, citizen_id: str, name: str,
                          coordinator_type: str = "NATIONAL",
                          department: Optional[str] = None) -> CoordinatorAgent:
        """إنشاء وكيل منسق"""
        if coordinator_type == "NATIONAL":
            coordinator = NationalCoordinator(citizen_id, name)
        else:
            coordinator = DepartmentalCoordinator(citizen_id, name, department or "GENERAL")
        
        if coordinator_type == "NATIONAL":
            self.national_coordinators[citizen_id] = coordinator
        else:
            self.departmental_coordinators[citizen_id] = coordinator
        
        self._save_hierarchy()
        return coordinator
    
    def assign_worker_to_supervisor(self, worker_id: str, supervisor_id: str) -> bool:
        """تعيين عامل لمشرف"""
        if worker_id not in self.workers or supervisor_id not in self.supervisors:
            return False
        
        worker = self.workers[worker_id]
        supervisor = self.supervisors[supervisor_id]
        
        success = supervisor.assign_worker(worker_id, worker.name)
        if success:
            worker.supervisor_id = supervisor_id
            worker._save_state()
        
        return success
    
    def assign_supervisor_to_coordinator(self, supervisor_id: str, coordinator_id: str) -> bool:
        """تعيين مشرف لمنسق"""
        if supervisor_id not in self.supervisors:
            return False
        
        supervisor = self.supervisors[supervisor_id]
        supervisor_info = {
            "id": supervisor_id,
            "name": supervisor.name,
            "department": getattr(supervisor, 'department', 'GENERAL'),
            "type": getattr(supervisor, '__class__', SupervisorAgent).__name__
        }
        
        # البحث عن المنسق المناسب
        coordinator = None
        if coordinator_id in self.national_coordinators:
            coordinator = self.national_coordinators[coordinator_id]
        elif coordinator_id in self.departmental_coordinators:
            coordinator = self.departmental_coordinators[coordinator_id]
        
        if coordinator is None:
            return False
        
        return coordinator.add_supervisor(supervisor_id, supervisor_info)
    
    def get_hierarchy_status(self) -> dict:
        """الحصول على حالة الهرمية الكاملة"""
        return {
            "sovereign": self.sovereign,
            "national_coordinators": {
                cid: {"name": c.name, "scope": c.scope}
                for cid, c in self.national_coordinators.items()
            },
            "departmental_coordinators": {
                cid: {"name": c.name, "department": getattr(c, 'department', 'N/A')}
                for cid, c in self.departmental_coordinators.items()
            },
            "supervisors": {
                cid: {"name": s.name, "department": getattr(s, 'department', 'GENERAL')}
                for cid, s in self.supervisors.items()
            },
            "workers": {
                cid: {"name": w.name, "specialization": getattr(w, 'specialization', 'GENERAL')}
                for cid, w in self.workers.items()
            },
            "totals": {
                "national_coordinators": len(self.national_coordinators),
                "departmental_coordinators": len(self.departmental_coordinators),
                "supervisors": len(self.supervisors),
                "workers": len(self.workers)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_organization_chart(self) -> dict:
        """إنشاء مخطط تنظيمي"""
        chart = {
            "sovereign": self.sovereign,
            "structure": {
                "national_coordinators": [],
                "departmental_coordinators": [],
                "supervisors": [],
                "workers": []
            }
        }
        
        # إضافة المنسقين الوطنيين
        for cid, coord in self.national_coordinators.items():
            coord_node = {
                "id": cid,
                "name": coord.name,
                "supervisors": []
            }
            
            # إضافة المشرفين تحت كل منسق
            for sup_id, sup_info in coord.supervisors.items():
                sup_node = {
                    "id": sup_id,
                    "name": sup_info.get("name", "Unknown"),
                    "workers": []
                }
                
                # إضافة العمال تحت كل مشرف
                if sup_id in self.supervisors:
                    sup_agent = self.supervisors[sup_id]
                    for w_id, w_name in sup_agent.workers.items():
                        sup_node["workers"].append({"id": w_id, "name": w_name})
                
                coord_node["supervisors"].append(sup_node)
            
            chart["structure"]["national_coordinators"].append(coord_node)
        
        return chart


# Import Path for the module
from pathlib import Path
