"""الهدف: حزمة التاج — جذر الثقة وحمايته: هوية، ومفاتيح، ومرساة، وأوامر، واستمرارية، وحارس.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

التصدير هنا **متأخر** (PEP 562) على منهاج `core.sovereignty`: وحدات هذه الحزمة
يعتمد بعضها على بعض (`succession` و`recovery` و`guard` تعتمد `audit`، و
`trust_anchor` يعتمد `key_registry`)، والاستيراد المبكر يُغلق الحلقة. والاتجاه
المسموح وحده:

    threats/identity/key_registry/audit  →  keystore/trust_anchor/command
                                         →  continuity/succession/recovery
                                         →  guard

والحزمة لا تحمل مادة سرية ولا مفتاحًا خاصًا. ما فيها: تحقق، ونسب، وسجل، وحدود
معلَنة بين ما تفعله البرمجية وما يحتاج بشرًا.
"""

from __future__ import annotations

from typing import Any

_EXPORTS: dict[str, str] = {

    # threats
    "ALL_THREATS": "threats",
    "DETECTABLE_BY_SOFTWARE": "threats",
    "REQUIRES_HUMAN": "threats",
    "THREATS_BY_ID": "threats",
    "DetectionCapability": "threats",
    "FalseMitigationClaimError": "threats",
    "MitigationStatus": "threats",
    "ResponsibleParty": "threats",
    "Threat": "threats",
    "ThreatDomain": "threats",
    "ThreatHorizon": "threats",
    "ThreatModelError": "threats",
    "boundary_report": "threats",
    "by_domain": "threats",
    "by_status": "threats",
    "coverage_matrix": "threats",
    "register_threat": "threats",
    "threat": "threats",
    "unresolved_threats": "threats",
    # identity
    "FORBIDDEN_KEY_MATERIAL": "identity",
    "IDENTITY_KINDS": "identity",
    "AuthenticationAssessment": "identity",
    "BiometricAsKeyError": "identity",
    "CrownCommandIdentity": "identity",
    "CrownCryptographicIdentity": "identity",
    "CrownDeviceIdentity": "identity",
    "CrownInstitutionalIdentity": "identity",
    "FactorEvidence": "identity",
    "FactorKind": "identity",
    "HumanSovereignIdentity": "identity",
    "IdentityBinding": "identity",
    "IdentityConflationError": "identity",
    "IdentityError": "identity",
    "IdentityGraph": "identity",
    "SigningCeremonyPolicy": "identity",
    "assert_not_key_material": "identity",
    "assess": "identity",
    # key_registry
    "DOMAIN_TAG_MANIFEST": "key_registry",
    "HYBRID_ALGORITHMS": "key_registry",
    "SUPPORTED_ALGORITHMS": "key_registry",
    "AlgorithmAgilityPlan": "key_registry",
    "AlgorithmError": "key_registry",
    "CrownKeyRecord": "key_registry",
    "CrownKeyRegistry": "key_registry",
    "KeyProvenance": "key_registry",
    "KeyRegistryError": "key_registry",
    "KeyState": "key_registry",
    "KeyStateError": "key_registry",
    "LineageError": "key_registry",
    "LineageKind": "key_registry",
    # keystore
    "CONTINUITY_ENVIRONMENTS": "keystore",
    "FORBIDDEN_MATERIAL_LOCATIONS": "keystore",
    "PERMITTED_REPOSITORY_CONTENT": "keystore",
    "ContinuityEnvironment": "keystore",
    "CrownKeystore": "keystore",
    "EphemeralTestKeystore": "keystore",
    "KeyMaterialLeakError": "keystore",
    "KeystoreCapabilities": "keystore",
    "KeystoreError": "keystore",
    "KeystoreKind": "keystore",
    "ProductionKeystoreUnavailableError": "keystore",
    "ReferenceProductionKeystore": "keystore",
    "SigningRequest": "keystore",
    "SigningResult": "keystore",
    "TestKeystoreInProductionError": "keystore",
    "assert_no_material_in": "keystore",
    # trust_anchor
    "DOMAIN_TAG_ANCHOR": "trust_anchor",
    "INDEPENDENT_PLANES": "trust_anchor",
    "SUBSTITUTION_VECTORS": "trust_anchor",
    "AnchorObservation": "trust_anchor",
    "AnchorSource": "trust_anchor",
    "AnchorSubstitutionError": "trust_anchor",
    "CircularTrustError": "trust_anchor",
    "CrownTrustAnchor": "trust_anchor",
    "DowngradeError": "trust_anchor",
    "OutOfBandVerificationRequiredError": "trust_anchor",
    "RollbackError": "trust_anchor",
    "RootKeyReuseError": "trust_anchor",
    "SignedKeyManifest": "trust_anchor",
    "SubstitutionVector": "trust_anchor",
    "TrustAnchorError": "trust_anchor",
    "TrustPlane": "trust_anchor",
    "substitution_matrix": "trust_anchor",
    # audit
    "DOMAIN_TAG_AUDIT": "audit",
    "AuditAppendOnlyError": "audit",
    "AuditChainBrokenError": "audit",
    "AuditError": "audit",
    "CrownAudit": "audit",
    "CrownAuditEntry": "audit",
    "CrownAuditEventKind": "audit",
    # command
    "DOMAIN_TAG_COMMAND": "command",
    "FORBIDDEN_UNSIGNED_FIELDS": "command",
    "CommandError": "command",
    "CommandLedger": "command",
    "ContextTamperError": "command",
    "CrownCommandVerifier": "command",
    "ExecutionRecord": "command",
    "ExpiredCommandError": "command",
    "ReplayError": "command",
    "RoyalCommandEnvelope": "command",
    "SignatureError": "command",
    "SignedRoyalCommand": "command",
    "UnsignedFieldError": "command",
    "VerificationOutcome": "command",
    "build_envelope": "command",
    # continuity
    "FORBIDDEN_CONCLUSIONS": "continuity",
    "INVALID_INFERENCES": "continuity",
    "LOCKDOWN_PROFILES": "continuity",
    "PLANE_ISOLATION": "continuity",
    "AutonomousSuccessionError": "continuity",
    "ContinuityDoctrine": "continuity",
    "ContinuityError": "continuity",
    "ContinuityState": "continuity",
    "CrownContinuity": "continuity",
    "InvalidInferenceError": "continuity",
    "LockdownLevel": "continuity",
    "LockdownProfile": "continuity",
    "PlaneIsolation": "continuity",
    "SecurityPlane": "continuity",
    "SignalObservation": "continuity",
    "SovereignCondition": "continuity",
    "SovereignSignal": "continuity",
    "StateDeclaration": "continuity",
    "UndeclaredTransitionError": "continuity",
    "assert_no_cross_plane_escalation": "continuity",
    "assert_not_inferred": "continuity",
    # succession
    "FORBIDDEN_SUCCESSION_DECIDERS": "succession",
    "FORBIDDEN_SUCCESSION_TRIGGERS": "succession",
    "MINIMUM_WITNESSES": "succession",
    "CrownSuccession": "succession",
    "SuccessionAuthorityError": "succession",
    "SuccessionCeremony": "succession",
    "SuccessionError": "succession",
    "SuccessionMandate": "succession",
    "SuccessionStage": "succession",
    "SuccessionStageError": "succession",
    "SuccessionWitness": "succession",
    "assert_eligible_decider": "succession",
    "assert_valid_trigger": "succession",
    # recovery
    "FORBIDDEN_RECOVERY_MECHANISMS": "recovery",
    "MINIMUM_DISTINCT_LOCATIONS": "recovery",
    "MINIMUM_QUORUM": "recovery",
    "MINIMUM_SHARE_HOLDERS": "recovery",
    "CrownRecovery": "recovery",
    "EmergencyBackdoorError": "recovery",
    "QuorumError": "recovery",
    "RecoveryCeremony": "recovery",
    "RecoveryError": "recovery",
    "RecoveryScheme": "recovery",
    "RecoveryStage": "recovery",
    "RecoveryStageError": "recovery",
    "RecoveryTrigger": "recovery",
    "ShareHolderDescriptor": "recovery",
    "assert_no_emergency_backdoor": "recovery",
    # guard
    "AUTHORIZED_RESPONSES": "guard",
    "CROWN_LOOKING_MARKERS": "guard",
    "FORBIDDEN_GUARD_POWERS": "guard",
    "AgentPosture": "guard",
    "AgentProfile": "guard",
    "Alert": "guard",
    "ContainmentAction": "guard",
    "EvolutionStage": "guard",
    "GuardAuthorityError": "guard",
    "GuardDisableAttemptError": "guard",
    "GuardError": "guard",
    "GuardEvolutionError": "guard",
    "GuardEvolutionProposal": "guard",
    "GuardIdentity": "guard",
    "GuardIntegrityError": "guard",
    "GuardLayer": "guard",
    "GuardLayerState": "guard",
    "LayerHealth": "guard",
    "Observation": "guard",
    "PrivilegeGraph": "guard",
    "Severity": "guard",
    "SovereignGuard": "guard",
    "UnauthorizedResponseError": "guard",
    "assert_authorized_response": "guard",
    "assert_not_sovereign_power": "guard",
    "compute_digest": "guard",
}


__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'core.crown' has no attribute '{name}'")
    from importlib import import_module

    value = getattr(import_module(f"core.crown.{module_name}"), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return __all__
