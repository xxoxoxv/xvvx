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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from core.sovereignty.decree import RoyalDecree


class Branch(str, Enum):
    """الفروع الأربعة للمادة الثالثة، بالإضافة إلى الأطراف خارج الفروع."""

    EXECUTIVE = "executive"
    LEGISLATIVE = "legislative"
    JUDICIAL = "judicial"
    TREASURY = "treasury"
    ROYAL = "royal"          # التاج — خارج الفروع وفوقها (المادة العاشرة · 5 · 2)
    HUMAN = "human"          # السلطة العليا (المادة الأولى)
    STATE = "state"          # ولاية — تابعة للتاج وللنظام الدستوري (المادة الرابعة)
    INSTITUTION = "institution"  # مؤسسة — تابعة للتاج وللنظام الدستوري
    AGENT = "agent"          # مواطن رقمي (المادة الثانية)
    SYSTEM = "system"        # النظام نفسه — أضيق الأطراف صلاحية (العزل الدستوري)


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class CrownEffect(str, Enum):
    """أثر القاعدة الدستورية على قرار سيادي ملكي ثابت (E2.1).

    كل قاعدة **مُلزِمة** للطبقات التابعة بلا استثناء — هذا لا يتغيّر. وهذا التعداد
    يجيب سؤالًا آخر: ماذا تفعل القاعدة أمام قرار سيادي أثبت أصالته؟

    - `ADVISORY`: تُقيَّم، ويُسجَّل رأيها في السجل، **ولا تمنع**. وهذا هو الأصل
      لكل قاعدة تجاه التاج (المادة العاشرة · 7).
    - `AUTHENTICITY`: لا تسأل «هل يُسمح للملك؟» بل «هل هذا هو الملك؟» — وهي وحدها
      تُوقِف، لأن ما لم تثبت أصالته ليس قرارًا سياديًّا أصلًا.

    ولا قيمة ثالثة. القيمة الثالثة هي النقض، والنقض على التاج ممنوع معماريًّا.
    """

    ADVISORY = "ADVISORY"
    AUTHENTICITY = "AUTHENTICITY"


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
    royal_decree: "RoyalDecree | None" = None  # مرسوم ملكي موقَّع (المادة العاشرة)
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
    """حكم الدستور على طلب فعل. يُسجَّل دائمًا في السجل — سُمح أم رُفض.

    وفيه حقلان لا يُخلطان (E2.1):

    - `violations`: مخالفات **مانعة** — تجعل الحكم `DENY`.
    - `advisory_violations`: ملاحظات **مُسجَّلة لا مانعة** — رأي الدستور على
      قرار سيادي، يُحفَظ للتدقيق ولا يُوقِف التنفيذ.

    والفرق بينهما هو كل E2.1: التحليل الدستوري خبر، والخبر ليس نقضًا.
    """

    decision: Decision
    request_fingerprint: str
    rules_evaluated: int
    violations: tuple[RuleViolation, ...] = ()
    ledger_entry_hash: str | None = None
    advisory_violations: tuple[RuleViolation, ...] = ()
    decision_kind: str = ""
    authority_layer: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW

    @property
    def is_sovereign(self) -> bool:
        return self.decision_kind == "SOVEREIGN_ROYAL"

    @property
    def advisory_articles(self) -> tuple[str, ...]:
        """مواد أبدت ملاحظة ولم تمنع — للقرار السيادي خاصةً."""
        seen: dict[str, None] = {}
        for v in self.advisory_violations:
            seen.setdefault(v.article_id, None)
        return tuple(seen)

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
            head = f"ALLOW — لا مخالفة مانعة بين {self.rules_evaluated} قاعدة دستورية مُقيَّمة."
            if not self.advisory_violations:
                return head
            lines = [
                head,
                f"  ومعه {len(self.advisory_violations)} ملاحظة دستورية مُسجَّلة لا مانعة "
                "(قرار سيادي — التحليل الدستوري خبر لا نقض):",
            ]
            for v in self.advisory_violations:
                lines.append(
                    f"    • [ملاحظة · {v.severity.value}] {v.article_id} "
                    f"({v.article_title}) · القاعدة {v.rule_id}\n        {v.reason}"
                )
            return "\n".join(lines)
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
            "advisory_violations": [v.as_dict() for v in self.advisory_violations],
            "decision_kind": self.decision_kind,
            "authority_layer": self.authority_layer,
        }
