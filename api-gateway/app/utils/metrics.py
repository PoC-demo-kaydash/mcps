"""
Prometheus metrics collection (optional)
"""
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge
from ..core.config import settings

# Only enable metrics if configured
METRICS_ENABLED = settings.metrics_enabled

if METRICS_ENABLED:
    # Request metrics
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"]
    )
    
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"]
    )
    
    # MCP Host communication metrics
    mcp_host_requests_total = Counter(
        "mcp_host_requests_total",
        "Total requests to MCP Host",
        ["endpoint", "status"]
    )
    
    mcp_host_request_duration_seconds = Histogram(
        "mcp_host_request_duration_seconds",
        "MCP Host request duration in seconds",
        ["endpoint"]
    )
    
    # Cache metrics
    cache_hits_total = Counter(
        "cache_hits_total",
        "Total cache hits"
    )
    
    cache_misses_total = Counter(
        "cache_misses_total",
        "Total cache misses"
    )
    
    # Rate limit metrics
    rate_limit_exceeded_total = Counter(
        "rate_limit_exceeded_total",
        "Total rate limit exceeded events"
    )
    
    # Active connections
    active_connections = Gauge(
        "active_connections",
        "Number of active connections"
    )
    
else:
    # Dummy metrics for when metrics are disabled
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self
        
        def inc(self, *args, **kwargs):
            pass
        
        def observe(self, *args, **kwargs):
            pass
        
        def set(self, *args, **kwargs):
            pass
    
    http_requests_total = DummyMetric()
    http_request_duration_seconds = DummyMetric()
    mcp_host_requests_total = DummyMetric()
    mcp_host_request_duration_seconds = DummyMetric()
    cache_hits_total = DummyMetric()
    cache_misses_total = DummyMetric()
    rate_limit_exceeded_total = DummyMetric()
    active_connections = DummyMetric()


def record_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    Record HTTP request metrics
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    if METRICS_ENABLED:
        http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_mcp_request(endpoint: str, status_code: int, duration: float):
    """
    Record MCP Host request metrics
    
    Args:
        endpoint: MCP Host endpoint
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    if METRICS_ENABLED:
        mcp_host_requests_total.labels(endpoint=endpoint, status=status_code).inc()
        mcp_host_request_duration_seconds.labels(endpoint=endpoint).observe(duration)


def record_cache_hit():
    """Record cache hit"""
    if METRICS_ENABLED:
        cache_hits_total.inc()


def record_cache_miss():
    """Record cache miss"""
    if METRICS_ENABLED:
        cache_misses_total.inc()


def record_rate_limit_exceeded():
    """Record rate limit exceeded event"""
    if METRICS_ENABLED:
        rate_limit_exceeded_total.inc()


def set_active_connections(count: int):
    """
    Set number of active connections
    
    Args:
        count: Number of active connections
    """
    if METRICS_ENABLED:
        active_connections.set(count)
