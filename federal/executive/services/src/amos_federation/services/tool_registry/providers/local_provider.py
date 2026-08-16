"""الهدف: مزوِّد محلّي يحقّق العقد فوق عملية فرعية على المضيف نفسه.

النطاق: services/tool_registry/providers
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

هذا المزوِّد ليس جديدًا في جوهره: هو تغليف لما كان يفعله
`tool_registry/sandbox.py` أصلًا — `subprocess` مع `RLIMIT_AS` ومهلة وبيئة
مقلَّصة. الجديد أنه صار يحقّق `SandboxProvider`، فيمكن استبداله بـModal أو E2B
بلا تغيير في مكان الاستدعاء.

صدق مخرَجه **REAL**: عملية حقيقية، ورمز خروجها حقيقي، ومخرَجها غير مُلفَّق.

وحدّه المُعلَن بالسلب — وهذا ما يجعله غير كافٍ وحده ويجعل Modal/E2B ضرورة لا
ترفًا: العملية تعمل على **المضيف نفسه**، تحت المستخدم نفسه، ونظام الملفّات
مشترك خارج مجلّد العمل، ولا عزل شبكي، ولا مساحة أسماء منفصلة. فقيود الموارد
والبيئة المقلَّصة تخفّض الخطر ولا تلغيه، و`network.enforcement` عنده
`DECLARED_ONLY` لا `PROVIDER_ENFORCED`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid

from amos_federation.services.executive_core.fidelity import ExecutionFidelity
from amos_federation.services.tool_registry.providers import network, secrets
from amos_federation.services.tool_registry.providers.contract import (
    ExecutionRequest,
    ExecutionResult,
    ProviderAvailability,
    SandboxHandle,
    SandboxProvider,
    SandboxSpec,
)

#: قالب يفرض حدّ الذاكرة داخل العملية نفسها قبل تنفيذ كود الأداة.
_RLIMIT_PREAMBLE = """import resource as _r
try:
    _r.setrlimit(_r.RLIMIT_AS, ({limit}, {limit}))
except Exception:
    pass
"""


class LocalSubprocessProvider(SandboxProvider):
    """تنفيذ على المضيف بعملية فرعية مقيَّدة — REAL بعزل جزئي مُعلَن."""

    name = "local"
    fidelity = ExecutionFidelity.REAL

    def availability(self) -> ProviderAvailability:
        """متاح دائمًا إن وُجد مُفسِّر Python — لا اعتماد ولا شبكة."""
        interpreter = shutil.which("python3")
        if interpreter is None:
            return ProviderAvailability(
                provider=self.name,
                available=False,
                fidelity=ExecutionFidelity.UNAVAILABLE.value,
                reason="لا مُفسِّر python3 على المضيف",
                missing_package="python3",
            )
        return ProviderAvailability(
            provider=self.name,
            available=True,
            fidelity=self.fidelity.value,
            reason="عملية فرعية على المضيف — عزل جزئي (DECLARED_ONLY للشبكة)",
        )

    def create_sandbox(self, spec: SandboxSpec) -> SandboxHandle:
        self.assert_usable()
        network.normalize_policy(spec.network_policy)
        secrets.assert_allowlist_is_safe(spec.secret_allowlist)
        workspace = tempfile.mkdtemp(prefix=f"amos_sbx_{spec.tool_id}_")
        return SandboxHandle(
            sandbox_id=f"local-{uuid.uuid4().hex[:12]}",
            provider=self.name,
            spec=spec,
            native=workspace,
        )

    def execute(self, handle: SandboxHandle, request: ExecutionRequest) -> ExecutionResult:
        self._guard_handle(handle)
        spec = handle.spec
        workspace = str(handle.native)
        timeout = request.timeout_seconds or spec.timeout_seconds

        env, plan = secrets.build_sandbox_env(
            spec.secret_allowlist,
            extra={
                "HOME": workspace,
                "TMPDIR": workspace,
                "AMOS_SANDBOX_ID": handle.sandbox_id,
                "AMOS_SANDBOX_PROVIDER": self.name,
                "AMOS_SANDBOX_NETWORK_POLICY": spec.network_policy,
            },
        )

        if request.command:
            argv = list(request.command)
        else:
            script = os.path.join(workspace, "amos_tool_entry.py")
            preamble = _RLIMIT_PREAMBLE.format(limit=spec.memory_limit_mb * 1024 * 1024)
            with open(script, "w", encoding="utf-8") as handle_file:
                handle_file.write(preamble + request.code)
            argv = ["python3", script]

        started = time.monotonic()
        try:
            proc = subprocess.run(  # noqa: S603
                argv,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workspace,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return self.result(
                handle,
                request,
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
                exit_code=None,
                duration_ms=int((time.monotonic() - started) * 1000),
                timed_out=True,
                secrets_injected=plan.injected,
                error=f"timeout بعد {timeout}s",
            )
        except OSError as exc:
            return self.result(
                handle,
                request,
                stdout="",
                stderr=str(exc),
                exit_code=None,
                duration_ms=int((time.monotonic() - started) * 1000),
                secrets_injected=plan.injected,
                error=f"os_error: {exc}",
            )

        return self.result(
            handle,
            request,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            exit_code=proc.returncode,
            duration_ms=int((time.monotonic() - started) * 1000),
            secrets_injected=plan.injected,
        )

    def terminate(self, handle: SandboxHandle) -> None:
        """لا عملية طويلة العمر هنا — الإنهاء تعليم المقبض، ومتكرِّر بلا خطأ."""
        if handle.provider != self.name:
            return
        handle.terminated = True

    def cleanup(self, handle: SandboxHandle) -> None:
        if handle.provider != self.name:
            return
        handle.terminated = True
        if handle.native:
            shutil.rmtree(str(handle.native), ignore_errors=True)
            handle.native = None
