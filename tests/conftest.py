"""Pytest fixtures and deterministic build for meadows-web tests.

BUSINESS RULE (MEADOWS §2 line 40): the app under test is a dumb file host. The
served page is produced by build.py (template injection of protocol constants +
env config). To keep tests deterministic and independent of the host
environment, we pin the env and (re)build dist/index.html once before the suite.
"""

from __future__ import annotations

import os

# Pin env BEFORE the app module is imported so create_app()'s _ensure_built()
# renders the template with these known values (invariant: deterministic tests).
os.environ.setdefault("MEADOWS_SERVER_URL", "http://localhost:8080")
os.environ.setdefault("MEADOWS_SYSTEM_NAME", "MEADOWS Chat")
os.environ.setdefault("MEADOWS_WEB_HOST", "0.0.0.0")
os.environ.setdefault("MEADOWS_WEB_PORT", "8081")

from meadows.web.build import build

# Render the served page once with the pinned config so the ASGI app has a
# concrete, assertion-friendly index.html to serve.
build()

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def system_name() -> str:
    """The display name injected into the page — asserted by test_app."""
    return os.environ["MEADOWS_SYSTEM_NAME"]
