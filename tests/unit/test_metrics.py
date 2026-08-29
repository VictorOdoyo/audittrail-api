from audittrail_api.observability.metrics import REQUEST_COUNT, observe_request


def test_request_metric_uses_bounded_labels() -> None:
    labels = {"method": "GET", "route": "/health/live", "status": "200"}
    before = REQUEST_COUNT.labels(**labels)._value.get()

    observe_request("GET", "/health/live", 200, 0.012)

    assert REQUEST_COUNT.labels(**labels)._value.get() == before + 1
