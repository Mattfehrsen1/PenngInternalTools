"""
Phase 4.3.1: Redis Caching Service for ElevenLabs Integration
Implements caching for frequent queries to optimize voice response latency
"""

import redis
import json
import hashlib
import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service for optimizing voice conversation performance
    Implements Phase 4.3.1 requirements with proper TTL and key management
    """
    
    def __init__(self):
        # Connect to Redis (use default localhost:6379 for development)
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Connected to Redis cache")
            self.enabled = True
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, caching disabled: {str(e)}")
            self.redis_client = None
            self.enabled = False
    
    def _get_cache_key(self, query: str, persona_id: str, cache_type: str = "rag_query") -> str:
        """
        Generate cache key for query-persona combination
        Uses MD5 hash to ensure consistent key length and avoid special characters
        """
        content = f"{cache_type}:{query}:{persona_id}"
        return f"voice_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    def _get_persona_summary_key(self, persona_id: str) -> str:
        """Generate cache key for persona summary information"""
        return f"persona_summary:{persona_id}"
    
    async def get_cached_response(self, query: str, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response for query-persona combination
        Returns None if not cached or caching disabled
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._get_cache_key(query, persona_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"📋 Cache hit for query: {query[:50]}...")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
            return None
    
    async def cache_response(
        self, 
        query: str, 
        persona_id: str, 
        response: Dict[str, Any], 
        ttl_minutes: int = 5
    ) -> bool:
        """
        Cache response for query-persona combination
        Default TTL is 5 minutes to balance freshness and performance
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._get_cache_key(query, persona_id)
            
            # Add cache metadata
            cache_data = {
                **response,
                "_cached_at": int(time.time()),
                "_cache_key": cache_key
            }
            
            # Store with TTL
            ttl_seconds = ttl_minutes * 60
            self.redis_client.setex(
                cache_key, 
                ttl_seconds, 
                json.dumps(cache_data)
            )
            
            logger.info(f"💾 Cached response for query: {query[:50]}... (TTL: {ttl_minutes}m)")
            return True
            
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
            return False
    
    async def cache_persona_summary(self, persona_id: str, persona_data: Dict[str, Any]) -> bool:
        """
        Cache persona summary for quick fallback responses
        Long TTL since persona data changes infrequently
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._get_persona_summary_key(persona_id)
            
            summary_data = {
                "persona_name": persona_data.get("name", "Unknown"),
                "persona_description": persona_data.get("description", ""),
                "cached_at": int(time.time())
            }
            
            # 1 hour TTL for persona data
            self.redis_client.setex(cache_key, 3600, json.dumps(summary_data))
            logger.info(f"💾 Cached persona summary for {persona_data.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Persona cache error: {str(e)}")
            return False
    
    async def get_persona_summary(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get cached persona summary for fallback responses"""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._get_persona_summary_key(persona_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Persona summary retrieval error: {str(e)}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        if not self.enabled:
            return {"enabled": False, "message": "Redis not available"}
        
        try:
            info = self.redis_client.info()
            
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "Unknown"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), 
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            return {"enabled": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    async def invalidate_persona_cache(self, persona_id: str) -> bool:
        """
        Invalidate all cached data for a specific persona
        Useful when persona knowledge base is updated
        """
        if not self.enabled:
            return False
        
        try:
            # Get all keys matching persona pattern
            pattern = f"voice_cache:*:{persona_id}"
            keys = self.redis_client.keys(pattern)
            
            # Also invalidate persona summary
            persona_key = self._get_persona_summary_key(persona_id)
            if self.redis_client.exists(persona_key):
                keys.append(persona_key)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} cache entries for persona {persona_id}")
                return deleted > 0
            
            return True
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
            return False

# Global cache service instance
cache_service = CacheService() 