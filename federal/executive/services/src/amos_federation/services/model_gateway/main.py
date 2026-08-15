"""
AMOS-Federation Model Gateway Service
الهدف: توجيه طلبات النماذج إلى مزود خارجي (Claude) مع fallback محلي حتمي + تتبع التكلفة + Shadow Testing
النطاق: خدمة model-gateway على المنفذ 8004
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import time
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from fastapi import HTTPException
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.config import settings
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.model_gateway.shadow import (
    InMemoryShadowStore,
    _alpha_response,
    _beta_response,
    _text_similarity,
)

router = APIRouter(prefix="/v1", tags=["model-gateway"])

# Cost tracking: تكلفة التقديم بالدولار لكل ألف رمز
COST_PER_1K_TOKENS = {
    "local-fallback": 0.0,
    "alpha-local": 0.0,
    "beta-candidate": 0.0,
    "claude-sonnet-4": 0.015,
    "claude-opus-4": 0.075,
}

# Cost log
_cost_log: list[dict[str, Any]] = []
_shadow_store = InMemoryShadowStore()


class ModelInvokeRequest(BaseModel):
    """طلب استدعاء نموذج."""

    prompt: str = Field(min_length=1, max_length=50000)
    model: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ModelInvokeResponse(BaseModel):
    """استجابة استدعاء نموذج."""

    text: str
    model_used: str
    tokens_used: int
    latency_ms: int
    source: str  # "external" أو "local_fallback"
    cost_usd: float = 0.0


class ModelRouteResponse(BaseModel):
    """استجابة توجيه نموذج."""

    recommended_model: str
    available_models: list[str]
    fallback_chain: list[str]


def _local_fallback(prompt: str, max_tokens: int) -> tuple[str, int]:
    """مولد حتمي محلي عند غياب مفتاح Claude API."""
    prompt_preview = prompt[:200]
    text = (
        f"[local-fallback] تم استلام الطلب: \"{prompt_preview}...\". "
        f"لا يتوفر مفتاح Claude API — هذه استجابة محلية حتمية للاختبارات."
    )
    tokens = len(text.split())
    return text, tokens


async def _invoke_claude(prompt: str, model: str, max_tokens: int) -> tuple[str, int]:
    """استدعاء Claude API عند توفر المفتاح."""
    import httpx

    api_key = settings.claude_api_key
    if not api_key:
        raise ValueError("لا يتوفر مفتاح Claude API")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        data = response.json()
        text = data["content"][0]["text"]
        tokens = data.get("usage", {}).get("output_tokens", len(text.split()))
        return text, tokens


@router.post("/models/route", response_model=ModelRouteResponse)
async def route_model(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ModelRouteResponse:
    """توجيه النموذج الموصى به مع سلسلة fallback."""
    default = settings.default_model
    available = [default] if settings.claude_api_key else ["local-fallback"]
    fallback = [default, "local-fallback"] if settings.claude_api_key else ["local-fallback"]
    return ModelRouteResponse(
        recommended_model=available[0],
        available_models=available,
        fallback_chain=fallback,
    )


@router.post("/models/invoke", response_model=ModelInvokeResponse)
async def invoke_model(
    request: ModelInvokeRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> ModelInvokeResponse:
    """استدعاء نموذج خارجي مع fallback محلي عند عدم توفر المفتاح."""
    model = request.model or settings.default_model
    start = time.monotonic()
    source = "external"
    try:
        if not settings.claude_api_key:
            raise ValueError("لا يتوفر مفتاح Claude API")
        text, tokens = await _invoke_claude(request.prompt, model, request.max_tokens)
    except Exception:
        text, tokens = _local_fallback(request.prompt, request.max_tokens)
        source = "local_fallback"
        model = "local-fallback"
    latency = int((time.monotonic() - start) * 1000)
    cost = round(tokens * COST_PER_1K_TOKENS.get(model, 0.0) / 1000, 6)
    _cost_log.append({
        "invocation_id": f"inv-{uuid.uuid4()}",
        "timestamp": datetime.now(UTC).isoformat(),
        "model": model,
        "tokens": tokens,
        "cost_usd": cost,
        "latency_ms": latency,
        "source": source,
    })
    return ModelInvokeResponse(
        text=text,
        model_used=model,
        tokens_used=tokens,
        latency_ms=latency,
        source=source,
        cost_usd=cost,
    )


class ShadowTestRequest(BaseModel):
    """طلب اختبار shadow بين نموذجين."""

    prompt: str = Field(min_length=1, max_length=50000)


@router.post("/shadow/test", response_model=dict, status_code=status.HTTP_201_CREATED)
async def run_shadow_test(
    request: ShadowTestRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تشغيل اختبار shadow: توجيه الطلب لكلا النموذجين (ألفا + بيتا) ومقارنة النتائج."""
    alpha = _alpha_response(request.prompt)
    beta = _beta_response(request.prompt)
    return _shadow_store.record({"prompt": request.prompt, "alpha": alpha, "beta": beta})


@router.get("/shadow/results", response_model=list[dict])
async def get_shadow_results(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض نتائج اختبارات shadow."""
    return _shadow_store.list_all(limit=limit)


@router.get("/shadow/results/{shadow_id}", response_model=dict)
async def get_shadow_result(
    shadow_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع نتيجة shadow بالمعرّف."""
    result = _shadow_store.get(shadow_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="نتيجة shadow غير موجودة")
    return result


@router.get("/shadow/stats", response_model=dict)
async def shadow_stats(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """ملخص إحصائيات shadow testing."""
    return _shadow_store.summary()


@router.get("/cost/summary", response_model=dict)
async def cost_summary(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """ملخص التكاليف لكل النماذج."""
    total_cost = sum(r["cost_usd"] for r in _cost_log)
    by_model: dict[str, dict[str, float]] = {}
    for entry in _cost_log:
        m = entry["model"]
        if m not in by_model:
            by_model[m] = {"invocations": 0, "total_tokens": 0, "total_cost": 0.0}
        by_model[m]["invocations"] += 1
        by_model[m]["total_tokens"] += entry["tokens"]
        by_model[m]["total_cost"] += entry["cost_usd"]
    for m in by_model:
        by_model[m]["total_cost"] = round(by_model[m]["total_cost"], 6)
    return {
        "total_invocations": len(_cost_log),
        "total_cost_usd": round(total_cost, 6),
        "by_model": by_model,
    }


# === Model Layer endpoints ===

@router.get("/models/cost-summary", response_model=dict)
async def get_persistent_cost_summary(
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """ملخص التكلفة الدائم من DB."""
    from amos_federation.services.model_gateway.model_layer import get_model_layer
    return get_model_layer().get_cost_summary()


@router.post("/models/invoke-cached", response_model=dict)
async def invoke_model_cached(
    request: ModelInvokeRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """استدعاء نموذج مع caching و cost tracking دائم."""
    from amos_federation.services.model_gateway.model_layer import get_model_layer
    model = request.model or settings.default_model or "local-fallback"
    return get_model_layer().invoke_with_cache(
        request.prompt, model, request.max_tokens
    )


@router.post("/models/benchmark", response_model=dict)
async def benchmark_models(
    _: Annotated[dict[str, object], Depends(require_auth)],
    prompts: list[str] = Query(...),
    models: list[str] = Query(default=["local-fallback"]),
) -> dict[str, Any]:
    """مقارنة أداء النماذج."""
    from amos_federation.services.model_gateway.model_layer import get_model_layer
    return get_model_layer().benchmark_models(prompts, models)


_service = SERVICES["model-gateway"]
app = create_service_app(_service["name"], _service["port"], "توجيه واستدعاء النماذج + Shadow Testing", [router])
