"""
AMOS Federal State - Institutions Framework
المؤسسات الفدرالية الكاملة

الهيكل الفدرالي الكامل:
1. السلطة التشريعية (Legislative)
2. السلطة التنفيذية (Executive)
3. السلطة القضائية (Judicial)
4. الهيئات المستقلة (Independent Bodies)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
from pathlib import Path


class FederalInstitution:
    """فئة أساسية للمؤسسات الفدرالية"""
    
    def __init__(self, institution_id: str, name: str, institution_type: str):
        self.id = institution_id
        self.name = name
        self.type = institution_type
        self.created_at = datetime.now().isoformat()
        self.status = "active"
        self.head: Optional[dict] = None
        self.members: List[dict] = []
        self.departments: Dict[str, Any] = {}
        self.decisions: List[dict] = []
        self.budget: dict = {"allocated": 0, "spent": 0}
        
        self.data_dir = Path("data/institutions") / institution_id
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
    
    def _load_state(self):
        """تحميل حالة المؤسسة"""
        state_file = self.data_dir / "state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.head = data.get("head")
                self.members = data.get("members", [])
                self.decisions = data.get("decisions", [])
                self.budget = data.get("budget", self.budget)
    
    def _save_state(self):
        """حفظ حالة المؤسسة"""
        state_file = self.data_dir / "state.json"
        data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "head": self.head,
            "members": self.members,
            "decisions": self.decisions,
            "budget": self.budget,
            "updated_at": datetime.now().isoformat()
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def set_head(self, citizen_id: str, name: str, role: str):
        """تعيين رئيس المؤسسة"""
        self.head = {
            "citizen_id": citizen_id,
            "name": name,
            "role": role,
            "appointed_at": datetime.now().isoformat()
        }
        self._save_state()
    
    def add_member(self, citizen_id: str, name: str, role: str):
        """إضافة عضو"""
        member = {
            "citizen_id": citizen_id,
            "name": name,
            "role": role,
            "joined_at": datetime.now().isoformat()
        }
        self.members.append(member)
        self._save_state()
    
    def make_decision(self, decision_type: str, description: str, votes: dict) -> dict:
        """اتخاذ قرار مؤسسي"""
        decision = {
            "id": str(uuid.uuid4()),
            "type": decision_type,
            "description": description,
            "votes": votes,
            "made_at": datetime.now().isoformat(),
            "status": "approved" if votes.get("yes", 0) > votes.get("no", 0) else "rejected"
        }
        self.decisions.append(decision)
        self._save_state()
        return decision
    
    def allocate_budget(self, amount: float, category: str = "general"):
        """تخصيص ميزانية"""
        self.budget["allocated"] += amount
        self.budget[f"{category}_allocated"] = self.budget.get(f"{category}_allocated", 0) + amount
        self._save_state()
    
    def get_status(self) -> dict:
        """الحصول على حالة المؤسسة"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "head": self.head,
            "members_count": len(self.members),
            "decisions_count": len(self.decisions),
            "budget": self.budget,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# السلطة التشريعية (Legislative Branch)
# ============================================================================

class Legislature(FederalInstitution):
    """السلطة التشريعية الفدرالية"""
    
    def __init__(self):
        super().__init__("legislature-001", "البرلمان الفدرالي", "LEGISLATIVE")
        self.chambers: Dict[str, dict] = {
            "senate": {"name": "مجلس الشيوخ", "members": [], "chair": None},
            "house": {"name": "مجلس النواب", "members": [], "speaker": None}
        }
        self.laws_proposed: List[dict] = []
        self.laws_passed: List[dict] = []
    
    def propose_law(self, proposer_id: str, law_title: str, law_text: str, chamber: str) -> str:
        """اقتراح قانون جديد"""
        law_id = str(uuid.uuid4())
        law = {
            "id": law_id,
            "title": law_title,
            "text": law_text,
            "proposer_id": proposer_id,
            "chamber": chamber,
            "status": "proposed",
            "proposed_at": datetime.now().isoformat(),
            "votes": {"yes": 0, "no": 0, "abstain": 0},
            "committees_review": []
        }
        self.laws_proposed.append(law)
        self._save_state()
        return law_id
    
    def vote_on_law(self, law_id: str, voter_id: str, vote: str) -> bool:
        """التصويت على قانون"""
        law = next((l for l in self.laws_proposed if l["id"] == law_id), None)
        if not law:
            return False
        
        if vote in ["yes", "no", "abstain"]:
            law["votes"][vote] = law["votes"].get(vote, 0) + 1
        
        # التحقق من أغلبية التصويت
        total_votes = sum(law["votes"].values())
        if total_votes >= 10:  # حد أدنى للتصويت
            if law["votes"]["yes"] > law["votes"]["no"]:
                law["status"] = "passed"
                self.laws_passed.append(law)
            else:
                law["status"] = "rejected"
        
        self._save_state()
        return True
    
    def get_laws(self, status: Optional[str] = None) -> List[dict]:
        """الحصول على القوانين"""
        if status:
            return [l for l in self.laws_proposed if l["status"] == status]
        return self.laws_proposed


class Senate(FederalInstitution):
    """مجلس الشيوخ"""
    
    def __init__(self):
        super().__init__("senate-001", "مجلس الشيوخ", "LEGISLATIVE_UPPER")
        self.senators: List[dict] = []
        self.committees: Dict[str, dict] = {}
    
    def add_senator(self, citizen_id: str, name: str, region: str):
        """إضافةSenator"""
        senator = {
            "citizen_id": citizen_id,
            "name": name,
            "region": region,
            "appointed_at": datetime.now().isoformat()
        }
        self.senators.append(senator)
        self._save_state()
    
    def create_committee(self, name: str, focus_area: str, members: List[str]) -> str:
        """إنشاء لجنة"""
        committee_id = str(uuid.uuid4())
        self.committees[committee_id] = {
            "name": name,
            "focus_area": focus_area,
            "members": members,
            "created_at": datetime.now().isoformat()
        }
        self._save_state()
        return committee_id


class HouseOfRepresentatives(FederalInstitution):
    """مجلس النواب"""
    
    def __init__(self):
        super().__init__("house-001", "مجلس النواب", "LEGISLATIVE_LOWER")
        self.representatives: List[dict] = []
        self.districts: Dict[str, str] = {}  # district_id -> representative_id
    
    def add_representative(self, citizen_id: str, name: str, district: str):
        """إضافة نائب"""
        rep = {
            "citizen_id": citizen_id,
            "name": name,
            "district": district,
            "elected_at": datetime.now().isoformat()
        }
        self.representatives.append(rep)
        self.districts[district] = citizen_id
        self._save_state()


# ============================================================================
# السلطة التنفيذية (Executive Branch)
# ============================================================================

class ExecutiveBranch(FederalInstitution):
    """السلطة التنفيذية الفدرالية"""
    
    def __init__(self):
        super().__init__("executive-001", "السلطة التنفيذية", "EXECUTIVE")
        self.president: Optional[dict] = None
        self.vice_president: Optional[dict] = None
        self.cabinet: Dict[str, dict] = {}  # ministry_name -> minister_info
        self.ministries: Dict[str, FederalInstitution] = {}
    
    def set_president(self, citizen_id: str, name: str):
        """تعيين الرئيس"""
        self.president = {
            "citizen_id": citizen_id,
            "name": name,
            "inaugurated_at": datetime.now().isoformat()
        }
        self.set_head(citizen_id, name, "President")
        self._save_state()
    
    def set_vice_president(self, citizen_id: str, name: str):
        """تعيين نائب الرئيس"""
        self.vice_president = {
            "citizen_id": citizen_id,
            "name": name,
            "inaugurated_at": datetime.now().isoformat()
        }
        self._save_state()
    
    def appoint_minister(self, ministry: str, citizen_id: str, name: str):
        """تعيين وزير"""
        self.cabinet[ministry] = {
            "citizen_id": citizen_id,
            "name": name,
            "appointed_at": datetime.now().isoformat()
        }
        self._save_state()
    
    def create_ministry(self, name: str, budget: float) -> str:
        """إنشاء وزارة"""
        ministry_id = str(uuid.uuid4())
        ministry = Ministry(ministry_id, name)
        ministry.allocate_budget(budget)
        self.ministries[name] = ministry
        self._save_state()
        return ministry_id


class Ministry(FederalInstitution):
    """وزارة تنفيذية"""
    
    def __init__(self, ministry_id: str, name: str):
        super().__init__(ministry_id, name, "MINISTRY")
        self.deputy_ministers: List[dict] = []
        self.agencies: List[str] = []
        self.programs: Dict[str, dict] = {}
    
    def add_deputy(self, citizen_id: str, name: str, portfolio: str):
        """إضافة نائب وزير"""
        deputy = {
            "citizen_id": citizen_id,
            "name": name,
            "portfolio": portfolio,
            "appointed_at": datetime.now().isoformat()
        }
        self.deputy_ministers.append(deputy)
        self._save_state()
    
    def launch_program(self, program_name: str, budget: float, objectives: List[str]) -> str:
        """إطلاق برنامج وزاري"""
        program_id = str(uuid.uuid4())
        self.programs[program_id] = {
            "name": program_name,
            "budget": budget,
            "objectives": objectives,
            "status": "active",
            "launched_at": datetime.now().isoformat()
        }
        self._save_state()
        return program_id


# ============================================================================
# السلطة القضائية (Judicial Branch)
# ============================================================================

class Judiciary(FederalInstitution):
    """السلطة القضائية الفدرالية"""
    
    def __init__(self):
        super().__init__("judiciary-001", "السلطة القضائية", "JUDICIAL")
        self.chief_justice: Optional[dict] = None
        self.supreme_court_justices: List[dict] = []
        self.courts: Dict[str, dict] = {
            "supreme": {"name": "المحكمة العليا", "justices": [], "cases": []},
            "appeals": {"name": "محاكم الاستئناف", "courts": []},
            "district": {"name": "المحاكم الابتدائية", "courts": []}
        }
    
    def set_chief_justice(self, citizen_id: str, name: str):
        """تعيين رئيس القضاة"""
        self.chief_justice = {
            "citizen_id": citizen_id,
            "name": name,
            "appointed_at": datetime.now().isoformat()
        }
        self.set_head(citizen_id, name, "Chief Justice")
        self._save_state()
    
    def add_justice(self, citizen_id: str, name: str, court_level: str = "supreme"):
        """إضافة قاضٍ"""
        justice = {
            "citizen_id": citizen_id,
            "name": name,
            "court_level": court_level,
            "appointed_at": datetime.now().isoformat()
        }
        
        if court_level == "supreme":
            self.supreme_court_justices.append(justice)
            self.courts["supreme"]["justices"].append(justice)
        
        self.add_member(citizen_id, name, f"Justice ({court_level})")
        self._save_state()
        return justice


class SupremeCourt(FederalInstitution):
    """المحكمة العليا"""
    
    def __init__(self):
        super().__init__("supreme-court-001", "المحكمة العليا", "JUDICIAL_SUPREME")
        self.justices: List[dict] = []
        self.cases: List[dict] = []
    
    def add_justice(self, citizen_id: str, name: str, position: str = "Associate Justice"):
        """إضافة قاضٍ بالمحكمة العليا"""
        justice = {
            "citizen_id": citizen_id,
            "name": name,
            "position": position,
            "appointed_at": datetime.now().isoformat()
        }
        self.justices.append(justice)
        self._save_state()
    
    def hear_case(self, case_id: str, case_title: str, parties: dict) -> dict:
        """النظر في قضية"""
        case = {
            "case_id": case_id,
            "title": case_title,
            "parties": parties,
            "filed_at": datetime.now().isoformat(),
            "status": "pending",
            "hearings": [],
            "ruling": None
        }
        self.cases.append(case)
        self._save_state()
        return case
    
    def issue_ruling(self, case_id: str, ruling: str, majority_vote: int, dissenting: int) -> bool:
        """إصدار حكم"""
        case = next((c for c in self.cases if c["case_id"] == case_id), None)
        if not case:
            return False
        
        case["ruling"] = {
            "decision": ruling,
            "majority_vote": majority_vote,
            "dissenting": dissenting,
            "issued_at": datetime.now().isoformat()
        }
        case["status"] = "closed"
        self._save_state()
        return True


# ============================================================================
# الهيئات المستقلة (Independent Bodies)
# ============================================================================

class CentralBank(FederalInstitution):
    """البنك المركزي الفدرالي"""
    
    def __init__(self):
        super().__init__("central-bank-001", "البنك المركزي الفدرالي", "INDEPENDENT_FINANCIAL")
        self.governor: Optional[dict] = None
        self.board_members: List[dict] = []
        self.monetary_policy: dict = {
            "interest_rate": 0.0,
            "reserve_requirement": 0.1,
            "inflation_target": 0.02
        }
        self.reserves: dict = {"gold": 0, "foreign_currency": 0, "crypto": 0}
    
    def set_governor(self, citizen_id: str, name: str):
        """تعيين المحافظ"""
        self.governor = {
            "citizen_id": citizen_id,
            "name": name,
            "appointed_at": datetime.now().isoformat()
        }
        self.set_head(citizen_id, name, "Governor")
        self._save_state()
    
    def set_interest_rate(self, rate: float):
        """تحديد سعر الفائدة"""
        self.monetary_policy["interest_rate"] = rate
        self._save_state()
    
    def update_reserves(self, asset_type: str, amount: float):
        """تحديث الاحتياطيات"""
        self.reserves[asset_type] = self.reserves.get(asset_type, 0) + amount
        self._save_state()


class ElectionCommission(FederalInstitution):
    """هيئة الانتخابات الفدرالية"""
    
    def __init__(self):
        super().__init__("election-commission-001", "هيئة الانتخابات", "INDEPENDENT_ELECTORAL")
        self.commissioners: List[dict] = []
        self.elections: Dict[str, dict] = {}
        self.voter_registry: Dict[str, bool] = {}  # citizen_id -> registered
    
    def add_commissioner(self, citizen_id: str, name: str, role: str):
        """إضافة مفوض"""
        commissioner = {
            "citizen_id": citizen_id,
            "name": name,
            "role": role,
            "appointed_at": datetime.now().isoformat()
        }
        self.commissioners.append(commissioner)
        self._save_state()
    
    def schedule_election(self, election_type: str, date: str, positions: List[str]) -> str:
        """جدولة انتخابات"""
        election_id = str(uuid.uuid4())
        self.elections[election_id] = {
            "type": election_type,
            "date": date,
            "positions": positions,
            "candidates": {},
            "results": None,
            "status": "scheduled"
        }
        self._save_state()
        return election_id
    
    def register_voter(self, citizen_id: str) -> bool:
        """تسجيل ناخب"""
        self.voter_registry[citizen_id] = True
        self._save_state()
        return True


class AuditBureau(FederalInstitution):
    """ديوان المحاسبة الفدرالي"""
    
    def __init__(self):
        super().__init__("audit-bureau-001", "ديوان المحاسبة", "INDEPENDENT_AUDIT")
        self.auditor_general: Optional[dict] = None
        self.audits: List[dict] = []
    
    def set_auditor_general(self, citizen_id: str, name: str):
        """تعيين رئيس الديوان"""
        self.auditor_general = {
            "citizen_id": citizen_id,
            "name": name,
            "appointed_at": datetime.now().isoformat()
        }
        self.set_head(citizen_id, name, "Auditor General")
        self._save_state()
    
    def initiate_audit(self, entity: str, audit_type: str, scope: str) -> str:
        """بدء مراجعة"""
        audit_id = str(uuid.uuid4())
        audit = {
            "id": audit_id,
            "entity": entity,
            "type": audit_type,
            "scope": scope,
            "initiated_at": datetime.now().isoformat(),
            "status": "in_progress",
            "findings": [],
            "report": None
        }
        self.audits.append(audit)
        self._save_state()
        return audit_id


class Ombudsman(FederalInstitution):
    """جهاز المظالم الفدرالي"""
    
    def __init__(self):
        super().__init__("ombudsman-001", "جهاز المظالم", "INDEPENDENT_OVERSIGHT")
        self.ombudsman: Optional[dict] = None
        self.complaints: List[dict] = []
    
    def set_ombudsman(self, citizen_id: str, name: str):
        """تعيين رئيس الجهاز"""
        self.ombudsman = {
            "citizen_id": citizen_id,
            "name": name,
            "appointed_at": datetime.now().isoformat()
        }
        self.set_head(citizen_id, name, "Ombudsman")
        self._save_state()
    
    def file_complaint(self, complainant_id: str, against_entity: str, description: str) -> str:
        """تقديم شكوى"""
        complaint_id = str(uuid.uuid4())
        complaint = {
            "id": complaint_id,
            "complainant_id": complainant_id,
            "against": against_entity,
            "description": description,
            "filed_at": datetime.now().isoformat(),
            "status": "under_review",
            "investigation": None,
            "resolution": None
        }
        self.complaints.append(complaint)
        self._save_state()
        return complaint_id


# ============================================================================
# Federal State Manager
# ============================================================================

class FederalStateManager:
    """مدير الدولة الفدرالية - يجمع كل المؤسسات"""
    
    def __init__(self):
        self.legislature = Legislature()
        self.executive = ExecutiveBranch()
        self.judiciary = Judiciary()
        
        self.independent_bodies = {
            "central_bank": CentralBank(),
            "election_commission": ElectionCommission(),
            "audit_bureau": AuditBureau(),
            "ombudsman": Ombudsman()
        }
        
        self.data_dir = Path("data/federal_state")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_full_status(self) -> dict:
        """الحصول على حالة كاملة للدولة الفدرالية"""
        return {
            "legislative": self.legislature.get_status(),
            "executive": self.executive.get_status(),
            "judicial": self.judiciary.get_status(),
            "independent_bodies": {
                name: body.get_status()
                for name, body in self.independent_bodies.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def save_state(self):
        """حفظ حالة الدولة الفدرالية"""
        state_file = self.data_dir / "federal_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_full_status(), f, indent=2, ensure_ascii=False)
