import time
from functools import wraps

from prometheus_client import Counter, Histogram, generate_latest

CHAT_LATENCY = Histogram(
    "chat_request_duration_ms",
    "End-to-end chat request latency in milliseconds",
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
)

GRAPH_NODE_LATENCY = Histogram(
    "graph_node_duration_ms",
    "Per-node latency in milliseconds",
    labelnames=["node"],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
)

CHAT_REQUESTS_TOTAL = Counter("chat_requests_total", "Total chat requests processed")
CHAT_ERRORS_TOTAL = Counter("chat_errors_total", "Total chat request errors")


def time_node(name: str):
    """
    Decorator to time an async function and record the latency in GRAPH_NODE_LATENCY.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                GRAPH_NODE_LATENCY.labels(node=name).observe(elapsed)

        return wrapper

    return decorator


def get_metrics_data():
    """
    Returns the latest metrics data in Prometheus format.
    """
    return generate_latest()
