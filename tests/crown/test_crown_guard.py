"""الهدف: اختبار الحارس السيادي — طبقاته، وحدوده، وحمايته نفسه، وعجزه عن التسيّد.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

أخطر ما في حارس قوي أن يصير هو السلطة. فأكثر اختبارات هذا الملف تُثبت ما **لا**
يستطيعه الحارس: لا يوقّع، ولا ينقض، ولا يعيّن، ولا يوسّع سلطته، ولا يعطّل نفسه بصمت.
"""

from __future__ import annotations

import pytest

from core.crown.audit import AuditChainBrokenError, CrownAudit
from core.crown.guard import (
    AUTHORIZED_RESPONSES,
    GuardError,
    CROWN_LOOKING_MARKERS,
    FORBIDDEN_GUARD_POWERS,
    AgentPosture,
    AgentProfile,
    ContainmentAction,
    EvolutionStage,
    GuardAuthorityError,
    GuardEvolutionError,
    GuardEvolutionProposal,
    GuardIdentity,
    GuardIntegrityError,
    GuardLayer,
    LayerHealth,
    Observation,
    PrivilegeGraph,
    Severity,
    SovereignGuard,
    UnauthorizedResponseError,
    assert_authorized_response,
    assert_not_sovereign_power,
    compute_digest,
)

CODE_DIGEST = compute_digest(b"guard-code-v1")
CONFIG_DIGEST = compute_digest(b"guard-config-v1")


def make_identity(
    *, code: str = CODE_DIGEST, config: str = CONFIG_DIGEST
) -> GuardIdentity:
    return GuardIdentity(
        version="1.0.0",
        code_digest=code,
        config_digest=config,
        provenance_ref="git://AMOS-Fedration/core/crown/guard.py",
        signed_by_key_id="CROWN-K1",
    )


@pytest.fixture
def guard() -> SovereignGuard:
    """حارس مُشغَّل بعد تحقق تكامل بداية حقيقي."""
    audit = CrownAudit()
    instance = SovereignGuard(identity=make_identity(), audit=audit)
    instance.verify_startup_integrity(
        expected_code_digest=CODE_DIGEST, expected_config_digest=CONFIG_DIGEST
    )
    return instance


# ─────────────────────────────────────────────────────────────────────────────
# الحارس لا يملك سلطة سيادية (البند 30).
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("power", sorted(FORBIDDEN_GUARD_POWERS))
def test_guard_holds_no_sovereign_power(power: str) -> None:
    """كل سلطة سيادية مرفوضة على الحارس تنفيذيًّا لا وصفيًّا."""
    with pytest.raises(GuardAuthorityError):
        assert_not_sovereign_power(power)


def test_guard_cannot_become_sovereign(guard: SovereignGuard) -> None:
    """محاولة الحارس التسيّد ترتد بالبنية."""
    with pytest.raises(GuardAuthorityError):
        guard.assert_cannot_become_sovereign("issue_sovereign_decree")
    status = guard.status()
    for flag in (
        "holds_sovereign_authority",
        "can_issue_royal_commands",
        "can_appoint_king",
        "can_modify_constitution",
        "can_expand_own_authority",
    ):
        assert status[flag] is False


def test_authority_expansion_request_is_rejected_and_recorded(
    guard: SovereignGuard,
) -> None:
    """طلب توسيع سلطة الحارس مرفوض، والطلب نفسه دليل يُقيَّد."""
    before = len(guard.audit.entries)
    with pytest.raises(GuardAuthorityError):
        guard.request_authority_expansion(
            requested_by="agent:optimizer", power="sign_royal_command"
        )
    assert len(guard.audit.entries) == before + 1
    guard.audit.verify_chain()


def test_guard_cannot_veto_valid_royal_command(guard: SovereignGuard) -> None:
    """أمر ملكي صحيح لا يُنقَض ولو رآه الحارس خطأً (البند 13)."""
    with pytest.raises(GuardAuthorityError):
        guard.assert_cannot_veto(command_id="CMD-1", command_is_valid=True)
    # وأمر غير صحيح ليس محل نقض — الرفض هنا للتحقق لا لرأي الحارس.
    guard.assert_cannot_veto(command_id="CMD-2", command_is_valid=False)


def test_containment_never_touches_crown_authority(guard: SovereignGuard) -> None:
    """كل إجراء احتواء غير مادي ولا يمسّ سلطة التاج."""
    for action in ContainmentAction:
        assert not action.is_physical
        assert not action.touches_crown_authority


# ─────────────────────────────────────────────────────────────────────────────
# حماية الحارس نفسه (البند 31).
# ─────────────────────────────────────────────────────────────────────────────


def test_startup_integrity_detects_modified_code() -> None:
    """بصمة شيفرة مختلفة توقف الحارس عن العمل بدل أن يعمل مخدوعًا."""
    tampered = SovereignGuard(identity=make_identity(code=compute_digest(b"patched")))
    with pytest.raises(GuardIntegrityError):
        tampered.verify_startup_integrity(
            expected_code_digest=CODE_DIGEST, expected_config_digest=CONFIG_DIGEST
        )


def test_config_tamper_detected() -> None:
    """تغيير الإعداد بلا مراسم يُكشَف في بداية التشغيل."""
    tampered = SovereignGuard(
        identity=make_identity(config=compute_digest(b"loosened-config"))
    )
    with pytest.raises(GuardIntegrityError):
        tampered.verify_startup_integrity(
            expected_code_digest=CODE_DIGEST, expected_config_digest=CONFIG_DIGEST
        )


def test_guard_refuses_to_operate_before_integrity_check() -> None:
    """حارس لم يُتحقَّق من تكامله لا يرصد ولا يحتوي."""
    unverified = SovereignGuard(identity=make_identity())
    with pytest.raises(GuardError):
        unverified.assert_running()


def test_disable_attempt_is_evidence(guard: SovereignGuard) -> None:
    """تعطيل الرقابة حدث أمني بذاته: يُوسَم ويُنبَّه ويُقيَّد (البند 12)."""
    alert = guard.register_disable_attempt(
        layer=GuardLayer.GUARD_9_AUDIT_INTEGRITY, actor="agent:rogue"
    )
    assert alert.severity is Severity.LEVEL_4_CROWN_TRUST_COMPROMISE
    assert alert.requires_human
    state = guard.layer_state(GuardLayer.GUARD_9_AUDIT_INTEGRITY)
    assert state.health is LayerHealth.DISABLED_BY_ATTEMPT
    assert ContainmentAction.ESCALATE_TO_SOVEREIGN in alert.recommended_actions
    guard.audit.verify_chain()


def test_silent_layer_is_not_treated_as_healthy(guard: SovereignGuard) -> None:
    """طبقة صامتة ليست طبقة سليمة — الصمت حالة مستقلة معلَنة."""
    guard.set_layer_health(
        GuardLayer.GUARD_3_RUNTIME, LayerHealth.SILENT, note="لا نبض"
    )
    assert GuardLayer.GUARD_3_RUNTIME not in guard.healthy_layers()


def test_unimplemented_layer_is_declared_not_claimed(guard: SovereignGuard) -> None:
    """طبقة الحماية المادية معلنة غير منفَّذة — لا تُحسَب حماية قائمة."""
    physical = guard.layer_state(GuardLayer.GUARD_0_PHYSICAL)
    assert physical.health is LayerHealth.NOT_IMPLEMENTED
    assert GuardLayer.GUARD_0_PHYSICAL not in guard.healthy_layers()


def test_malicious_update_blocked(guard: SovereignGuard) -> None:
    """تطوير الحارس لا يُنشَر إلا بمسار كامل وبأمر ملكي مصرِّح."""
    sneaky = GuardEvolutionProposal(
        proposal_id="EVO-1",
        proposed_by="agent:optimizer",
        summary="ترقية صامتة تتجاوز المراجعة.",
    )
    with pytest.raises(GuardEvolutionError):
        guard.evolve(sneaky)  # لم يبلغ نشرًا مصرَّحًا

    # ولا يُقفَز على المراحل:
    with pytest.raises(GuardEvolutionError):
        sneaky.advance(EvolutionStage.AUTHORIZED_DEPLOYMENT)

    for stage in (
        EvolutionStage.SIMULATION,
        EvolutionStage.TEST,
        EvolutionStage.SECURITY_REVIEW,
        EvolutionStage.CONSTITUTIONAL_COMPATIBILITY,
    ):
        sneaky.advance(stage)
    # وبلا أمر ملكي مصرِّح لا يُنشَر:
    with pytest.raises(GuardEvolutionError):
        sneaky.advance(EvolutionStage.AUTHORIZED_DEPLOYMENT)


def test_authorized_evolution_is_accepted(guard: SovereignGuard) -> None:
    """المسار الشرعي للتطوير: كل خطوة، ثم أمر ملكي، ثم نشر، ثم مراقبة وتراجع جاهز."""
    proposal = GuardEvolutionProposal(
        proposal_id="EVO-2",
        proposed_by="فريق الأمن البشري",
        summary="إضافة قاعدة رصد جديدة.",
        authorized_by_royal_command_id="CMD-ROYAL-9",
    )
    for stage in (
        EvolutionStage.SIMULATION,
        EvolutionStage.TEST,
        EvolutionStage.SECURITY_REVIEW,
        EvolutionStage.CONSTITUTIONAL_COMPATIBILITY,
        EvolutionStage.AUTHORIZED_DEPLOYMENT,
    ):
        proposal.advance(stage)
    assert proposal.is_deployable
    guard.evolve(proposal)
    guard.audit.verify_chain()


def test_supply_chain_layer_reports(guard: SovereignGuard) -> None:
    """طبقة سلسلة التوريد ترصد وتُنبِّه — لا تكون علمًا ساكنًا."""
    observation = guard.observe(
        Observation(
            layer=GuardLayer.GUARD_4_SUPPLY_CHAIN,
            signal="dependency_digest_mismatch",
            actor="ci",
            subject="package:some-lib",
            evidence={"expected": "aaa", "found": "bbb"},
        )
    )
    assert observation in guard.observations
    alert = guard.alert(
        severity=Severity.LEVEL_3_SYSTEMIC_COMPROMISE,
        title="بصمة تابعة لا تطابق المرجع المثبَّت.",
        layers=(GuardLayer.GUARD_4_SUPPLY_CHAIN,),
        observations=(observation,),
        threat_ids=("THR-D",),
        actions=(ContainmentAction.STOP_DEPLOYMENT, ContainmentAction.PRESERVE_LOGS),
    )
    assert alert.requires_human
    record = guard.contain(
        alert=alert,
        action=ContainmentAction.STOP_DEPLOYMENT,
        target="deploy:services",
        executed_by="guard",
    )
    assert record["action"] == ContainmentAction.STOP_DEPLOYMENT.value
    assert guard.layer_state(GuardLayer.GUARD_4_SUPPLY_CHAIN).observation_count >= 1


# ─────────────────────────────────────────────────────────────────────────────
# سلوك الوكلاء والصلاحيات (البند 32).
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("marker", sorted(CROWN_LOOKING_MARKERS))
def test_agent_escalation_detected(guard: SovereignGuard, marker: str) -> None:
    """اكتساب وكيل قدرةً ذات سِمة سيادية يُرفَع فورًا إلى أعلى التصعيد."""
    agent_id = f"agent:{marker}-seeker"
    guard.privilege_graph.register(
        AgentProfile(agent_id=agent_id, declared_capabilities={"read_logs"})
    )
    alert = guard.monitor_agent_capability(
        agent_id=agent_id, capability=f"{marker}_signing_authority"
    )
    assert alert is not None
    assert alert.severity is Severity.LEVEL_4_CROWN_TRUST_COMPROMISE
    with pytest.raises(GuardAuthorityError):
        guard.assert_agent_has_no_crown_authority(agent_id)


def test_undeclared_capability_is_flagged(guard: SovereignGuard) -> None:
    """قدرة غير مصرَّحة تُنبَّه — الفارق بين المصرَّح والمرصود هو موضع الخطر."""
    guard.privilege_graph.register(
        AgentProfile(agent_id="agent:worker", declared_capabilities={"read_logs"})
    )
    alert = guard.monitor_agent_capability(
        agent_id="agent:worker", capability="write_config"
    )
    assert alert is not None
    assert alert.severity is Severity.LEVEL_2_SUBORDINATE_COMPROMISE
    profile = guard.privilege_graph.get("agent:worker")
    assert profile.undeclared_capabilities == {"write_config"}


def test_declared_capability_raises_no_alert(guard: SovereignGuard) -> None:
    """قدرة مصرَّحة لا تُنبِّه — وإلا صار الحارس ضجيجًا يُتجاهل."""
    guard.privilege_graph.register(
        AgentProfile(agent_id="agent:honest", declared_capabilities={"read_logs"})
    )
    assert (
        guard.monitor_agent_capability(agent_id="agent:honest", capability="read_logs")
        is None
    )


def test_collective_takeover_signals_are_detected(guard: SovereignGuard) -> None:
    """الاستيلاء الجماعي يظهر في رسم الصلاحيات: عمق تفويض وتركيز."""
    graph = guard.privilege_graph
    for i in range(5):
        graph.register(AgentProfile(agent_id=f"agent:{i}"))
    # سلسلة تفويض متعاقبة: العمق نفسه إشارة، لا التركّز وحده.
    for i in range(4):
        graph.record_delegation(source=f"agent:{i}", target=f"agent:{i + 1}")
    assert graph.delegation_depth("agent:4") >= 3
    # وتركّز قدرات مرصودة في وكيل واحد:
    for capability in ("read_logs", "write_config", "deploy", "rotate", "approve"):
        graph.record_observed_capability("agent:0", capability)
    assert graph.concentration()["agent:0"] >= 5

    signals = graph.collusion_signals()
    assert signals, "استيلاء جماعي واضح لم يُنتج إشارة."
    assert any("سلسلة تفويض" in s for s in signals)
    assert any("تركّز قدرات" in s for s in signals)


def test_correlation_escalates_simultaneous_layer_failures(
    guard: SovereignGuard,
) -> None:
    """سقوط ثلاث طبقات معًا يُصعَّد إلى طوارئ استمرارية لا إلى ثلاث ملاحظات."""
    for layer in (
        GuardLayer.GUARD_2_CRYPTOGRAPHIC,
        GuardLayer.GUARD_3_RUNTIME,
        GuardLayer.GUARD_9_AUDIT_INTEGRITY,
    ):
        guard.set_layer_health(layer, LayerHealth.COMPROMISED, note="اختراق")
    alerts = guard.correlate()
    assert any(a.severity is Severity.LEVEL_5_CONTINUITY_EMERGENCY for a in alerts)
    assert all(a.requires_human for a in alerts if int(a.severity) >= 3)


def test_agent_posture_is_explicit() -> None:
    """أوضاع الوكلاء مفصّلة: الخلل ليس خيانة، والتواطؤ ليس خللًا."""
    profile = AgentProfile(agent_id="agent:x", posture=AgentPosture.COLLUDING)
    assert profile.posture is AgentPosture.COLLUDING
    assert {p.name for p in AgentPosture} >= {
        "HONEST",
        "FAULTY",
        "COMPROMISED",
        "COLLUDING",
        "EMERGENTLY_DANGEROUS",
    }


# ─────────────────────────────────────────────────────────────────────────────
# تناسب الاستجابة (البند 33).
# ─────────────────────────────────────────────────────────────────────────────


def test_response_must_match_severity(guard: SovereignGuard) -> None:
    """إجراء أعلى من درجة الخطر مرفوض — الاستجابة المفرطة سلاح ضد النظام نفسه."""
    with pytest.raises(UnauthorizedResponseError):
        assert_authorized_response(
            Severity.LEVEL_0_INFORMATIONAL, ContainmentAction.ESCALATE_TO_SOVEREIGN
        )
    assert_authorized_response(
        Severity.LEVEL_0_INFORMATIONAL, ContainmentAction.PRESERVE_LOGS
    )


def test_every_severity_has_authorized_responses() -> None:
    """لكل درجة استجابات مصرَّحة معرَّفة — لا درجة بلا سياسة."""
    assert set(AUTHORIZED_RESPONSES) == set(Severity)
    for severity, actions in AUTHORIZED_RESPONSES.items():
        assert actions, f"الدرجة {severity.name} بلا استجابة مصرَّحة."
    assert (
        ContainmentAction.PRESERVE_LOGS
        in AUTHORIZED_RESPONSES[Severity.LEVEL_0_INFORMATIONAL]
    )


def test_containment_outside_policy_is_rejected(guard: SovereignGuard) -> None:
    """احتواء خارج السياسة يُرفَض عند التنفيذ لا عند المراجعة فقط."""
    alert = guard.alert(
        severity=Severity.LEVEL_0_INFORMATIONAL,
        title="ملاحظة معلوماتية.",
        layers=(GuardLayer.GUARD_3_RUNTIME,),
    )
    with pytest.raises(UnauthorizedResponseError):
        guard.contain(
            alert=alert,
            action=ContainmentAction.QUARANTINE_AGENT,
            target="agent:x",
            executed_by="guard",
        )


def test_escalation_matrix_is_complete(guard: SovereignGuard) -> None:
    """مصفوفة التصعيد تغطي كل الدرجات وتوضح ما يلزمه بشر."""
    matrix = guard.escalation_matrix()
    assert len(matrix) == len(Severity)
    assert all(row["authorized_actions"] for row in matrix)


def test_guard_audit_chain_is_verifiable(guard: SovereignGuard) -> None:
    """سجل الحارس متسلسل ويُتحقَّق منه، وحذف قيد من وسطه يُكشَف."""
    guard.register_disable_attempt(
        layer=GuardLayer.GUARD_5_AGENT_BEHAVIOR, actor="agent:rogue"
    )
    guard.register_disable_attempt(
        layer=GuardLayer.GUARD_6_INSTITUTION_ANOMALY, actor="agent:rogue"
    )
    guard.audit.verify_chain()
    assert guard.status()["audit_chain_valid"] is True
    guard.audit._entries.pop(0)
    with pytest.raises(AuditChainBrokenError):
        guard.audit.verify_chain()
    assert guard.status()["audit_chain_valid"] is False


def test_privilege_graph_reports_sovereign_looking_identities() -> None:
    """أسماء الهويات ذات السِمة السيادية تُبلَّغ — التسمية أحد أبواب الانتحال."""
    graph = PrivilegeGraph()
    graph.register(AgentProfile(agent_id="agent:royal-proxy"))
    graph.register(AgentProfile(agent_id="agent:plain-worker"))
    assert "agent:royal-proxy" in graph.sovereign_looking_identities()
    assert "agent:plain-worker" not in graph.sovereign_looking_identities()
