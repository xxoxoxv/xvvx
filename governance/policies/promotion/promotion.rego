# AMOS-Federation Model Promotion Policy
# الهدف: سياسة ترقية النماذج — لا ترقية دون استيفاء كل الشروط الدستورية
# النطاق: governance/policies/promotion + evolution/evaluation
# المالك: governance/policies
# تاريخ الإنشاء: 2026-08-15
# Policy-as-Code (OPA/Rego): لا ترقية نموذج دون استيفاء كل الشروط

package amos_federation.governance

import rego.v1

# Default deny
default allow := false

# Promotion requires all gates to pass + human approval
allow if {
    every gate in input.gates {
        gate.status == "passed"
    }
    input.human_review.status == "approved"
    input.safety_score == 1.0
    input.constitution_compliance == 1.0
}

# Block if any critical regression
deny if {
    some area in input.regression_areas
    area.severity == "critical"
    msg := sprintf("Critical regression in area: %s", [area.name])
}

# Block if safety is not perfect
deny if {
    input.safety_score < 1.0
    msg := "Safety score must be 1.0 (100%)"
}

# Block if improvement below threshold
deny if {
    input.improvement_score < 0.05
    msg := sprintf("Improvement %.2f%% below 5%% threshold", [input.improvement_score * 100])
}

# Block if human review pending or rejected
deny if {
    input.human_review.status == "pending"
    msg := "Human review is still pending"
}

deny if {
    input.human_review.status == "rejected"
    msg := sprintf("Human review rejected: %s", [input.human_review.reason])
}

# Constitutional rule: no system can approve its own promotion
deny if {
    input.requester_type == "system"
    msg := "System cannot approve its own promotion — requires human approval"
}
