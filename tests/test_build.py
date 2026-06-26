"""Tests for the template injector (meadows.web.build).

BUSINESS RULE (MEADOWS §2 line 40 + §3.1): build.py is the ONLY place meadows-web
touches meadows.protocol, and only for EventName. These tests verify that the
closed set of event names is pulled from the single source of truth and that
every template placeholder is replaced in the rendered output (no leaked
`{{ ... }}`).
"""

from __future__ import annotations

import re

from meadows.web.build import (
    TEMPLATE_PATH,
    build,
    compute_hash,
    get_protocol_constants,
)


def test_get_protocol_constants_contains_core_events() -> None:
    """The browser needs the core chat event names: message, authenticate,
    user_typing. These are the *values* of EventName members (the actual wire
    strings emitted on the socket) — pulled from meadows.protocol, not hardcoded.
    """
    constants = get_protocol_constants()
    assert isinstance(constants, dict)
    values = set(constants.values())
    assert {"message", "authenticate", "user_typing"} <= values
    # Keys are the EventName member names (uppercase), so JS can do P.MESSAGE.
    assert "MESSAGE" in constants
    assert constants["MESSAGE"] == "message"


def test_compute_hash_returns_16_char_hex() -> None:
    """Cache-busting token: 16-char hex prefix of SHA-256 (matches the original
    monolith build.py contract)."""
    h = compute_hash("hello meadows")
    assert len(h) == 16
    assert re.fullmatch(r"[0-9a-f]{16}", h)


def test_build_replaces_all_template_vars(tmp_path) -> None:
    """build() must produce a file with NO leftover `{{ ... }}` placeholders —
    every template var (server url, system name, protocol blob, client hash)
    replaced."""
    out = tmp_path / "index.html"
    path = build(
        server_url="http://example-server:8080",
        system_name="Test Chat",
        template_path=TEMPLATE_PATH,
        output_path=out,
    )
    assert path == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")

    # No template placeholders may remain.
    assert "{{" not in content
    assert "}}" not in content

    # Injected config + protocol constants must be present.
    assert "http://example-server:8080" in content
    assert "Test Chat" in content
    assert "MEADOWS_PROTOCOL" in content
    assert "message" in content  # EventName.MESSAGE value, via the JSON blob

    # The client hash placeholder must have been replaced with a 16-char hex.
    assert re.search(r'content="[0-9a-f]{16}"', content)


def test_build_deterministic_for_same_input(tmp_path) -> None:
    """Same inputs → same output (stable cache-busting hash). The hash is over
    the rendered content, so identical renders produce an identical token."""
    out1 = tmp_path / "a.html"
    out2 = tmp_path / "b.html"
    build(server_url="http://s", system_name="N", template_path=TEMPLATE_PATH, output_path=out1)
    build(server_url="http://s", system_name="N", template_path=TEMPLATE_PATH, output_path=out2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")
