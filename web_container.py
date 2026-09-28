"""Serve the existing FastAPI API and compiled React UI in one container."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
MODEL_BASE_URL = os.environ.get("MODEL_BASE_URL", "").rstrip("/")
parsed = urlparse(MODEL_BASE_URL)
if parsed.scheme not in {"http", "https"} or not parsed.hostname:
    raise RuntimeError("Set MODEL_BASE_URL to the existing model's HTTP /v1 endpoint.")
if not parsed.path.endswith("/v1"):
    raise RuntimeError("MODEL_BASE_URL must end in /v1.")
if not (ROOT / "guardrails_config").is_dir():
    raise RuntimeError("Mount the existing guardrails_config directory at /app/guardrails_config.")

sys.path.insert(0, str(ROOT / "benchmark"))
import model_endpoint as endpoint
from fastapi.staticfiles import StaticFiles

# model_endpoint creates its client during import; configure it before requests.
endpoint.client.endpoint_url = MODEL_BASE_URL
if endpoint.rails is None:
    raise RuntimeError("Guardrails initialization failed. Check the preceding application logs and configuration.")

app = endpoint.app


@app.get("/healthz", include_in_schema=False)
def healthz():
    """Application readiness only; this does not certify model connectivity."""
    return {"status": "ok", "guardrails_initialized": True}


# Register the UI last so existing API routes retain priority.
app.mount("/", StaticFiles(directory=str(ROOT / "frontend" / "dist"), html=True), name="frontend")
