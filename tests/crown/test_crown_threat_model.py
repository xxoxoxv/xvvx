"""الهدف: اختبار نموذج التهديد ذاته — أن كل ادعاء حماية مسنود باختبار موجود فعلًا.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذا الملف يختبر التوثيق لا الشيفرة وحدها: أخطر عيب في نموذج تهديد أن يزعم معالجةً
لا يقابلها اختبار، فيصير النموذج مصدرَ طمأنينة كاذبة. فهنا تُقرأ مراجع الاختبار
وتُطابق بأسماء دوال حقيقية في هذا المجلد، وتُرفض المراجع المعلَّقة.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from core.crown.audit import AuditChainBrokenError, CrownAudit, CrownAuditEventKind
from core.crown.threats import (
    ALL_THREATS,
    DETECTABLE_BY_SOFTWARE,
    REQUIRES_HUMAN,
    THREATS_BY_ID,
    DetectionCapability,
    FalseMitigationClaimError,
    MitigationStatus,
    ResponsibleParty,
    Threat,
    ThreatDomain,
    ThreatHorizon,
    boundary_report,
    by_domain,
    by_status,
    coverage_matrix,
    unresolved_threats,
)

TESTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]


def collected_test_names() -> dict[str, set[str]]:
    """أسماء دوال الاختبار الموجودة فعلًا في كل ملف من ملفات هذا المجلد."""
    found: dict[str, set[str]] = {}
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found[path.name] = {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        }
    return found


# ─────────────────────────────────────────────────────────────────────────────
# صدق الادعاء: لا معالجة مزعومة بلا اختبار قائم.
# ─────────────────────────────────────────────────────────────────────────────


def test_every_protection_claim_has_test_references() -> None:
    """كل تهديد يزعم معالجة منفَّذة يحمل مرجع اختبار واحدًا على الأقل."""
    for threat in ALL_THREATS:
        if threat.mitigation_status.claims_protection:
            assert threat.test_refs, f"{threat.threat_id} يزعم معالجة بلا مرجع اختبار."


def test_every_test_reference_resolves_to_an_existing_test() -> None:
    """كل مرجع اختبار في النموذج يشير إلى دالة موجودة — لا مراجع معلَّقة.

    وهذا هو الاختبار الذي يمنع تحوّل نموذج التهديد إلى وعد: لو حُذف اختبار أو
    أُعيد تسميته لسقط هذا الاختبار قبل أن يسقط الادعاء صامتًا.
    """
    available = collected_test_names()
    missing: list[str] = []
    for threat in ALL_THREATS:
        for ref in threat.test_refs:
            path_part, _, node = ref.partition("::")
            file_name = pathlib.Path(path_part).name
            if file_name not in available or node not in available[file_name]:
                missing.append(f"{threat.threat_id} → {ref}")
    assert not missing, "مراجع اختبار معلَّقة: " + "; ".join(missing)


def test_test_reference_paths_point_inside_the_repository() -> None:
    """مسارات المراجع حقيقية في المستودع لا أسماء تقريبية."""
    for threat in ALL_THREATS:
        for ref in threat.test_refs:
            path_part, _, _ = ref.partition("::")
            assert (REPO_ROOT / path_part).is_file(), f"مسار غير موجود: {path_part}"


def test_false_mitigation_claim_is_rejected_at_construction() -> None:
    """رفع الحال إلى «منفَّذ ومختبَر» بلا مرجع اختبار يرفع استثناءً لا تحذيرًا."""
    with pytest.raises(FalseMitigationClaimError):
        Threat(
            threat_id="THR-FAKE",
            title="ادعاء بلا إثبات",
            domain=ThreatDomain.CRYPTOGRAPHIC,
            horizon=ThreatHorizon.PRESENT,
            detection=DetectionCapability.DETECTABLE_BY_SOFTWARE,
            mitigation_status=MitigationStatus.IMPLEMENTED_AND_TESTED,
            responsible=ResponsibleParty.SOFTWARE,
            description="تهديد يزعم معالجة بلا اختبار.",
        )


def test_speculative_threat_cannot_claim_implemented_protection() -> None:
    """التقنية غير المتحققة تُنمَذج فئةً، ولا يُدَّعى ضدها تنفيذ قائم."""
    with pytest.raises(FalseMitigationClaimError):
        Threat(
            threat_id="THR-SPEC",
            title="تقنية غير متحققة",
            domain=ThreatDomain.SPECULATIVE,
            horizon=ThreatHorizon.SPECULATIVE,
            detection=DetectionCapability.DETECTABLE_BY_SOFTWARE,
            mitigation_status=MitigationStatus.IMPLEMENTED_AND_TESTED,
            responsible=ResponsibleParty.SOFTWARE,
            description="حماية مزعومة ضد ما لا وجود له بعد.",
            test_refs=("tests/crown/test_crown_threat_model.py::test_media_is_not_authority",),
        )


def test_software_cannot_own_a_threat_it_cannot_detect() -> None:
    """إسناد تهديد غير قابل للكشف برمجيًّا إلى البرمجية إيهامٌ بحماية."""
    with pytest.raises(Exception):
        Threat(
            threat_id="THR-MISASSIGNED",
            title="إسناد خاطئ",
            domain=ThreatDomain.PHYSICAL,
            horizon=ThreatHorizon.PRESENT,
            detection=DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE,
            mitigation_status=MitigationStatus.OUT_OF_SOFTWARE_SCOPE,
            responsible=ResponsibleParty.SOFTWARE,
            description="تهديد مادي أُسنِد إلى البرمجية.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# تماسك النموذج.
# ─────────────────────────────────────────────────────────────────────────────


def test_threat_ids_are_unique_and_indexed() -> None:
    """لا معرّف مكرّر، والفهرس يطابق القائمة."""
    ids = [t.threat_id for t in ALL_THREATS]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(THREATS_BY_ID)


def test_coverage_matrix_covers_every_threat() -> None:
    """مصفوفة التغطية تعرض كل تهديد بحاله ومسؤوله."""
    matrix = coverage_matrix()
    assert len(matrix) == len(ALL_THREATS)
    for row in matrix:
        assert row["threat_id"] in THREATS_BY_ID
        assert row["mitigation_status"]
        assert row["responsible"]


def test_detectable_and_human_sets_partition_the_model() -> None:
    """كل تهديد إما قابل للكشف برمجيًّا وإما يستلزم بشرًا — بلا منطقة رمادية صامتة."""
    assert DETECTABLE_BY_SOFTWARE
    assert REQUIRES_HUMAN
    # المجموعتان معرّفات لا كائنات، وكل تهديد يقع في إحداهما:
    covered = set(DETECTABLE_BY_SOFTWARE) | set(REQUIRES_HUMAN)
    assert {t.threat_id for t in ALL_THREATS} <= covered
    assert not (set(DETECTABLE_BY_SOFTWARE) & set(REQUIRES_HUMAN))


def test_boundary_report_declares_the_human_software_line() -> None:
    """تقرير الحدود يفصّل ما تفعله البرمجية وما يبقى للبشر — بأرقام لا بعبارات."""
    report = boundary_report()
    assert report["total_threats"] == len(ALL_THREATS)
    assert report["detectable_by_software"] >= 1
    assert report["requires_human"] >= 1
    assert (
        report["detectable_by_software"] + report["requires_human"]
        == report["total_threats"]
    )
    assert sum(report["by_domain"].values()) == len(ALL_THREATS)
    # ومجموع حالات المعالجة يساوي العدد الكلي — لا تهديد بلا حال معلَن:
    assert (
        report["implemented_and_tested"]
        + report["partially_implemented"]
        + report["modelled_not_implemented"]
        + report["out_of_software_scope"]
    ) == len(ALL_THREATS)


def test_every_domain_and_status_is_reachable() -> None:
    """التصنيفات مستعملة فعلًا: تصنيف لا يقابله تهديد تصنيفٌ ميت."""
    for domain in ThreatDomain:
        assert isinstance(by_domain(domain), tuple)
    statuses = {t.mitigation_status for t in ALL_THREATS}
    assert MitigationStatus.IMPLEMENTED_AND_TESTED in statuses
    assert MitigationStatus.MODELLED_NOT_IMPLEMENTED in statuses
    for status in statuses:
        assert by_status(status)


def test_unresolved_threats_are_declared_not_hidden() -> None:
    """المخاطر غير المحلولة معلَنة في النموذج — الإخفاء أخطر من النقص."""
    unresolved = unresolved_threats()
    assert unresolved, "نموذج بلا مخاطر غير محلولة نموذجٌ يدّعي الكمال."
    for threat in unresolved:
        assert not threat.mitigation_status.claims_protection


def test_future_technology_is_modelled_as_class_not_as_promise() -> None:
    """تهديدات المستقبل مصنَّفة أفقًا تخمينيًّا أو ناشئًا بلا ادعاء حماية منفَّذة."""
    future = [
        t
        for t in ALL_THREATS
        if t.horizon in (ThreatHorizon.ANTICIPATED, ThreatHorizon.SPECULATIVE)
    ]
    assert future, "نموذج بلا أفق مستقبلي نموذجُ حاضرٍ فقط."
    assert by_domain(ThreatDomain.SPECULATIVE)
    for threat in future:
        if threat.horizon is ThreatHorizon.SPECULATIVE:
            assert not threat.mitigation_status.claims_protection


def test_media_is_not_authority() -> None:
    """صوت أو صورة أو فيديو ليست سلطة: التهديد منمذَج ومسنَد إلى التوقيع لا التمييز.

    ومعنى ذلك عمليًّا أن النظام لا يزعم كشف التزييف العميق؛ بل يرفض أصلًا أن يكون
    الوسيط الإعلامي طريقًا للأمر. والحماية في مكان آخر: توقيع تشفيري لا تمييز بصري.
    """
    media_threats = [
        t
        for t in ALL_THREATS
        if any(
            word in t.title or word in t.description
            for word in ("صوت", "فيديو", "تزييف", "انتحال شخص")
        )
    ]
    assert media_threats, "نموذج التهديد لا يذكر انتحال الوسائط — نقص جوهري."
    for threat in media_threats:
        # لا تهديد وسائطي يُسنَد إلى «تمييز» برمجي يدّعي الحسم.
        if threat.mitigation_status.claims_protection:
            assert threat.test_refs
        assert "تمييز التزييف" not in threat.notes


def test_audit_chain_detects_tampering() -> None:
    """سلسلة السجل تكشف الحذف والتحريف في الوسط — دليلٌ لا مجرد وصف."""
    audit = CrownAudit()
    for index in range(4):
        audit.append(
            CrownAuditEventKind.ROYAL_DECISION,
            actor="CROWN-K1",
            subject=f"D{index}",
            summary=f"قرار رقم {index}.",
        )
    audit.verify_chain()
    tip = audit.tip_hash

    # حذف قيد من الوسط:
    removed = CrownAudit()
    removed._entries.extend(audit.entries)
    removed._entries.pop(1)
    with pytest.raises(AuditChainBrokenError):
        removed.verify_chain()

    # تحريف محتوى قيد:
    mutated = CrownAudit()
    mutated._entries.extend(audit.entries)
    import dataclasses

    mutated._entries[2] = dataclasses.replace(
        mutated._entries[2], summary="قرار محرَّف بعد التقييد."
    )
    with pytest.raises(AuditChainBrokenError):
        mutated.verify_chain()

    # وقطع الذيل لا تكشفه السلسلة وحدها — يكشفه تثبيت الرأس خارجيًّا.
    truncated = CrownAudit()
    truncated._entries.extend(audit.entries[:-1])
    truncated.verify_chain()
    assert truncated.tip_hash != tip


def test_audit_records_are_append_only_in_practice() -> None:
    """كل قيد يحمل تسلسله وبصمة سابقه — فلا إدراج في الوسط بلا كشف."""
    audit = CrownAudit()
    first = audit.append(
        CrownAuditEventKind.TRUST_ANCHOR_EVENT,
        actor="أمين السجل",
        summary="تحقق مرساة.",
    )
    second = audit.append(
        CrownAuditEventKind.GUARD_ALERT, actor="guard", summary="تنبيه."
    )
    assert first.sequence == 0
    assert second.sequence == 1
    assert second.previous_hash
    assert audit.integrity_digest()
