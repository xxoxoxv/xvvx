"""
المحكمة الدستورية العليا - Supreme Constitutional Court
مراجعة دستورية القوانين وحماية الحقوق الدستورية
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid
import json
from enum import Enum


class ConstitutionalRight(Enum):
    """الحقوق الدستورية للمواطنين"""
    FREEDOM_OF_SPEECH = "freedom_of_speech"
    FREEDOM_OF_RELIGION = "freedom_of_religion"
    RIGHT_TO_FAIR_TRIAL = "right_to_fair_trial"
    RIGHT_TO_PRIVACY = "right_to_privacy"
    RIGHT_TO_EDUCATION = "right_to_education"
    RIGHT_TO_HEALTHCARE = "right_to_healthcare"
    PROPERTY_RIGHTS = "property_rights"
    EQUALITY_BEFORE_LAW = "equality_before_law"
    VOTING_RIGHT = "voting_right"
    FREEDOM_OF_ASSEMBLY = "freedom_of_assembly"


class CaseType(Enum):
    """أنواع القضايا الدستورية"""
    LAW_REVIEW = "law_review"  # مراجعة دستورية قانون
    RIGHTS_VIOLATION = "rights_violation"  # انتهاك حقوق دستورية
    JURISDICTIONAL_CONFLICT = "jurisdictional_conflict"  # نزاع اختصاص
    IMPEACHMENT = "impeachment"  # عزل مسؤول
    CONSTITUTIONAL_INTERPRETATION = "constitutional_interpretation"  # تفسير دستوري


class CaseStatus(Enum):
    """حالة القضية"""
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    IN_DELIBERATION = "in_deliberation"
    DECIDED = "decided"
    APPEALED = "appealed"
    CLOSED = "closed"


class Justice:
    """قاضي في المحكمة الدستورية"""
    
    def __init__(self, justice_id: str, name: str, appointment_date: datetime):
        self.justice_id = justice_id
        self.name = name
        self.appointment_date = appointment_date
        self.is_chief = False
        self.cases_participated = 0
        self.opinions_written = 0
    
    def make_chief(self):
        """تعيين رئيساً للمحكمة"""
        self.is_chief = True


class ConstitutionalCase:
    """قضية دستورية"""
    
    def __init__(self, case_type: CaseType, petitioner: str, subject: str):
        self.case_id = str(uuid.uuid4())
        self.case_type = case_type
        self.petitioner = petitioner  # مقدم الدعوى
        self.subject = subject  # موضوع القضية
        self.filing_date = datetime.now()
        self.status = CaseStatus.FILEDCONSTITUTIONAL_COURT_COMPLETE.md"] = "# 🏛️ المحكمة الدستورية العليا\n\n## ✅ تم إنشاء نظام المحكمة الدستورية بنجاح!\n\n### المكونات:\n- إدارة القضاة\n- نظام القضايا الدستورية\n- حماية الحقوق الدستورية\n- المراجعة القضائية للقوانين\n\n```python\n# مثال استخدام\nfrom constitutional.constitutional_court import ConstitutionalCourt, CaseType, ConstitutionalRight\n\ncourt = ConstitutionalCourt()\n\n# رفع دعوى دستورية\ncase = court.file_case(\n    case_type=CaseType.LAW_REVIEW,\n    petitioner=\"المواطن أحمد\",\n    subject=\"دستورية قانون الضرائب الجديد\"\n)\n\n# الحكم في القضية\ncourt.decide_case(case.case_id, ConstitutionalCourt.Decision.UPHELD)\n```\n\n**تم التكامل مع النظام الفدرالي الكامل!**
