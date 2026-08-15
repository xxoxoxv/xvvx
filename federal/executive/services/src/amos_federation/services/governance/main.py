"""
AMOS-Federation Governance Service
الهدف: Policy-as-Code + Audit Log + Kill Switch + Promotion Gates + Canary
النطاق: خدمة governance على المنفذ 8009
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.persistent import PersistentAuditStore
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.governance.canary import (
    KILL_SWITCH_LEVELS,
    create_canary,
    create_promotion,
    check_gate,
    get_canary,
    get_promotion,
    get_system_status,
    is_system_halted,
    list_canaries,
    list_promotions,
    reset_kill_switch,
    rollback_canary,
    update_canary_metrics,
)
from amos_federation.services.governance.policy import POLICIES, check_policy
from amos_federation.services.governance.policy_engine import get_policy_engine

router = APIRouter(prefix="/v1", tags=["governance"])

# === Audit Log (hash chain) — دائم بـ SQLAlchemy ===

_audit_store = PersistentAuditStore()


def _append_audit(action: str, actor: str, details: dict[str, Any]) -> dict[str, Any]:
    """إضافة سجل audit مع hash chain دائم."""
    return _audit_store.append(action, actor, details)


# === Request Models ===

class PolicyCheckRequest(BaseModel):
    """طلب فحص سياسة."""

    policy_name: str
    context: dict[str, Any] = Field(default_factory=dict)


class EngineEvaluateRequest(BaseModel):
    """طلب تقييم بمحرك السياسات الحقيقي."""

    context: dict[str, Any] = Field(default_factory=dict)
    tool: str | None = None
    role: str | None = None
    system_state: str | None = None


class KillSwitchRequest(BaseModel):
    """طلب تفعيل مفتاح الإيقاف."""

    level: str = Field(pattern="^(normal|alert|degraded|halt)$")
    reason: str = Field(min_length=1)
    activated_by: str = Field(min_length=1)


class PromotionCreateRequest(BaseModel):
    """طلب إنشاء ترقية."""

    model_id: str = Field(min_length=1)


class GateCheckRequest(BaseModel):
    """طلب فحص بوابة."""

    gate_name: str
    passed: bool
    notes: str = ""


class CanaryCreateRequest(BaseModel):
    """طلب إنشاء Canary."""

    model_id: str = Field(min_length=1)
    traffic_percentage: int = Field(default=5, ge=1, le=100)


class CanaryMetricsRequest(BaseModel):
    """طلب تحديث مقاييس Canary."""

    requests: int = Field(ge=0)
    errors: int = Field(ge=0)
    avg_latency_ms: int = Field(ge=0)
    quality_score: float = Field(ge=0.0, le=1.0)


# === Policy Endpoints ===

@router.get("/policies", response_model=dict)
async def list_policies(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """عرض كل السياسات المعرفة."""
    return {"policies": POLICIES, "count": len(POLICIES)}


@router.post("/policies/check", response_model=dict)
async def check_policy_endpoint(
    request: PolicyCheckRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """فحص سياسة ضد سياق قرار."""
    result = check_policy(request.policy_name, request.context)
    _append_audit("policy_check", "system", result)
    return result


# === Kill Switch Endpoints ===

@router.get("/system/status", response_model=dict)
async def system_status(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """حالة النظام الحالية."""
    return get_system_status()


@router.post("/system/kill-switch", response_model=dict)
async def activate_kill_switch(
    request: KillSwitchRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تفعيل مفتاح الإيقاف متعدد المستويات."""
    result = _activate_kill_switch_safe(request.level, request.reason, request.activated_by)
    _append_audit("kill_switch_activated", request.activated_by, result)
    return result


@router.post("/system/kill-switch/reset", response_model=dict)
async def reset_kill_switch_endpoint(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إعادة ضبط مفتاح الإيقاف."""
    result = reset_kill_switch()
    _append_audit("kill_switch_reset", "system", result)
    return result


def _activate_kill_switch_safe(level: str, reason: str, activated_by: str) -> dict[str, Any]:
    """Wrapper آمن لتفعيل مفتاح الإيقاف."""
    from amos_federation.services.governance.canary import activate_kill_switch
    return activate_kill_switch(level, reason, activated_by)


# === Promotion Gate Endpoints ===

@router.post("/promotions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_promotion_endpoint(
    request: PromotionCreateRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إنشاء طلب ترقية نموذج بـ 5 بوابات."""
    promo = create_promotion(request.model_id)
    _append_audit("promotion_created", "system", {"model_id": request.model_id})
    return promo


@router.get("/promotions", response_model=list[dict])
async def list_promotions_endpoint(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض طلبات الترقية."""
    return list_promotions(limit=limit)


@router.get("/promotions/{promotion_id}", response_model=dict)
async def get_promotion_endpoint(
    promotion_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع طلب ترقية."""
    promo = get_promotion(promotion_id)
    if promo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="طلب الترقية غير موجود")
    return promo


@router.post("/promotions/{promotion_id}/gates", response_model=dict)
async def check_gate_endpoint(
    promotion_id: str,
    request: GateCheckRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """فحص بوابة ترقية."""
    try:
        result = check_gate(promotion_id, request.gate_name, request.passed, request.notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    _append_audit("gate_checked", "system", {
        "promotion_id": promotion_id,
        "gate": request.gate_name,
        "passed": request.passed,
    })
    return result


# === Canary Endpoints ===

@router.post("/canary", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_canary_endpoint(
    request: CanaryCreateRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إنشاء Canary deployment."""
    canary = create_canary(request.model_id, request.traffic_percentage)
    _append_audit("canary_created", "system", {"model_id": request.model_id})
    return canary


@router.get("/canary", response_model=list[dict])
async def list_canaries_endpoint(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض Canary deployments."""
    return list_canaries(limit=limit)


@router.get("/canary/{canary_id}", response_model=dict)
async def get_canary_endpoint(
    canary_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع Canary deployment."""
    canary = get_canary(canary_id)
    if canary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canary غير موجود")
    return canary


@router.patch("/canary/{canary_id}/metrics", response_model=dict)
async def update_canary_metrics_endpoint(
    canary_id: str,
    request: CanaryMetricsRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تحديث مقاييس Canary."""
    try:
        result = update_canary_metrics(
            canary_id, request.requests, request.errors,
            request.avg_latency_ms, request.quality_score
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    _append_audit("canary_metrics_updated", "system", {"canary_id": canary_id, "metrics": result["metrics"]})
    return result


@router.post("/canary/{canary_id}/rollback", response_model=dict)
async def rollback_canary_endpoint(
    canary_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تراجع عن Canary deployment."""
    try:
        result = rollback_canary(canary_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    _append_audit("canary_rollback", "system", {"canary_id": canary_id})
    return result


# === Audit Log Endpoints ===

@router.get("/audit", response_model=list[dict])
async def list_audit_log(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    """عرض سجل التدقيق."""
    return _audit_store.list_all(limit=limit)


@router.get("/audit/verify", response_model=dict)
async def verify_audit_chain(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """التحقق من سلامة سلسلة Audit Log."""
    return _audit_store.verify_chain()


# === Event Bus endpoints ===

@router.get("/events", response_model=list[dict])
async def list_events(
    _: Annotated[dict[str, object], Depends(require_auth)],
    subject: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    """عرض الأحداث المنشورة في Event Bus."""
    from amos_federation.common.event_bus import get_event_bus
    return get_event_bus().get_events(subject=subject, limit=limit)


@router.get("/events/count", response_model=dict)
async def count_events(
    _: Annotated[dict[str, object], Depends(require_auth)],
    subject: str | None = Query(default=None),
) -> dict[str, Any]:
    """عدد الأحداث في Event Bus."""
    from amos_federation.common.event_bus import get_event_bus
    return {"count": get_event_bus().count(subject=subject)}


@router.get("/events/contracts", response_model=dict)
async def list_event_contracts(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """عرض عقود الأحداث المعرفة."""
    from amos_federation.common.event_bus import EVENT_CONTRACTS
    return EVENT_CONTRACTS


# === Policy Engine (Rego-like) ===

@router.get("/policy/rules", response_model=list[dict])
async def list_policy_rules(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """عرض قواعد محرك السياسات."""
    return get_policy_engine().list_rules()


@router.post("/policy/evaluate", response_model=dict)
async def evaluate_policy_engine(
    _: Annotated[dict[str, object], Depends(require_auth)],
    req: EngineEvaluateRequest,
) -> dict[str, Any]:
    """تقييم سياق بمحرك السياسات الحقيقي."""
    engine = get_policy_engine()
    if req.tool and req.role:
        state = req.system_state or get_system_status()["level"]
        result = engine.evaluate_tool_access(req.tool, req.role, state)
    else:
        result = engine.evaluate(req.context)
    # تسجيل التقييم في audit
    _append_audit("policy.evaluate", "system", result)
    return result


@router.post("/policy/check-tool", response_model=dict)
async def check_tool_access(
    _: Annotated[dict[str, object], Depends(require_auth)],
    tool: str = Query(...),
    role: str = Query(...),
) -> dict[str, Any]:
    """فحص وصول أداة عبر Policy Engine."""
    engine = get_policy_engine()
    state = get_system_status()["level"]
    result = engine.evaluate_tool_access(tool, role, state)
    _append_audit("tool.access_check", role, {"tool": tool, "result": result})
    return result


_service = SERVICES["governance"]
app = create_service_app(_service["name"], _service["port"], "Policy Engine + Audit Log + Kill Switch + Canary", [router])
