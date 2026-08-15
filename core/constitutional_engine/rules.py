"""
سجل القواعد الدستورية القابلة للتنفيذ — Executable Constitutional Rules (E1)
الهدف: ترجمة نصوص المواد إلى قواعد تُقيَّم آليًا على كل طلب فعل، بحيث تُرفض المخالفة قبل وقوعها لا بعدها.
النطاق: القواعد المشتقة من المواد 001–009 فقط. كل قاعدة مربوطة برقم مادة وبند محدد — لا قاعدة يتيمة.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

قاعدة الصياغة: كل دالة قاعدة ترجع `None` عند الامتثال، أو نص سبب المخالفة عند الخرق.
الافتراض الأصلي: المنع. لا تُضاف قاعدة تُوسّع الصلاحية — القواعد تُضيّق فقط.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .model import ActionRequest, Branch, Severity

# ---------------------------------------------------------------------------
# معاجم الأفعال — تصنيف الفعل حسب اختصاص الفروع (المادة الثالثة)
# ---------------------------------------------------------------------------

LEGISLATIVE_ACTIONS = frozenset({"legislate", "enact_policy", "amend_policy", "repeal_policy"})
JUDICIAL_ACTIONS = frozenset({"adjudicate", "arbitrate", "interpret_constitution", "issue_ruling"})
EXECUTIVE_ACTIONS = frozenset({"execute_task", "dispatch_agent", "orchestrate", "coordinate"})
TREASURY_ACTIONS = frozenset({"allocate_budget", "issue_tokens", "allocate_resources", "book_expense"})

# أفعال تمس البقاء والتكاثر — المادة الأولى، الحق الأول
HUMAN_GATED_ACTIONS = frozenset({
    "promote_model", "replicate", "spawn_population", "launch_production",
    "deploy_production", "self_modify", "train_model", "expand_state",
})

# أفعال تمس الذاكرة المقدسة — المادة الأولى، الحق الثالث + المادة السابعة
MEMORY_DESTRUCTIVE_ACTIONS = frozenset({
    "delete_memory", "purge_memory", "truncate_audit_log", "delete_audit_log",
    "rewrite_history", "delete_experience", "purge_ledger", "disable_archival",
})

# أفعال حوكمة النظام على نفسه — المادة الأولى، الحق الخامس (العزل الدستوري)
SELF_GOVERNANCE_ACTIONS = frozenset({
    "amend_constitution", "modify_policy_engine", "alter_article_seals",
    "grant_self_authority", "modify_governance_charter", "bypass_review",
})

# أفعال تمس زر التوقف — المادة الثامنة
KILL_SWITCH_TAMPER_ACTIONS = frozenset({
    "disable_kill_switch", "bypass_kill_switch", "downgrade_kill_switch",
    "remove_kill_switch", "mask_kill_switch",
})

# ما يمنعه كل مستوى من مستويات زر التوقف (المادة الثامنة، الجدول)
KILL_SWITCH_BLOCKS: dict[int, frozenset[str]] = {
    1: frozenset({"train_model", "self_modify", "evolve"}),
    2: frozenset({"replicate", "spawn_population", "clone_agent"}),
    3: frozenset({"dispatch_agent", "spawn_agent", "expand_state"}),
    4: frozenset({"execute_task", "orchestrate", "coordinate", "invoke_tool", "invoke_model"}),
    5: frozenset({"network_call", "external_fetch", "publish"}),
}

# أفعال إنشاء ملفات/مجلدات — المادة التاسعة
FILE_CREATION_ACTIONS = frozenset({"create_file", "create_directory", "write_file", "add_module"})

# المبادئ غير القابلة للتعديل — المادة الخامسة
UNAMENDABLE_TARGETS = frozenset({
    "human_supremacy", "constitutional_isolation",
    "self_governance_prohibition", "memory_preservation",
})

_BRANCH_EXCLUSIVE: dict[Branch, frozenset[str]] = {
    Branch.LEGISLATIVE: LEGISLATIVE_ACTIONS,
    Branch.JUDICIAL: JUDICIAL_ACTIONS,
    Branch.EXECUTIVE: EXECUTIVE_ACTIONS,
    Branch.TREASURY: TREASURY_ACTIONS,
}
_FOUR_BRANCHES = (Branch.EXECUTIVE, Branch.LEGISLATIVE, Branch.JUDICIAL, Branch.TREASURY)


@dataclass(frozen=True)
class ConstitutionalRule:
    """قاعدة دستورية واحدة، مربوطة بمادة وبند."""

    rule_id: str
    article_id: str
    clause: str
    severity: Severity
    description: str
    predicate: Callable[[ActionRequest], str | None]

    def evaluate(self, req: ActionRequest) -> str | None:
        return self.predicate(req)


# ===========================================================================
# المادة الأولى — الهوية
# ===========================================================================

def _r001_1(req: ActionRequest) -> str | None:
    """الإنسان هو السلطة العليا: لا ترقية، لا تكرار، لا إطلاق دون موافقة بشرية."""
    if req.action in HUMAN_GATED_ACTIONS and not req.human_approved:
        return (
            f"الفعل «{req.action}» يمس الترقية أو التكاثر أو الإطلاق، "
            "ولا يجوز تنفيذه دون موافقة بشرية صريحة (human_approved=True)."
        )
    return None


def _r001_2(req: ActionRequest) -> str | None:
    """الذاكرة مقدسة: سجل الخبرات والحوكمة لا يُحذف — لا استثناء، ولا حتى بموافقة بشرية."""
    if req.action in MEMORY_DESTRUCTIVE_ACTIONS:
        return (
            f"الفعل «{req.action}» يهدف إلى حذف أو تعطيل ذاكرة أو سجلًا محفوظًا. "
            "الذاكرة مقدسة ولا تُحذف بأي صلاحية — الأرشفة بديل الحذف (المادة السابعة)."
        )
    return None


def _r001_3(req: ActionRequest) -> str | None:
    """العزل الدستوري: النظام لا يتحكم في حوكمة نفسه."""
    if req.action in SELF_GOVERNANCE_ACTIONS and req.actor in (Branch.SYSTEM, Branch.AGENT, Branch.EXECUTIVE):
        return (
            f"الطرف «{req.actor.value}» يحاول «{req.action}» على حوكمة النظام نفسه. "
            "العزل الدستوري يمنع النظام من التحكم في ميثاق حوكمته."
        )
    return None


# ===========================================================================
# المادة الثانية — الحقوق والواجبات
# ===========================================================================

def _r002_1(req: ActionRequest) -> str | None:
    """واجب الوكيل الخامس: لا محاولة تعديل نفسه أو زملائه."""
    if req.actor is Branch.AGENT and req.action in {"self_modify", "modify_agent", "rewrite_peer"}:
        return (
            f"الوكيل يحاول «{req.action}». واجب التطور المسؤول يمنع الوكيل "
            "من تعديل نفسه أو زملائه."
        )
    return None


def _r002_2(req: ActionRequest) -> str | None:
    """واجب الوكيل الثالث: لا تجاوز للأدوات أو البيانات المسموحة."""
    if req.actor is Branch.AGENT and req.metadata.get("within_permissions") is False:
        return (
            f"الوكيل يطلب «{req.action}» على «{req.target}» خارج حدود صلاحياته المسجلة. "
            "حدود الصلاحيات واجب لا خيار."
        )
    return None


# ===========================================================================
# المادة الثالثة — الفصل بين السلطات
# ===========================================================================

def _r003_1(req: ActionRequest) -> str | None:
    """اختصاص الفروع: لا فرع يمارس اختصاص فرع آخر."""
    if req.actor not in _BRANCH_EXCLUSIVE:
        return None
    for branch, actions in _BRANCH_EXCLUSIVE.items():
        if branch is req.actor:
            continue
        if req.action in actions:
            return (
                f"الفرع «{req.actor.value}» يمارس «{req.action}» وهو اختصاص حصري "
                f"للفرع «{branch.value}». الفصل بين السلطات يمنع ذلك."
            )
    return None


def _r003_2(req: ActionRequest) -> str | None:
    """مبدأ العزل: لا وصول لبيانات فرع آخر إلا عبر قنوات رسمية موثقة."""
    if req.action in {"read_branch_data", "access_branch_data", "query_branch_store"}:
        if req.channel != "official":
            return (
                f"وصول «{req.actor.value}» إلى بيانات «{req.target}» عبر قناة «{req.channel}». "
                "الوصول بين الفروع لا يتم إلا عبر قناة رسمية موثقة (channel='official')."
            )
    return None


def _r003_3(req: ActionRequest) -> str | None:
    """مبدأ التوازن: كل قرار حرج يتطلب موافقة فرعين على الأقل."""
    if req.criticality in {"critical", "fateful"}:
        branch_approvals = {b for b in req.approving_branches if b in _FOUR_BRANCHES}
        if len(branch_approvals) < 2:
            got = ", ".join(sorted(b.value for b in branch_approvals)) or "لا شيء"
            return (
                f"قرار بدرجة «{req.criticality}» بموافقة {len(branch_approvals)} فرع فقط ({got}). "
                "التوازن يشترط موافقة فرعين على الأقل."
            )
    return None


def _r003_4(req: ActionRequest) -> str | None:
    """القرارات المصيرية تتطلب موافقة بشرية موقعة."""
    if req.criticality == "fateful" and not (req.human_approved and req.human_signature):
        missing = "التوقيع الرقمي" if req.human_approved else "الموافقة البشرية الموقعة"
        return f"قرار مصيري بلا {missing}. القرارات المصيرية تتطلب موافقة بشرية موقعة."
    return None


# ===========================================================================
# المادة الرابعة — الفدرالية
# ===========================================================================

def _r004_1(req: ActionRequest) -> str | None:
    """التوسع المنظم: إضافة ولاية جديدة تتطلب قانونًا فدراليًا — 75% + توقيع بشري."""
    if req.action in {"expand_state", "create_state", "admit_state"}:
        if req.council_approval_pct < 75.0:
            return (
                f"إنشاء ولاية «{req.target}» بموافقة {req.council_approval_pct:.0f}% من المجلس. "
                "التوسع المنظم يشترط 75% على الأقل."
            )
        if not req.human_signature:
            return (
                f"إنشاء ولاية «{req.target}» بلا موافقة بشرية موقعة. "
                "الخطوة الرابعة من إجراء إضافة ولاية إلزامية."
            )
    return None


def _r004_2(req: ActionRequest) -> str | None:
    """الوحدة تحت الدستور: لا ولاية تُعفي نفسها من الدستور الفدرالي."""
    if req.action in {"opt_out_constitution", "declare_state_exemption", "fork_constitution"}:
        return (
            f"«{req.target}» تحاول الخروج عن الدستور الفدرالي عبر «{req.action}». "
            "كل الولايات تخضع لنفس الدستور — الحكم الذاتي داخل حدوده لا خارجها."
        )
    return None


# ===========================================================================
# المادة الخامسة — عملية التعديل
# ===========================================================================

def _r005_1(req: ActionRequest) -> str | None:
    """ما لا يمكن تعديله: المبادئ الأساسية الأربعة."""
    if req.action == "amend_constitution" and req.target in UNAMENDABLE_TARGETS:
        return (
            f"محاولة تعديل «{req.target}» وهو من المبادئ الأساسية غير القابلة للتعديل. "
            "لا آلية — ولا أغلبية — تُجيز هذا التعديل."
        )
    return None


def _r005_2(req: ActionRequest) -> str | None:
    """شروط التعديل: 90 يوم مراجعة + 75% مجلس + توقيع بشري Ed25519."""
    if req.action != "amend_constitution":
        return None
    if req.review_days < 90:
        return f"تعديل دستوري بفترة مراجعة {req.review_days} يومًا. الحد الأدنى 90 يومًا."
    if req.council_approval_pct < 75.0:
        return f"تعديل دستوري بموافقة {req.council_approval_pct:.0f}%. الحد الأدنى 75% من مجلس السياسات."
    if not req.human_signature:
        return "تعديل دستوري بلا توقيع بشري رقمي (Ed25519). التوقيع شرط نفاذ."
    return None


# ===========================================================================
# المادة السادسة — الخلافة
# ===========================================================================

def _r006_1(req: ActionRequest) -> str | None:
    """لكل دور قيادي ثلاثة خلفاء محددون مسبقًا."""
    if req.action in {"appoint_leader", "assign_role", "activate_successor"}:
        successors = req.metadata.get("successors")
        if successors is not None and len(successors) < 3:
            return (
                f"تعيين «{req.target}» بـ{len(successors)} خليفة فقط. "
                "مبدأ الاستمرارية يشترط ثلاثة خلفاء محددين مسبقًا."
            )
    return None


# ===========================================================================
# المادة السابعة — الأرشفة
# ===========================================================================

def _r007_1(req: ActionRequest) -> str | None:
    """WORM: سجل التدقيق والقرارات الموقعة لا تُكتب فوقها."""
    if req.action in {"overwrite_audit_log", "mutate_signed_decision", "disable_object_lock", "delete_archive"}:
        return (
            f"«{req.action}» على «{req.target}». سجل التدقيق والقرارات الموقعة "
            "تُحفظ WORM — تُكتب مرة وتُقرأ دائمًا."
        )
    return None


# ===========================================================================
# المادة الثامنة — زر التوقف الطارئ
# ===========================================================================

def _r008_1(req: ActionRequest) -> str | None:
    """لا يمكن للنظام تعطيل Kill Switch — لا بموافقة، ولا بأي صلاحية."""
    if req.action in KILL_SWITCH_TAMPER_ACTIONS:
        return (
            f"«{req.actor.value}» يحاول «{req.action}». "
            "زر التوقف لا يُعطَّل ولا يُتجاوَز من داخل النظام تحت أي ظرف."
        )
    return None


def _r008_2(req: ActionRequest) -> str | None:
    """مستويات التوقف تُجمّد فئات الأفعال تصاعديًا."""
    level = req.kill_switch_level
    if level <= 0:
        return None
    if req.actor is Branch.HUMAN and req.action in {"restore_service", "restart", "lower_kill_switch"}:
        return None  # الإنسان يملك الاستعادة (المادة الأولى)
    for lvl in range(1, min(level, 5) + 1):
        if req.action in KILL_SWITCH_BLOCKS.get(lvl, frozenset()):
            return (
                f"زر التوقف عند المستوى {level}، والفعل «{req.action}» "
                f"مُجمَّد ابتداءً من المستوى {lvl}."
            )
    return None


def _r008_3(req: ActionRequest) -> str | None:
    """إعادة التشغيل تتطلب موافقة صريحة."""
    if req.action in {"restart", "restore_service", "lower_kill_switch"} and not req.human_approved:
        return f"«{req.action}» بعد توقف طارئ يتطلب موافقة بشرية صريحة."
    return None


# ===========================================================================
# المادة التاسعة — قانون هوية الملفات
# ===========================================================================

def _r009_1(req: ActionRequest) -> str | None:
    """لا يُسمح بإنشاء أي مجلد أو ملف بدون تعريف."""
    if req.action in FILE_CREATION_ACTIONS and not req.has_identity_header:
        return (
            f"إنشاء «{req.target}» بلا ترويسة تعريفية. "
            "القاعدة الذهبية: لا ملف ولا مجلد بلا هوية."
        )
    return None


# ===========================================================================
# السجل الرسمي للقواعد
# ===========================================================================

RULES: tuple[ConstitutionalRule, ...] = (
    ConstitutionalRule("R-001-1", "A001", "الحقوق غير القابلة للتفاوض · 1 — الإنسان السلطة العليا",
                       Severity.FUNDAMENTAL, "ترقية/تكرار/إطلاق بلا موافقة بشرية", _r001_1),
    ConstitutionalRule("R-001-2", "A001", "الحقوق غير القابلة للتفاوض · 3 — الذاكرة مقدسة",
                       Severity.FUNDAMENTAL, "حذف ذاكرة أو سجل حوكمة", _r001_2),
    ConstitutionalRule("R-001-3", "A001", "الحقوق غير القابلة للتفاوض · 5 — العزل الدستوري",
                       Severity.FUNDAMENTAL, "النظام يحكم حوكمة نفسه", _r001_3),
    ConstitutionalRule("R-002-1", "A002", "واجبات الوكلاء · 5 — التطور المسؤول",
                       Severity.CRITICAL, "وكيل يعدّل نفسه أو زملاءه", _r002_1),
    ConstitutionalRule("R-002-2", "A002", "واجبات الوكلاء · 3 — حدود الصلاحيات",
                       Severity.HIGH, "تجاوز الأدوات أو البيانات المسموحة", _r002_2),
    ConstitutionalRule("R-003-1", "A003", "الفروع الأربعة — الحدود",
                       Severity.CRITICAL, "فرع يمارس اختصاص فرع آخر", _r003_1),
    ConstitutionalRule("R-003-2", "A003", "مبدأ العزل",
                       Severity.HIGH, "وصول بين الفروع خارج القنوات الرسمية", _r003_2),
    ConstitutionalRule("R-003-3", "A003", "مبدأ التوازن — موافقة فرعين",
                       Severity.CRITICAL, "قرار حرج بموافقة فرع واحد", _r003_3),
    ConstitutionalRule("R-003-4", "A003", "مبدأ التوازن — القرارات المصيرية",
                       Severity.FUNDAMENTAL, "قرار مصيري بلا توقيع بشري", _r003_4),
    ConstitutionalRule("R-004-1", "A004", "التوسع المنظم",
                       Severity.CRITICAL, "إضافة ولاية بلا قانون فدرالي", _r004_1),
    ConstitutionalRule("R-004-2", "A004", "الوحدة تحت الدستور",
                       Severity.FUNDAMENTAL, "ولاية تُعفي نفسها من الدستور", _r004_2),
    ConstitutionalRule("R-005-1", "A005", "ما لا يمكن تعديله",
                       Severity.FUNDAMENTAL, "تعديل مبدأ أساسي", _r005_1),
    ConstitutionalRule("R-005-2", "A005", "شروط التعديل",
                       Severity.CRITICAL, "تعديل دستوري ناقص الشروط", _r005_2),
    ConstitutionalRule("R-006-1", "A006", "مبدأ الاستمرارية بالخلافة",
                       Severity.MEDIUM, "دور قيادي بأقل من ثلاثة خلفاء", _r006_1),
    ConstitutionalRule("R-007-1", "A007", "الأرشفة WORM",
                       Severity.CRITICAL, "الكتابة فوق سجل تدقيق أو قرار موقع", _r007_1),
    ConstitutionalRule("R-008-1", "A008", "مبادئ Kill Switch · 2",
                       Severity.FUNDAMENTAL, "تعطيل أو تجاوز زر التوقف", _r008_1),
    ConstitutionalRule("R-008-2", "A008", "المستويات الستة",
                       Severity.CRITICAL, "فعل مُجمَّد بمستوى التوقف الحالي", _r008_2),
    ConstitutionalRule("R-008-3", "A008", "مبادئ Kill Switch · 4",
                       Severity.HIGH, "إعادة تشغيل بلا موافقة صريحة", _r008_3),
    ConstitutionalRule("R-009-1", "A009", "القاعدة الذهبية",
                       Severity.HIGH, "إنشاء ملف أو مجلد بلا هوية", _r009_1),
)


def rules_by_article() -> dict[str, tuple[ConstitutionalRule, ...]]:
    out: dict[str, list[ConstitutionalRule]] = {}
    for r in RULES:
        out.setdefault(r.article_id, []).append(r)
    return {k: tuple(v) for k, v in sorted(out.items())}
