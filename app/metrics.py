"""Prometheus metrics and timing utilities."""
import time
import functools
from typing import Callable
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'removebg_requests_total',
    'Total number of background removal requests',
    ['status']
)

ERROR_COUNT = Counter(
    'removebg_errors_total',
    'Total number of errors',
    ['error_type']
)

REQUEST_LATENCY = Histogram(
    'removebg_request_duration_seconds',
    'Request duration in seconds',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            REQUEST_LATENCY.observe(duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            REQUEST_LATENCY.observe(duration)
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            REQUEST_LATENCY.observe(duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            REQUEST_LATENCY.observe(duration)
            raise
    
    if functools.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def get_metrics() -> Response:
    """Generate Prometheus metrics response."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
