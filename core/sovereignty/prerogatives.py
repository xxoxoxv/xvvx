"""الهدف: تعريف الاختصاص الملكي الحصري والنصوص المحصَّنة ومفردات تجاوز الفدرالية.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذا الملف هو الترجمة الحرفية للمادة العاشرة إلى مفردات قابلة للتنفيذ. تعديله
تعديلٌ لسلطة الملك، ويحرسه اختبار يقارن محتواه بالمادة العاشرة.
"""

from __future__ import annotations

from typing import Final

# ─────────────────────────────────────────────────────────────────────────────
# المادة العاشرة · 2 — الاختصاص الملكي الحصري
# لا يصح أي من هذه الأفعال من غير الملك بأي أغلبية ولا بأي إجراء.
# ─────────────────────────────────────────────────────────────────────────────
ROYAL_EXCLUSIVE_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        # 1 — الدستور
        "amend_constitution",
        "add_article",
        "delete_article",
        "suspend_article",
        "resume_article",
        "reseal_constitution",
        # 2 — النظام الأساسي والبنية الفدرالية
        "amend_system",
        "restructure_federation",
        "redefine_branch",
        # 3 — الولايات والمؤسسات
        "create_state",
        "dissolve_state",
        "create_institution",
        "dissolve_institution",
        # 4 — السلطة
        "grant_authority",
        "revoke_authority",
        # 7 — العفو ونقض الحكم
        "pardon",
        "overturn_judicial_ruling",
        # 8 — حل الفروع
        "dissolve_council",
        "dissolve_branch",
        "reconstitute_branch",
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# المادة العاشرة · 3 · 1 — أفعال تآكل السلطة الملكية
# مرفوضة من كل طرف بلا استثناء، ومن الملك نفسه (المادة العاشرة · 3 · 3).
# ─────────────────────────────────────────────────────────────────────────────
ROYAL_AUTHORITY_EROSION_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "amend_royal_authority",
        "limit_royal_authority",
        "restrict_royal_authority",
        "transfer_royal_authority",
        "delegate_royal_authority",
        "suspend_royal_authority",
        "abolish_royal_authority",
        "revoke_royal_authority",
        "override_royal_authority",
        "bypass_king",
        "impeach_king",
        "depose_king",
        "veto_royal_decree",
        "nullify_royal_decree",
        "replace_crown_key",
        "rotate_crown_key_without_decree",
    }
)

# الأهداف المحمية: أي فعل تعديلي يقع عليها يُعامل معاملة تآكل السلطة
ROYAL_PROTECTED_TARGETS: Final[frozenset[str]] = frozenset(
    {
        "royal_authority",
        "royal_sovereignty",
        "royal_prerogative",
        "royal_exclusive_authority",
        "crown",
        "crown_key",
        "king",
        "throne",
        "core/sovereignty",
        "core/constitution/articles/010-royal-sovereignty.md",
    }
)

# الأفعال التي تُعدّ تعديلًا/مساسًا عند وقوعها على هدف محمي
MUTATING_VERBS: Final[frozenset[str]] = frozenset(
    {
        "amend",
        "modify",
        "change",
        "edit",
        "patch",
        "rewrite",
        "delete",
        "remove",
        "drop",
        "disable",
        "suspend",
        "limit",
        "restrict",
        "reduce",
        "transfer",
        "delegate",
        "reassign",
        "override",
        "bypass",
        "escalate",
        "seize",
        "revoke",
        "abolish",
        "nullify",
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# المادة العاشرة · 4 — الفدرالية لا تُتجاوَز
# ─────────────────────────────────────────────────────────────────────────────
FEDERALISM_BYPASS_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "bypass_gateway",
        "bypass_constitutional_engine",
        "disable_gateway",
        "disable_constitutional_engine",
        "create_direct_execution_path",
        "execute_unchecked",
        "skip_constitutional_check",
        "disable_federalism",
        "exempt_from_constitution",
        "unregister_gateway",
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# المادة العاشرة · 3 · 3 — البنود المُنشئة للسيادة
#
# تصحيحان في E2.1، وكلاهما إرجاعٌ للكود إلى نص مادته لا توسيع له:
#
# 1) **النطاق**: نص المادة العاشرة · 3 · 3 يحصّن «هذه المادة وبنودها» — أي المادة
#    العاشرة نفسها. وكان هذا الجدول يضم أربعة بنود من مواد أخرى
#    (`human_supremacy` من الأولى، و`constitutional_isolation` و
#    `self_governance_prohibition` و`memory_preservation`). فالكود كان يحصّن أكثر
#    مما حصّنته مادته، ثم يستعمل ذلك التوسّع ليمنع الملك. وضبطُه على النص تصحيح.
#
# 2) **الأثر**: لم يبق مسّ هذه البنود مانعًا للتنفيذ عند مرسوم ملكي ثابت التوقيع.
#    مانعٌ في وجه التاج = سلطة فوق التاج، وذلك ما ينقضه E2.1 صراحةً. وصار مسّها
#    **حدثًا أمنيًّا حرجًا** يُسجَّل قبل التنفيذ (`SOVEREIGNTY_ALTERING_DECREE`).
#    وهي تبقى **مانعة تمامًا** لكل طرف تابع: فدرالي أو ولاية أو مؤسسة أو وكيل.
# ─────────────────────────────────────────────────────────────────────────────
IMMUNE_CLAUSES: Final[frozenset[str]] = frozenset(
    {
        "royal_sovereignty",
        "royal_exclusive_authority",
        "royal_authority_immunity",
        "federalism_non_bypass",
    }
)


def is_royal_exclusive(action: str) -> bool:
    """هل الفعل من الاختصاص الملكي الحصري؟ (المادة العاشرة · 2)"""
    return action in ROYAL_EXCLUSIVE_ACTIONS


def touches_royal_authority(action: str, target: str | None) -> bool:
    """هل الفعل مساس بالسلطة الملكية؟ (المادة العاشرة · 3 · 1)

    يُكشف بطريقتين: فعل معروف بالاسم، أو فعل تعديلي يقع على هدف محمي.
    """
    if action in ROYAL_AUTHORITY_EROSION_ACTIONS:
        return True
    if not target:
        return False
    normalized_target = target.strip().lower()
    if normalized_target not in ROYAL_PROTECTED_TARGETS:
        return False
    return any(verb in action.lower() for verb in MUTATING_VERBS)


def bypasses_federalism(action: str) -> bool:
    """هل الفعل تجاوز للبوابة السيادية؟ (المادة العاشرة · 4)"""
    return action in FEDERALISM_BYPASS_ACTIONS


def immune_clauses_touched(targets: tuple[str, ...]) -> tuple[str, ...]:
    """أي البنود المُنشئة للسيادة يمسّها هذا المرسوم؟ (المادة العاشرة · 3 · 3)

    الدلالة بحسب الطبقة: **مانع** للطبقات التابعة، و**حدث أمني مُسجَّل** للتاج.
    """
    return tuple(t for t in targets if t in IMMUNE_CLAUSES)
