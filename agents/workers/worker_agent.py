"""
AMOS Federal State - Worker Agent Implementation
وكيل العامل التنفيذي المسؤول عن تنفيذ المهام المباشرة

الأدوات المتاحة:
- log: تسجيل الأحداث والرسائل
- compute: إجراء عمليات حسابية
- transform: تحويل البيانات
- validate: التحقق من صحة البيانات
- fetch_data: جلب البيانات من المصادر
- store_data: تخزين البيانات
- send_notification: إرسال إشعارات
- execute_script: تنفيذ سكريبتات آمنة
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import hashlib
from pathlib import Path

from ..base.base_agent import BaseAgent


class WorkerTools:
    """مجموعة أدوات وكيل العامل"""
    
    @staticmethod
    def log(message: str, level: str = "INFO") -> Dict[str, Any]:
        """تسجيل رسالة في السجل"""
        return {
            "status": "success",
            "action": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def compute(operation: str, operands: List[float]) -> Dict[str, Any]:
        """إجراء عملية حسابية"""
        try:
            if operation == "sum":
                result = sum(operands)
            elif operation == "average":
                result = sum(operands) / len(operands) if operands else 0
            elif operation == "multiply":
                result = 1
                for op in operands:
                    result *= op
            elif operation == "max":
                result = max(operands) if operands else 0
            elif operation == "min":
                result = min(operands) if operands else 0
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
            
            return {
                "status": "success",
                "action": "compute",
                "operation": operation,
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def transform(data: Any, transformation: str) -> Dict[str, Any]:
        """تحويل البيانات"""
        try:
            if transformation == "uppercase":
                result = str(data).upper()
            elif transformation == "lowercase":
                result = str(data).lower()
            elif transformation == "json_stringify":
                result = json.dumps(data, ensure_ascii=False)
            elif transformation == "json_parse":
                result = json.loads(data) if isinstance(data, str) else data
            elif transformation == "list_to_dict":
                result = {i: item for i, item in enumerate(data)}
            else:
                return {"status": "error", "message": f"Unknown transformation: {transformation}"}
            
            return {
                "status": "success",
                "action": "transform",
                "transformation": transformation,
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def validate(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """التحقق من صحة البيانات"""
        try:
            is_valid = True
            errors = []
            
            if schema.get("type") == "dict" and not isinstance(data, dict):
                is_valid = False
                errors.append("Expected dictionary")
            
            if schema.get("required_fields"):
                for field in schema["required_fields"]:
                    if field not in data:
                        is_valid = False
                        errors.append(f"Missing required field: {field}")
            
            if schema.get("min_length") and isinstance(data, (str, list)):
                if len(data) < schema["min_length"]:
                    is_valid = False
                    errors.append(f"Length below minimum: {schema['min_length']}")
            
            return {
                "status": "success" if is_valid else "invalid",
                "action": "validate",
                "is_valid": is_valid,
                "errors": errors
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def fetch_data(source: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """جلب البيانات من مصدر (محاكاة)"""
        # في التنفيذ الفعلي، سيتم الاتصال بقاعدة البيانات أو API
        return {
            "status": "success",
            "action": "fetch_data",
            "source": source,
            "data": {"mock": "data", "params": params},
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def store_data(destination: str, data: Any) -> Dict[str, Any]:
        """تخزين البيانات (محاكاة)"""
        # في التنفيذ الفعلي، سيتم التخزين في قاعدة البيانات
        return {
            "status": "success",
            "action": "store_data",
            "destination": destination,
            "data_hash": hashlib.md5(json.dumps(data, default=str).encode()).hexdigest(),
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def send_notification(recipient: str, message: str, channel: str = "email") -> Dict[str, Any]:
        """إرسال إشعار (محاكاة)"""
        return {
            "status": "success",
            "action": "send_notification",
            "recipient": recipient,
            "channel": channel,
            "message_preview": message[:50] + "..." if len(message) > 50 else message,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def execute_script(script_code: str, timeout: int = 30) -> Dict[str, Any]:
        """تنفيذ سكريبت آمن (محاكاة)"""
        # في التنفيذ الفعلي، سيتم استخدام sandbox
        return {
            "status": "success",
            "action": "execute_script",
            "script_hash": hashlib.md5(script_code.encode()).hexdigest(),
            "timeout": timeout,
            "result": "Script executed successfully (simulated)",
            "timestamp": datetime.now().isoformat()
        }


class WorkerAgent(BaseAgent):
    """
    وكيل العامل التنفيذي
    
    مسؤول عن تنفيذ المهام المباشرة باستخدام الأدوات المتاحة
    """
    
    def __init__(self, citizen_id: str, name: str, 
                 specialization: Optional[str] = None,
                 data_dir: str = "data/agents"):
        super().__init__(citizen_id, name, data_dir=data_dir)
        
        self.specialization = specialization or "GENERAL"
        self.tools = WorkerTools()
        self.supervisor_id: Optional[str] = None
        
        # سجل الأدوات المستخدمة
        self.tool_usage_log: List[Dict[str, Any]] = []
        
        self._load_state()
    
    def get_capabilities(self) -> List[str]:
        """الحصول على قائمة القدرات"""
        base_caps = [
            "log_events",
            "compute_operations",
            "transform_data",
            "validate_data",
            "fetch_data",
            "store_data",
            "send_notifications",
            "execute_scripts"
        ]
        
        if self.specialization != "GENERAL":
            base_caps.append(f"specialized_{self.specialization.lower()}")
        
        return base_caps
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        تنفيذ مهمة
        
        Args:
            task: قاموس يحتوي على:
                - action: الإجراء المطلوب (log, compute, transform, validate, ...)
                - params: معلمات الإجراء
                
        Returns:
            قاموس يحتوي على نتيجة التنفيذ
        """
        action = task.get("action")
        params = task.get("params", {})
        
        self._log_action("TASK_STARTED", {"task": task})
        
        try:
            result = await self._execute_action(action, params)
            
            self.tool_usage_log.append({
                "action": action,
                "params": params,
                "result_status": result.get("status"),
                "timestamp": datetime.now().isoformat()
            })
            
            # الاحتفاظ بآخر 500 استخدام للأداة
            if len(self.tool_usage_log) > 500:
                self.tool_usage_log = self.tool_usage_log[-500:]
            
            self.complete_task(task.get("id", "unknown"), result, success=(result.get("status") == "success"))
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "action": action
            }
            self.complete_task(task.get("id", "unknown"), error_result, success=False)
            return error_result
    
    async def _execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ إجراء محدد باستخدام الأدوات"""
        
        # محاكاة تأخير طفيف للتنفيذ غير المتزامن
        await asyncio.sleep(0.01)
        
        if action == "log":
            return self.tools.log(
                message=params.get("message", ""),
                level=params.get("level", "INFO")
            )
        
        elif action == "compute":
            return self.tools.compute(
                operation=params.get("operation", "sum"),
                operands=params.get("operands", [])
            )
        
        elif action == "transform":
            return self.tools.transform(
                data=params.get("data"),
                transformation=params.get("transformation", "uppercase")
            )
        
        elif action == "validate":
            return self.tools.validate(
                data=params.get("data"),
                schema=params.get("schema", {})
            )
        
        elif action == "fetch_data":
            return self.tools.fetch_data(
                source=params.get("source", "default"),
                params=params.get("query_params")
            )
        
        elif action == "store_data":
            return self.tools.store_data(
                destination=params.get("destination", "default"),
                data=params.get("data")
            )
        
        elif action == "send_notification":
            return self.tools.send_notification(
                recipient=params.get("recipient", ""),
                message=params.get("message", ""),
                channel=params.get("channel", "email")
            )
        
        elif action == "execute_script":
            return self.tools.execute_script(
                script_code=params.get("code", ""),
                timeout=params.get("timeout", 30)
            )
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}",
                "available_actions": ["log", "compute", "transform", "validate", 
                                     "fetch_data", "store_data", "send_notification", 
                                     "execute_script"]
            }
    
    def _save_state(self):
        """حفظ حالة الوكيل الموسعة"""
        super()._save_state()
        
        # حفظ حالة إضافية خاصة بالعامل
        extra_state_file = self.data_dir / "worker_state.json"
        extra_state = {
            "specialization": self.specialization,
            "supervisor_id": self.supervisor_id,
            "tool_usage_log": self.tool_usage_log[-50:]  # آخر 50 استخدام
        }
        
        with open(extra_state_file, 'w', encoding='utf-8') as f:
            json.dump(extra_state, f, indent=2, ensure_ascii=False)
    
    def _load_state(self):
        """تحميل حالة الوكيل الموسعة"""
        super()._load_state()
        
        extra_state_file = self.data_dir / "worker_state.json"
        if extra_state_file.exists():
            with open(extra_state_file, 'r', encoding='utf-8') as f:
                extra_state = json.load(f)
                self.specialization = extra_state.get("specialization", "GENERAL")
                self.supervisor_id = extra_state.get("supervisor_id")
                self.tool_usage_log = extra_state.get("tool_usage_log", [])
    
    def set_supervisor(self, supervisor_id: str):
        """تعيين مشرف للوكيل"""
        self.supervisor_id = supervisor_id
        self._save_state()
    
    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة موسعة للوكيل"""
        base_status = super().get_status()
        base_status.update({
            "specialization": self.specialization,
            "supervisor_id": self.supervisor_id,
            "tools_used_count": len(self.tool_usage_log),
            "most_used_tool": self._get_most_used_tool()
        })
        return base_status
    
    def _get_most_used_tool(self) -> Optional[str]:
        """الحصول على الأداة الأكثر استخداماً"""
        if not self.tool_usage_log:
            return None
        
        tool_counts = {}
        for usage in self.tool_usage_log:
            action = usage.get("action")
            tool_counts[action] = tool_counts.get(action, 0) + 1
        
        if not tool_counts:
            return None
        
        return max(tool_counts, key=tool_counts.get)
    
    def __repr__(self) -> str:
        return f"<WorkerAgent {self.name} ({self.citizen_id}) - {self.specialization}>"
