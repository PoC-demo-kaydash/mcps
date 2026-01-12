"""
Cache service for Redis-based caching
"""
from typing import Optional, Any
import json
import redis.asyncio as redis
from ..core.config import settings
from ..core.exceptions import ServiceUnavailable
from ..utils.logger import logger


class CacheService:
    """Redis cache service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl
    
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if not self.enabled:
            raise ServiceUnavailable("Cache is disabled")
        
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Redis connection failed: {str(e)}")
                raise ServiceUnavailable(f"Cannot connect to Redis: {str(e)}")
        
        return self.redis_client
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            client = await self._get_client()
            value = await client.get(key)
            
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: from settings)
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            client = await self._get_client()
            
            # Serialize value
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            # Set with TTL
            ttl = ttl or self.ttl
            await client.setex(key, ttl, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        if not self.enabled:
            return False
        
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self.enabled:
            return False
        
        try:
            client = await self._get_client()
            result = await client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache exists error: {str(e)}")
            return False
    
    async def ping(self) -> bool:
        """
        Check if Redis is responding
        
        Returns:
            True if Redis is healthy
        """
        if not self.enabled:
            return False
        
        try:
            client = await self._get_client()
            await client.ping()
            return True
        except Exception:
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment counter
        
        Args:
            key: Cache key
            amount: Increment amount
            
        Returns:
            New counter value
        """
        if not self.enabled:
            return 0
        
        try:
            client = await self._get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache incr error: {str(e)}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            client = await self._get_client()
            return await client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error: {str(e)}")
            return False
