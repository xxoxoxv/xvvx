"""
AMOS Memory Systems - أنظمة الذاكرة
Redis for short-term memory, Qdrant for vector memory, Experience Replay
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """أنواع الذاكرة"""
    SHORT_TERM = "short_term"      # Redis
    LONG_TERM = "long_term"        # Persistent
    VECTOR = "vector"              # Qdrant
    EPISODIC = "episodic"          # Experience replay
    SEMANTIC = "semantic"          # Knowledge


@dataclass
class MemoryEntry:
    """مدخل الذاكرة"""
    id: str
    content: Any
    memory_type: MemoryType
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'memory_type': self.memory_type.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata,
            'embedding': self.embedding,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(
            id=data['id'],
            content=data['content'],
            memory_type=MemoryType(data['memory_type']),
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            metadata=data.get('metadata', {}),
            embedding=data.get('embedding'),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        )


class RedisMemory:
    """
    ذاكرة قصيرة المدى باستخدام Redis
    Short-term memory with TTL support
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._connected = False
        self._cache: Dict[str, MemoryEntry] = {}  # In-memory fallback
        
        logger.info(f"Redis Memory initialized (host={host}, port={port})")
    
    async def connect(self) -> bool:
        """الاتصال بـ Redis"""
        try:
            # Try to import redis
            import redis.asyncio as redis
            
            self._client = redis.Redis(host=self.host, port=self.port, db=self.db)
            await self._client.ping()
            self._connected = True
            
            logger.info("Connected to Redis")
            return True
            
        except ImportError:
            logger.warning("Redis not installed, using in-memory fallback")
            self._connected = False
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using in-memory fallback")
            self._connected = False
            return False
    
    async def set(self, key: str, value: Any, 
                 ttl_seconds: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        """تخزين قيمة في الذاكرة"""
        entry_id = hashlib.sha256(f"{key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        entry = MemoryEntry(
            id=entry_id,
            content=value,
            memory_type=MemoryType.SHORT_TERM,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        if self._connected:
            try:
                await self._client.setex(
                    f"amos:mem:{key}",
                    ttl_seconds or 86400,
                    json.dumps(entry.to_dict())
                )
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
                self._cache[key] = entry
        else:
            self._cache[key] = entry
        
        logger.debug(f"Memory set: {key} (TTL={ttl_seconds}s)")
        return entry
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """الحصول على قيمة من الذاكرة"""
        if self._connected:
            try:
                data = await self._client.get(f"amos:mem:{key}")
                if data:
                    entry = MemoryEntry.from_dict(json.loads(data))
                    
                    # Update access stats
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
                    
                    # Refresh TTL
                    await self._client.expire(f"amos:mem:{key}", 86400)
                    
                    return entry
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
                return self._cache.get(key)
        else:
            entry = self._cache.get(key)
            if entry:
                entry.access_count += 1
                entry.last_accessed = datetime.utcnow()
            return entry
    
    async def delete(self, key: str) -> bool:
        """حذف قيمة من الذاكرة"""
        if self._connected:
            try:
                await self._client.delete(f"amos:mem:{key}")
            except Exception as e:
                logger.error(f"Redis delete failed: {e}")
        
        if key in self._cache:
            del self._cache[key]
        
        logger.debug(f"Memory deleted: {key}")
        return True
    
    async def clear(self) -> None:
        """مسح الذاكرة"""
        if self._connected:
            try:
                keys = await self._client.keys("amos:mem:*")
                if keys:
                    await self._client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear failed: {e}")
        
        self._cache.clear()
        logger.info("Memory cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات الذاكرة"""
        if self._connected:
            try:
                info = await self._client.info("memory")
                return {
                    'type': 'redis',
                    'connected': True,
                    'used_memory': info.get('used_memory_human', 'unknown'),
                    'keys_count': len(await self._client.keys("amos:mem:*"))
                }
            except:
                pass
        
        return {
            'type': 'in-memory',
            'connected': False,
            'keys_count': len(self._cache)
        }


class QdrantVectorMemory:
    """
    ذاكرة متجهات باستخدام Qdrant
    Vector memory for semantic search and similarity
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6333, collection_name: str = 'amos_memory'):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._connected = False
        self._vectors: Dict[str, Dict[str, Any]] = {}  # In-memory fallback
        
        logger.info(f"Qdrant Vector Memory initialized (collection={collection_name})")
    
    async def connect(self, embedding_dim: int = 768) -> bool:
        """الاتصال بـ Qdrant"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self._client = QdrantClient(host=self.host, port=self.port)
            
            # Create collection if not exists
            collections = self._client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if not collection_exists:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
                )
            
            self._connected = True
            logger.info(f"Connected to Qdrant, collection: {self.collection_name}")
            return True
            
        except ImportError:
            logger.warning("Qdrant client not installed, using in-memory fallback")
            self._connected = False
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}, using in-memory fallback")
            self._connected = False
            return False
    
    async def store(self, text: str, embedding: List[float], 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """تخزين متجه مع نص"""
        entry_id = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        if self._connected:
            try:
                from qdrant_client.models import PointStruct
                
                self._client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=hashlib.md5(entry_id.encode()).int_value() % (2**63),
                            vector=embedding,
                            payload={'text': text, 'metadata': metadata or {}}
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Qdrant store failed: {e}")
                self._vectors[entry_id] = {'text': text, 'embedding': embedding, 'metadata': metadata or {}}
        else:
            self._vectors[entry_id] = {'text': text, 'embedding': embedding, 'metadata': metadata or {}}
        
        logger.debug(f"Vector stored: {entry_id}")
        return entry_id
    
    async def search(self, query_embedding: List[float], 
                    limit: int = 5,
                    min_score: float = 0.7) -> List[Dict[str, Any]]:
        """بحث عن متجهات مشابهة"""
        if self._connected:
            try:
                results = self._client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit
                )
                
                return [
                    {
                        'id': str(r.id),
                        'text': r.payload.get('text', ''),
                        'metadata': r.payload.get('metadata', {}),
                        'score': r.score
                    }
                    for r in results
                    if r.score >= min_score
                ]
            except Exception as e:
                logger.error(f"Qdrant search failed: {e}")
        
        # Fallback: simple cosine similarity in-memory
        return self._cosine_similarity_search(query_embedding, limit, min_score)
    
    def _cosine_similarity_search(self, query: List[float], 
                                  limit: int, 
                                  min_score: float) -> List[Dict[str, Any]]:
        """بحث تشابه جيب التمام في الذاكرة"""
        import math
        
        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            dot_product = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.sqrt(sum(a * a for a in v1))
            norm2 = math.sqrt(sum(b * b for b in v2))
            return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0
        
        results = []
        for entry_id, data in self._vectors.items():
            score = cosine_similarity(query, data['embedding'])
            if score >= min_score:
                results.append({
                    'id': entry_id,
                    'text': data['text'],
                    'metadata': data.get('metadata', {}),
                    'score': score
                })
        
        return sorted(results, key=lambda x: x['score'], reverse=True)[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات الذاكرة المتجهة"""
        if self._connected:
            try:
                info = self._client.get_collection(self.collection_name)
                return {
                    'type': 'qdrant',
                    'connected': True,
                    'vectors_count': info.points_count,
                    'dimensions': info.config.params.vectors.size
                }
            except:
                pass
        
        return {
            'type': 'in-memory',
            'connected': False,
            'vectors_count': len(self._vectors)
        }


class ExperienceReplay:
    """
    نظام تجربة الخبرة
    Stores and replays agent experiences for learning
    """
    
    def __init__(self, max_size: int = 10000, batch_size: int = 32):
        self.max_size = max_size
        self.batch_size = batch_size
        self.experiences: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        
        logger.info(f"Experience Replay initialized (max_size={max_size}, batch_size={batch_size})")
    
    async def store_experience(self, 
                              state: Any,
                              action: Any,
                              reward: float,
                              next_state: Any,
                              done: bool,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        """تخزين تجربة"""
        async with self._lock:
            experience = {
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': next_state,
                'done': done,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            self.experiences.append(experience)
            
            # Remove oldest if exceeding max size
            if len(self.experiences) > self.max_size:
                self.experiences.pop(0)
            
            logger.debug(f"Experience stored (total: {len(self.experiences)})")
    
    async def sample_batch(self, batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """أخذ عينة عشوائية من التجارب"""
        import random
        
        async with self._lock:
            if not self.experiences:
                return []
            
            size = batch_size or self.batch_size
            size = min(size, len(self.experiences))
            
            return random.sample(self.experiences, size)
    
    async def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """الحصول على آخر التجارب"""
        async with self._lock:
            return self.experiences[-count:]
    
    async def clear(self) -> None:
        """مسح جميع التجارب"""
        async with self._lock:
            self.experiences.clear()
            logger.info("Experience replay cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات نظام الخبرة"""
        async with self._lock:
            if not self.experiences:
                return {
                    'total_experiences': 0,
                    'avg_reward': 0,
                    'positive_ratio': 0
                }
            
            rewards = [e['reward'] for e in self.experiences]
            positive = sum(1 for r in rewards if r > 0)
            
            return {
                'total_experiences': len(self.experiences),
                'avg_reward': sum(rewards) / len(rewards),
                'min_reward': min(rewards),
                'max_reward': max(rewards),
                'positive_ratio': positive / len(rewards)
            }


class MemorySystem:
    """
    نظام الذاكرة الموحد
    Unified interface for all memory systems
    """
    
    def __init__(self):
        self.short_term = RedisMemory()
        self.vector_memory = QdrantVectorMemory()
        self.experience_replay = ExperienceReplay()
        self._initialized = False
        
        logger.info("Memory System initialized")
    
    async def initialize(self) -> None:
        """تهيئة جميع أنظمة الذاكرة"""
        await self.short_term.connect()
        await self.vector_memory.connect()
        self._initialized = True
        logger.info("Memory System fully initialized")
    
    async def store(self, key: str, value: Any, 
                   memory_type: MemoryType = MemoryType.SHORT_TERM,
                   **kwargs) -> MemoryEntry:
        """تخزين في النظام المناسب"""
        if memory_type == MemoryType.SHORT_TERM:
            return await self.short_term.set(key, value, **kwargs)
        elif memory_type == MemoryType.VECTOR:
            embedding = kwargs.get('embedding', [])
            metadata = kwargs.get('metadata', {})
            entry_id = await self.vector_memory.store(value, embedding, metadata)
            return MemoryEntry(id=entry_id, content=value, memory_type=MemoryType.VECTOR, metadata=metadata)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")
    
    async def retrieve(self, key: str, 
                      memory_type: MemoryType = MemoryType.SHORT_TERM) -> Optional[Any]:
        """استرجاع من النظام المناسب"""
        if memory_type == MemoryType.SHORT_TERM:
            entry = await self.short_term.get(key)
            return entry.content if entry else None
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")
    
    async def search_similar(self, embedding: List[float], 
                            limit: int = 5) -> List[Dict[str, Any]]:
        """بحث عن ذكريات مشابهة"""
        return await self.vector_memory.search(embedding, limit)
    
    async def store_experience(self, **kwargs) -> None:
        """تخزين تجربة"""
        await self.experience_replay.store_experience(**kwargs)
    
    async def sample_experiences(self, batch_size: int = 32) -> List[Dict[str, Any]]:
        """أخذ عينة من التجارب"""
        return await self.experience_replay.sample_batch(batch_size)
    
    async def get_stats(self) -> Dict[str, Any]:
        """إحصائيات شاملة"""
        return {
            'initialized': self._initialized,
            'short_term': await self.short_term.get_stats(),
            'vector_memory': await self.vector_memory.get_stats(),
            'experience_replay': await self.experience_replay.get_stats()
        }


# Singleton instance
_memory_system_instance: Optional[MemorySystem] = None


def get_memory_system() -> MemorySystem:
    """الحصول على مثان نظام الذاكرة الوحيد"""
    global _memory_system_instance
    if _memory_system_instance is None:
        _memory_system_instance = MemorySystem()
    return _memory_system_instance


async def initialize_memory_system() -> MemorySystem:
    """تهيئة نظام الذاكرة"""
    system = get_memory_system()
    await system.initialize()
    return system
