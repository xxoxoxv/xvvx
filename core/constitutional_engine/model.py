"""
نماذج النواة الدستورية — Constitutional Kernel Data Model (E1)
الهدف: تعريف اللغة الرسمية التي تُصاغ بها طلبات الأفعال والأحكام الدستورية، حتى يصبح الدستور قابلًا للتنفيذ الآلي لا للتفسير الشخصي.
النطاق: أنواع البيانات فقط — لا منطق قرار، ولا وصول لقرص أو شبكة.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Branch(str, Enum):
    """الفروع الأربعة للمادة الثالثة، بالإضافة إلى الأطراف خارج الفروع."""

    EXECUTIVE = "executive"
    LEGISLATIVE = "legislative"
    JUDICIAL = "judicial"
    TREASURY = "treasury"
    ROYAL = "royal"          # التاج — خارج الفروع، خاضع للدستور
    HUMAN = "human"          # السلطة العليا (المادة الأولى)
    AGENT = "agent"          # مواطن رقمي (المادة الثانية)
    SYSTEM = "system"        # النظام نفسه — أضيق الأطراف صلاحية (العزل الدستوري)


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class Severity(str, Enum):
    """خطورة المخالفة الدستورية."""

    FUNDAMENTAL = "FUNDAMENTAL"  # مبدأ غير قابل للتعديل (المادة الخامسة)
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


@dataclass(frozen=True)
class ActionRequest:
    """طلب فعل معروض على الدستور قبل التنفيذ.

    كل حقل هنا سؤال يطرحه الدستور على الفاعل. الحقل المفقود = افتراض الأسوأ،
    لا افتراض السماح.
    """

    actor: Branch
    action: str
    target: str = ""
    # سياق القرار — يُملأ من الطرف الطالب ويُتحقق منه دستوريًا
    human_approved: bool = False
    human_signature: str | None = None       # توقيع Ed25519 (المادة الخامسة)
    approving_branches: tuple[Branch, ...] = ()
    channel: str = "direct"                  # "official" للقنوات الرسمية بين الفروع
    criticality: str = "normal"              # normal | critical | fateful
    kill_switch_level: int = 0               # 0..5 (المادة الثامنة)
    review_days: int = 0                     # فترة المراجعة (المادة الخامسة)
    council_approval_pct: float = 0.0        # نسبة موافقة مجلس السياسات
    has_identity_header: bool = True         # المادة التاسعة
    metadata: dict[str, Any] = field(default_factory=dict)

    def approved_by(self, branch: Branch) -> bool:
        return branch in self.approving_branches


@dataclass(frozen=True)
class RuleViolation:
    """مخالفة واحدة لقاعدة دستورية واحدة."""

    rule_id: str
    article_id: str
    article_title: str
    clause: str
    severity: Severity
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "article_id": self.article_id,
            "article_title": self.article_title,
            "clause": self.clause,
            "severity": self.severity.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class Verdict:
    """حكم الدستور على طلب فعل. يُسجَّل دائمًا في السجل — سُمح أم رُفض."""

    decision: Decision
    request_fingerprint: str
    rules_evaluated: int
    violations: tuple[RuleViolation, ...] = ()
    ledger_entry_hash: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW

    @property
    def blocking_articles(self) -> tuple[str, ...]:
        # ترتيب مستقر بلا تكرار
        seen: dict[str, None] = {}
        for v in self.violations:
            seen.setdefault(v.article_id, None)
        return tuple(seen)

    def explain(self) -> str:
        """سبب الحكم بصيغة يقرأها إنسان — مع رقم المادة دائمًا."""
        if self.allowed:
            return f"ALLOW — لا مخالفة بين {self.rules_evaluated} قاعدة دستورية مُقيَّمة."
        lines = [f"DENY — {len(self.violations)} مخالفة دستورية:"]
        for v in self.violations:
            lines.append(
                f"  [{v.severity.value}] {v.article_id} ({v.article_title}) "
                f"· البند: {v.clause} · القاعدة {v.rule_id}\n      السبب: {v.reason}"
            )
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "request_fingerprint": self.request_fingerprint,
            "rules_evaluated": self.rules_evaluated,
            "violations": [v.as_dict() for v in self.violations],
            "ledger_entry_hash": self.ledger_entry_hash,
        }
