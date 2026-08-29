"""Low-cardinality Prometheus metrics."""

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "audittrail_http_requests_total",
    "Total HTTP requests handled by the API.",
    ("method", "route", "status"),
)
REQUEST_DURATION = Histogram(
    "audittrail_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)


def observe_request(method: str, route: str, status_code: int, duration_seconds: float) -> None:
    """Record one request using route templates instead of raw paths."""

    REQUEST_COUNT.labels(method=method, route=route, status=str(status_code)).inc()
    REQUEST_DURATION.labels(method=method, route=route).observe(duration_seconds)
