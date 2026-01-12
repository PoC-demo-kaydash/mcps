"""
캐시 유틸리티

shared.cache 래퍼
"""

from shared.cache import Cache

# 전역 캐시 인스턴스
cache = Cache()

__all__ = ["cache"]
