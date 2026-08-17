"""
AMOS Federal State - Parliament Implementation
البرلمان الفدرالي - السلطة التشريعية

المكونات:
- مجلس النواب (House of Representatives)
- مجلس الشيوخ (Senate)
- اللجان البرلمانية
- نظام التصويت والتشريع
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid
from pathlib import Path


class VoteResult(Enum):
    """نتيجة التصويت"""
    PASSED = "PASSED"
    REJECTED = "REJECTED"
    TIED = "TIED"
    PENDING = "PENDING"


class BillStatus(Enum):
    """حالة مشروع القانون"""
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    IN_COMMITTEE = "IN_COMMITTEE"
    ON_FLOOR = "ON_FLOOR"
    VOTED = "VOTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VETOED = "VETOED"
    ENACTED = "ENACTED"


class Member:
    """عضو البرلمان"""
    
    def __init__(self, member_id: str, name: str, party: str, 
                 chamber: str, constituency: Optional[str] = None):
        self.member_id = member_id
        self.name = name
        self.party = party
        self.chamber = chamber  # "REPRESENTATIVES" or "SENATE"
        self.constituency = constituency
        self.joined_date = datetime.now()
        self.votes_cast = 0
        self.bills_sponsored = 0
        self.attendance_rate = 1.0
    
    def to_dict(self) -> dict:
        return {
            "member_id": self.member_id,
            "name": self.name,
            "party": self.party,
            "chamber": self.chamber,
            "constituency": self.constituency,
            "joined_date": self.joined_date.isoformat(),
            "votes_cast": self.votes_cast,
            "bills_sponsored": self.bills_sponsored,
            "attendance_rate": self.attendance_rate
        }


class Bill:
    """مشروع قانون"""
    
    def __init__(self, bill_id: str, title: str, description: str,
                 sponsor_id: str, chamber: str):
        self.bill_id = bill_id
        self.title = title
        self.description = description
        self.sponsor_id = sponsor_id
        self.chamber = chamber
        self.status = BillStatus.DRAFT
        self.created_at = datetime.now()
        self.votes_for = 0
        self.votes_against = 0
        self.votes_abstain = 0
        self.committee_referral: Optional[str] = None
        self.text: str = ""
        self.amendments: List[dict] = []
    
    def add_text(self, text: str):
        """إضافة نص للقانون"""
        self.text = text
        if self.status == BillStatus.DRAFT:
            self.status = BillStatus.UNDER_REVIEW
    
    def add_amendment(self, amendment: dict):
        """إضافة تعديل"""
        self.amendments.append({
            **amendment,
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> dict:
        return {
            "bill_id": self.bill_id,
            "title": self.title,
            "description": self.description,
            "sponsor_id": self.sponsor_id,
            "chamber": self.chamber,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "votes_abstain": self.votes_abstain,
            "committee_referral": self.committee_referral,
            "amendments_count": len(self.amendments)
        }


class Parliament:
    """البرلمان الفدرالي"""
    
    def __init__(self, data_dir: str = "data/federal"):
        self.data_dir = Path(data_dir) / "parliament"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.members: Dict[str, Member] = {}
        self.bills: Dict[str, Bill] = {}
        self.committees: Dict[str, dict] = {}
        
        # غرف البرلمان
        self.house_representatives: List[str] = []  # member_ids
        self.senate: List[str] = []  # member_ids
        
        self._load_state()
    
    def _load_state(self):
        """تحميل حالة البرلمان"""
        state_file = self.data_dir / "state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # يمكن تحميل البيانات هنا
    
    def _save_state(self):
        """حفظ حالة البرلمان"""
        state_file = self.data_dir / "state.json"
        state = {
            "members_count": len(self.members),
            "bills_count": len(self.bills),
            "house_count": len(self.house_representatives),
            "senate_count": len(self.senate),
            "committees_count": len(self.committees),
            "updated_at": datetime.now().isoformat()
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def add_member(self, member_id: str, name: str, party: str,
                   chamber: str, constituency: Optional[str] = None) -> Member:
        """إضافة عضو للبرلمان"""
        if chamber not in ["REPRESENTATIVES", "SENATE"]:
            raise ValueError("Chamber must be REPRESENTATIVES or SENATE")
        
        member = Member(member_id, name, party, chamber, constituency)
        self.members[member_id] = member
        
        if chamber == "REPRESENTATIVES":
            self.house_representatives.append(member_id)
        else:
            self.senate.append(member_id)
        
        self._save_state()
        return member
    
    def create_bill(self, title: str, description: str,
                    sponsor_id: str, chamber: str) -> Bill:
        """إنشاء مشروع قانون"""
        if sponsor_id not in self.members:
            raise ValueError("Sponsor must be a parliament member")
        
        bill_id = f"BILL-{uuid.uuid4().hex[:8].upper()}"
        bill = Bill(bill_id, title, description, sponsor_id, chamber)
        self.bills[bill_id] = bill
        
        # زيادة عدد مشاريع القوانين للمقدم
        self.members[sponsor_id].bills_sponsored += 1
        
        self._save_state()
        return bill
    
    def refer_to_committee(self, bill_id: str, committee_name: str):
        """إحالة مشروع قانون للجنة"""
        if bill_id not in self.bills:
            raise ValueError("Bill not found")
        
        bill = self.bills[bill_id]
        bill.committee_referral = committee_name
        bill.status = BillStatus.IN_COMMITTEE
        
        self._save_state()
    
    def vote_on_bill(self, bill_id: str, votes: Dict[str, str]) -> VoteResult:
        """
        التصويت على مشروع قانون
        
        Args:
            bill_id: معرف مشروع القانون
            votes: قاموس {member_id: "FOR"|"AGAINST"|"ABSTAIN"}
        
        Returns:
            نتيجة التصويت
        """
        if bill_id not in self.bills:
            raise ValueError("Bill not found")
        
        bill = self.bills[bill_id]
        bill.votes_for = 0
        bill.votes_against = 0
        bill.votes_abstain = 0
        
        for member_id, vote in votes.items():
            if member_id not in self.members:
                continue
            
            member = self.members[member_id]
            member.votes_cast += 1
            
            if vote.upper() == "FOR":
                bill.votes_for += 1
            elif vote.upper() == "AGAINST":
                bill.votes_against += 1
            else:
                bill.votes_abstain += 1
        
        # تحديد النتيجة
        if bill.votes_for > bill.votes_against:
            result = VoteResult.PASSED
            bill.status = BillStatus.APPROVED
        elif bill.votes_against > bill.votes_for:
            result = VoteResult.REJECTED
            bill.status = BillStatus.REJECTED
        else:
            result = VoteResult.TIED
            bill.status = BillStatus.VOTED
        
        bill.status = BillStatus.VOTED
        self._save_state()
        
        return result
    
    def create_committee(self, name: str, chair_id: str, members: List[str],
                         jurisdiction: str):
        """إنشاء لجنة برلمانية"""
        committee_id = f"COMM-{uuid.uuid4().hex[:6].upper()}"
        self.committees[committee_id] = {
            "name": name,
            "chair_id": chair_id,
            "members": members,
            "jurisdiction": jurisdiction,
            "created_at": datetime.now().isoformat()
        }
        self._save_state()
        return committee_id
    
    def get_statistics(self) -> dict:
        """الحصول على إحصائيات البرلمان"""
        return {
            "total_members": len(self.members),
            "house_representatives": len(self.house_representatives),
            "senate": len(self.senate),
            "total_bills": len(self.bills),
            "active_bills": sum(1 for b in self.bills.values() 
                               if b.status in [BillStatus.DRAFT, BillStatus.UNDER_REVIEW, 
                                              BillStatus.IN_COMMITTEE, BillStatus.ON_FLOOR]),
            "approved_bills": sum(1 for b in self.bills.values() 
                                 if b.status == BillStatus.APPROVED),
            "rejected_bills": sum(1 for b in self.bills.values() 
                                 if b.status == BillStatus.REJECTED),
            "committees": len(self.committees),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_session_report(self) -> dict:
        """تقرير الجلسة البرلمانية"""
        return {
            "parliament_status": "ACTIVE",
            "members": [m.to_dict() for m in self.members.values()],
            "pending_bills": [b.to_dict() for b in self.bills.values() 
                             if b.status in [BillStatus.DRAFT, BillStatus.UNDER_REVIEW,
                                            BillStatus.IN_COMMITTEE, BillStatus.ON_FLOOR]],
            "committees": self.committees,
            "statistics": self.get_statistics()
        }


# Export
__all__ = ['Parliament', 'Member', 'Bill', 'VoteResult', 'BillStatus']
