"""
AMOS-Federation Policy Engine
الهدف: Policy-as-Code لفحص القرارات (ترقية، وصول، ميزانية)
النطاق: governance (policy)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Any

# تعريفات السياسات
POLICIES: dict[str, dict[str, Any]] = {
    "promotion_policy": {
        "description": "سياسة ترقية النماذج: يجب اجتياز كل البوابات الخمس",
        "required_gates": ["evaluation", "shadow", "canary", "human_approval", "activation"],
        "min_quality_score": 0.7,
        "min_benchmark_pass_rate": 0.8,
    },
    "access_policy": {
        "description": "سياسة الوصول: الأدوات الخطيرة تتطلب موافقة بشرية",
        "restricted_tools": ["python_execute", "sql_query"],
        "required_role": "admin",
    },
    "budget_policy": {
        "description": "سياسة الميزانية: حد يومي لكل نموذج",
        "daily_limit_usd": 100.0,
        "alert_threshold": 0.8,
    },
}


def check_policy(policy_name: str, context: dict[str, Any]) -> dict[str, Any]:
    """فحص سياسة معينة ضد سياق قرار."""
    policy = POLICIES.get(policy_name)
    if policy is None:
        return {"allowed": False, "reason": f"السياسة '{policy_name}' غير موجودة"}

    violations: list[str] = []

    if policy_name == "promotion_policy":
        # فحص البوابات
        gates_passed = context.get("gates_passed", [])
        required = policy["required_gates"]
        missing = [g for g in required if g not in gates_passed]
        if missing:
            violations.append(f"بوابات ناقصة: {', '.join(missing)}")

        # فحص درجة الجودة
        quality = context.get("quality_score", 0)
        if quality < policy["min_quality_score"]:
            violations.append(
                f"درجة الجودة {quality} أقل من الحد الأدنى {policy['min_quality_score']}"
            )

        # فحص معدل اجتياز المعيار
        pass_rate = context.get("benchmark_pass_rate", 0)
        if pass_rate < policy["min_benchmark_pass_rate"]:
            violations.append(
                f"معدل اجتياز المعيار {pass_rate} أقل من {policy['min_benchmark_pass_rate']}"
            )

    elif policy_name == "access_policy":
        tool = context.get("tool", "")
        role = context.get("role", "user")
        if tool in policy["restricted_tools"] and role != policy["required_role"]:
            violations.append(f"الأداة '{tool}' تتطلب دور '{policy['required_role']}'")

    elif policy_name == "budget_policy":
        daily_spend = context.get("daily_spend_usd", 0)
        if daily_spend > policy["daily_limit_usd"]:
            violations.append(
                f"الإنفاق اليومي {daily_spend} يتجاوز الحد {policy['daily_limit_usd']}"
            )

    return {
        "policy": policy_name,
        "allowed": len(violations) == 0,
        "violations": violations,
        "policy_version": "1.0",
    }
