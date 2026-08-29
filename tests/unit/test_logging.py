import json
import logging

from audittrail_api.logging import JSONFormatter, configure_logging


def test_json_formatter_includes_operational_context() -> None:
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="audittrail.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-42"
    record.status_code = 201

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "request completed"
    assert payload["request_id"] == "request-42"
    assert payload["status_code"] == 201


def test_logging_configuration_replaces_existing_handlers() -> None:
    configure_logging(logging.WARNING)

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JSONFormatter)
