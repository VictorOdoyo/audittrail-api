from unittest.mock import patch

from audittrail_api.cli import main


def test_cli_runs_local_uvicorn_server() -> None:
    with patch("audittrail_api.cli.uvicorn.run") as run:
        main()

    run.assert_called_once_with(
        "audittrail_api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
