"""App-factory construction test.

Builds the FastAPI app without a running database/Redis (the lifespan is not
entered, so no external connections are made) and asserts the expected routes
are registered.
"""

from __future__ import annotations

from app.config import settings
from app.main import create_app


def test_create_app_builds():
    app = create_app()
    assert app.title


def test_expected_routes_registered():
    app = create_app()
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/health" in paths
    assert "/health/ready" in paths
    assert "/metrics" in paths


def test_openapi_lists_v1_endpoints():
    app = create_app()
    schema = app.openapi()
    prefix = settings.api_v1_prefix
    documented = set(schema["paths"].keys())
    assert f"{prefix}/auth/login" in documented
    assert f"{prefix}/auth/register" in documented
    assert f"{prefix}/lessons/generate" in documented
