"""
AMOS Policy Engine - محرك السياسات
Rule-based policy evaluation and enforcement for the federal state
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

logger = logging.getLogger(__name__)


class PolicyEffect(Enum):
    """تأثير السياسة"""
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


class PolicyPriority(Enum):
    """أولوية السياسة"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PolicyRule:
    """قاعدة سياسة"""
    id: str
    name: str
    description: str
    effect: PolicyEffect
    priority: PolicyPriority = PolicyPriority.NORMAL
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'effect': self.effect.value,
            'priority': self.priority.value,
            'conditions': self.conditions,
            'actions': self.actions,
            'resources': self.resources,
            'subjects': self.subjects,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class PolicyEvaluationResult:
    """نتيجة تقييم السياسة"""
    allowed: bool
    policy_id: Optional[str] = None
    reason: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'allowed': self.allowed,
            'policy_id': self.policy_id,
            'reason': self.reason,
            'conditions': self.conditions,
            'evaluated_at': self.evaluated_at.isoformat()
        }


class ConditionEvaluator:
    """مقيم الشروط"""
    
    def __init__(self):
        self._custom_evaluators: Dict[str, Callable] = {}
    
    def register_evaluator(self, name: str, evaluator: Callable) -> None:
        """تسجيل مقيم شرط مخصص"""
        self._custom_evaluators[name] = evaluator
        logger.debug(f"Custom evaluator registered: {name}")
    
    def evaluate(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """تقييم شرط واحد"""
        op = condition.get('operator', 'equals')
        field = condition.get('field')
        value = condition.get('value')
        
        # Get actual value from context
        actual_value = self._get_context_value(field, context)
        
        # Use custom evaluator if available
        if op in self._custom_evaluators:
            return self._custom_evaluators[op](actual_value, value, context)
        
        # Built-in operators
        if op == 'equals':
            return actual_value == value
        elif op == 'not_equals':
            return actual_value != value
        elif op == 'greater_than':
            return actual_value > value
        elif op == 'less_than':
            return actual_value < value
        elif op == 'greater_than_or_equal':
            return actual_value >= value
        elif op == 'less_than_or_equal':
            return actual_value <= value
        elif op == 'in':
            return actual_value in value
        elif op == 'not_in':
            return actual_value not in value
        elif op == 'contains':
            return value in actual_value
        elif op == 'regex':
            return bool(re.match(value, str(actual_value)))
        elif op == 'exists':
            return actual_value is not None
        elif op == 'not_exists':
            return actual_value is None
        elif op == 'and':
            return all(self.evaluate(c, context) for c in value)
        elif op == 'or':
            return any(self.evaluate(c, context) for c in value)
        elif op == 'not':
            return not self.evaluate(value[0], context)
        else:
            logger.warning(f"Unknown operator: {op}")
            return False
    
    def _get_context_value(self, field: str, context: Dict[str, Any]) -> Any:
        """الحصول على قيمة من السياق"""
        if not field:
            return None
        
        parts = field.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value


class PolicyEngine:
    """
    محرك السياسات
    Evaluates and enforces policies based on rules and context
    """
    
    def __init__(self):
        self.policies: Dict[str, PolicyRule] = {}
        self.condition_evaluator = ConditionEvaluator()
        self._lock = asyncio.Lock()
        
        # Register default evaluators
        self._register_default_evaluators()
        
        logger.info("Policy Engine initialized")
    
    def _register_default_evaluators(self) -> None:
        """تسجيل المقيّمات الافتراضية"""
        # Time-based evaluator
        def time_check(actual, expected, context):
            current_hour = datetime.utcnow().hour
            if expected == 'business_hours':
                return 9 <= current_hour <= 17
            elif expected == 'weekend':
                return datetime.utcnow().weekday() >= 5
            return False
        
        self.condition_evaluator.register_evaluator('time_check', time_check)
    
    async def add_policy(self, policy: PolicyRule) -> None:
        """إضافة سياسة"""
        async with self._lock:
            self.policies[policy.id] = policy
            logger.info(f"Policy added: {policy.id} ({policy.name})")
    
    async def remove_policy(self, policy_id: str) -> None:
        """إزالة سياسة"""
        async with self._lock:
            if policy_id in self.policies:
                del self.policies[policy_id]
                logger.info(f"Policy removed: {policy_id}")
    
    async def enable_policy(self, policy_id: str) -> None:
        """تفعيل سياسة"""
        async with self._lock:
            if policy_id in self.policies:
                self.policies[policy_id].enabled = True
                logger.info(f"Policy enabled: {policy_id}")
    
    async def disable_policy(self, policy_id: str) -> None:
        """تعطيل سياسة"""
        async with self._lock:
            if policy_id in self.policies:
                self.policies[policy_id].enabled = False
                logger.info(f"Policy disabled: {policy_id}")
    
    async def evaluate(self, action: str, 
                      resource: str, 
                      subject: str,
                      context: Optional[Dict[str, Any]] = None) -> PolicyEvaluationResult:
        """
        تقييم طلب ضد جميع السياسات
        Returns the most restrictive applicable policy result
        """
        context = context or {}
        context['action'] = action
        context['resource'] = resource
        context['subject'] = subject
        
        async with self._lock:
            applicable_policies = []
            
            for policy in self.policies.values():
                if not policy.enabled:
                    continue
                
                if policy.expires_at and datetime.utcnow() > policy.expires_at:
                    continue
                
                # Check if policy applies
                if self._policy_applies(policy, action, resource, subject):
                    applicable_policies.append(policy)
            
            if not applicable_policies:
                return PolicyEvaluationResult(
                    allowed=True,
                    reason="No applicable policies"
                )
            
            # Sort by priority (highest first)
            applicable_policies.sort(key=lambda p: p.priority.value, reverse=True)
            
            # Evaluate each policy
            for policy in applicable_policies:
                result = await self._evaluate_policy(policy, context)
                
                if result.allowed and policy.effect == PolicyEffect.ALLOW:
                    return result
                elif not result.allowed and policy.effect == PolicyEffect.DENY:
                    return result
                elif policy.effect == PolicyEffect.CONDITIONAL:
                    return result
            
            # Default deny if no explicit allow
            return PolicyEvaluationResult(
                allowed=False,
                reason="No explicit allow policy matched"
            )
    
    def _policy_applies(self, policy: PolicyRule, 
                       action: str, 
                       resource: str, 
                       subject: str) -> bool:
        """التحقق مما إذا كانت السياسة تنطبق"""
        # Check subjects
        if policy.subjects and '*' not in policy.subjects:
            if subject not in policy.subjects:
                return False
        
        # Check actions
        if policy.actions and '*' not in policy.actions:
            if action not in policy.actions:
                return False
        
        # Check resources
        if policy.resources and '*' not in policy.resources:
            if not any(resource.startswith(r) for r in policy.resources):
                return False
        
        return True
    
    async def _evaluate_policy(self, policy: PolicyRule, 
                              context: Dict[str, Any]) -> PolicyEvaluationResult:
        """تقييم سياسة واحدة"""
        # Evaluate conditions
        conditions_met = True
        failed_conditions = []
        
        for condition in policy.conditions.get('rules', []):
            if not self.condition_evaluator.evaluate(condition, context):
                conditions_met = False
                failed_conditions.append(condition)
        
        if policy.effect == PolicyEffect.ALLOW:
            if conditions_met:
                return PolicyEvaluationResult(
                    allowed=True,
                    policy_id=policy.id,
                    reason=f"Policy {policy.name} allows this action",
                    conditions={'met': True}
                )
            else:
                return PolicyEvaluationResult(
                    allowed=False,
                    policy_id=policy.id,
                    reason=f"Policy {policy.name} conditions not met",
                    conditions={'met': False, 'failed': failed_conditions}
                )
        elif policy.effect == PolicyEffect.DENY:
            if conditions_met:
                return PolicyEvaluationResult(
                    allowed=False,
                    policy_id=policy.id,
                    reason=f"Policy {policy.name} denies this action",
                    conditions={'met': True}
                )
            else:
                return PolicyEvaluationResult(
                    allowed=True,
                    policy_id=policy.id,
                    reason=f"Policy {policy.name} denial conditions not met",
                    conditions={'met': False}
                )
        else:  # CONDITIONAL
            return PolicyEvaluationResult(
                allowed=conditions_met,
                policy_id=policy.id,
                reason=f"Policy {policy.name} conditional evaluation",
                conditions={'met': conditions_met, 'failed': failed_conditions if not conditions_met else []}
            )
    
    async def get_policies(self, 
                          enabled_only: bool = False,
                          effect: Optional[PolicyEffect] = None) -> List[PolicyRule]:
        """الحصول على قائمة السياسات"""
        async with self._lock:
            policies = list(self.policies.values())
            
            if enabled_only:
                policies = [p for p in policies if p.enabled]
            
            if effect:
                policies = [p for p in policies if p.effect == effect]
            
            return policies
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات المحرك"""
        async with self._lock:
            total = len(self.policies)
            enabled = sum(1 for p in self.policies.values() if p.enabled)
            by_effect = {
                'allow': sum(1 for p in self.policies.values() if p.effect == PolicyEffect.ALLOW),
                'deny': sum(1 for p in self.policies.values() if p.effect == PolicyEffect.DENY),
                'conditional': sum(1 for p in self.policies.values() if p.effect == PolicyEffect.CONDITIONAL)
            }
            
            return {
                'total_policies': total,
                'enabled_policies': enabled,
                'disabled_policies': total - enabled,
                'by_effect': by_effect
            }


# Common policy templates
def create_role_based_policy(role: str, 
                            actions: List[str], 
                            resources: List[str],
                            effect: PolicyEffect = PolicyEffect.ALLOW) -> PolicyRule:
    """إنشاء سياسة قائمة على الأدوار"""
    import hashlib
    policy_id = hashlib.sha256(f"rbac_{role}_{ '_'.join(actions) }".encode()).hexdigest()[:16]
    
    return PolicyRule(
        id=f"rbac-{policy_id}",
        name=f"Role-based policy for {role}",
        description=f"Allows {role} to perform {actions} on {resources}",
        effect=effect,
        priority=PolicyPriority.NORMAL,
        conditions={},
        actions=actions,
        resources=resources,
        subjects=[role]
    )


def create_time_restricted_policy(name: str,
                                 actions: List[str],
                                 resources: List[str],
                                 time_condition: str = 'business_hours') -> PolicyRule:
    """إنشاء سياسة مقيدة بالوقت"""
    import hashlib
    policy_id = hashlib.sha256(f"time_{name}_{time_condition}".encode()).hexdigest()[:16]
    
    return PolicyRule(
        id=f"time-{policy_id}",
        name=f"Time-restricted policy: {name}",
        description=f"Allows {actions} during {time_condition}",
        effect=PolicyEffect.CONDITIONAL,
        priority=PolicyPriority.NORMAL,
        conditions={
            'rules': [{
                'operator': 'time_check',
                'field': 'time',
                'value': time_condition
            }]
        },
        actions=actions,
        resources=resources,
        subjects=['*']
    )


# Singleton instance
_engine_instance: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    """الحصول على مثان المحرك الوحيد"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PolicyEngine()
    return _engine_instance


async def initialize_policy_engine() -> PolicyEngine:
    """تهيئة محرك السياسات"""
    engine = get_policy_engine()
    
    # Add default policies
    default_policies = [
        create_role_based_policy('admin', ['*'], ['*'], PolicyEffect.ALLOW),
        create_role_based_policy('user', ['read'], ['public/*'], PolicyEffect.ALLOW),
        create_role_based_policy('user', ['write', 'delete'], ['*'], PolicyEffect.DENY),
    ]
    
    for policy in default_policies:
        await engine.add_policy(policy)
    
    logger.info("Policy Engine initialized with default policies")
    return engine
