"""Console entry point for the development API."""

import uvicorn


def main() -> None:
    """Run the application with development-friendly defaults."""

    uvicorn.run("audittrail_api.main:app", host="127.0.0.1", port=8000, reload=True)
