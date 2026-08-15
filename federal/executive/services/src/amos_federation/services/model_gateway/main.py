"""
AMOS-Federation Model Gateway Service
الهدف: توجيه طلبات النماذج إلى مزود خارجي (Claude) مع fallback محلي حتمي
النطاق: خدمة model-gateway على المنفذ 8004
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.common.config import settings
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app

router = APIRouter(prefix="/v1", tags=["model-gateway"])


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
    return ModelInvokeResponse(
        text=text,
        model_used=model,
        tokens_used=tokens,
        latency_ms=latency,
        source=source,
    )


_service = SERVICES["model-gateway"]
app = create_service_app(_service["name"], _service["port"], "توجيه واستدعاء النماذج", [router])
