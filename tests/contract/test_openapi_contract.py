from typing import Any

from audittrail_api.main import app


def test_openapi_contract_exposes_versioned_operational_surface() -> None:
    schema = app.openapi()
    paths: dict[str, dict[str, Any]] = schema["paths"]
    expected_paths = {
        "/api/v1/auth/token",
        "/api/v1/auth/me",
        "/api/v1/events",
        "/api/v1/events/batch",
        "/api/v1/events/verify-chain",
        "/api/v1/exports",
        "/api/v1/dead-letters",
        "/api/v1/dead-letters/{record_id}/retry",
        "/api/v1/organizations/{organization_id}/retention/preview",
        "/api/v1/organizations/{organization_id}/retention/runs",
        "/health/live",
        "/health/ready",
    }

    assert schema["info"]["version"] == "1.0.0"
    assert expected_paths <= paths.keys()
    assert "/metrics" not in paths


def test_openapi_operations_have_unique_ids_and_response_contracts() -> None:
    schema = app.openapi()
    operation_ids: list[str] = []
    for path_item in schema["paths"].values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation_ids.append(operation["operationId"])
            assert "responses" in operation
            assert operation["responses"]

    assert len(operation_ids) == len(set(operation_ids))
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
