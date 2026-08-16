"""
محرك الدستور — Constitutional Engine (E1)
الهدف: تقييم كل طلب فعل مقابل كل قاعدة دستورية قبل تنفيذه، وإصدار حكم مُعلَّل برقم المادة، وتسجيله في سجل غير قابل للعبث.
النطاق: القرار الدستوري فقط. لا ينفذ الفعل، ولا يعرف كيف يُنفَّذ — يأذن أو يمنع.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

الافتراض الأصلي: المنع. أي خطأ داخلي في تقييم قاعدة = رفض الفعل، لا تجاوزه.
لا سقوط صامت: تعذّر تحميل الدستور أو كسر السجل يوقف المحرك بدل أن يسمح.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from .articles import Article, load_articles, verify_seals
from .ledger import ConstitutionalLedger
from .model import (
    ActionRequest,
    CrownEffect,
    Decision,
    RuleViolation,
    Severity,
    Verdict,
)
from .rules import RULES, ConstitutionalRule


class ConstitutionalEngine:
    """المرجع الوحيد لسؤال: هل هذا الفعل دستوري؟"""

    def __init__(
        self,
        *,
        articles: list[Article] | None = None,
        ledger: ConstitutionalLedger | None = None,
        ledger_path: Path | str | None = None,
        rules: tuple[ConstitutionalRule, ...] = RULES,
        enforce_seals: bool = False,
    ) -> None:
        # تحميل الدستور — يرفع ConstitutionNotFoundError إن غاب. لا افتراضات.
        self.articles = articles if articles is not None else load_articles()
        self._by_id = {a.article_id: a for a in self.articles}
        self.rules = rules
        self.ledger = ledger if ledger is not None else ConstitutionalLedger(ledger_path)

        self._orphans = tuple(sorted({r.article_id for r in self.rules} - set(self._by_id)))
        if self._orphans:
            raise ValueError(
                f"قواعد مربوطة بمواد غير موجودة: {', '.join(self._orphans)}. "
                "لا قاعدة يتيمة في هذه الدولة."
            )

        if enforce_seals:
            problems = verify_seals(articles=self.articles)
            if problems:
                raise SealViolation(
                    "الدستور مُعدَّل خارج إجراء التعديل (المادة الخامسة):\n  - "
                    + "\n  - ".join(problems)
                )

    # -- التقييم -----------------------------------------------------------
    @staticmethod
    def fingerprint(req: ActionRequest) -> str:
        raw = "|".join(
            [
                req.actor.value, req.action, req.target,
                str(req.human_approved), str(req.human_signature),
                ",".join(sorted(b.value for b in req.approving_branches)),
                req.channel, req.criticality,
                str(req.kill_switch_level), str(req.review_days),
                f"{req.council_approval_pct:.2f}", str(req.has_identity_header),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def evaluate(
        self,
        req: ActionRequest,
        *,
        record: bool = True,
        sovereign: bool = False,
        decision_kind: str = "",
        authority_layer: str = "",
    ) -> Verdict:
        """قيّم طلبًا. يُسجَّل الحكم دائمًا — سُمح أم رُفض (الشفافية المطلقة).

        معامل `sovereign` ليس راية تجاوز، ولا يُقرّره الطالب: تُمرّره البوابة
        السيادية **بعد** ثبوت توقيع Ed25519 مقابل مفتاح التاج. وأثره ليس تخطي القواعد
        بل **تغيير وزنها**: تُقيَّم كلها وتُسجَّل كلها، ثم تُدرَج في
        `advisory_violations` لا في `violations` (المادة العاشرة · 7 · 2).

        ولاحظ أن عدد القواعد المُقيَّمة واحد في المسارين: الدستور لا يسكت أمام
        التاج، بل يُبدي رأيه ولا يملك منعه.
        """
        violations: list[RuleViolation] = []
        advisory: list[RuleViolation] = []

        for rule in self.rules:
            article = self._by_id[rule.article_id]
            try:
                reason = rule.evaluate(req)
            except Exception as exc:  # noqa: BLE001 — الفشل يعني المنع، لا التجاوز
                violations.append(
                    RuleViolation(
                        rule_id=rule.rule_id,
                        article_id=rule.article_id,
                        article_title=article.title,
                        clause=rule.clause,
                        severity=Severity.CRITICAL,
                        reason=(
                            f"تعذّر تقييم القاعدة ({type(exc).__name__}: {exc}). "
                            "القاعدة غير المُقيَّمة تُعامَل كمخالفة — الافتراض الأصلي هو المنع."
                        ),
                    )
                )
                continue
            if reason:
                found = RuleViolation(
                    rule_id=rule.rule_id,
                    article_id=rule.article_id,
                    article_title=article.title,
                    clause=rule.clause,
                    severity=rule.severity,
                    reason=reason,
                )
                # الفرق الوحيد بين المسارين: أين تُدرَج النتيجة — لا هل تُقيَّم.
                if sovereign and rule.crown_effect is CrownEffect.ADVISORY:
                    advisory.append(found)
                else:
                    violations.append(found)

        verdict = Verdict(
            decision=Decision.DENY if violations else Decision.ALLOW,
            request_fingerprint=self.fingerprint(req),
            rules_evaluated=len(self.rules),
            violations=tuple(violations),
            advisory_violations=tuple(advisory),
            decision_kind=decision_kind,
            authority_layer=authority_layer,
        )

        if record:
            entry = self.ledger.append(
                {
                    "type": "CONSTITUTIONAL_VERDICT",
                    "actor": req.actor.value,
                    "action": req.action,
                    "target": req.target,
                    "criticality": req.criticality,
                    "kill_switch_level": req.kill_switch_level,
                    "decision": verdict.decision.value,
                    "request_fingerprint": verdict.request_fingerprint,
                    "rules_evaluated": verdict.rules_evaluated,
                    "violations": [v.as_dict() for v in verdict.violations],
                    "advisory_violations": [
                        v.as_dict() for v in verdict.advisory_violations
                    ],
                    "decision_kind": verdict.decision_kind,
                    "authority_layer": verdict.authority_layer,
                    "sovereign_path": sovereign,
                }
            )
            verdict = replace(verdict, ledger_entry_hash=entry.entry_hash)

        return verdict

    def enforce(self, req: ActionRequest) -> Verdict:
        """قيّم وامنع. يرفع ConstitutionalViolation عند الرفض — لا يمكن تجاهل القيمة المرجعة."""
        verdict = self.evaluate(req)
        if not verdict.allowed:
            raise ConstitutionalViolation(verdict)
        return verdict

    # -- استعلام ------------------------------------------------------------
    def article(self, article_id: str) -> Article:
        return self._by_id[article_id]

    def coverage(self) -> dict[str, int]:
        """كم قاعدة قابلة للتنفيذ تحرس كل مادة."""
        counts = {a.article_id: 0 for a in self.articles}
        for r in self.rules:
            counts[r.article_id] += 1
        return counts

    def unguarded_articles(self) -> tuple[str, ...]:
        """مواد سارية بلا قاعدة تنفيذية واحدة — دين دستوري يجب سداده."""
        return tuple(aid for aid, n in sorted(self.coverage().items()) if n == 0)


class ConstitutionalViolation(Exception):
    """الفعل مخالف للدستور. يحمل الحكم كاملًا برقم المادة والسبب."""

    def __init__(self, verdict: Verdict) -> None:
        self.verdict = verdict
        super().__init__(verdict.explain())


class SealViolation(Exception):
    """نص الدستور مُعدَّل خارج إجراء التعديل الدستوري."""
