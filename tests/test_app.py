"""Tests for the dumb HTTP host (meadows.web.app).

BUSINESS RULE (MEADOWS §2 line 40): meadows-web serves index.html and static
assets, and nothing else. These tests pin the three behaviours the host is
allowed to have — serve `/`, 404 unknown paths, 404 missing static assets —
and assert that the served page carries the injected protocol constants
(proof that build.py pulled EventName from meadows.protocol).
"""

from __future__ import annotations

from starlette.testclient import TestClient

from meadows.web.app import app


def test_root_returns_200_and_contains_system_name(system_name: str) -> None:
    """GET / serves the built index.html, which embeds the system display name
    injected by build.py (MEADOWS §2 line 40: template injection)."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert system_name in response.text


def test_root_contains_injected_protocol_constants() -> None:
    """The served page must carry the protocol event-name constants pulled from
    meadows.protocol.EventName (invariant #3: protocol constants only). "message"
    is EventName.MESSAGE's wire value — its presence proves the injection ran."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.text
    assert "MEADOWS_PROTOCOL" in response.text


def test_nonexistent_path_returns_404() -> None:
    """A dumb host has no API surface: anything that isn't `/` or `/static/*`
    is a 404."""
    client = TestClient(app)
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_missing_static_asset_returns_404() -> None:
    """`/static/*` is a StaticFiles mount; a missing asset 404s rather than
    falling through to a catch-all. The host serves only existing assets."""
    client = TestClient(app)
    response = client.get("/static/does-not-exist.css")
    assert response.status_code == 404
