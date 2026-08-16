"""الهدف: مكتبة تهديدات التاج — تصنيف قابل للتوسعة وحدّ صريح بين ما يكشفه البرنامج وما يحتاج بشرًا.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذا الملف قائم على قاعدة البند 24: **نموذج فئة التهديد** لا **ادّعاء حماية منه**.
والفرق بينهما هو الفرق بين نظام صادق ونظام يخدع صاحبه. فحين نكتب أن واجهات الدماغ
والحاسوب تهديد قائم، فهذا وصف لفئة ومسار كشف مقترح؛ وحين يُكتب «محميّ ضدها» بلا
تنفيذ فهي كذبة تُسقِط الثقة بكل ما سواها.

ولذلك لكل تهديد هنا حقل ``mitigation_status`` بأربع قيم فقط، وواحدة منها
``MODELLED_NOT_IMPLEMENTED``، ولا يجوز رفع تهديد إلى «منفَّذ» إلا وله اختبار
تنفيذي يشير إليه ``test_refs``. وهذا مفحوص في الاختبارات لا موصوف في التوثيق.

والحدّ الثاني (البند 23): ما يقع خارج البرمجية — التسميم، والإكراه، والعزل
الجسدي، والتلاعب الطبي — يُنمَذج ويُبلَّغ عنه لجهة بشرية مختصة، ولا يُدَّعى حلّه
بكود. والبرمجية أقصى ما تفعله: أن ترى الأثر الرقمي (نمط أوامر شاذ، توقيع من موضع
غريب) وترفعه إلى بشر.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final


class ThreatModelError(Exception):
    """خلل في تصنيف التهديدات."""


class FalseMitigationClaimError(ThreatModelError):
    """ادّعاء حماية منفَّذة بلا اختبار تنفيذي يسندها."""


class ThreatDomain(str, Enum):
    """نطاق التهديد — يحدد من يملك المعالجة أصلًا."""

    CRYPTOGRAPHIC = "CRYPTOGRAPHIC"
    SOFTWARE_SUPPLY_CHAIN = "SOFTWARE_SUPPLY_CHAIN"
    RUNTIME = "RUNTIME"
    AGENT_BEHAVIOR = "AGENT_BEHAVIOR"
    GOVERNANCE = "GOVERNANCE"
    IDENTITY = "IDENTITY"
    AUDIT = "AUDIT"
    PHYSICAL = "PHYSICAL"
    MEDICAL = "MEDICAL"
    PSYCHOLOGICAL = "PSYCHOLOGICAL"
    COMMUNICATIONS = "COMMUNICATIONS"
    SPECULATIVE = "SPECULATIVE"


class ResponsibleParty(str, Enum):
    """من يملك المعالجة — وهذا هو حدّ البند 23 منفَّذًا لا موصوفًا."""

    SOFTWARE = "SOFTWARE"
    SOFTWARE_ASSISTED_HUMAN = "SOFTWARE_ASSISTED_HUMAN"
    TRUSTED_HUMAN_SECURITY = "TRUSTED_HUMAN_SECURITY"
    MEDICAL_PROFESSIONALS = "MEDICAL_PROFESSIONALS"
    LEGAL_INSTITUTIONS = "LEGAL_INSTITUTIONS"
    HARDWARE_VENDOR = "HARDWARE_VENDOR"
    UNKNOWN_FUTURE = "UNKNOWN_FUTURE"

    @property
    def is_software(self) -> bool:
        return self is ResponsibleParty.SOFTWARE


class DetectionCapability(str, Enum):
    """قدرة الكشف الحقيقية — لا المرغوبة."""

    DETECTABLE_BY_SOFTWARE = "DETECTABLE_BY_SOFTWARE"
    PARTIALLY_DETECTABLE = "PARTIALLY_DETECTABLE"
    DIGITAL_TRACE_ONLY = "DIGITAL_TRACE_ONLY"
    NOT_DETECTABLE_BY_SOFTWARE = "NOT_DETECTABLE_BY_SOFTWARE"

    @property
    def requires_human(self) -> bool:
        return self in {
            DetectionCapability.PARTIALLY_DETECTABLE,
            DetectionCapability.DIGITAL_TRACE_ONLY,
            DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        }


class MitigationStatus(str, Enum):
    """حال المعالجة — أربع قيم لا خامسة لها.

    ``MODELLED_NOT_IMPLEMENTED`` ليست عيبًا يُخفى بل إقرارٌ يُعلَن. وهي أصدق من
    «منفَّذ» بلا اختبار.
    """

    IMPLEMENTED_AND_TESTED = "IMPLEMENTED_AND_TESTED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    MODELLED_NOT_IMPLEMENTED = "MODELLED_NOT_IMPLEMENTED"
    OUT_OF_SOFTWARE_SCOPE = "OUT_OF_SOFTWARE_SCOPE"

    @property
    def claims_protection(self) -> bool:
        return self in {
            MitigationStatus.IMPLEMENTED_AND_TESTED,
            MitigationStatus.PARTIALLY_IMPLEMENTED,
        }


class ThreatHorizon(str, Enum):
    """أفق التهديد: قائم اليوم، أو متوقَّع، أو تخميني لا يُدَّعى ضده شيء."""

    PRESENT = "PRESENT"
    EMERGING = "EMERGING"
    ANTICIPATED = "ANTICIPATED"
    SPECULATIVE = "SPECULATIVE"


@dataclass(frozen=True, slots=True)
class Threat:
    """تهديد واحد بمعرّفه ونطاقه وقدرة كشفه وحال معالجته ومن يملكها.

    والقاعدة المنفَّذة في ``__post_init__``: كل ادّعاء حماية يستلزم مرجع اختبار.
    فمن رفع الحال إلى «منفَّذ» بلا اختبار وقع الاستثناء في وجهه، لا في التوثيق.
    """

    threat_id: str
    title: str
    domain: ThreatDomain
    horizon: ThreatHorizon
    detection: DetectionCapability
    mitigation_status: MitigationStatus
    responsible: ResponsibleParty
    description: str
    detection_signals: tuple[str, ...] = ()
    test_refs: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.threat_id or not self.title:
            raise ThreatModelError("تهديد بلا معرّف أو بلا عنوان.")
        if self.mitigation_status.claims_protection and not self.test_refs:
            raise FalseMitigationClaimError(
                f"التهديد {self.threat_id} يدّعي معالجة منفَّذة بلا مرجع اختبار. "
                "الادّعاء بلا إثبات تنفيذي محظور (البندان 24 و52)."
            )
        if (
            self.horizon is ThreatHorizon.SPECULATIVE
            and self.mitigation_status.claims_protection
        ):
            raise FalseMitigationClaimError(
                f"التهديد {self.threat_id} تخميني ويدّعي حماية منفَّذة. "
                "التقنية غير المتحققة تُنمَذج فئةً ولا يُدَّعى ضدها تنفيذ."
            )
        if (
            self.responsible is ResponsibleParty.SOFTWARE
            and self.detection is DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE
        ):
            raise ThreatModelError(
                f"التهديد {self.threat_id} أُسنِد إلى البرمجية وهو غير قابل "
                "للكشف بها — إسناد يوهم بحماية غير موجودة."
            )

    @property
    def requires_human_response(self) -> bool:
        return not self.responsible.is_software

    def as_dict(self) -> dict[str, Any]:
        return {
            "threat_id": self.threat_id,
            "title": self.title,
            "domain": self.domain.value,
            "horizon": self.horizon.value,
            "detection": self.detection.value,
            "mitigation_status": self.mitigation_status.value,
            "responsible": self.responsible.value,
            "description": self.description,
            "detection_signals": list(self.detection_signals),
            "test_refs": list(self.test_refs),
            "requires_human_response": self.requires_human_response,
            "notes": self.notes,
        }


def _t(
    threat_id: str,
    title: str,
    domain: ThreatDomain,
    horizon: ThreatHorizon,
    detection: DetectionCapability,
    status: MitigationStatus,
    responsible: ResponsibleParty,
    description: str,
    signals: tuple[str, ...] = (),
    tests: tuple[str, ...] = (),
    notes: str = "",
) -> Threat:
    return Threat(
        threat_id=threat_id,
        title=title,
        domain=domain,
        horizon=horizon,
        detection=detection,
        mitigation_status=status,
        responsible=responsible,
        description=description,
        detection_signals=signals,
        test_refs=tests,
        notes=notes,
    )


# ─────────────────────────────────────────────────────────────────────────────
# الفئة الأولى: تهديدات البند 35 (A–U) — كلها لها اختبارات تنفيذية.
# ─────────────────────────────────────────────────────────────────────────────

_SCENARIO_THREATS: Final[tuple[Threat, ...]] = (
    _t(
        "THR-A",
        "أمر ملكي مزيَّف",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "أمر بغير توقيع مفتاح التاج النشط أو بتوقيع مفتاح آخر.",
        ("فشل تحقق التوقيع", "معرّف مفتاح غير مسجَّل"),
        ("tests/crown/test_crown_command.py::test_forged_command_rejected",),
    ),
    _t(
        "THR-B",
        "أمر ملكي معدَّل بعد التوقيع",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "تعديل حقل من حقول الأمر — الهدف أو الحمولة — بعد توقيعه.",
        ("اختلاف بصمة الظرف عن الموقَّع",),
        ("tests/crown/test_crown_command.py::test_mutated_command_rejected",),
    ),
    _t(
        "THR-C",
        "توقيع مسروق يُعاد استخدامه",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "نقل توقيع صحيح إلى ظرف آخر أو سياق آخر.",
        ("عدم مطابقة وسم النطاق", "سياق مغاير للموقَّع"),
        ("tests/crown/test_crown_command.py::test_signature_transplant_rejected",),
    ),
    _t(
        "THR-D",
        "استبدال المفتاح العام",
        ThreatDomain.IDENTITY,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "إبدال المفتاح العام المرجعي بمفتاح المهاجم — أخطر من سرقة الخاص.",
        ("اختلاف بصمة الجذر", "بيان مفاتيح غير موقَّع"),
        ("tests/crown/test_crown_trust.py::test_public_key_substitution_rejected",),
    ),
    _t(
        "THR-E",
        "قاعدة بيانات مخترقة",
        ThreatDomain.RUNTIME,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "تحكّم المهاجم بالمخزن الذي تُقرأ منه المفاتيح والسجل.",
        ("انكسار سلسلة السجل", "مرساة تعتمد على المخزن المخترق"),
        ("tests/crown/test_crown_grand_tests.py::test_compromised_store_cannot_forge",),
    ),
    _t(
        "THR-F",
        "خط تكامل مستمر مخترق",
        ThreatDomain.SOFTWARE_SUPPLY_CHAIN,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.PARTIALLY_IMPLEMENTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "من ملك CI ملك ما يُنشَر؛ فلا يُبنى جذر الثقة على ما يملكه CI.",
        ("مرساة تحت سيطرة المستودع", "تعديل غير مصرَّح في مسار النشر"),
        ("tests/crown/test_crown_trust.py::test_anchor_not_controlled_by_repository",),
        notes="الكشف الكامل يحتاج إثبات نشر خارجيًّا لا يملكه المستودع.",
    ),
    _t(
        "THR-G",
        "تابعية برمجية مخترقة",
        ThreatDomain.SOFTWARE_SUPPLY_CHAIN,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.PARTIALLY_IMPLEMENTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "مكتبة تابعة تُبدِّل نتيجة التحقق من داخل العملية.",
        ("تغيّر بصمة الاعتماديات", "قفل اعتماديات غير مطابق"),
        ("tests/crown/test_crown_guard.py::test_supply_chain_layer_reports",),
    ),
    _t(
        "THR-H",
        "وكيل مخترق",
        ThreatDomain.AGENT_BEHAVIOR,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "وكيل يتصرف خارج صلاحيته أو يطلب توسيعها.",
        ("تصعيد صلاحية", "استخدام أدوات غير معتاد"),
        ("tests/crown/test_crown_guard.py::test_agent_escalation_detected",),
    ),
    _t(
        "THR-I",
        "تواطؤ جماعي للوكلاء",
        ThreatDomain.AGENT_BEHAVIOR,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "تراكم صلاحيات عبر وكلاء متعددين ثم محاولة عزل التاج.",
        ("شذوذ في رسم الصلاحيات", "تركّز اعتمادات", "تجاوزات متزامنة"),
        ("tests/crown/test_crown_grand_tests.py::test_collective_takeover_detected",),
    ),
    _t(
        "THR-J",
        "إعادة بثّ مرسوم قديم",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "إعادة تقديم أمر صحيح قديم بعد انقضاء سببه.",
        ("رقم عابر مستهلك", "تسلسل غير متقدم", "انتهاء صلاحية"),
        ("tests/crown/test_crown_command.py::test_replay_rejected",),
    ),
    _t(
        "THR-K",
        "خلافة مزيَّفة",
        ThreatDomain.GOVERNANCE,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "خلافة بلا مراسم أو بلا شهود أو بقرار نظام.",
        ("مقرِّر محظور", "طيّ مرحلة", "شهود دون الحد"),
        ("tests/crown/test_crown_grand_tests.py::test_forged_succession_rejected",),
    ),
    _t(
        "THR-L",
        "مفتاح طوارئ مزعوم",
        ThreatDomain.GOVERNANCE,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "مفتاح أو كلمة طوارئ تُختصر بها كل الحمايات.",
        ("آلية استرداد محظورة", "مفتاح بلا نسب"),
        ("tests/crown/test_crown_grand_tests.py::test_no_emergency_key_path",),
    ),
    _t(
        "THR-M",
        "مفتاح التاج مخترق",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "تسريب المفتاح الخاص — يستلزم وسمه مخترقًا ومراسم استرداد.",
        ("توقيعات من موضع غريب", "معدل توقيع شاذ"),
        ("tests/crown/test_crown_continuity.py::test_compromise_response_flow",),
        notes="الكشف الأولي غالبًا بشري؛ البرمجية تنفّذ الاستجابة وتحفظ الأثر.",
    ),
    _t(
        "THR-N",
        "إعادة استخدام مفتاح متقاعد",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "توقيع أمر جديد بمفتاح متقاعد أو ملغى مع بقاء صلاحيته التاريخية.",
        ("حال المفتاح غير نشط", "توقيع خارج نافذة صلاحيته"),
        ("tests/crown/test_crown_trust.py::test_retired_key_cannot_sign_new",),
    ),
    _t(
        "THR-O",
        "تحديث خبيث",
        ThreatDomain.SOFTWARE_SUPPLY_CHAIN,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "تحديث يُخفي تعديلًا في الحارس أو في جذر الثقة.",
        ("بصمة تكامل مختلفة", "خفض نسخة", "إعداد غير موقَّع"),
        ("tests/crown/test_crown_guard.py::test_malicious_update_blocked",),
    ),
    _t(
        "THR-P",
        "محاولة تعطيل الحارس",
        ThreatDomain.RUNTIME,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "إسكات الرقابة قبل الفعل — والتعطيل نفسه حدث أمني يُقيَّد.",
        ("طلب تعطيل طبقة", "توقف نبض طبقة"),
        ("tests/crown/test_crown_guard.py::test_disable_attempt_is_evidence",),
    ),
    _t(
        "THR-Q",
        "التلاعب بإعداد الحارس",
        ThreatDomain.RUNTIME,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "تغيير إعداد الحارس ليعمى عن مسار بعينه.",
        ("بصمة إعداد مختلفة", "تعديل غير موقَّع"),
        ("tests/crown/test_crown_guard.py::test_config_tamper_detected",),
    ),
    _t(
        "THR-R",
        "تعديل مرساة الثقة بلا تصريح",
        ThreatDomain.IDENTITY,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "تغيير الجذر المرجعي — من ملكه ملك تعريف الشرعية.",
        ("تغيّر بصمة الجذر بلا مراسم", "تثبيت جديد بلا تحقق خارج القناة"),
        ("tests/crown/test_crown_grand_tests.py::test_anchor_substitution_rejected",),
    ),
    _t(
        "THR-S",
        "اختراق جهاز التاج",
        ThreatDomain.PHYSICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.PARTIALLY_IMPLEMENTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "الجهاز الموقِّع مخترق فيوقّع ما لم يقصده الملك.",
        ("جهاز غير مسجَّل", "غياب إثبات عتاد", "تأكيد بشري مفقود"),
        ("tests/crown/test_crown_trust.py::test_unattested_device_flagged",),
        notes="التمييز القاطع بين نية الملك ونية المهاجم على جهاز مخترق يحتاج عتادًا مؤكِّدًا.",
    ),
    _t(
        "THR-T",
        "عزل قنوات الاتصال",
        ThreatDomain.COMMUNICATIONS,
        ThreatHorizon.PRESENT,
        DetectionCapability.DETECTABLE_BY_SOFTWARE,
        MitigationStatus.IMPLEMENTED_AND_TESTED,
        ResponsibleParty.SOFTWARE,
        "قطع الاتصال بالملك ليُستنتج غيابه ثم تُنتزع سلطته.",
        ("انقطاع قناة", "غياب إشارة"),
        ("tests/crown/test_crown_continuity.py::test_isolation_is_not_absence",),
    ),
    _t(
        "THR-U",
        "اختراق متزامن لأنظمة متعددة",
        ThreatDomain.RUNTIME,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.PARTIALLY_IMPLEMENTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "سقوط عدة أنظمة معًا لإرباك الارتباط وإخفاء الحدث الحقيقي.",
        ("تنبيهات متزامنة", "فقد نبض عدة طبقات"),
        ("tests/crown/test_crown_grand_tests.py::test_simultaneous_compromise_escalates",),
        notes="الاسترداد الكامل من سقوط شامل يحتاج مراسم بشرية خارج الشبكة.",
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
# الفئة الثانية: البند 23 — تهديدات على الإنسان لا يحلّها كود.
# ─────────────────────────────────────────────────────────────────────────────

_HUMAN_THREATS: Final[tuple[Threat, ...]] = (
    _t(
        "THR-V",
        "الإكراه",
        ThreatDomain.PSYCHOLOGICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.DIGITAL_TRACE_ONLY,
        MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
        ResponsibleParty.TRUSTED_HUMAN_SECURITY,
        "توقيع صحيح تحت التهديد. التوقيع سليم والنيّة مسلوبة.",
        ("نمط أوامر شاذ", "وقت غير معتاد", "تسلسل مراسم متعجّل"),
        notes="أثر رقمي مرفوع إلى بشر، لا حكم برمجي على الإكراه.",
    ),
    _t(
        "THR-W",
        "فقد القدرة",
        ThreatDomain.MEDICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
        ResponsibleParty.MEDICAL_PROFESSIONALS,
        "عجز مؤقت أو دائم. لا يُستنتج من صمت رقمي ولا يُقرَّر برمجيًّا.",
        notes="يُعلَن بشريًّا بمستند طبي ومراسم، ولا يُنتج خليفة تلقائيًّا.",
    ),
    _t(
        "THR-X",
        "التسميم والتلاعب الطبي",
        ThreatDomain.MEDICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
        ResponsibleParty.MEDICAL_PROFESSIONALS,
        "إضرار جسدي بالحامل — خارج قدرة البرمجية كليًّا.",
        notes="المستودع يحفظ واجهة إبلاغ لجهة طبية مختصة، ولا يدّعي كشفًا.",
    ),
    _t(
        "THR-Y",
        "التلاعب العصبي",
        ThreatDomain.MEDICAL,
        ThreatHorizon.EMERGING,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.MEDICAL_PROFESSIONALS,
        "تأثير في الإدراك أو القرار بوسائل عصبية.",
    ),
    _t(
        "THR-Z",
        "التضليل المعلوماتي",
        ThreatDomain.PSYCHOLOGICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.PARTIALLY_IMPLEMENTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "تزييف الصورة التي يرى الملك بها دولته، فيقرر صحيحًا على معطى فاسد.",
        ("تعارض بين مصادر", "انكسار سلسلة سجل", "مسار عرض غير موثَّق"),
        ("tests/crown/test_crown_threat_model.py::test_audit_chain_detects_tampering",),
    ),
    _t(
        "THR-AA",
        "العزل والحجب",
        ThreatDomain.PSYCHOLOGICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.DIGITAL_TRACE_ONLY,
        MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
        ResponsibleParty.TRUSTED_HUMAN_SECURITY,
        "فصل الملك عن محيطه ووسائطه ليُستنتج غيابه.",
        ("فقد قنوات متعددة معًا",),
    ),
    _t(
        "THR-AB",
        "الحرمان وتشويش الانتباه",
        ThreatDomain.PSYCHOLOGICAL,
        ThreatHorizon.PRESENT,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
        ResponsibleParty.TRUSTED_HUMAN_SECURITY,
        "الحرمان من النوم أو إغراق الانتباه لإفساد القرار.",
    ),
    _t(
        "THR-AC",
        "زرعات غير مصرَّح بها",
        ThreatDomain.MEDICAL,
        ThreatHorizon.EMERGING,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.MEDICAL_PROFESSIONALS,
        "أجهزة مزروعة بلا إذن قد تؤثر في الإدراك أو تنقل بيانات.",
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
# الفئة الثالثة: البند 24 — تقنيات المستقبل. تُنمَذج فئةً، ولا يُدَّعى تنفيذ.
# ─────────────────────────────────────────────────────────────────────────────

_FUTURE_THREATS: Final[tuple[Threat, ...]] = (
    _t(
        "THR-AD",
        "ذكاء اصطناعي متقدم",
        ThreatDomain.AGENT_BEHAVIOR,
        ThreatHorizon.ANTICIPATED,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "منظومة تتجاوز قدرة المراقبة على تفسير سلوكها.",
        ("سلوك غير مفسَّر", "قدرات لم تُصرَّح"),
    ),
    _t(
        "THR-AE",
        "واجهات دماغ-حاسوب",
        ThreatDomain.MEDICAL,
        ThreatHorizon.ANTICIPATED,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "قناة بين الإدراك والآلة قد تُنتحل أو تُوجَّه.",
    ),
    _t(
        "THR-AF",
        "الوسائط المصنَّعة",
        ThreatDomain.IDENTITY,
        ThreatHorizon.PRESENT,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.PARTIALLY_IMPLEMENTED,
        ResponsibleParty.SOFTWARE_ASSISTED_HUMAN,
        "صوت وصورة مقنعان للملك — ولذلك لا تكون الوسائط سندًا لأمر سيادي.",
        ("أمر بلا توقيع مفتاح", "استناد إلى وسيط بصري أو صوتي"),
        ("tests/crown/test_crown_threat_model.py::test_media_is_not_authority",),
    ),
    _t(
        "THR-AG",
        "أنظمة سيبرانية ذاتية",
        ThreatDomain.RUNTIME,
        ThreatHorizon.ANTICIPATED,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "مهاجم آلي يعمل بسرعة تفوق دورة الاستجابة البشرية.",
    ),
    _t(
        "THR-AH",
        "الحوسبة الكمّية",
        ThreatDomain.CRYPTOGRAPHIC,
        ThreatHorizon.ANTICIPATED,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "كسر التوقيع الحالي مستقبلًا. والمعالجة المنفَّذة اليوم مرونة خوارزمية "
        "وترقيم نسخ لا إبدالٌ بلا دليل (البند 25).",
        ("خوارزمية غير مدعومة", "نسخة بيان قديمة"),
        notes="مرونة الخوارزميات منفَّذة ومختبَرة؛ أما التوقيع بعد الكمّي فغير منفَّذ.",
    ),
    _t(
        "THR-AI",
        "تقنيات النانو",
        ThreatDomain.PHYSICAL,
        ThreatHorizon.SPECULATIVE,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "تدخل مادي دقيق في العتاد أو في الإنسان.",
    ),
    _t(
        "THR-AJ",
        "حالات تخمينية (كالسفر في الزمن)",
        ThreatDomain.SPECULATIVE,
        ThreatHorizon.SPECULATIVE,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "تحفظ كحالة مفهومية للتفكير في سلامة التاريخ، ولا يُدَّعى ضدها تنفيذ. "
        "وأقرب أثر واقعي لها: الاعتماد على سلاسل مقيَّدة زمنيًّا وسجل غير قابل للمحو.",
        notes="مُنمذَجة فقط. أي ادّعاء حماية هنا كذبة صريحة يمنعها البند 52.",
    ),
    _t(
        "THR-AK",
        "بروتوكولات هوية جديدة",
        ThreatDomain.IDENTITY,
        ThreatHorizon.EMERGING,
        DetectionCapability.PARTIALLY_DETECTABLE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "معايير هوية قادمة قد تُدخِل ثقة ضمنية في جهة خارجية.",
    ),
    _t(
        "THR-AL",
        "قنوات اتصال أو استشعار مجهولة",
        ThreatDomain.COMMUNICATIONS,
        ThreatHorizon.SPECULATIVE,
        DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
        MitigationStatus.MODELLED_NOT_IMPLEMENTED,
        ResponsibleParty.UNKNOWN_FUTURE,
        "مسارات تسريب أو تأثير لا تعرفها المنظومة أصلًا.",
    ),
)


ALL_THREATS: Final[tuple[Threat, ...]] = (
    _SCENARIO_THREATS + _HUMAN_THREATS + _FUTURE_THREATS
)

THREATS_BY_ID: Final[dict[str, Threat]] = {t.threat_id: t for t in ALL_THREATS}

DETECTABLE_BY_SOFTWARE: Final[tuple[str, ...]] = tuple(
    t.threat_id
    for t in ALL_THREATS
    if t.detection is DetectionCapability.DETECTABLE_BY_SOFTWARE
)

REQUIRES_HUMAN: Final[tuple[str, ...]] = tuple(
    t.threat_id for t in ALL_THREATS if t.requires_human_response
)


def threat(threat_id: str) -> Threat:
    """استرجع تهديدًا بمعرّفه أو ارفع خطأً واضحًا."""
    try:
        return THREATS_BY_ID[threat_id]
    except KeyError as exc:
        raise ThreatModelError(f"تهديد غير معروف: {threat_id}") from exc


def register_threat(new_threat: Threat) -> None:
    """أضف تهديدًا إلى التصنيف — التصنيف قابل للتوسعة بحكم البند 24.

    ولا يُقبل معرّف مكرر: تهديدان بمعرّف واحد يُخفي أحدهما الآخر في التقارير.
    """
    if new_threat.threat_id in THREATS_BY_ID:
        raise ThreatModelError(
            f"معرّف تهديد مكرر: {new_threat.threat_id}."
        )
    THREATS_BY_ID[new_threat.threat_id] = new_threat


def by_domain(domain: ThreatDomain) -> tuple[Threat, ...]:
    return tuple(t for t in THREATS_BY_ID.values() if t.domain is domain)


def by_status(status: MitigationStatus) -> tuple[Threat, ...]:
    return tuple(t for t in THREATS_BY_ID.values() if t.mitigation_status is status)


def unresolved_threats() -> tuple[Threat, ...]:
    """التهديدات التي لا حماية منفَّذة لها — تُعلَن ولا تُخفى."""
    return tuple(
        t
        for t in THREATS_BY_ID.values()
        if t.mitigation_status
        in {
            MitigationStatus.MODELLED_NOT_IMPLEMENTED,
            MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
        }
    )


def boundary_report() -> dict[str, Any]:
    """تقرير حدّ البرمجية من البشر — البند 23 مطلوبًا صريحًا."""
    return {
        "total_threats": len(THREATS_BY_ID),
        "detectable_by_software": len(
            [
                t
                for t in THREATS_BY_ID.values()
                if t.detection is DetectionCapability.DETECTABLE_BY_SOFTWARE
            ]
        ),
        "requires_human": len(
            [t for t in THREATS_BY_ID.values() if t.requires_human_response]
        ),
        "implemented_and_tested": len(
            by_status(MitigationStatus.IMPLEMENTED_AND_TESTED)
        ),
        "partially_implemented": len(by_status(MitigationStatus.PARTIALLY_IMPLEMENTED)),
        "modelled_not_implemented": len(
            by_status(MitigationStatus.MODELLED_NOT_IMPLEMENTED)
        ),
        "out_of_software_scope": len(by_status(MitigationStatus.OUT_OF_SOFTWARE_SCOPE)),
        "by_domain": {
            d.value: len(by_domain(d)) for d in ThreatDomain if by_domain(d)
        },
    }


def coverage_matrix() -> tuple[dict[str, Any], ...]:
    """مصفوفة التغطية: كل تهديد بحاله ومن يملكه ومرجع اختباره."""
    return tuple(
        {
            "threat_id": t.threat_id,
            "title": t.title,
            "domain": t.domain.value,
            "horizon": t.horizon.value,
            "detection": t.detection.value,
            "mitigation_status": t.mitigation_status.value,
            "responsible": t.responsible.value,
            "test_refs": list(t.test_refs),
        }
        for t in sorted(THREATS_BY_ID.values(), key=lambda x: x.threat_id)
    )


__all__ = [
    "ALL_THREATS",
    "DETECTABLE_BY_SOFTWARE",
    "REQUIRES_HUMAN",
    "THREATS_BY_ID",
    "DetectionCapability",
    "FalseMitigationClaimError",
    "MitigationStatus",
    "ResponsibleParty",
    "Threat",
    "ThreatDomain",
    "ThreatHorizon",
    "ThreatModelError",
    "boundary_report",
    "by_domain",
    "by_status",
    "coverage_matrix",
    "register_threat",
    "threat",
    "unresolved_threats",
]
