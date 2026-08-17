"""
النواة الدستورية — Constitutional Kernel (E1)
الهدف: تحويل دستور الدولة من نصوص تُقرأ إلى محرك يمنع المخالفة قبل وقوعها ويسجل كل حكم في سلسلة غير قابلة للعبث.
النطاق: المواد 001–009 في core/constitution/. لا يعرف هذا المحرك شيئًا عن التنفيذ — يأذن أو يمنع فقط.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16
"""

from .articles import (
    Article,
    ConstitutionNotFoundError,
    SealMismatchError,
    load_articles,
    verify_seals,
    write_seals,
)
from .engine import ConstitutionalEngine, ConstitutionalViolation, SealViolation
from .ledger import ConstitutionalLedger, LedgerEntry, LedgerTamperError
from .model import ActionRequest, Branch, Decision, RuleViolation, Severity, Verdict
from .rules import RULES, ConstitutionalRule, rules_by_article

__all__ = [
    "RULES",
    "ActionRequest",
    "Article",
    "Branch",
    "ConstitutionNotFoundError",
    "ConstitutionalEngine",
    "ConstitutionalLedger",
    "ConstitutionalRule",
    "ConstitutionalViolation",
    "Decision",
    "LedgerEntry",
    "LedgerTamperError",
    "RuleViolation",
    "SealMismatchError",
    "SealViolation",
    "Severity",
    "Verdict",
    "load_articles",
    "rules_by_article",
    "verify_seals",
    "write_seals",
]
