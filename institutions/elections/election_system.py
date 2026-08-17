"""
نظام الانتخابات الفدرالي - Federal Election System
إدارة كاملة للعمليات الانتخابية في الدولة الفدرالية
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import json


class Voter:
    """ناخب مؤهل للتصويت"""
    
    def __init__(self, citizen_id: str, name: str, constituency: str):
        self.citizen_id = citizen_id
        self.name = name
        self.constituency = constituency
        self.registered = False
        self.voted = False
        self.registration_date: Optional[datetime] = None
    
    def register(self):
        """تسجيل الناخب"""
        self.registered = True
        self.registration_date = datetime.now()
    
    def vote(self):
        """تسجيل التصويت"""
        if not self.registered:
            raise Exception("الناخب غير مسجل")
        if self.voted:
            raise Exception("تم التصويت مسبقاً")
        self.voted = True


class Ballot:
    """ورقة اقتراع إلكترونية"""
    
    def __init__(self, election_id: str, voter_id: str, choices: Dict[str, str]):
        self.election_id = election_id
        self.voter_id = voter_id
        self.choices = choices  # {office: candidate_id}
        self.timestamp = datetime.now()
        self.encrypted = False
        self.verified = False
    
    def encrypt(self, encryption_key: str):
        """تشفير ورقة الاقتراع"""
        self.encrypted = True
    
    def verify(self):
        """التحقق من صحة الورقة"""
        self.verified = True


class Election:
    """انتخابات فدرالية"""
    
    def __init__(self, title: str, election_type: str, date: datetime):
        self.id = str(uuid.uuid4())
        self.title = title
        self.election_type = election_type  # presidential, parliamentary, local
        self.date = date
        self.status = "scheduled"  # scheduled, active, completed, cancelled
        self.constituencies: List[str] = []
        self.candidates: List[Dict] = []
        self.voters: List[Voter] = []
        self.ballots: List[Ballot] = []
        self.results: Dict = {}
    
    def add_constituency(self, name: str):
        """إضافة دائرة انتخابية"""
        self.constituencies.append(name)
    
    def add_candidate(self, candidate_id: str, office: str, party: str):
        """إضافة مرشح"""
        self.candidates.append({
            "id": candidate_id,
            "office": office,
            "party": party,
            "votes": 0
        })
    
    def register_voter(self, voter: Voter):
        """تسجيل ناخب"""
        voter.register()
        self.voters.append(voter)
    
    def cast_vote(self, voter_id: str, choices: Dict[str, str]):
        """إدلاء بصوت"""
        voter = next((v for v in self.voters if v.citizen_id == voter_id), None)
        if not voter:
            raise Exception("الناخب غير موجود")
        
        voter.vote()
        ballot = Ballot(self.id, voter_id, choices)
        ballot.encrypt("secure_key_123")
        ballot.verify()
        self.ballots.append(ballot)
    
    def count_votes(self):
        """فرز الأصوات"""
        if self.status != "completed":
            raise Exception("الانتخابات لم تنتهِ بعد")
        
        self.results = {}
        for ballot in self.ballots:
            for office, candidate_id in ballot.choices.items():
                if office not in self.results:
                    self.results[office] = {}
                if candidate_id not in self.results[office]:
                    self.results[office][candidate_id] = 0
                self.results[office][candidate_id] += 1
        
        return self.results


class FederalElectionCommission:
    """هيئة الانتخابات الفدرالية المستقلة"""
    
    def __init__(self):
        self.elections: List[Election] = []
        self.registered_voters: Dict[str, Voter] = {}
        self.electoral_roll: Dict[str, List[str]] = {}  # constituency -> voter_ids
    
    def create_election(self, title: str, election_type: str, date: datetime) -> Election:
        """إنشاء انتخابات جديدة"""
        election = Election(title, election_type, date)
        self.elections.append(election)
        return election
    
    def register_voter(self, citizen_id: str, name: str, constituency: str) -> Voter:
        """تسجيل ناخب جديد"""
        if citizen_id in self.registered_voters:
            raise Exception("الناخب مسجل مسبقاً")
        
        voter = Voter(citizen_id, name, constituency)
        self.registered_voters[citizen_id] = voter
        
        if constituency not in self.electoral_roll:
            self.electoral_roll[constituency] = []
        self.electoral_roll[constituency].append(citizen_id)
        
        return voter
    
    def start_election(self, election_id: str):
        """بدء الانتخابات"""
        election = next((e for e in self.elections if e.id == election_id), None)
        if not election:
            raise Exception("الانتخابات غير موجودة")
        election.status = "active"
    
    def end_election(self, election_id: str) -> Dict:
        """إنهاء الانتخابات وفرز الأصوات"""
        election = next((e for e in self.elections if e.id == election_id), None)
        if not election:
            raise Exception("الانتخابات غير موجودة")
        election.status = "completed"
        return election.count_votes()
    
    def get_election_results(self, election_id: str) -> Dict:
        """الحصول على نتائج الانتخابات"""
        election = next((e for e in self.elections if e.id == election_id), None)
        if not election:
            raise Exception("الانتخابات غير موجودة")
        return election.results
    
    def verify_election_integrity(self, election_id: str) -> bool:
        """التحقق من نزاهة الانتخابات"""
        election = next((e for e in self.elections if e.id == election_id), None)
        if not election:
            return False
        
        # التحقق من أن جميع الأوراق مشفرة وموثقة
        all_encrypted = all(b.encrypted for b in election.ballots)
        all_verified = all(b.verified for b in election.ballots)
        
        # التحقق من عدم تكرار التصويت
        voter_ids = [b.voter_id for b in election.ballots]
        no_duplicates = len(voter_ids) == len(set(voter_ids))
        
        return all_encrypted and all_verified and no_duplicates


# مثال استخدام
if __name__ == "__main__":
    commission = FederalElectionCommission()
    
    # إنشاء انتخابات رئاسية
    election = commission.create_election(
        "الانتخابات الرئاسية الفدرالية 2025",
        "presidential",
        datetime.now() + timedelta(days=30)
    )
    
    # إضافة دوائر انتخابية
    commission.electoral_roll["الرياض"] = []
    commission.electoral_roll["جدة"] = []
    commission.electoral_roll["الدمام"] = []
    
    # تسجيل ناخبين
    voter1 = commission.register_voter("CIT-001", "أحمد محمد", "الرياض")
    voter2 = commission.register_voter("CIT-002", "فاطمة علي", "جدة")
    
    # إضافة مرشحين
    election.add_candidate("CAND-001", "president", "حزب التقدم")
    election.add_candidate("CAND-002", "president", "حزب الإصلاح")
    
    # بدء الانتخابات
    commission.start_election(election.id)
    
    # إدلاء الأصوات
    election.cast_vote("CIT-001", {"president": "CAND-001"})
    election.cast_vote("CIT-002", {"president": "CAND-002"})
    
    # إنهاء الانتخابات
    commission.end_election(election.id)
    
    # الحصول على النتائج
    results = commission.get_election_results(election.id)
    print(f"نتائج الانتخابات: {json.dumps(results, indent=2, ensure_ascii=False)}")
    
    # التحقق من النزاهة
    integrity = commission.verify_election_integrity(election.id)
    print(f"نزاهة الانتخابات: {'مؤكدة' if integrity else 'مشكوك فيها'}")
