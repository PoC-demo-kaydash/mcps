"""
메모리 기반 캐시 시스템
========================

TTL(Time To Live)과 LRU(Least Recently Used) 정책을 지원하는 
스레드 안전한 메모리 캐시를 제공합니다.

기능:
- TTL 지원
- LRU 정책 (최대 크기 초과 시)
- 스레드 안전
- 캐시 데코레이터
- 통계 (히트/미스)

사용 예:
    from shared.cache import Cache, cached
    
    # 직접 사용
    cache = Cache(max_size=100, default_ttl=300)
    cache.set("key", "value")
    value = cache.get("key")
    
    # 데코레이터
    @cached(ttl=600)
    def get_user(user_id):
        return db.query(user_id)
"""

from typing import Any, Optional, Dict, Callable, List
from datetime import datetime, timedelta
from functools import wraps
import threading
import logging

logger = logging.getLogger(__name__)


# ===========================================
# 캐시 항목
# ===========================================

class CacheEntry:
    """캐시 항목"""
    
    __slots__ = ['value', 'created_at', 'expires_at', 'access_count', 'last_accessed']
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """만료 여부"""
        return datetime.now() > self.expires_at
    
    def access(self):
        """접근 기록"""
        self.access_count += 1
        self.last_accessed = datetime.now()


# ===========================================
# 메인 캐시 클래스
# ===========================================

class Cache:
    """
    메모리 캐시
    
    특징:
    - TTL 지원
    - LRU 정책 (max_size 초과 시 가장 오래 접근하지 않은 항목 제거)
    - 스레드 안전 (threading.Lock)
    
    Example:
        cache = Cache(max_size=1000, default_ttl=300)
        
        # 저장
        cache.set("user:U001", {"name": "홍길동"}, ttl=600)
        
        # 조회
        user = cache.get("user:U001")
        
        # 삭제
        cache.delete("user:U001")
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        초기화
        
        Args:
            max_size: 최대 캐시 항목 수
            default_ttl: 기본 TTL (초)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.Lock()
        
        # 통계
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        캐시 조회
        
        Args:
            key: 캐시 키
        
        Returns:
            값 또는 None (미스 또는 만료)
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # 만료 확인
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                logger.debug(f"Cache expired: {key}")
                return None
            
            # 접근 기록
            entry.access()
            self.hits += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        캐시 저장
        
        Args:
            key: 캐시 키
            value: 값
            ttl: TTL (초), None이면 default_ttl
        """
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl
            
            # 크기 초과 시 LRU 제거
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # 캐시 저장
            self.cache[key] = CacheEntry(value, ttl)
            
            logger.debug(f"Cache set: {key} (ttl={ttl}s)")
    
    def delete(self, key: str) -> bool:
        """
        캐시 삭제
        
        Returns:
            삭제 성공 여부
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    
    def clear(self):
        """전체 캐시 삭제"""
        with self.lock:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def exists(self, key: str) -> bool:
        """캐시 존재 여부 (만료되지 않은)"""
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            
            if entry.is_expired():
                del self.cache[key]
                return False
            
            return True
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        캐시 조회 또는 생성
        
        캐시에 값이 없으면 factory 함수를 호출하여 값을 생성하고 저장합니다.
        
        Args:
            key: 캐시 키
            factory: 값 생성 함수
            ttl: TTL
        
        Example:
            user = cache.get_or_set(
                f"user:{user_id}",
                lambda: db.get_user(user_id),
                ttl=600
            )
        """
        value = self.get(key)
        
        if value is not None:
            return value
        
        # 캐시 미스 - 값 생성
        value = factory()
        self.set(key, value, ttl)
        
        return value
    
    def _evict_lru(self):
        """LRU 항목 제거"""
        if not self.cache:
            return
        
        # 가장 오래전에 접근한 항목 찾기
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        del self.cache[lru_key]
        self.evictions += 1
        
        logger.debug(f"Cache evicted (LRU): {lru_key}")
    
    def cleanup_expired(self) -> int:
        """
        만료된 항목 정리
        
        Returns:
            삭제된 항목 수
        """
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계
        
        Returns:
            {
                "size": 현재 캐시 크기,
                "max_size": 최대 크기,
                "hits": 히트 수,
                "misses": 미스 수,
                "hit_rate": 히트율 (0-1),
                "evictions": 제거 수
            }
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self.evictions,
            }
    
    def reset_stats(self):
        """통계 초기화"""
        with self.lock:
            self.hits = 0
            self.misses = 0
            self.evictions = 0
    
    def keys(self) -> List[str]:
        """모든 키 목록 (만료되지 않은)"""
        with self.lock:
            return [
                key for key, entry in self.cache.items()
                if not entry.is_expired()
            ]
    
    def size(self) -> int:
        """현재 캐시 크기"""
        with self.lock:
            return len(self.cache)


# ===========================================
# 전역 캐시 인스턴스
# ===========================================

_default_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """기본 캐시 인스턴스 가져오기"""
    global _default_cache
    
    if _default_cache is None:
        _default_cache = Cache()
    
    return _default_cache


def set_default_cache(cache: Cache):
    """기본 캐시 인스턴스 설정"""
    global _default_cache
    _default_cache = cache


# ===========================================
# 캐시 데코레이터
# ===========================================

def cached(
    ttl: int = 300,
    key_func: Optional[Callable] = None,
    cache_instance: Optional[Cache] = None
):
    """
    함수 결과 캐싱 데코레이터
    
    Args:
        ttl: TTL (초)
        key_func: 캐시 키 생성 함수 (args, kwargs를 받아 문자열 반환)
        cache_instance: 사용할 캐시 인스턴스 (None이면 기본 캐시)
    
    Example:
        @cached(ttl=600)
        def get_user(user_id):
            return db.query(user_id)
        
        # 커스텀 키
        @cached(ttl=300, key_func=lambda args, kwargs: f"user:{args[0]}")
        def get_user(user_id):
            ...
        
        # 캐시 무효화
        get_user.invalidate("U001")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = cache_instance or get_cache()
            
            # 캐시 키 생성
            if key_func:
                cache_key = key_func(args, kwargs)
            else:
                # 기본 키: 함수명 + 인자 해시
                import hashlib
                args_str = str((args, sorted(kwargs.items())))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
                cache_key = f"{func.__module__}.{func.__name__}:{args_hash}"
            
            # 캐시 조회
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            # 캐시 미스 - 함수 실행
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # 캐시 저장 (None이 아닌 경우만)
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        # 캐시 무효화 함수 추가
        def invalidate(*args, **kwargs):
            cache = cache_instance or get_cache()
            
            if key_func:
                cache_key = key_func(args, kwargs)
            else:
                import hashlib
                args_str = str((args, sorted(kwargs.items())))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
                cache_key = f"{func.__module__}.{func.__name__}:{args_hash}"
            
            cache.delete(cache_key)
            logger.debug(f"Cache invalidated: {cache_key}")
        
        wrapper.invalidate = invalidate
        wrapper.cache_key_func = key_func
        
        return wrapper
    
    return decorator


def cached_property(ttl: int = 300):
    """
    프로퍼티 캐싱 데코레이터
    
    클래스의 프로퍼티 결과를 캐싱합니다.
    
    Example:
        class User:
            @cached_property(ttl=600)
            def permissions(self):
                return db.get_permissions(self.id)
    """
    def decorator(func):
        cache_attr = f"_cached_{func.__name__}"
        expires_attr = f"_cached_{func.__name__}_expires"
        
        @wraps(func)
        def wrapper(self):
            now = datetime.now()
            
            # 캐시 확인
            if hasattr(self, cache_attr) and hasattr(self, expires_attr):
                if now < getattr(self, expires_attr):
                    return getattr(self, cache_attr)
            
            # 캐시 미스 - 함수 실행
            result = func(self)
            
            # 캐시 저장
            setattr(self, cache_attr, result)
            setattr(self, expires_attr, now + timedelta(seconds=ttl))
            
            return result
        
        return property(wrapper)
    
    return decorator


# ===========================================
# 특화된 캐시 클래스
# ===========================================

class PermissionCache(Cache):
    """
    권한 캐시 (짧은 TTL)
    
    권한 정보는 자주 변경될 수 있으므로 짧은 TTL 사용
    """
    
    def __init__(self):
        super().__init__(max_size=500, default_ttl=60)


class UserCache(Cache):
    """
    사용자 캐시
    
    사용자 정보는 상대적으로 덜 변경되므로 중간 TTL 사용
    """
    
    def __init__(self):
        super().__init__(max_size=1000, default_ttl=300)


class ToolCache(Cache):
    """
    Tool 메타데이터 캐시 (긴 TTL)
    
    Tool 메타데이터는 거의 변경되지 않으므로 긴 TTL 사용
    """
    
    def __init__(self):
        super().__init__(max_size=200, default_ttl=3600)


class DocumentCache(Cache):
    """
    문서 캐시
    
    문서 내용 캐싱용 (중간 TTL)
    """
    
    def __init__(self):
        super().__init__(max_size=500, default_ttl=300)


# ===========================================
# Public API
# ===========================================

__all__ = [
    # 클래스
    "Cache",
    "CacheEntry",
    
    # 전역 캐시
    "get_cache",
    "set_default_cache",
    
    # 데코레이터
    "cached",
    "cached_property",
    
    # 특화 캐시
    "PermissionCache",
    "UserCache",
    "ToolCache",
    "DocumentCache",
]
