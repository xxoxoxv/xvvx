"""
AMOS-Federation Kill Switch + Promotion Gates + Canary Controller
الهدف: مفتاح إيقاف متعدد المستويات + بوابات ترقية + Canary deployment
النطاق: governance (canary)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid
from datetime import UTC, datetime
from typing import Any

# === Kill Switch ===

KILL_SWITCH_LEVELS = ["normal", "alert", "degraded", "halt"]
_system_state = {"level": "normal", "reason": "", "activated_at": None, "activated_by": ""}


def get_system_status() -> dict[str, Any]:
    """حالة النظام الحالية."""
    return _system_state.copy()


def activate_kill_switch(level: str, reason: str, activated_by: str) -> dict[str, Any]:
    """تفعيل مفتاح الإيقاف."""
    if level not in KILL_SWITCH_LEVELS:
        raise ValueError(f"مستوى غير صالح: {level}")
    _system_state["level"] = level
    _system_state["reason"] = reason
    _system_state["activated_at"] = datetime.now(UTC).isoformat()
    _system_state["activated_by"] = activated_by
    # نشر حدث
    from amos_federation.common.event_bus import get_event_bus

    get_event_bus().publish(
        "amos_federation.policy.checked",
        {
            "policy_name": "kill_switch",
            "allowed": level == "normal",
            "violations": [reason] if level != "normal" else [],
            "level": level,
            "activated_by": activated_by,
        },
    )
    return _system_state.copy()


def reset_kill_switch() -> dict[str, Any]:
    """إعادة ضبط مفتاح الإيقاف."""
    _system_state["level"] = "normal"
    _system_state["reason"] = ""
    _system_state["activated_at"] = None
    _system_state["activated_by"] = ""
    return _system_state.copy()


def is_system_halted() -> bool:
    """هل النظام متوقف؟"""
    return _system_state["level"] == "halt"


def is_execution_blocked(tool: str | None = None) -> bool:
    """هل التنفيذ محجوب؟ في halt كل شيء محجوب. في degraded الأدوات الخطيرة محجوبة."""
    level = _system_state["level"]
    if level == "halt":
        return True
    return bool(level == "degraded" and tool in ["python_execute", "sql_query", "http_request"])


def enforce_kill_switch(tool: str, role: str = "user") -> dict[str, Any]:
    """تطبيق Kill Switch على تنفيذ أداة. يرمي HTTPException إذا محجوب."""
    from fastapi import HTTPException

    level = _system_state["level"]
    if level == "halt":
        raise HTTPException(
            status_code=503,
            detail={
                "error": "system_halted",
                "message": "النظام متوقف — Kill Switch مفعّل بمستوى halt",
                "level": level,
                "reason": _system_state["reason"],
            },
        )
    if level == "degraded" and tool in ["python_execute", "sql_query", "http_request"]:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "system_degraded",
                "message": f"النظام في وضع متدهور — الأداة '{tool}' محجوبة",
                "level": level,
                "reason": _system_state["reason"],
            },
        )
    return {"allowed": True, "level": level}


# === Promotion Gates ===

PROMOTION_GATES = [
    "evaluation",
    "shadow",
    "canary",
    "human_approval",
    "activation",
]

# قاموس حالات الترقية
_promotions: list[dict[str, Any]] = []


def create_promotion(model_id: str) -> dict[str, Any]:
    """إنشاء طلب ترقية نموذج."""
    promotion = {
        "promotion_id": f"promo-{uuid.uuid4()}",
        "model_id": model_id,
        "gates": {gate: {"status": "pending", "checked_at": None} for gate in PROMOTION_GATES},
        "status": "in_progress",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _promotions.append(promotion)
    return promotion


def check_gate(promotion_id: str, gate_name: str, passed: bool, notes: str = "") -> dict[str, Any]:
    """فحص بوابة ترقية."""
    for promo in _promotions:
        if promo["promotion_id"] == promotion_id:
            if gate_name not in promo["gates"]:
                raise ValueError(f"بوابة غير صالحة: {gate_name}")
            promo["gates"][gate_name] = {
                "status": "passed" if passed else "failed",
                "checked_at": datetime.now(UTC).isoformat(),
                "notes": notes,
            }
            promo["updated_at"] = datetime.now(UTC).isoformat()

            # إذا فشلت بوابة، تتوقف الترقية
            if not passed:
                promo["status"] = "failed"
            # إذا اجتازت كل البوابات
            elif all(g["status"] == "passed" for g in promo["gates"].values()):
                promo["status"] = "promoted"

            return promo.copy()
    raise ValueError(f"ترقية غير موجودة: {promotion_id}")


def get_promotion(promotion_id: str) -> dict[str, Any] | None:
    """إرجاع طلب ترقية."""
    for p in _promotions:
        if p["promotion_id"] == promotion_id:
            return p.copy()
    return None


def list_promotions(limit: int = 50) -> list[dict[str, Any]]:
    """عرض طلبات الترقية."""
    return [p.copy() for p in _promotions[:limit]]


# === Canary Controller ===

_canary_deployments: list[dict[str, Any]] = []


def create_canary(model_id: str, traffic_percentage: int = 5) -> dict[str, Any]:
    """إنشاء Canary deployment لنموذج."""
    if traffic_percentage < 1 or traffic_percentage > 100:
        raise ValueError("نسبة المرور يجب أن تكون 1-100")
    deployment = {
        "canary_id": f"canary-{uuid.uuid4()}",
        "model_id": model_id,
        "traffic_percentage": traffic_percentage,
        "status": "active",
        "metrics": {
            "requests": 0,
            "errors": 0,
            "avg_latency_ms": 0,
            "quality_score": 0.0,
        },
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _canary_deployments.append(deployment)
    return deployment


def update_canary_metrics(
    canary_id: str, requests: int, errors: int, avg_latency: int, quality: float
) -> dict[str, Any]:
    """تحديث مقاييس Canary."""
    for d in _canary_deployments:
        if d["canary_id"] == canary_id:
            d["metrics"] = {
                "requests": requests,
                "errors": errors,
                "avg_latency_ms": avg_latency,
                "quality_score": quality,
            }
            d["updated_at"] = datetime.now(UTC).isoformat()
            # فحص شروط التراجع
            error_rate = errors / requests if requests > 0 else 0
            if error_rate > 0.1 or quality < 0.5:
                d["status"] = "rolled_back"
            return d.copy()
    raise ValueError(f"Canary غير موجود: {canary_id}")


def rollback_canary(canary_id: str) -> dict[str, Any]:
    """تراجع عن Canary deployment."""
    for d in _canary_deployments:
        if d["canary_id"] == canary_id:
            d["status"] = "rolled_back"
            d["updated_at"] = datetime.now(UTC).isoformat()
            return d.copy()
    raise ValueError(f"Canary غير موجود: {canary_id}")


def get_canary(canary_id: str) -> dict[str, Any] | None:
    """إرجاع Canary."""
    for d in _canary_deployments:
        if d["canary_id"] == canary_id:
            return d.copy()
    return None


def list_canaries(limit: int = 50) -> list[dict[str, Any]]:
    """عرض Canary deployments."""
    return [d.copy() for d in _canary_deployments[:limit]]
