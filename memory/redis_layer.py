"""
Redis Layer for State Management, Caching, and Pub/Sub
"""

import json
import redis.asyncio as redis
from typing import Any, Optional, List
from datetime import timedelta


class RedisLayer:
    """Async Redis client for AMOS state management"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True
        )
        await self.client.ping()
        print(f"✓ Connected to Redis at {self.host}:{self.port}")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set a value with optional TTL"""
        serialized = json.dumps(value)
        if ttl:
            await self.client.setex(key, int(ttl.total_seconds()), serialized)
        else:
            await self.client.set(key, serialized)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        result = await self.client.delete(key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0
    
    async def publish(self, channel: str, message: dict):
        """Publish message to channel"""
        await self.client.publish(channel, json.dumps(message))
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels"""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        return await self.client.incr(key)
    
    async def decrement(self, key: str) -> int:
        """Decrement counter"""
        return await self.client.decr(key)
    
    async def list_push(self, key: str, *values: Any):
        """Push to list"""
        serialized = [json.dumps(v) for v in values]
        await self.client.rpush(key, *serialized)
    
    async def list_pop(self, key: str, count: int = 1) -> List[Any]:
        """Pop from list"""
        items = await self.client.lrange(key, 0, count - 1)
        if items:
            await self.client.ltrim(key, count, -1)
            return [json.loads(i) for i in items]
        return []
    
    async def list_length(self, key: str) -> int:
        """Get list length"""
        return await self.client.llen(key)
    
    async def set_add(self, key: str, *members: str):
        """Add members to set"""
        await self.client.sadd(key, *members)
    
    async def set_members(self, key: str) -> List[str]:
        """Get all set members"""
        return await self.client.smembers(key)
    
    async def hash_set(self, name: str, key: str, value: Any):
        """Set hash field"""
        await self.client.hset(name, key, json.dumps(value))
    
    async def hash_get(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        data = await self.client.hget(name, key)
        if data:
            return json.loads(data)
        return None
    
    async def hash_get_all(self, name: str) -> dict:
        """Get all hash fields"""
        data = await self.client.hgetall(name)
        return {k: json.loads(v) for k, v in data.items()}
    
    async def scan_keys(self, pattern: str) -> List[str]:
        """Scan keys matching pattern"""
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        return keys
    
    async def flush_db(self):
        """Clear all data in current database"""
        await self.client.flushdb()
    
    async def health_check(self) -> dict:
        """Check Redis health"""
        info = await self.client.info()
        return {
            'status': 'healthy',
            'connected_clients': info.get('connected_clients', 0),
            'used_memory': info.get('used_memory_human', 'N/A'),
            'uptime': info.get('uptime_in_seconds', 0)
        }


# Singleton instance
_redis_layer: Optional[RedisLayer] = None


def get_redis_layer() -> RedisLayer:
    """Get or create Redis layer singleton"""
    global _redis_layer
    if _redis_layer is None:
        _redis_layer = RedisLayer()
    return _redis_layer
