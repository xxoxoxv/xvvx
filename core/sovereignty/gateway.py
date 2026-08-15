"""الهدف: البوابة السيادية — المسار الوحيد الذي يُنفَّذ من خلاله أي فعل في الدولة.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذه الوحدة تُغلق الدين الأكبر في E1: كان المحرك يحكم ولا يمنع، لأن لا شيء كان
مُلزَمًا بسؤاله. البوابة تجعل السؤال شرط التنفيذ لا خيارًا مجاورًا له.

قرار معماري ملزم: لا توجد — ولن تُضاف — راية تجاوز، ولا وضع تشخيصي،
ولا متغير بيئة، ولا معامل `force`. تجاوز الفدرالية مخالفة دستورية بحد ذاتها
(المادة العاشرة · 4 · 3)، ويحرس ذلك اختبار يفحص توقيع الدوال نفسه.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from core.constitutional_engine.engine import ConstitutionalEngine, ConstitutionalViolation
from core.constitutional_engine.model import ActionRequest, Verdict
from core.sovereignty.crown import crown_is_provisioned
from core.sovereignty.decree import DecreeRegistry, RoyalDecree
from core.sovereignty.prerogatives import is_royal_exclusive

T = TypeVar("T")

# أسماء ممنوعة في معاملات البوابة — تُفحَص آليًا في الاختبارات
FORBIDDEN_BYPASS_PARAMS = frozenset(
    {"force", "bypass", "skip_check", "unchecked", "override", "no_verify", "unsafe"}
)


class GatewayError(Exception):
    """خطأ في البوابة السيادية."""


class SovereigntyViolation(GatewayError):
    """رُفض الفعل: البوابة لم تُنفّذه."""

    def __init__(self, verdict: Verdict) -> None:
        self.verdict = verdict
        super().__init__(verdict.explain())


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """أثر مرور فعل بالبوابة — تُنفَّذ أو لا تُنفَّذ، والأثر يبقى."""

    fingerprint: str
    action: str
    actor: str
    decision: str
    executed: bool
    ledger_entry_hash: str | None
    decree_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "action": self.action,
            "actor": self.actor,
            "decision": self.decision,
            "executed": self.executed,
            "ledger_entry_hash": self.ledger_entry_hash,
            "decree_id": self.decree_id,
        }


class SovereignGateway:
    """البوابة السيادية: تُقيّم دستوريًا، ثم تُنفّذ أو تمنع — بهذا الترتيب دائمًا.

    الترتيب ليس تفصيلًا: `execute` لا تستدعي المُنفِّذ قبل صدور حكم `ALLOW`،
    ولا يوجد فرع في الكود يعكس ذلك.
    """

    def __init__(
        self,
        engine: ConstitutionalEngine | None = None,
        *,
        decree_registry: DecreeRegistry | None = None,
    ) -> None:
        self._engine = engine or ConstitutionalEngine()
        self._decrees = decree_registry or DecreeRegistry()
        self._records: list[ExecutionRecord] = []

    # ── الاستعلام ─────────────────────────────────────────────────────────
    @property
    def engine(self) -> ConstitutionalEngine:
        return self._engine

    @property
    def records(self) -> tuple[ExecutionRecord, ...]:
        return tuple(self._records)

    def crown_status(self) -> str:
        return "provisioned" if crown_is_provisioned() else "unprovisioned"

    # ── التقييم ───────────────────────────────────────────────────────────
    def review(self, request: ActionRequest) -> Verdict:
        """حكم دستوري بلا تنفيذ. يُسجَّل في السجل الدستوري كأي حكم."""
        return self._engine.evaluate(request)

    # ── التنفيذ ───────────────────────────────────────────────────────────
    def execute(
        self,
        request: ActionRequest,
        executor: Callable[[], T],
    ) -> T:
        """المسار الوحيد للتنفيذ.

        1. يُقيَّم الطلب دستوريًا (10 مواد · 26 قاعدة).
        2. إن رُفض: يُسجَّل الرفض ويُرفع `SovereigntyViolation` — ولا يُستدعى المُنفِّذ.
        3. إن سُمح ومعه مرسوم ملكي: يُستهلك المرسوم فلا يُعاد استخدامه.
        4. يُستدعى المُنفِّذ.

        لا معامل يُغيّر هذا الترتيب. لا استثناء لأي فاعل، ولا للملك.
        """
        verdict = self._engine.evaluate(request)
        decree = request.royal_decree
        decree_id = getattr(decree, "decree_id", None) if decree is not None else None

        if not verdict.allowed:
            self._records.append(
                ExecutionRecord(
                    fingerprint=verdict.request_fingerprint,
                    action=request.action,
                    actor=request.actor.value,
                    decision=verdict.decision.value,
                    executed=False,
                    ledger_entry_hash=verdict.ledger_entry_hash,
                    decree_id=decree_id,
                )
            )
            raise SovereigntyViolation(verdict)

        if isinstance(decree, RoyalDecree) and is_royal_exclusive(request.action):
            self._decrees.consume(decree)

        self._records.append(
            ExecutionRecord(
                fingerprint=verdict.request_fingerprint,
                action=request.action,
                actor=request.actor.value,
                decision=verdict.decision.value,
                executed=True,
                ledger_entry_hash=verdict.ledger_entry_hash,
                decree_id=decree_id,
            )
        )
        return executor()

    # ── حراسة ذاتية ───────────────────────────────────────────────────────
    def self_check(self) -> dict[str, Any]:
        """فحص ذاتي: هل البوابة ما زالت البوابة؟"""
        engine_coverage = self._engine.coverage()
        return {
            "crown": self.crown_status(),
            "articles_guarded": len(engine_coverage),
            "unguarded_articles": list(self._engine.unguarded_articles()),
            "rules": sum(engine_coverage.values()),
            "decrees_consumed": len(self._decrees),
            "records": len(self._records),
            "bypass_parameters": [],
        }


__all__ = [
    "ExecutionRecord",
    "GatewayError",
    "SovereignGateway",
    "SovereigntyViolation",
    "ConstitutionalViolation",
    "FORBIDDEN_BYPASS_PARAMS",
]
