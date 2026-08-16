"""الهدف: عقد واحد لتنفيذ الأدوات في صندوق رملي — أيَّ كان المزوِّد.

النطاق: services/tool_registry/providers
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

قبل هذه الوحدة كان في المستودع صندوقان رمليان بلا عقد يجمعهما: واحد في
`agent_runtime/sandbox.py` كله دوالّ `_mock_*`، وواحد في
`tool_registry/sandbox.py` ينفّذ عملية فرعية حقيقية على المضيف نفسه. ولا واحد
منهما يعرف معنى «مزوِّد»، فإضافة Modal أو E2B كانت ستعني استيرادهما في مكان
التنفيذ مباشرةً — أي ربط بيئة تشغيل الوكلاء بمزوِّد بعينه.

ما تفرضه هذه الوحدة:

- **دورة حياة مُسمّاة:** `create_sandbox` ثم `execute` ثم `terminate` ثم
  `cleanup`. لا تنفيذ بلا صندوق مُنشأ، ولا صندوق يُترك بلا إنهاء.
- **مخرَج موحَّد:** `stdout` و`stderr` و`exit_code` — بهذه الأسماء عند كل
  مزوِّد. مزوِّد لا يعطي `exit_code` حقيقيًّا لا يخترعه صفرًا.
- **بيانات نَسَب إلزامية:** `task_id` و`agent_id` و`execution_id` و
  `correlation_id` و`tool_id` و`provider` و`sandbox_id` و`execution_fidelity`
  مرفقة بكل نتيجة، فلا تنفيذ مجهول الأصل في السجل.
- **الغياب يُقال:** `ProviderUnavailableError` حالتها `UNAVAILABLE`، ولا
  تُترجَم إلى `SIMULATION`. الفرق بينهما هو الفرق بين «لم يُنفَّذ» و«نُفِّذ
  زائفًا بقصد مُعلَن».
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from amos_federation.services.executive_core.fidelity import ExecutionFidelity

#: أسماء الحقول التي يجب أن تحملها كل نتيجة تنفيذ — تُفحَص في الاختبارات.
REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "task_id",
    "agent_id",
    "execution_id",
    "correlation_id",
    "tool_id",
    "provider",
    "sandbox_id",
    "execution_fidelity",
)

#: عقد دورة الحياة الذي يجب أن يحقّقه كل مزوِّد.
PROVIDER_CONTRACT_METHODS: tuple[str, ...] = (
    "create_sandbox",
    "execute",
    "terminate",
    "cleanup",
)


class SandboxProviderError(RuntimeError):
    """خطأ في طبقة المزوِّدات — الأصل الذي ترث منه كل الأخطاء المُسمّاة."""

    #: الصدق الذي يُعلَن عند هذا الخطأ. لا يُستنتج في مكان الاستدعاء.
    fidelity: ExecutionFidelity = ExecutionFidelity.UNAVAILABLE


class ProviderUnavailableError(SandboxProviderError):
    """المزوِّد غير قابل للاستعمال: اعتماد ناقص أو حزمة غائبة أو خدمة ساقطة.

    هذه ليست فشل تنفيذ. لم يُنفَّذ شيء أصلًا، ولذلك حالتها `UNAVAILABLE` ولا
    يجوز لأي مسار أن يحوّلها إلى `SIMULATION` ليبدو الطلب ناجحًا.
    """

    fidelity: ExecutionFidelity = ExecutionFidelity.UNAVAILABLE


class ProviderCredentialsMissingError(ProviderUnavailableError):
    """اعتماد المزوِّد غائب — تُسمّى المتغيّرات الناقصة لا قيمها."""


class ProviderExecutionError(SandboxProviderError):
    """التنفيذ بدأ فعلًا عند المزوِّد ثم فشل — فشل حقيقي يُنشَر كما هو."""

    fidelity: ExecutionFidelity = ExecutionFidelity.REAL


class SandboxTimeoutError(ProviderExecutionError):
    """انقضت المدّة المسموحة — الصندوق يُنهى ولا تُلفَّق نتيجة."""


class SandboxNotCreatedError(SandboxProviderError):
    """طُلب تنفيذ بلا `create_sandbox` — انتهاك ترتيب دورة الحياة."""

    fidelity: ExecutionFidelity = ExecutionFidelity.UNAVAILABLE


class SandboxTerminatedError(SandboxProviderError):
    """طُلب تنفيذ في صندوق أُنهي — لا إحياء صامتًا."""

    fidelity: ExecutionFidelity = ExecutionFidelity.UNAVAILABLE


@dataclass(frozen=True)
class ExecutionContext:
    """نَسَب التنفيذ — من أي مهمّة ولأي وكيل وبأي ارتباط.

    `execution_id` و`correlation_id` يُولَّدان إن لم يُمرَّرا، لأن تنفيذًا بلا
    معرّف لا يمكن تتبّعه في السجل بعد وقوعه.
    """

    tool_id: str
    agent_id: str | None = None
    task_id: str | None = None
    execution_id: str = field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:12]}")
    correlation_id: str = field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:12]}")

    def as_metadata(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True)
class SandboxSpec:
    """ما يُطلب من الصندوق قبل إنشائه — لا إعداد ضمني بعد الإنشاء.

    `secret_allowlist` أسماء الأسرار المسموح تمريرها لهذه الأداة بعينها. القائمة
    الفارغة تعني بيئة بلا سرّ واحد، وهو الافتراضي المقصود: لا وراثة شاملة
    لبيئة المضيف.
    """

    tool_id: str
    timeout_seconds: int = 10
    memory_limit_mb: int = 256
    runtime: str = "python3"
    network_policy: str = "DENY"
    secret_allowlist: tuple[str, ...] = ()
    workdir: str = "/tmp/amos_sandbox"

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds يجب أن يكون موجبًا")
        if self.memory_limit_mb <= 0:
            raise ValueError("memory_limit_mb يجب أن يكون موجبًا")


@dataclass
class SandboxHandle:
    """مقبض صندوق قائم عند مزوِّد — معرّفه عند المزوِّد لا معرّف محلّي مُخترَع."""

    sandbox_id: str
    provider: str
    spec: SandboxSpec
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    terminated: bool = False
    native: Any = None

    def as_metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "sandbox_id": self.sandbox_id,
            "sandbox_created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ExecutionRequest:
    """طلب تنفيذ داخل صندوق قائم."""

    code: str = ""
    command: tuple[str, ...] = ()
    context: ExecutionContext | None = None
    timeout_seconds: int | None = None

    def __post_init__(self) -> None:
        if not self.code and not self.command:
            raise ValueError("طلب التنفيذ يلزمه `code` أو `command`")


@dataclass(frozen=True)
class ExecutionResult:
    """نتيجة تنفيذ واحدة — بمخرَج موحَّد ونَسَب كامل وصدق مُعلَن.

    `exit_code = None` تعني أن المزوِّد لم يُعطِ رمز خروج، ولا يُخترَع صفرًا:
    الصفر المُخترَع يعني «نجح» زورًا.
    """

    stdout: str
    stderr: str
    exit_code: int | None
    provider: str
    sandbox_id: str
    execution_fidelity: str
    tool_id: str
    execution_id: str
    correlation_id: str
    agent_id: str | None = None
    task_id: str | None = None
    duration_ms: int | None = None
    timed_out: bool = False
    fidelity_reason: str | None = None
    fallback_from: str | None = None
    fallback_reason: str | None = None
    network_policy: str = "DENY"
    secrets_injected: tuple[str, ...] = ()
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None and self.exit_code == 0 and not self.timed_out

    def as_dict(self) -> dict[str, Any]:
        """قاموس مُسطَّح — يُنشَر في الأحداث والسجل كما هو."""
        payload: dict[str, Any] = {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "provider": self.provider,
            "sandbox_id": self.sandbox_id,
            "execution_fidelity": self.execution_fidelity,
            "tool_id": self.tool_id,
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "network_policy": self.network_policy,
            "secrets_injected": list(self.secrets_injected),
            "succeeded": self.succeeded,
        }
        if self.fidelity_reason:
            payload["fidelity_reason"] = self.fidelity_reason
        if self.fallback_from:
            payload["fallback_from"] = self.fallback_from
            payload["fallback_reason"] = self.fallback_reason
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class ProviderAvailability:
    """هل المزوِّد قابل للاستعمال الآن، وإن لا فبأي سبب مُسمّى."""

    provider: str
    available: bool
    fidelity: str
    reason: str | None = None
    missing_credentials: tuple[str, ...] = ()
    missing_package: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "available": self.available,
            "execution_fidelity": self.fidelity,
            "reason": self.reason,
            "missing_credentials": list(self.missing_credentials),
            "missing_package": self.missing_package,
        }


class SandboxProvider(ABC):
    """العقد الذي يحقّقه كل مزوِّد صندوق رملي.

    قاعدة صارمة على المُنفِّذات: `__init__` لا يتّصل بالشبكة ولا يستورد حزمة
    المزوِّد. الاستيراد يقع داخل `create_sandbox`/`availability()` وحدهما، حتى
    يبقى استيراد الوحدة رخيصًا وحتى لا يسقط النظام كلّه لغياب حزمة مزوِّد غير
    مُختار.
    """

    #: اسم المزوِّد كما يُكتَب في `SANDBOX_PROVIDER` ويظهر في كل نتيجة.
    name: str = "abstract"

    #: صدق مخرَج هذا المزوِّد عند نجاحه.
    fidelity: ExecutionFidelity = ExecutionFidelity.UNAVAILABLE

    @abstractmethod
    def availability(self) -> ProviderAvailability:
        """هل يمكن الاستعمال الآن — بلا إنشاء صندوق وبلا كتم سبب الغياب."""

    @abstractmethod
    def create_sandbox(self, spec: SandboxSpec) -> SandboxHandle:
        """إنشاء صندوق وفق المواصفة.

        Raises:
            ProviderUnavailableError: إن كان المزوِّد غير قابل للاستعمال.
        """

    @abstractmethod
    def execute(
        self,
        handle: SandboxHandle,
        request: ExecutionRequest,
    ) -> ExecutionResult:
        """تنفيذ داخل صندوق قائم وإرجاع مخرَج موحَّد.

        Raises:
            SandboxNotCreatedError: إن لم يكن المقبض لهذا المزوِّد.
            SandboxTerminatedError: إن كان الصندوق مُنهىً.
        """

    @abstractmethod
    def terminate(self, handle: SandboxHandle) -> None:
        """إنهاء الصندوق عند المزوِّد — متكرِّر الاستدعاء بلا خطأ."""

    @abstractmethod
    def cleanup(self, handle: SandboxHandle) -> None:
        """تنظيف ما تبقّى محليًّا بعد الإنهاء — متكرِّر الاستدعاء بلا خطأ."""

    def assert_usable(self) -> None:
        """ارفع الغياب صراحةً قبل أي محاولة إنشاء."""
        state = self.availability()
        if state.available:
            return
        if state.missing_credentials:
            raise ProviderCredentialsMissingError(
                f"{self.name}: اعتماد ناقص — {', '.join(state.missing_credentials)}"
            )
        raise ProviderUnavailableError(f"{self.name}: {state.reason or 'غير متاح'}")

    def _guard_handle(self, handle: SandboxHandle) -> None:
        """امنع التنفيذ في مقبض ليس لهذا المزوِّد أو في صندوق مُنهىً."""
        if handle.provider != self.name:
            raise SandboxNotCreatedError(f"المقبض للمزوِّد '{handle.provider}' لا '{self.name}'")
        if handle.terminated:
            raise SandboxTerminatedError(f"الصندوق '{handle.sandbox_id}' مُنهىً")

    def result(
        self,
        handle: SandboxHandle,
        request: ExecutionRequest,
        *,
        stdout: str,
        stderr: str,
        exit_code: int | None,
        fidelity: ExecutionFidelity | None = None,
        fidelity_reason: str | None = None,
        duration_ms: int | None = None,
        timed_out: bool = False,
        secrets_injected: tuple[str, ...] = (),
        error: str | None = None,
    ) -> ExecutionResult:
        """ابنِ نتيجة موحَّدة — المسار الوحيد لبناء `ExecutionResult` في المُنفِّذات.

        وجود هذه الدالّة يمنع مزوِّدًا من نسيان حقل نَسَب أو من إعلان صدق مختلف
        عن صدقه المُصرَّح.
        """
        context = request.context or ExecutionContext(tool_id=handle.spec.tool_id)
        declared = fidelity or self.fidelity
        if declared is not ExecutionFidelity.REAL and not fidelity_reason:
            raise ValueError(f"إعلان {declared.value} يلزمه سبب مُسمّى")
        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            provider=self.name,
            sandbox_id=handle.sandbox_id,
            execution_fidelity=declared.value,
            tool_id=context.tool_id,
            execution_id=context.execution_id,
            correlation_id=context.correlation_id,
            agent_id=context.agent_id,
            task_id=context.task_id,
            duration_ms=duration_ms,
            timed_out=timed_out,
            fidelity_reason=fidelity_reason,
            network_policy=handle.spec.network_policy,
            secrets_injected=secrets_injected,
            error=error,
        )
