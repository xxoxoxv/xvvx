"""
AMOS Federation Policy Engine
محرك السياسات والقواعد
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio
import logging
import re
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """أنواع السياسات"""
    ACCESS_CONTROL = "access_control"
    RATE_LIMITING = "rate_limiting"
    RESOURCE_QUOTA = "resource_quota"
    DATA_VALIDATION = "data_validation"
    WORKFLOW = "workflow"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class Effect(Enum):
    """تأثير السياسة"""
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


@dataclass
class PolicyRule:
    """قاعدة سياسة"""
    rule_id: str
    name: str
    description: str
    policy_type: PolicyType
    effect: Effect
    conditions: Dict[str, Any]
    actions: List[str]
    resources: List[str]
    subjects: List[str]
    priority: int = 0
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type.value,
            "effect": self.effect.value,
            "conditions": self.conditions,
            "actions": self.actions,
            "resources": self.resources,
            "subjects": self.subjects,
            "priority": self.priority,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRule":
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data.get("description", ""),
            policy_type=PolicyType(data["policy_type"]),
            effect=Effect(data["effect"]),
            conditions=data.get("conditions", {}),
            actions=data.get("actions", []),
            resources=data.get("resources", []),
            subjects=data.get("subjects", []),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


class PolicyCondition:
    """شرط السياسة"""
    
    def __init__(self, condition_type: str, field: str, operator: str, value: Any):
        self.condition_type = condition_type
        self.field = field
        self.operator = operator
        self.value = value
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """تقييم الشرط"""
        field_value = self._get_field_value(context, self.field)
        
        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "neq":
            return field_value != self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "lte":
            return field_value <= self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        elif self.operator == "contains":
            return self.value in field_value
        elif self.operator == "regex":
            return bool(re.match(self.value, str(field_value)))
        elif self.operator == "exists":
            return field_value is not None
        elif self.operator == "not_exists":
            return field_value is None
        
        return False
    
    def _get_field_value(self, context: Dict[str, Any], field: str) -> Any:
        """الحصول على قيمة الحقل من السياق"""
        parts = field.split(".")
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value


class PolicyEvaluator:
    """مقيّم السياسات"""
    
    def __init__(self):
        self._custom_evaluators: Dict[str, Callable] = {}
    
    def register_evaluator(self, policy_type: str, evaluator: Callable):
        """تسجيل مقيّم مخصص"""
        self._custom_evaluators[policy_type] = evaluator
    
    async def evaluate(
        self,
        rules: List[PolicyRule],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تقييم مجموعة قواعد"""
        # ترتيب القواعد حسب الأولوية
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        
        results = {
            "allowed": True,
            "denied": False,
            "matched_rules": [],
            "denied_rules": [],
            "reason": None
        }
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            if not self._rule_matches(rule, context):
                continue
            
            results["matched_rules"].append(rule.rule_id)
            
            # تقييم الشروط
            if not self._evaluate_conditions(rule, context):
                continue
            
            # تطبيق التأثير
            if rule.effect == Effect.DENY:
                results["denied"] = True
                results["allowed"] = False
                results["denied_rules"].append(rule.rule_id)
                results["reason"] = f"Denied by rule: {rule.name}"
                
                # الـ DENY له أولوية قصوى
                break
            
            elif rule.effect == Effect.ALLOW:
                results["allowed"] = True
            
            elif rule.effect == Effect.CONDITIONAL:
                # تقييم مشروط مخصص
                if rule.policy_type.value in self._custom_evaluators:
                    custom_result = await self._custom_evaluators[rule.policy_type.value](
                        rule, context
                    )
                    if not custom_result.get("allowed", True):
                        results["denied"] = True
                        results["allowed"] = False
                        results["denied_rules"].append(rule.rule_id)
                        results["reason"] = custom_result.get("reason", "Conditional denial")
                        break
        
        return results
    
    def _rule_matches(self, rule: PolicyRule, context: Dict[str, Any]) -> bool:
        """التحقق من مطابقة القاعدة للسياق"""
        subject = context.get("subject")
        action = context.get("action")
        resource = context.get("resource")
        
        # التحقق من الموضوع
        if rule.subjects and subject not in rule.subjects and "*" not in rule.subjects:
            return False
        
        # التحقق من الإجراء
        if rule.actions and action not in rule.actions and "*" not in rule.actions:
            return False
        
        # التحقق من المورد
        if rule.resources:
            resource_matched = False
            for res_pattern in rule.resources:
                if res_pattern == "*":
                    resource_matched = True
                    break
                if res_pattern == resource:
                    resource_matched = True
                    break
                # دعم الأنماط البسيطة
                if res_pattern.endswith("*") and resource.startswith(res_pattern[:-1]):
                    resource_matched = True
                    break
            
            if not resource_matched:
                return False
        
        return True
    
    def _evaluate_conditions(self, rule: PolicyRule, context: Dict[str, Any]) -> bool:
        """تقييم شروط القاعدة"""
        conditions = rule.conditions.get("rules", [])
        logic = rule.conditions.get("logic", "AND")  # AND أو OR
        
        if not conditions:
            return True
        
        results = []
        for cond_data in conditions:
            condition = PolicyCondition(
                condition_type=cond_data.get("type", "field"),
                field=cond_data["field"],
                operator=cond_data["operator"],
                value=cond_data["value"]
            )
            results.append(condition.evaluate(context))
        
        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        
        return all(results)


class PolicyEngine:
    """محرك السياسات"""
    
    def __init__(self):
        self._rules: Dict[str, PolicyRule] = {}
        self._evaluator = PolicyEvaluator()
        self._audit_log: List[Dict[str, Any]] = []
    
    def add_rule(self, rule: PolicyRule):
        """إضافة قاعدة"""
        self._rules[rule.rule_id] = rule
        logger.info(f"Policy rule added: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """إزالة قاعدة"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"Policy rule removed: {rule_id}")
            return True
        return False
    
    def update_rule(self, rule: PolicyRule) -> bool:
        """تحديث قاعدة"""
        if rule.rule_id in self._rules:
            rule.updated_at = datetime.utcnow()
            self._rules[rule.rule_id] = rule
            logger.info(f"Policy rule updated: {rule.rule_id}")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[PolicyRule]:
        """الحصول على قاعدة"""
        return self._rules.get(rule_id)
    
    def get_all_rules(self) -> List[PolicyRule]:
        """الحصول على جميع القواعد"""
        return list(self._rules.values())
    
    def enable_rule(self, rule_id: str) -> bool:
        """تفعيل قاعدة"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True
            rule.updated_at = datetime.utcnow()
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """تعطيل قاعدة"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False
            rule.updated_at = datetime.utcnow()
            return True
        return False
    
    async def check_access(
        self,
        subject: str,
        action: str,
        resource: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """التحقق من الصلاحية"""
        context = {
            "subject": subject,
            "action": action,
            "resource": resource,
            **(additional_context or {})
        }
        
        rules = self.get_applicable_rules(context)
        result = await self._evaluator.evaluate(rules, context)
        
        # تسجيل التدقيق
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "subject": subject,
            "action": action,
            "resource": resource,
            "result": result
        })
        
        return result
    
    def get_applicable_rules(self, context: Dict[str, Any]) -> List[PolicyRule]:
        """الحصول على القواعد المنطبقة"""
        applicable = []
        
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            
            # تحقق سريع من المطابقة
            subject = context.get("subject")
            action = context.get("action")
            resource = context.get("resource")
            
            if rule.subjects and subject not in rule.subjects and "*" not in rule.subjects:
                continue
            
            if rule.actions and action not in rule.actions and "*" not in rule.actions:
                continue
            
            applicable.append(rule)
        
        return applicable
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """الحصول على سجل التدقيق"""
        return self._audit_log[-limit:]
    
    def clear_audit_log(self):
        """مسح سجل التدقيق"""
        self._audit_log.clear()
    
    def register_custom_evaluator(self, policy_type: str, evaluator: Callable):
        """تسجيل مقيّم مخصص"""
        self._evaluator.register_evaluator(policy_type, evaluator)


# دوال مساعدة لإنشاء القواعد الشائعة
def create_allow_rule(
    rule_id: str,
    name: str,
    subjects: List[str],
    actions: List[str],
    resources: List[str],
    conditions: Optional[Dict[str, Any]] = None,
    priority: int = 0
) -> PolicyRule:
    return PolicyRule(
        rule_id=rule_id,
        name=name,
        description=f"Allow rule: {name}",
        policy_type=PolicyType.ACCESS_CONTROL,
        effect=Effect.ALLOW,
        conditions=conditions or {},
        actions=actions,
        resources=resources,
        subjects=subjects,
        priority=priority,
        enabled=True,
        created_at=datetime.utcnow()
    )


def create_deny_rule(
    rule_id: str,
    name: str,
    subjects: List[str],
    actions: List[str],
    resources: List[str],
    conditions: Optional[Dict[str, Any]] = None,
    priority: int = 100  # DENY rules have higher priority
) -> PolicyRule:
    return PolicyRule(
        rule_id=rule_id,
        name=name,
        description=f"Deny rule: {name}",
        policy_type=PolicyType.ACCESS_CONTROL,
        effect=Effect.DENY,
        conditions=conditions or {},
        actions=actions,
        resources=resources,
        subjects=subjects,
        priority=priority,
        enabled=True,
        created_at=datetime.utcnow()
    )
