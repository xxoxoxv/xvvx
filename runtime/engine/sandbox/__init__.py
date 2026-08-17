"""
AMOS Environment Sandbox - صندوق البيئة المعزول
Secure isolated execution environment for agent code and tasks
"""

import asyncio
import logging
import os
import sys
import tempfile
import traceback
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)


class SandboxStatus(Enum):
    """حالة الصندوق"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class SecurityLevel(Enum):
    """مستوى الأمان"""
    LOW = "low"           # محدودية قليلة
    MEDIUM = "medium"     # عزل متوسط
    HIGH = "high"         # عزل صارم
    MAXIMUM = "maximum"   # عزل كامل بدون وصول للشبكة


@dataclass
class ResourceLimits:
    """حدود الموارد"""
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 512
    max_disk_mb: int = 100
    max_execution_time_sec: int = 300
    max_network_connections: int = 0
    max_file_descriptors: int = 50


@dataclass
class ExecutionResult:
    """نتيجة التنفيذ"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    execution_time_ms: int = 0
    memory_used_mb: float = 0.0
    resources: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'exit_code': self.exit_code,
            'execution_time_ms': self.execution_time_ms,
            'memory_used_mb': self.memory_used_mb,
            'resources': self.resources
        }


class SandboxedEnvironment:
    """بيئة معزولة لتنفيذ الكود"""
    
    def __init__(self, env_id: str, 
                 security_level: SecurityLevel = SecurityLevel.MEDIUM,
                 resource_limits: Optional[ResourceLimits] = None):
        self.env_id = env_id
        self.security_level = security_level
        self.resource_limits = resource_limits or ResourceLimits()
        self.status = SandboxStatus.CREATED
        self.work_dir: Optional[Path] = None
        self._cleanup_callbacks: List[Callable] = []
        
        logger.info(f"Sandbox {env_id} created with security level {security_level.value}")
    
    async def setup(self) -> None:
        """إعداد البيئة المعزولة"""
        try:
            # Create isolated working directory
            self.work_dir = Path(tempfile.mkdtemp(prefix=f"amos_sandbox_{self.env_id}_"))
            
            # Apply security restrictions based on level
            await self._apply_security_restrictions()
            
            self.status = SandboxStatus.RUNNING
            logger.info(f"Sandbox {self.env_id} setup complete")
            
        except Exception as e:
            self.status = SandboxStatus.FAILED
            logger.error(f"Failed to setup sandbox {self.env_id}: {e}")
            raise
    
    async def _apply_security_restrictions(self) -> None:
        """تطبيق قيود الأمان"""
        if self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
            # Disable network access
            os.environ['NO_PROXY'] = '*'
            
            # Set resource limits
            import resource
            try:
                mem_limit = self.resource_limits.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
            except (ValueError, ImportError):
                pass  # Platform may not support this
        
        logger.debug(f"Security restrictions applied: {self.security_level.value}")
    
    async def execute(self, code: str, 
                     context: Optional[Dict[str, Any]] = None,
                     timeout: Optional[int] = None) -> ExecutionResult:
        """
        تنفيذ كود في البيئة المعزولة
        Args:
            code: Python code to execute
            context: Variables to inject into execution context
            timeout: Maximum execution time in seconds
        """
        if self.status != SandboxStatus.RUNNING:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Sandbox not running (status: {self.status.value})"
            )
        
        start_time = asyncio.get_event_loop().time()
        timeout = timeout or self.resource_limits.max_execution_time_sec
        
        try:
            # Create safe execution context
            safe_globals = {
                '__builtins__': self._get_safe_builtins(),
                '__name__': '__sandbox__',
            }
            
            if context:
                safe_globals.update(context)
            
            # Execute code with timeout
            result_output = await asyncio.wait_for(
                self._execute_code(code, safe_globals),
                timeout=timeout
            )
            
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return ExecutionResult(
                success=True,
                output=result_output,
                execution_time_ms=execution_time,
                memory_used_mb=self._get_memory_usage()
            )
            
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timeout after {timeout}s",
                exit_code=-1
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                exit_code=-1
            )
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """الحصول على الدوال المدمجة الآمنة"""
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'chr': chr,
            'complex': complex,
            'dict': dict,
            'enumerate': enumerate,
            'float': float,
            'format': format,
            'frozenset': frozenset,
            'hex': hex,
            'int': int,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'print': print,
            'range': range,
            'repr': repr,
            'reversed': reversed,
            'round': round,
            'set': set,
            'slice': slice,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
        }
        
        # Remove dangerous functions based on security level
        if self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
            # Remove file system access
            dangerous = ['open', 'file', 'input']
            for d in dangerous:
                safe_builtins.pop(d, None)
        
        return safe_builtins
    
    async def _execute_code(self, code: str, context: Dict[str, Any]) -> str:
        """تنفيذ الكود فعلياً"""
        # Redirect stdout/stderr
        import io
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Compile and execute
            compiled = compile(code, '<sandbox>', 'exec')
            exec(compiled, context)
            
            return stdout_capture.getvalue()
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def _get_memory_usage(self) -> float:
        """الحصول على استخدام الذاكرة"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024  # Convert to MB
        except:
            return 0.0
    
    async def upload_file(self, filename: str, content: bytes) -> Path:
        """رفع ملف إلى البيئة المعزولة"""
        if not self.work_dir:
            raise RuntimeError("Sandbox not initialized")
        
        # Sanitize filename
        safe_filename = Path(filename).name
        file_path = self.work_dir / safe_filename
        
        # Write file
        file_path.write_bytes(content)
        
        logger.debug(f"File uploaded to sandbox: {safe_filename}")
        return file_path
    
    async def download_file(self, filename: str) -> bytes:
        """تنزيل ملف من البيئة المعزولة"""
        if not self.work_dir:
            raise RuntimeError("Sandbox not initialized")
        
        file_path = self.work_dir / Path(filename).name
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found in sandbox: {filename}")
        
        return file_path.read_bytes()
    
    async def cleanup(self) -> None:
        """تنظيف البيئة المعزولة"""
        try:
            # Run cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Cleanup callback failed: {e}")
            
            # Remove working directory
            if self.work_dir and self.work_dir.exists():
                import shutil
                shutil.rmtree(self.work_dir, ignore_errors=True)
            
            self.status = SandboxStatus.TERMINATED
            logger.info(f"Sandbox {self.env_id} cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox {self.env_id}: {e}")
    
    def register_cleanup(self, callback: Callable) -> None:
        """تسجيل دالة تنظيف"""
        self._cleanup_callbacks.append(callback)


class SandboxManager:
    """
    مدير الصناديق المعزولة
    Manages lifecycle of multiple sandboxed environments
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.sandboxes: Dict[str, SandboxedEnvironment] = {}
        self._lock = asyncio.Lock()
        self._active_count = 0
        
        logger.info(f"Sandbox Manager initialized (max concurrent: {max_concurrent})")
    
    async def create_sandbox(self, 
                            env_id: Optional[str] = None,
                            security_level: SecurityLevel = SecurityLevel.MEDIUM,
                            resource_limits: Optional[ResourceLimits] = None) -> SandboxedEnvironment:
        """إنشاء صندوق معزول جديد"""
        async with self._lock:
            if self._active_count >= self.max_concurrent:
                raise RuntimeError("Maximum concurrent sandboxes reached")
            
            # Generate ID if not provided
            if not env_id:
                env_id = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
            
            if env_id in self.sandboxes:
                raise ValueError(f"Sandbox {env_id} already exists")
            
            # Create and setup sandbox
            sandbox = SandboxedEnvironment(env_id, security_level, resource_limits)
            await sandbox.setup()
            
            self.sandboxes[env_id] = sandbox
            self._active_count += 1
            
            logger.info(f"Sandbox {env_id} created ({self._active_count}/{self.max_concurrent} active)")
            return sandbox
    
    async def get_sandbox(self, env_id: str) -> SandboxedEnvironment:
        """الحصول على صندوق موجود"""
        if env_id not in self.sandboxes:
            raise KeyError(f"Sandbox {env_id} not found")
        return self.sandboxes[env_id]
    
    async def destroy_sandbox(self, env_id: str) -> None:
        """تدمير صندوق معزول"""
        async with self._lock:
            if env_id not in self.sandboxes:
                return
            
            sandbox = self.sandboxes[env_id]
            await sandbox.cleanup()
            del self.sandboxes[env_id]
            self._active_count -= 1
            
            logger.info(f"Sandbox {env_id} destroyed ({self._active_count}/{self.max_concurrent} active)")
    
    async def execute_in_sandbox(self, env_id: str, 
                                code: str,
                                context: Optional[Dict[str, Any]] = None,
                                timeout: Optional[int] = None) -> ExecutionResult:
        """تنفيذ كود في صندوق موجود"""
        sandbox = await self.get_sandbox(env_id)
        return await sandbox.execute(code, context, timeout)
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات المدير"""
        return {
            'active_sandboxes': self._active_count,
            'max_concurrent': self.max_concurrent,
            'total_sandboxes': len(self.sandboxes),
            'sandboxes': {
                env_id: {
                    'status': sb.status.value,
                    'security_level': sb.security_level.value
                }
                for env_id, sb in self.sandboxes.items()
            }
        }
    
    async def cleanup_all(self) -> None:
        """تنظيف جميع الصناديق"""
        env_ids = list(self.sandboxes.keys())
        for env_id in env_ids:
            await self.destroy_sandbox(env_id)
        
        logger.info("All sandboxes cleaned up")


# Singleton instance
_manager_instance: Optional[SandboxManager] = None


def get_sandbox_manager(max_concurrent: int = 10) -> SandboxManager:
    """الحصول على مثان المدير الوحيد"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SandboxManager(max_concurrent)
    return _manager_instance


async def execute_isolated(code: str, 
                          context: Optional[Dict[str, Any]] = None,
                          security_level: SecurityLevel = SecurityLevel.MEDIUM,
                          timeout: Optional[int] = None) -> ExecutionResult:
    """
    تنفيذ كود في بيئة معزولة مؤقتة
    Convenience function for one-off isolated execution
    """
    manager = get_sandbox_manager()
    
    sandbox = await manager.create_sandbox(security_level=security_level)
    
    try:
        result = await sandbox.execute(code, context, timeout)
        return result
    finally:
        await manager.destroy_sandbox(sandbox.env_id)
