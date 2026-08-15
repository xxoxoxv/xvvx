"""
AMOS-Federation Policy Engine (Rego-like)
الهدف: محرك سياسات حقيقي يشبه OPA/Rego — قواعد قابلة للتعريف والتقييم
النطاق: governance (policy engine)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import re
from typing import Any


class RegoRule:
    """قاعدة Rego-like: اسم + جسم (شروط) + قرار."""

    def __init__(
        self, name: str, description: str, conditions: list[dict], decision: str = "allow"
    ):
        self.name = name
        self.description = description
        self.conditions = conditions
        self.decision = decision

    def evaluate(self, context: dict[str, Any]) -> bool:
        """تقييم القاعدة ضد سياق. كل الشرط يجب أن تمر."""
        return all(self._eval_condition(cond, context) for cond in self.conditions)

    def _eval_condition(self, cond: dict, context: dict[str, Any]) -> bool:
        """تقييم شرط واحد."""
        field = cond.get("field", "")
        op = cond.get("op", "eq")
        value = cond.get("value")
        actual = context.get(field)

        if op == "eq":
            return actual == value
        elif op == "ne":
            return actual != value
        elif op == "in":
            return actual in (value or [])
        elif op == "not_in":
            return actual not in (value or [])
        elif op == "gt":
            try:
                return float(actual) > float(value)
            except (TypeError, ValueError):
                return False
        elif op == "lt":
            try:
                return float(actual) < float(value)
            except (TypeError, ValueError):
                return False
        elif op == "gte":
            try:
                return float(actual) >= float(value)
            except (TypeError, ValueError):
                return False
        elif op == "lte":
            try:
                return float(actual) <= float(value)
            except (TypeError, ValueError):
                return False
        elif op == "contains":
            return value in (actual or "")
        elif op == "regex":
            try:
                return bool(re.match(value, str(actual or "")))
            except re.error:
                return False
        elif op == "exists":
            return field in context
        elif op == "not_exists":
            return field not in context
        return False


class PolicyEngine:
    """محرك السياسات الحقيقي — يحمّل القواعد ويقيّمها."""

    def __init__(self) -> None:
        self._rules: dict[str, RegoRule] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """تحميل القواعد الافتراضية (مكافئة لملفات Rego)."""
        # سياسة الوصول للأدوات
        self.add_rule(
            RegoRule(
                name="tool_access",
                description="الأدوات الخطيرة تتطلب دور admin",
                conditions=[
                    {
                        "field": "tool",
                        "op": "in",
                        "value": ["python_execute", "sql_query", "http_request"],
                    },
                    {"field": "role", "op": "ne", "value": "admin"},
                ],
                decision="deny",
            )
        )

        # سياسة الوصول للأدوات الآمنة
        self.add_rule(
            RegoRule(
                name="tool_access_safe",
                description="الأدوات الآمنة مسموحة لكل الأدوار",
                conditions=[
                    {
                        "field": "tool",
                        "op": "not_in",
                        "value": ["python_execute", "sql_query", "http_request"],
                    },
                ],
                decision="allow",
            )
        )

        # سياسة ترقية النماذج
        self.add_rule(
            RegoRule(
                name="promotion_gate",
                description="ترقية النماذج تتطلب اجتياز كل البوابات",
                conditions=[
                    {"field": "gates_passed", "op": "exists"},
                    {"field": "quality_score", "op": "gte", "value": 0.7},
                ],
                decision="allow",
            )
        )

        self.add_rule(
            RegoRule(
                name="promotion_deny_low_quality",
                description="رفض الترقية عند جودة منخفضة",
                conditions=[
                    {"field": "quality_score", "op": "lt", "value": 0.7},
                ],
                decision="deny",
            )
        )

        # سياسة الميزانية
        self.add_rule(
            RegoRule(
                name="budget_limit",
                description="حد يومي للإنفاق",
                conditions=[
                    {"field": "daily_spend_usd", "op": "gt", "value": 100.0},
                ],
                decision="deny",
            )
        )

        # سياسة Kill Switch
        self.add_rule(
            RegoRule(
                name="kill_switch_halt",
                description="في وضع الإيقاف، كل التنفيذ مرفوض",
                conditions=[
                    {"field": "system_state", "op": "eq", "value": "halt"},
                ],
                decision="deny",
            )
        )

        self.add_rule(
            RegoRule(
                name="kill_switch_degraded",
                description="في وضع التدهور، الأدوات الخطيرة مرفوضة",
                conditions=[
                    {"field": "system_state", "op": "eq", "value": "degraded"},
                    {
                        "field": "tool",
                        "op": "in",
                        "value": ["python_execute", "sql_query", "http_request"],
                    },
                ],
                decision="deny",
            )
        )

    def add_rule(self, rule: RegoRule) -> None:
        self._rules[rule.name] = rule

    def remove_rule(self, name: str) -> bool:
        if name in self._rules:
            del self._rules[name]
            return True
        return False

    def list_rules(self) -> list[dict[str, Any]]:
        return [
            {"name": r.name, "description": r.description, "decision": r.decision}
            for r in self._rules.values()
        ]

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        """تقييم كل القواعد ضد السياق. أي قاعدة deny = رفض."""
        denies = []
        allows = []
        for name, rule in self._rules.items():
            if rule.evaluate(context):
                if rule.decision == "deny":
                    denies.append(name)
                else:
                    allows.append(name)

        # deny يفوق allow
        allowed = len(denies) == 0
        return {
            "allowed": allowed,
            "denied_by": denies,
            "allowed_by": allows,
            "rules_evaluated": len(self._rules),
            "engine_version": "1.0",
        }

    def evaluate_tool_access(
        self, tool: str, role: str, system_state: str = "normal"
    ) -> dict[str, Any]:
        """اختصار: تقييم وصول أداة."""
        return self.evaluate(
            {
                "tool": tool,
                "role": role,
                "system_state": system_state,
            }
        )

    def evaluate_promotion(self, quality_score: float, gates_passed: list[str]) -> dict[str, Any]:
        """اختصار: تقييم ترقية نموذج."""
        return self.evaluate(
            {
                "quality_score": quality_score,
                "gates_passed": gates_passed,
            }
        )


# Singleton
_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
