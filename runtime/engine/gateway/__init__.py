"""
AMOS Model Gateway - بوابة توجيه النماذج
Unified interface for multiple AI model providers with fallback and load balancing
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """مزودو النماذج"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelCapability(Enum):
    """قدرات النموذج"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"


@dataclass
class ModelConfig:
    """تكوين النموذج"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    retry_count: int = 3
    capabilities: List[ModelCapability] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = [ModelCapability.TEXT_GENERATION]


@dataclass
class ModelResponse:
    """استجابة النموذج"""
    content: str
    model: str
    provider: ModelProvider
    usage: Dict[str, int] = None
    latency_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}


class ModelClient:
    """عميل نموذج فردي"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._healthy = True
        self._request_count = 0
        self._error_count = 0
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """توليد استجابة من النموذج"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Simulate API call (replace with actual implementation)
            await asyncio.sleep(0.1)
            
            response = ModelResponse(
                content=f"Response from {self.config.provider.value}:{self.config.model_name}",
                model=self.config.model_name,
                provider=self.config.provider,
                usage={'prompt_tokens': len(prompt.split()), 'completion_tokens': 50, 'total_tokens': len(prompt.split()) + 50},
                latency_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
            )
            
            self._request_count += 1
            self._healthy = True
            return response
            
        except Exception as e:
            self._error_count += 1
            self._healthy = self._error_count / max(self._request_count, 1) < 0.5
            
            return ModelResponse(
                content="",
                model=self.config.model_name,
                provider=self.config.provider,
                success=False,
                error=str(e),
                latency_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
            )
    
    def is_healthy(self) -> bool:
        """التحقق من صحة العميل"""
        return self._healthy
    
    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات العميل"""
        return {
            'provider': self.config.provider.value,
            'model': self.config.model_name,
            'requests': self._request_count,
            'errors': self._error_count,
            'healthy': self._healthy,
            'error_rate': self._error_count / max(self._request_count, 1)
        }


class ModelGateway:
    """
    بوابة توجيه النماذج
    Handles routing, load balancing, and failover between multiple model providers
    """
    
    def __init__(self):
        self.clients: Dict[str, ModelClient] = {}
        self.routing_table: Dict[ModelCapability, List[str]] = {}
        self.default_models: List[str] = []
        self._lock = asyncio.Lock()
        
        logger.info("Model Gateway initialized")
    
    def register_model(self, name: str, config: ModelConfig) -> None:
        """تسجيل نموذج جديد"""
        client = ModelClient(config)
        self.clients[name] = client
        
        # Add to routing table based on capabilities
        for capability in config.capabilities:
            if capability not in self.routing_table:
                self.routing_table[capability] = []
            self.routing_table[capability].append(name)
        
        if not self.default_models:
            self.default_models.append(name)
        
        logger.info(f"Model {name} registered with capabilities: {[c.value for c in config.capabilities]}")
    
    def unregister_model(self, name: str) -> None:
        """إلغاء تسجيل نموذج"""
        if name in self.clients:
            del self.clients[name]
            
            # Remove from routing table
            for capability in self.routing_table:
                if name in self.routing_table[capability]:
                    self.routing_table[capability].remove(name)
            
            if name in self.default_models:
                self.default_models.remove(name)
            
            logger.info(f"Model {name} unregistered")
    
    async def route_request(self, prompt: str, 
                          required_capability: Optional[ModelCapability] = None,
                          preferred_provider: Optional[ModelProvider] = None,
                          **kwargs) -> ModelResponse:
        """
        توجيه الطلب إلى النموذج الأنسب
        Implements intelligent routing with fallback
        """
        async with self._lock:
            # Determine candidate models
            if required_capability:
                candidates = self.routing_table.get(required_capability, self.default_models)
            else:
                candidates = self.default_models
            
            if preferred_provider:
                candidates = [
                    name for name in candidates 
                    if self.clients[name].config.provider == preferred_provider
                ]
            
            if not candidates:
                return ModelResponse(
                    content="",
                    model="none",
                    provider=ModelProvider.CUSTOM,
                    success=False,
                    error="No suitable model found"
                )
            
            # Try models in order with fallback
            last_error = None
            for model_name in candidates:
                client = self.clients.get(model_name)
                
                if not client or not client.is_healthy():
                    logger.warning(f"Model {model_name} unavailable, trying next")
                    continue
                
                try:
                    response = await client.generate(prompt, **kwargs)
                    
                    if response.success:
                        logger.info(f"Request routed to {model_name}")
                        return response
                    
                    last_error = response.error
                    
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Model {model_name} failed: {e}")
            
            # All models failed
            return ModelResponse(
                content="",
                model="none",
                provider=ModelProvider.CUSTOM,
                success=False,
                error=f"All models failed. Last error: {last_error}"
            )
    
    async def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """واجهة توليد مبسطة"""
        return await self.route_request(prompt, **kwargs)
    
    async def batch_generate(self, prompts: List[str], **kwargs) -> List[ModelResponse]:
        """توليد دفعي متوازي"""
        tasks = [self.route_request(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """الحصول على النماذج المتاحة"""
        return [
            {
                'name': name,
                **client.get_stats()
            }
            for name, client in self.clients.items()
        ]
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """الحصول على القدرات المتاحة"""
        return {
            capability.value: models
            for capability, models in self.routing_table.items()
        }


# Singleton instance
_gateway_instance: Optional[ModelGateway] = None


def get_gateway() -> ModelGateway:
    """الحصول على مثان البوابة الوحيد"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ModelGateway()
    return _gateway_instance


def initialize_default_models() -> ModelGateway:
    """تهيئة النماذج الافتراضية"""
    gateway = get_gateway()
    
    # Register default local model
    gateway.register_model(
        'local-default',
        ModelConfig(
            provider=ModelProvider.LOCAL,
            model_name='amos-local-v1',
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.ANALYSIS
            ]
        )
    )
    
    logger.info("Default models initialized")
    return gateway
