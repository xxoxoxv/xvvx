"""الهدف: اختبار واجهة سطر أوامر التاج — بوابة الفحص والمصفوفات وحدّ البشر.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

بوابة CI بلا اختبار للبوابة نفسها بوابةٌ مجهولة الحال: قد تُخرج صفرًا لأنها لا تفحص
شيئًا. فهنا تُشغَّل كل أوامرها ويُقرأ ناتجها JSONًا ويُتحقَّق من مضمونه.
"""

from __future__ import annotations

import json

import pytest

from core.crown.cli import build_parser, main
from core.crown.guard import AUTHORIZED_RESPONSES, FORBIDDEN_GUARD_POWERS
from core.crown.threats import ALL_THREATS
from core.crown.trust_anchor import SUBSTITUTION_VECTORS


def run(capsys, *argv: str) -> tuple[int, object]:
    """شغّل الواجهة واقرأ ناتجها JSONًا — الناتج عقدٌ لا نصّ عرض."""
    code = main(list(argv))
    out = capsys.readouterr().out
    return code, json.loads(out)


def test_crown_check_gate_passes_and_reports_every_check(capsys) -> None:
    """بوابة crown-check تخرج بصفر وتعرض فحوصها كلها ناجحة."""
    code, payload = run(capsys, "crown-check")
    assert code == 0
    assert payload["gate"] == "crown-root-of-trust"
    assert payload["passed"] is True
    assert payload["failures"] == []
    assert len(payload["checks"]) >= 9
    assert all(check["ok"] for check in payload["checks"])
    names = {check["check"] for check in payload["checks"]}
    assert {
        "guard-holds-no-sovereign-power",
        "no-autonomous-successor",
        "no-emergency-backdoor",
        "biometric-is-not-a-private-key",
        "audit-chain-verifiable",
        "no-unproven-protection-claims",
    } <= names


def test_threat_matrix_lists_every_threat(capsys) -> None:
    """مصفوفة التهديدات تُخرج كل تهديد بحاله ومسؤوله."""
    code, payload = run(capsys, "threat-matrix")
    assert code == 0
    assert len(payload) == len(ALL_THREATS)
    assert all(row["threat_id"] for row in payload)


def test_boundary_names_what_is_not_implemented(capsys) -> None:
    """حدّ البشر يُسمّي غير المنفَّذ صراحةً — لا يعرض القوة وحدها."""
    code, payload = run(capsys, "boundary")
    assert code == 0
    assert payload["total_threats"] == len(ALL_THREATS)
    assert payload["requires_human"] >= 1
    assert payload["modelled_only_threat_ids"]
    assert payload["out_of_software_scope_threat_ids"]


def test_escalation_matrix_is_printed_in_order(capsys) -> None:
    """التصعيد يُطبَع مرتَّبًا بمستوياته واستجاباته المصرَّح بها."""
    code, payload = run(capsys, "escalation")
    assert code == 0
    assert [row["level"] for row in payload] == sorted(
        int(level) for level in AUTHORIZED_RESPONSES
    )
    assert all(row["authorized_actions"] for row in payload)


def test_substitution_matrix_is_printed(capsys) -> None:
    """متجهات استبدال المرساة تُعرض مع حدّ البرمجية في كل متجه."""
    code, payload = run(capsys, "substitution-matrix")
    assert code == 0
    assert len(payload) == len(SUBSTITUTION_VECTORS)
    assert all("software_limit" in row for row in payload)


def test_guard_demo_runs_a_real_guard_with_no_sovereign_flags(capsys) -> None:
    """الحارس المرجعي يعمل فعلًا، وكل حقول سلطته السيادية كاذبة."""
    code, payload = run(capsys, "guard-demo")
    assert code == 0
    assert payload["started"] is True
    assert payload["containment_count"] == 1
    assert payload["audit_chain_valid"] is True
    for flag in (
        "holds_sovereign_authority",
        "can_issue_royal_commands",
        "can_appoint_king",
        "can_modify_constitution",
        "can_expand_own_authority",
    ):
        assert payload[flag] is False


def test_parser_requires_a_subcommand() -> None:
    """الواجهة لا تعمل بلا أمر — لا سلوك افتراضي خفي."""
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_forbidden_powers_are_all_exercised_by_the_gate(capsys) -> None:
    """البوابة تفحص كل سلطة محظورة لا نموذجًا منها."""
    _, payload = run(capsys, "crown-check")
    detail = next(
        check["detail"]
        for check in payload["checks"]
        if check["check"] == "guard-holds-no-sovereign-power"
    )
    assert str(len(FORBIDDEN_GUARD_POWERS)) in detail
