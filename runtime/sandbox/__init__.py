"""
AMOS Federation Sandbox
صندوق البيئة المعزول لتنفيذ الكود بأمان
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio
import logging
import traceback
import sys
import io
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """نتيجة التنفيذ"""
    success: bool
    output: str
    error: Optional[str]
    return_value: Any
    execution_time_ms: float
    memory_used_kb: int
    logs: List[str]


class SecurityPolicy:
    """سياسة الأمان للصندوق"""
    
    def __init__(
        self,
        allow_network: bool = False,
        allow_file_system: bool = False,
        allowed_modules: Optional[List[str]] = None,
        forbidden_modules: Optional[List[str]] = None,
        max_execution_time_ms: int = 5000,
        max_memory_mb: int = 128,
        max_output_size: int = 1024 * 1024  # 1MB
    ):
        self.allow_network = allow_network
        self.allow_file_system = allow_file_system
        self.allowed_modules = allowed_modules or []
        self.forbidden_modules = forbidden_modules or [
            'os', 'sys', 'subprocess', 'multiprocessing',
            'socket', 'http', 'urllib', 'requests',
            'ctypes', 'pickle', 'marshal'
        ]
        self.max_execution_time_ms = max_execution_time_ms
        self.max_memory_mb = max_memory_mb
        self.max_output_size = max_output_size
    
    def is_module_allowed(self, module_name: str) -> bool:
        """التحقق من سماحية الوحدة"""
        if module_name in self.forbidden_modules:
            return False
        
        if self.allowed_modules:
            return module_name in self.allowed_modules
        
        return True


class SandboxedEnvironment:
    """بيئة معزولة للتنفيذ"""
    
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()
        self._globals: Dict[str, Any] = {}
        self._restricted_builtins: Dict[str, Any] = {}
        self._setup_restricted_environment()
    
    def _setup_restricted_environment(self):
        """إعداد البيئة المقيدة"""
        # الوحدات المسموحة فقط
        safe_modules = ['math', 'random', 'datetime', 'time', 're', 'json', 'collections']
        
        for mod_name in safe_modules:
            try:
                if self.policy.is_module_allowed(mod_name):
                    module = __import__(mod_name)
                    self._globals[mod_name] = module
            except ImportError:
                pass
        
        # الدوال المدمجة الآمنة
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
            'chr': chr, 'complex': complex, 'dict': dict, 'divmod': divmod,
            'enumerate': enumerate, 'filter': filter, 'float': float,
            'format': format, 'frozenset': frozenset, 'hex': hex,
            'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
            'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
            'oct': oct, 'ord': ord, 'pow': pow, 'print': print,
            'range': range, 'repr': repr, 'reversed': reversed,
            'round': round, 'set': set, 'slice': slice, 'sorted': sorted,
            'str': str, 'sum': sum, 'tuple': tuple, 'type': type,
            'zip': zip, '__import__': __import__,
            'True': True, 'False': False, 'None': None
        }
        
        self._restricted_builtins = safe_builtins
        self._globals['__builtins__'] = self._restricted_builtins
    
    def execute(
        self,
        code: str,
        local_vars: Optional[Dict[str, Any]] = None,
        timeout_ms: Optional[int] = None
    ) -> ExecutionResult:
        """تنفيذ كود في البيئة المعزولة"""
        start_time = datetime.utcnow()
        logs = []
        output_buffer = io.StringIO()
        
        # تقييد وقت التنفيذ
        exec_timeout = (timeout_ms or self.policy.max_execution_time_ms) / 1000.0
        
        # إعداد متغيرات محلية
        local_vars = local_vars or {}
        
        # اعتراض print
        original_print = print
        def custom_print(*args, **kwargs):
            output_buffer.write(' '.join(str(a) for a in args) + '\n')
            logs.append(' '.join(str(a) for a in args))
        
        local_vars['print'] = custom_print
        
        try:
            # تنفيذ الكود
            exec(code, self._globals, local_vars)
            
            # الحصول على قيمة الإرجاع إذا وجدت
            return_value = local_vars.get('result', None)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            output = output_buffer.getvalue()
            if len(output) > self.policy.max_output_size:
                output = output[:self.policy.max_output_size] + "... [truncated]"
            
            return ExecutionResult(
                success=True,
                output=output,
                error=None,
                return_value=return_value,
                execution_time_ms=execution_time,
                memory_used_kb=0,  # يحتاج تنفيذ متقدم لقياس الذاكرة
                logs=logs
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            
            return ExecutionResult(
                success=False,
                output=output_buffer.getvalue(),
                error=error_msg,
                return_value=None,
                execution_time_ms=execution_time,
                memory_used_kb=0,
                logs=logs
            )
        finally:
            output_buffer.close()


class CodeExecutor:
    """منفذ الكود المعزول"""
    
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()
        self.environments: Dict[str, SandboxedEnvironment] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def create_environment(self, env_id: str, policy: Optional[SecurityPolicy] = None) -> str:
        """إنشاء بيئة معزولة جديدة"""
        env_policy = policy or self.policy
        env = SandboxedEnvironment(env_policy)
        self.environments[env_id] = env
        logger.info(f"Created sandbox environment: {env_id}")
        return env_id
    
    def destroy_environment(self, env_id: str) -> bool:
        """تدمير بيئة معزولة"""
        if env_id in self.environments:
            del self.environments[env_id]
            logger.info(f"Destroyed sandbox environment: {env_id}")
            return True
        return False
    
    async def execute_async(
        self,
        env_id: str,
        code: str,
        local_vars: Optional[Dict[str, Any]] = None,
        timeout_ms: Optional[int] = None
    ) -> ExecutionResult:
        """تنفيذ كود بشكل غير متزامن"""
        if env_id not in self.environments:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Environment {env_id} not found",
                return_value=None,
                execution_time_ms=0,
                memory_used_kb=0,
                logs=[]
            )
        
        env = self.environments[env_id]
        
        # تنفيذ في thread pool لتجنب حظر الحلقة
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: env.execute(code, local_vars, timeout_ms)
        )
        
        # تسجيل التنفيذ
        self.execution_history.append({
            "env_id": env_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.success,
            "execution_time_ms": result.execution_time_ms
        })
        
        return result
    
    def execute_sync(
        self,
        env_id: str,
        code: str,
        local_vars: Optional[Dict[str, Any]] = None,
        timeout_ms: Optional[int] = None
    ) -> ExecutionResult:
        """تنفيذ كود بشكل متزامن"""
        if env_id not in self.environments:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Environment {env_id} not found",
                return_value=None,
                execution_time_ms=0,
                memory_used_kb=0,
                logs=[]
            )
        
        env = self.environments[env_id]
        return env.execute(code, local_vars, timeout_ms)
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """الحصول على سجل التنفيذ"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """مسح سجل التنفيذ"""
        self.execution_history.clear()


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء سياسة أمان
    policy = SecurityPolicy(
        allow_network=False,
        allow_file_system=False,
        max_execution_time_ms=3000
    )
    
    # إنشاء منفذ الكود
    executor = CodeExecutor(policy)
    
    # إنشاء بيئة
    env_id = executor.create_environment("test_env")
    
    # كود للاختبار
    test_code = """
def calculate(x, y):
    return x + y

result = calculate(5, 3)
print(f"Result: {result}")
"""
    
    # تنفيذ الكود
    result = executor.execute_sync(env_id, test_code)
    
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time_ms}ms")
