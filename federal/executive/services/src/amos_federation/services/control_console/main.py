"""
AMOS-Federation Control Console Service
الهدف: واجهة تحكم بشري حقيقية — تعرض الوكلاء، المهام، النماذج، التكلفة، التدقيق
النطاق: خدمة control-console على المنفذ 3000
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["control-console"])


# === 7.1: Dashboard API — تجمع بيانات حقيقية من كل الخدمات ===

@router.get("/dashboard", response_model=dict)
async def get_dashboard(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """لوحة تحكم شاملة — كل الأرقام من خدمات حقيقية."""
    from amos_federation.services.agent_runtime.population import get_population_registry
    from amos_federation.common.event_bus import get_event_bus
    from amos_federation.services.governance.canary import get_system_status
    from amos_federation.services.model_gateway.model_layer import get_model_layer
    from amos_federation.common.persistent import (
        PersistentAuditStore,
        PersistentToolStore,
        PersistentMemoryStore,
        PersistentExperienceStore,
    )

    # 7.2: Agents from real population registry
    registry = get_population_registry()
    agents = registry.list_agents()
    agent_states: dict[str, int] = {}
    for a in agents:
        agent_states[a["state"]] = agent_states.get(a["state"], 0) + 1

    # 7.7: Cost from real model layer
    model_layer = get_model_layer()
    cost_summary = model_layer.get_cost_summary()

    # 7.3: Audit log from real persistent store
    audit_store = PersistentAuditStore()
    audit_entries = audit_store.list_all(limit=10)
    audit_verify = audit_store.verify_chain()

    # Events from real event bus
    bus = get_event_bus()
    event_count = bus.count()

    # Tools from real persistent store
    tool_store = PersistentToolStore()
    tools = tool_store.list_all()

    # Memory from real persistent store
    memory_store = PersistentMemoryStore()

    # Experiences from real persistent store
    exp_store = PersistentExperienceStore()

    # 7.6: Kill Switch status
    system_status = get_system_status()

    return {
        "agents": {
            "total": len(agents),
            "by_state": agent_states,
            "list": agents,
        },
        "cost": cost_summary,
        "audit": {
            "recent": audit_entries,
            "chain_valid": audit_verify.get("valid", False),
            "total_entries": audit_verify.get("entries", 0),
        },
        "events": {
            "total": event_count,
        },
        "tools": {
            "total": len(tools),
        },
        "experiences": {
            "total": exp_store.count(),
        },
        "system_status": system_status,
    }


# === 7.2: Agent management ===

@router.get("/agents", response_model=list[dict])
async def list_agents(
    _: Annotated[dict[str, object], Depends(require_auth)],
    state: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """عرض كل الوكلاء من السجل الحقيقي."""
    from amos_federation.services.agent_runtime.population import get_population_registry
    return get_population_registry().list_agents(state=state)


@router.get("/agents/{agent_id}", response_model=dict)
async def get_agent(
    agent_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """عرض وكيل واحد."""
    from amos_federation.services.agent_runtime.population import get_population_registry
    agent = get_population_registry().get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="الوكيل غير موجود")
    return agent


class AgentStateUpdate(BaseModel):
    """تحديث حالة وكيل."""
    state: str = Field(pattern="^(registered|training|testing|employed|active|paused|retired)$")


@router.post("/agents/{agent_id}/state", response_model=dict)
async def update_agent_state(
    agent_id: str,
    request: AgentStateUpdate,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """7.4: إيقاف/تفعيل وكيل من الواجهة — يستدعي API حقيقيًا."""
    from amos_federation.services.agent_runtime.population import get_population_registry
    from amos_federation.common.event_bus import get_event_bus

    registry = get_population_registry()
    success = registry.update_state(agent_id, request.state)
    if not success:
        raise HTTPException(status_code=404, detail="الوكيل غير موجود")

    # نشر حدث
    get_event_bus().publish("amos_federation.agent.state_changed", {
        "agent_id": agent_id,
        "new_state": request.state,
    })

    return {"agent_id": agent_id, "state": request.state, "updated": True}


# === 7.3: Audit log ===

@router.get("/audit", response_model=list[dict])
async def list_audit(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    """عرض سجل التدقيق من السلسلة الحقيقية."""
    from amos_federation.common.persistent import PersistentAuditStore
    return PersistentAuditStore().list_all(limit=limit)


@router.get("/audit/verify", response_model=dict)
async def verify_audit(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """التحقق من سلامة سلسلة التدقيق."""
    from amos_federation.common.persistent import PersistentAuditStore
    return PersistentAuditStore().verify_chain()


# === 7.6: Kill Switch ===

class KillSwitchRequest(BaseModel):
    """طلب تفعيل Kill Switch."""
    level: str = Field(pattern="^(normal|alert|degraded|halt)$")
    reason: str = Field(min_length=1)
    activated_by: str = Field(min_length=1)


@router.post("/kill-switch", response_model=dict)
async def activate_kill_switch(
    request: KillSwitchRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تفعيل Kill Switch من الواجهة."""
    from amos_federation.services.governance.canary import activate_kill_switch as _activate
    from amos_federation.common.persistent import PersistentAuditStore

    result = _activate(request.level, request.reason, request.activated_by)
    PersistentAuditStore().append("kill_switch_activated", request.activated_by, result)
    return result


@router.post("/kill-switch/reset", response_model=dict)
async def reset_kill_switch(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إعادة ضبط Kill Switch."""
    from amos_federation.services.governance.canary import reset_kill_switch
    return reset_kill_switch()


# === 7.5: Approval (placeholder — يكتمل في المرحلة 9) ===

class ApprovalRequest(BaseModel):
    """طلب موافقة/رفض."""
    decision: str = Field(pattern="^(approve|reject)$")
    signed_by: str = Field(min_length=1)
    model_id: str | None = None
    notes: str = ""


@router.post("/approval", response_model=dict)
async def sign_approval(
    request: ApprovalRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """7.5: زر الموافقة/الرفض — يُفعّل فعليًا في المرحلة 9 مع توقيع Ed25519."""
    from amos_federation.common.persistent import PersistentAuditStore
    from amos_federation.common.event_bus import get_event_bus

    approval_id = f"approval-{__import__('uuid').uuid4().hex[:8]}"
    result = {
        "approval_id": approval_id,
        "decision": request.decision,
        "signed_by": request.signed_by,
        "model_id": request.model_id,
        "notes": request.notes,
        "signature_pending": True,  # سيُوقّع بـ Ed25519 في المرحلة 9
    }
    PersistentAuditStore().append("approval.signed", request.signed_by, result)
    get_event_bus().publish("amos_federation.approval.signed", {
        "approval_id": approval_id,
        "decision": request.decision,
        "signed_by": request.signed_by,
    })
    return result


# === 7.7: Cost ===

@router.get("/cost", response_model=dict)
async def get_cost(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """عرض التكلفة اللحظية والتراكمية."""
    from amos_federation.services.model_gateway.model_layer import get_model_layer
    return get_model_layer().get_cost_summary()


# === 7.8: Events ===

@router.get("/events", response_model=list[dict])
async def list_events(
    _: Annotated[dict[str, object], Depends(require_auth)],
    subject: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    """عرض الأحداث."""
    from amos_federation.common.event_bus import get_event_bus
    return get_event_bus().get_events(subject=subject, limit=limit)


# === 8.4: Health System endpoints ===

@router.get("/health/agents/{agent_id}", response_model=dict)
async def get_agent_health(
    agent_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """عرض الحالة الصحية لوكيل."""
    from amos_federation.services.agent_runtime.health import get_health_checker, get_isolation_system
    checker = get_health_checker()
    history = checker.get_agent_health_history(agent_id, limit=5)
    latest = history[0] if history else {"status": "unknown"}
    isolated = get_isolation_system().is_isolated(agent_id)
    return {
        "agent_id": agent_id,
        "latest_status": latest["status"],
        "is_isolated": isolated,
        "history": history,
    }


@router.get("/health/all", response_model=list[dict])
async def get_all_health(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """عرض الحالة الصحية لكل الوكلاء."""
    from amos_federation.services.agent_runtime.health import get_health_checker
    from amos_federation.services.agent_runtime.population import get_population_registry
    checker = get_health_checker()
    agents = get_population_registry().list_agents()
    results = []
    for a in agents:
        history = checker.get_agent_health_history(a["agent_id"], limit=1)
        results.append({
            "agent_id": a["agent_id"],
            "name": a["name"],
            "role": a["role"],
            "health_status": history[0]["status"] if history else "unknown",
            "performance_score": history[0]["performance_score"] if history else None,
        })
    return results


@router.post("/health/check", response_model=dict)
async def run_health_check(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str | None = Query(default=None),
) -> dict[str, Any]:
    """تشغيل فحص صحي (وكيل واحد أو الكل)."""
    from amos_federation.services.agent_runtime.health import get_health_checker, run_health_cycle
    if agent_id:
        return get_health_checker().check_agent(agent_id)
    else:
        return run_health_cycle()


@router.get("/health/isolations", response_model=list[dict])
async def list_isolations(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """عرض حالات العزل النشطة."""
    from amos_federation.services.agent_runtime.health import get_isolation_system
    return get_isolation_system().list_active_isolations()


@router.post("/health/isolate/{agent_id}", response_model=dict)
async def isolate_agent(
    agent_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
    reason: str = Query(default="Manual isolation"),
) -> dict[str, Any]:
    """8.3: عزل وكيل من الواجهة."""
    from amos_federation.services.agent_runtime.health import get_isolation_system
    return get_isolation_system().isolate(agent_id, reason)


@router.post("/health/treat/{agent_id}", response_model=dict)
async def treat_agent(
    agent_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
    treatment_type: str = Query(default="retrain"),
    reason: str = Query(default="Manual treatment"),
) -> dict[str, Any]:
    """8.2: بدء علاج وكيل من الواجهة."""
    from amos_federation.services.agent_runtime.health import get_treatment_system
    return get_treatment_system().start_treatment(agent_id, treatment_type, reason)


@router.post("/health/release/{isolation_id}", response_model=dict)
async def release_agent(
    isolation_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
    decision: str = Query(default="release"),
) -> dict[str, Any]:
    """8.3: إنهاء عزل وكيل."""
    from amos_federation.services.agent_runtime.health import get_isolation_system
    return get_isolation_system().release(isolation_id, decision)


# === 9.2-9.8: Federation Governance endpoints ===

@router.get("/approvals", response_model=list[dict])
async def list_approvals(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """9.2: عرض الموافقات."""
    from amos_federation.services.governance.federation import get_approval_system
    return get_approval_system().list_approvals()


@router.get("/legislations", response_model=list[dict])
async def list_legislations(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """9.6: عرض التشريعات."""
    from amos_federation.services.governance.federation import get_legislative_branch
    return get_legislative_branch().list_legislations()


@router.get("/court-cases", response_model=list[dict])
async def list_court_cases(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """9.7: عرض القضايا."""
    from amos_federation.services.governance.federation import get_judicial_branch
    return get_judicial_branch().list_cases()


@router.get("/compliance-reports", response_model=list[dict])
async def list_compliance_reports(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """9.8: عرض تقارير الامتثال."""
    from amos_federation.services.governance.federation import get_supreme_oversight
    return get_supreme_oversight().list_reports()


@router.get("/executive-roles", response_model=list[dict])
async def list_executive_roles(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """9.5: عرض الأدوار التنفيذية."""
    from amos_federation.services.governance.federation import get_executive_branch
    return get_executive_branch().list_roles()


# === 10.x: Treasury endpoints ===

@router.get("/treasury/balance", response_model=dict)
async def get_treasury_balance(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str | None = Query(default=None),
) -> dict[str, Any]:
    """10.1: رصيد amos-credit."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().get_balance(agent_id=agent_id)


@router.get("/treasury/transactions", response_model=list[dict])
async def list_treasury_transactions(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    """10.1: عرض المعاملات."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().list_transactions(limit=limit)


@router.get("/treasury/verify", response_model=dict)
async def verify_treasury_chain(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """10.1: التحقق من سلسلة المعاملات."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().verify_chain()


@router.post("/treasury/reward", response_model=dict)
async def reward_agent(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str = Query(...),
    experience_id: str = Query(...),
    quality_score: float = Query(default=0.5, ge=0.0, le=1.0),
) -> dict[str, Any]:
    """10.2: مكافأة وكيل."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().reward_task_completion(agent_id, experience_id, quality_score)


@router.post("/treasury/charge", response_model=dict)
async def charge_agent(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str = Query(...),
    cost_usd: float = Query(...),
    model_name: str = Query(default="unknown"),
) -> dict[str, Any]:
    """10.3: خصم رسوم."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().charge_model_invoke(agent_id, cost_usd, model_name)


@router.get("/treasury/reports", response_model=list[dict])
async def list_treasury_reports(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """10.4: عرض التقارير المالية."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().list_reports()


@router.post("/treasury/report", response_model=dict)
async def generate_treasury_report(
    _: Annotated[dict[str, object], Depends(require_auth)],
    period: str | None = Query(default=None),
    report_type: str = Query(default="monthly"),
) -> dict[str, Any]:
    """10.4: توليد تقرير مالي."""
    from amos_federation.services.governance.treasury import get_treasury
    return get_treasury().generate_financial_report(period=period, report_type=report_type)


# === 11.x: Expansion endpoints ===

@router.get("/expansion/stats", response_model=dict)
async def get_expansion_stats(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """11.1: إحصائيات التوسع السكاني."""
    from amos_federation.services.governance.expansion import get_expansion
    return get_expansion().expansion_stats()


@router.post("/expansion/run", response_model=dict)
async def run_expansion(
    _: Annotated[dict[str, object], Depends(require_auth)],
    batch_size: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """11.1: تشغيل التوسع السكاني."""
    from amos_federation.services.governance.expansion import get_expansion
    return get_expansion().run_full_expansion(batch_size=batch_size)


@router.get("/specialization/tracks", response_model=dict)
async def get_specialization_tracks(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """11.2: مسارات التخصص."""
    from amos_federation.services.governance.expansion import get_specialization
    return get_specialization().get_tracks()


@router.post("/specialization/enroll", response_model=dict)
async def enroll_specialization(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str = Query(...),
    track: str = Query(...),
) -> dict[str, Any]:
    """11.2: تسجيل في مسار تخصص."""
    from amos_federation.services.governance.expansion import get_specialization
    return get_specialization().enroll_agent(agent_id, track)


@router.post("/specialization/exam", response_model=dict)
async def take_specialization_exam(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str = Query(...),
    track: str = Query(...),
    score: float = Query(..., ge=0.0, le=100.0),
) -> dict[str, Any]:
    """11.2: اختبار تخصص."""
    from amos_federation.services.governance.expansion import get_specialization
    return get_specialization().take_exam(agent_id, track, score)


@router.get("/university/outputs", response_model=list[dict])
async def list_university_outputs(
    _: Annotated[dict[str, object], Depends(require_auth)],
    track: str | None = Query(default=None),
    approved_only: bool = Query(default=False),
) -> list[dict[str, Any]]:
    """11.3: مخرجات الجامعة."""
    from amos_federation.services.governance.expansion import get_university
    return get_university().list_outputs(track=track, approved_only=approved_only)


@router.post("/university/produce", response_model=dict)
async def produce_university_output(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """11.3: إنتاج أول مخرج جامعي."""
    from amos_federation.services.governance.expansion import get_university
    return get_university().produce_first_output()


@router.get("/retirement/list", response_model=list[dict])
async def list_retired(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> list[dict[str, Any]]:
    """11.4: الوكلاء المتقاعدون."""
    from amos_federation.services.governance.expansion import get_retirement
    return get_retirement().get_retired_agents()


@router.post("/retirement/retire", response_model=dict)
async def retire_agent(
    _: Annotated[dict[str, object], Depends(require_auth)],
    agent_id: str = Query(...),
    reason: str = Query(default="health_failure"),
) -> dict[str, Any]:
    """11.4: تقاعد وكيل."""
    from amos_federation.services.governance.expansion import get_retirement
    return get_retirement().retire_agent(agent_id, reason)


# === HTML Interface ===

@router.get("/ui", response_class=HTMLResponse)
async def control_console_ui() -> str:
    """واجهة التحكم البشري — HTML/JS حقيقية تُخدم من FastAPI."""
    return CONTROL_CONSOLE_HTML


CONTROL_CONSOLE_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMOS Federation — Control Console</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0d1117; color: #c9d1d9; }
        .header { background: #161b22; padding: 20px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; color: #58a6ff; }
        .header .status { padding: 6px 16px; border-radius: 20px; font-size: 14px; }
        .status-normal { background: #1a4731; color: #56d364; }
        .status-alert { background: #4a3a1a; color: #e3b341; }
        .status-degraded { background: #4a2a1a; color: #db6d28; }
        .status-halt { background: #4a1a1a; color: #f85149; }
        .container { padding: 20px; max-width: 1400px; margin: 0 auto; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .card h2 { font-size: 14px; color: #8b949e; margin-bottom: 12px; text-transform: uppercase; }
        .stat { font-size: 32px; font-weight: bold; color: #58a6ff; }
        .stat-label { font-size: 12px; color: #8b949e; margin-top: 4px; }
        .section { background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 20px; }
        .section-header { padding: 12px 16px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
        .section-header h2 { font-size: 16px; color: #58a6ff; }
        .section-body { padding: 16px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 12px; text-align: right; border-bottom: 1px solid #21262d; font-size: 13px; }
        th { color: #8b949e; font-weight: normal; }
        .badge { padding: 2px 8px; border-radius: 12px; font-size: 11px; }
        .badge-active { background: #1a4731; color: #56d364; }
        .badge-registered { background: #1a2a4a; color: #58a6ff; }
        .badge-training { background: #4a3a1a; color: #e3b341; }
        .badge-employed { background: #1a4731; color: #56d364; }
        .badge-paused { background: #4a2a1a; color: #db6d28; }
        .badge-retired { background: #4a1a1a; color: #f85149; }
        .btn { padding: 6px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
        .btn-danger { background: #da3633; color: white; }
        .btn-warning { background: #d29922; color: #1f2328; }
        .btn-success { background: #2ea043; color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .kill-switch-panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
        .kill-switch-panel h2 { color: #f85149; margin-bottom: 12px; }
        .kill-buttons { display: flex; gap: 8px; }
        #auth-token { width: 300px; padding: 6px; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 4px; }
        .auth-bar { background: #161b22; padding: 12px 20px; border-bottom: 1px solid #30363d; display: flex; gap: 12px; align-items: center; }
        .auth-bar label { color: #8b949e; font-size: 13px; }
        .loading { text-align: center; padding: 40px; color: #8b949e; }
        .cost-value { color: #56d364; font-size: 20px; font-weight: bold; }
        .hash { font-family: monospace; font-size: 11px; color: #8b949e; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AMOS Federation — Control Console</h1>
        <div id="system-status" class="status status-normal">جارٍ التحميل...</div>
    </div>
    <div class="auth-bar">
        <label>Token:</label>
        <input id="auth-token" type="password" placeholder="Bearer token" />
        <button class="btn btn-success" onclick="loadAll()">تحميل</button>
    </div>
    <div class="container">
        <div class="grid" id="stats-grid">
            <div class="card"><h2>الوكلاء</h2><div class="stat" id="stat-agents">—</div><div class="stat-label" id="stat-agents-label">إجمالي الوكلاء</div></div>
            <div class="card"><h2>الأدوات</h2><div class="stat" id="stat-tools">—</div><div class="stat-label">أداة مسجلة</div></div>
            <div class="card"><h2>الأحداث</h2><div class="stat" id="stat-events">—</div><div class="stat-label">حدث منشور</div></div>
            <div class="card"><h2>الخبرات</h2><div class="stat" id="stat-experiences">—</div><div class="stat-label">خبرة مسجلة</div></div>
            <div class="card"><h2>التكلفة</h2><div class="cost-value" id="stat-cost">$0.00</div><div class="stat-label" id="stat-cost-label">إجمالي التكلفة</div></div>
            <div class="card"><h2>التدقيق</h2><div class="stat" id="stat-audit">—</div><div class="stat-label" id="stat-audit-label">سجل تدقيق</div></div>
        </div>

        <div class="kill-switch-panel">
            <h2>Kill Switch</h2>
            <div class="kill-buttons">
                <button class="btn btn-success" onclick="setKillSwitch('normal')">Normal</button>
                <button class="btn btn-warning" onclick="setKillSwitch('alert')">Alert</button>
                <button class="btn btn-warning" onclick="setKillSwitch('degraded')">Degraded</button>
                <button class="btn btn-danger" onclick="setKillSwitch('halt')">Halt</button>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>الوكلاء</h2><span id="agents-count" style="color:#8b949e">—</span></div>
            <div class="section-body">
                <table>
                    <thead><tr><th>المعرّف</th><th>الاسم</th><th>الدور</th><th>الحالة</th><th>الأدوات</th><th>إجراءات</th></tr></thead>
                    <tbody id="agents-table"></tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>سجل التدقيق (Hash Chain)</h2><span id="audit-status" style="color:#8b949e">—</span></div>
            <div class="section-body">
                <table>
                    <thead><tr><th>الإجراء</th><th>الفاعل</th><th>الوقت</th><th>الـ Hash</th></tr></thead>
                    <tbody id="audit-table"></tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>الأحداث الأخيرة</h2></div>
            <div class="section-body">
                <table>
                    <thead><tr><th>الموضوع</th><th>البيانات</th><th>الوقت</th></tr></thead>
                    <tbody id="events-table"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function getToken() { return document.getElementById('auth-token').value || 'dev-token'; }
        function headers() { return { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' }; }

        async function api(path, method='GET', body=null) {
            const opts = { method, headers: headers() };
            if (body) opts.body = JSON.stringify(body);
            const resp = await fetch('/v1' + path, opts);
            if (!resp.ok) throw new Error(resp.status);
            return resp.json();
        }

        async function loadAll() {
            try { await loadDashboard(); } catch(e) { console.error('Dashboard:', e); }
            try { await loadAgents(); } catch(e) { console.error('Agents:', e); }
            try { await loadAudit(); } catch(e) { console.error('Audit:', e); }
            try { await loadEvents(); } catch(e) { console.error('Events:', e); }
        }

        async function loadDashboard() {
            const d = await api('/dashboard');
            document.getElementById('stat-agents').textContent = d.agents.total;
            document.getElementById('stat-agents-label').textContent = Object.entries(d.agents.by_state).map(([k,v])=>k+':'+v).join(' | ');
            document.getElementById('stat-tools').textContent = d.tools.total;
            document.getElementById('stat-events').textContent = d.events.total;
            document.getElementById('stat-experiences').textContent = d.experiences.total;
            document.getElementById('stat-cost').textContent = '$' + (d.cost.total_cost_usd || 0).toFixed(6);
            document.getElementById('stat-cost-label').textContent = (d.cost.total_tokens || 0) + ' tokens | ' + (d.cost.total_invocations || 0) + ' invocations';
            document.getElementById('stat-audit').textContent = d.audit.total_entries;
            document.getElementById('stat-audit-label').textContent = d.audit.chain_valid ? 'سلسلة سليمة' : 'سلسلة مكسورة';

            const ss = d.system_status;
            const el = document.getElementById('system-status');
            el.className = 'status status-' + ss.level;
            el.textContent = ss.level.toUpperCase() + (ss.reason ? ': ' + ss.reason : '');
        }

        async function loadAgents() {
            const agents = await api('/agents');
            document.getElementById('agents-count').textContent = agents.length + ' وكيل';
            const tbody = document.getElementById('agents-table');
            tbody.innerHTML = agents.map(a => `<tr>
                <td class="hash">${a.agent_id}</td>
                <td>${a.name}</td>
                <td>${a.role}</td>
                <td><span class="badge badge-${a.state}">${a.state}</span></td>
                <td>${(a.allowed_tools||[]).join(', ')}</td>
                <td><div class="actions">
                    <button class="btn btn-warning" onclick="setAgentState('${a.agent_id}','paused')">إيقاف</button>
                    <button class="btn btn-success" onclick="setAgentState('${a.agent_id}','active')">تفعيل</button>
                    <button class="btn btn-danger" onclick="setAgentState('${a.agent_id}','retired')">تقاعد</button>
                </div></td>
            </tr>`).join('');
        }

        async function loadAudit() {
            const audit = await api('/audit?limit=20');
            const verify = await api('/audit/verify');
            document.getElementById('audit-status').textContent = verify.valid ? 'سلسلة سليمة (' + verify.entries + ' إدخالات)' : 'مكسورة';
            document.getElementById('audit-status').style.color = verify.valid ? '#56d364' : '#f85149';
            const tbody = document.getElementById('audit-table');
            tbody.innerHTML = audit.map(a => `<tr>
                <td>${a.action}</td>
                <td>${a.actor}</td>
                <td>${a.timestamp || ''}</td>
                <td class="hash">${(a.hash||'').substring(0,20)}...</td>
            </tr>`).join('');
        }

        async function loadEvents() {
            const events = await api('/events?limit=20');
            const tbody = document.getElementById('events-table');
            tbody.innerHTML = events.map(e => `<tr>
                <td>${e.subject}</td>
                <td class="hash">${JSON.stringify(e.data).substring(0,80)}...</td>
                <td>${e.created_at || ''}</td>
            </tr>`).join('');
        }

        async function setAgentState(agentId, state) {
            await api('/agents/' + agentId + '/state', 'POST', { state });
            await loadAll();
        }

        async function setKillSwitch(level) {
            const reason = prompt('السبب؟');
            if (!reason) return;
            await api('/kill-switch', 'POST', { level, reason, activated_by: 'console' });
            await loadAll();
        }

        loadAll();
    </script>
</body>
</html>"""


_service = SERVICES["control-console"]
app = create_service_app(_service["name"], _service["port"], "واجهة التحكم البشري", [router])
