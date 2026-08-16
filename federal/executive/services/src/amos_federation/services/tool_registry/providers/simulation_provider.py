"""الهدف: مزوِّد محاكاة — مسار اختبار صريح، ممنوع في الإنتاج.

النطاق: services/tool_registry/providers
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

سبب وجوده: اختبار عقد المزوِّدات نفسه (الترتيب، المهلة، رمز الخروج، الإنهاء،
النَسَب) يحتاج مزوِّدًا حتميًّا لا يخرج من العملية. وسبب تقييده أشدّ: مزوِّد
محاكاة متاح في الإنتاج هو الطريق الأقصر إلى نجاح كاذب.

القيد المُنفَّذ في `availability()`، لا في التوثيق:

- في بيئة إنتاج (`production` / `prod` / `staging`) يُعلن **غير متاح** دائمًا،
  ولا يُفتَح بأي متغيّر.
- خارجها يلزمه إذن صريح: بيئة اختبار (`test`/`testing`) أو
  `AMOS_SANDBOX_ALLOW_SIMULATION=1`.

وكل نتيجة منه تحمل `execution_fidelity = "SIMULATION"` مع سبب مُسمّى — لا
يستطيع الإفلات من ذلك لأن `SandboxProvider.result` ترفض إعلان غير REAL بلا سبب.
وهو **ليس** مسار سقوط: لا شيء في `selection.py` يهبط إليه عند فشل مزوِّد حقيقي.
"""

from __future__ import annotations

import os
import time

from amos_federation.services.executive_core.fidelity import ExecutionFidelity
from amos_federation.services.tool_registry.providers import secrets
from amos_federation.services.tool_registry.providers.contract import (
    ExecutionRequest,
    ExecutionResult,
    ProviderAvailability,
    SandboxHandle,
    SandboxProvider,
    SandboxSpec,
)

#: بيئات يُحظَر فيها مزوِّد المحاكاة حظرًا غير قابل للتعطيل.
FORBIDDEN_ENVIRONMENTS: frozenset[str] = frozenset({"production", "prod", "staging"})

#: بيئات يُسمح فيها بلا متغيّر إضافي.
TEST_ENVIRONMENTS: frozenset[str] = frozenset({"test", "testing"})

#: السبب المرفق بكل نتيجة — نصٌّ ثابت يُفحَص في الاختبارات.
SIMULATION_REASON = "مزوِّد محاكاة صريح لاختبار العقد — ليس تنفيذًا حقيقيًّا"


class SimulationProvider(SandboxProvider):
    """مزوِّد حتمي مُعلَن كمحاكاة، لاختبار العقد وحده."""

    name = "simulation"
    fidelity = ExecutionFidelity.SIMULATION

    def __init__(self, exit_code: int = 0, stdout: str = "", stderr: str = "") -> None:
        self._exit_code = exit_code
        self._stdout = stdout
        self._stderr = stderr

    @staticmethod
    def _environment() -> str:
        return os.environ.get("AMOS_ENVIRONMENT", "development").strip().lower()

    def availability(self) -> ProviderAvailability:
        environment = self._environment()
        if environment in FORBIDDEN_ENVIRONMENTS:
            return ProviderAvailability(
                provider=self.name,
                available=False,
                fidelity=ExecutionFidelity.UNAVAILABLE.value,
                reason=f"مزوِّد المحاكاة محظور في بيئة '{environment}'",
            )
        allowed = environment in TEST_ENVIRONMENTS or os.environ.get(
            "AMOS_SANDBOX_ALLOW_SIMULATION"
        ) in {"1", "true", "TRUE", "yes"}
        if not allowed:
            return ProviderAvailability(
                provider=self.name,
                available=False,
                fidelity=ExecutionFidelity.UNAVAILABLE.value,
                reason="يلزمه إذن صريح: بيئة اختبار أو AMOS_SANDBOX_ALLOW_SIMULATION=1",
            )
        return ProviderAvailability(
            provider=self.name,
            available=True,
            fidelity=self.fidelity.value,
            reason=SIMULATION_REASON,
        )

    def create_sandbox(self, spec: SandboxSpec) -> SandboxHandle:
        self.assert_usable()
        secrets.assert_allowlist_is_safe(spec.secret_allowlist)
        return SandboxHandle(
            sandbox_id=f"simulation-{spec.tool_id}",
            provider=self.name,
            spec=spec,
            native={"executions": 0},
        )

    def execute(self, handle: SandboxHandle, request: ExecutionRequest) -> ExecutionResult:
        self._guard_handle(handle)
        handle.native["executions"] += 1
        _env, plan = secrets.build_sandbox_env(handle.spec.secret_allowlist)
        started = time.monotonic()
        stdout = self._stdout or f"SIMULATION::{handle.spec.tool_id}::{len(request.code)}"
        return self.result(
            handle,
            request,
            stdout=stdout,
            stderr=self._stderr,
            exit_code=self._exit_code,
            fidelity_reason=SIMULATION_REASON,
            duration_ms=int((time.monotonic() - started) * 1000),
            secrets_injected=plan.injected,
            error=None if self._exit_code == 0 else "simulated_failure",
        )

    def terminate(self, handle: SandboxHandle) -> None:
        if handle.provider != self.name:
            return
        handle.terminated = True

    def cleanup(self, handle: SandboxHandle) -> None:
        if handle.provider != self.name:
            return
        handle.terminated = True
        handle.native = None
