"""
BUSINESS RULE (MEADOWS §2 line 40): meadows-web injects protocol constants
into the template. The browser needs to know event names (e.g. "message",
"authenticate", "user_typing") to talk to meadows-server. Rather than
hardcoding string literals in JS (which is what the monolith did — see
MEADOWS-migration-intent.md §1 line 11, where the protocol "zat verstopt
in de handlers en in conventies"), we inject them from the single source of
truth: meadows.protocol.EventName.

This module is the ONLY place meadows-web touches meadows.protocol, and it
touches it ONLY for EventName. Per architecture invariant #3, it does not
import Message, JWTClaims, or anything else — the web host doesn't need them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from meadows.protocol import EventName

# BUSINESS RULE (MEADOWS §2 line 40): the template is the one artifact this host
# shapes before serving. Paths are relative to this module so the build works
# whether invoked from the repo root or from `python -m meadows.web.build`.
_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_PATH = _TEMPLATES_DIR / "index.html"
OUTPUT_PATH = Path(__file__).resolve().parent / "dist" / "index.html"


def get_protocol_constants() -> dict[str, str]:
    """BUSINESS RULE (MEADOWS §2 line 40 + §3.1): expose the closed set of event
    names to the browser as a JSON blob.

    The protocol package declares EventName as the single source of truth for the
    Socket.IO events the system contracts (meadows-protocol/src/meadows/protocol/
    events.py). The browser JS must emit and listen for these exact names. We
    serialize `{MEMBER_NAME: string_value}` so JS can reference
    `window.MEADOWS_PROTOCOL.MESSAGE` etc. without hardcoding literals.

    This is a pure declaration pull — no behavior is imported, keeping invariant
    #3 (protocol constants only).
    """
    return {member.name: member.value for member in EventName}


def compute_hash(content: str) -> str:
    """BUSINESS RULE: produce a cache-busting token for the served page.

    The original monolith build.py (chat.openit.chat/webchat/build.py) computed a
    SHA-256 prefix for the same purpose. We keep the 16-char hex prefix so CDN /
    browser caches invalidate whenever the rendered content (and thus the injected
    protocol constants or config) changes.
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def build(
    *,
    server_url: str | None = None,
    system_name: str | None = None,
    template_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """BUSINESS RULE (MEADOWS §2 line 40): render templates/index.html into
    dist/index.html with env config + protocol constants injected.

    This is the meadows-web equivalent of the monolith's build.py — but the only
    protocol knowledge it carries is EventName (invariant #3). The rendered file
    is what app.py serves at `/`. TLS, auth and sockets are deliberately absent
    (invariants #1 and #2); the browser uses the injected MEADOWS_SERVER_URL to
    open its own Socket.IO connection straight to meadows-server.

    Defaults read from the environment so `python -m meadows.web.build` works in
    the container (env vars come from docker-compose / check_env in tasks.py).
    Returns the path to the built file so callers (tests, CLI) can locate it.
    """
    import os

    server_url = server_url if server_url is not None else os.environ.get("MEADOWS_SERVER_URL", "http://localhost:8080")
    system_name = system_name if system_name is not None else os.environ.get("MEADOWS_SYSTEM_NAME", "MEADOWS Chat")

    template_path = template_path if template_path is not None else TEMPLATE_PATH
    output_path = output_path if output_path is not None else OUTPUT_PATH

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    content = template_path.read_text(encoding="utf-8")

    # Inject config + protocol constants (single source of truth = EventName).
    protocol_json = json.dumps(get_protocol_constants(), indent=2, sort_keys=True)
    content = content.replace("{{ MEADOWS_SERVER_URL }}", server_url)
    content = content.replace("{{ MEADOWS_SYSTEM_NAME }}", system_name)
    content = content.replace("{{ MEADOWS_PROTOCOL }}", protocol_json)

    # Cache-busting hash: computed over the rendered content, then injected
    # as a meta tag before </head> (matching the monolith's build.py pattern).
    client_hash = compute_hash(content)
    content = content.replace(
        "</head>",
        f'<meta name="meadows-hash" content="{client_hash}"></head>',
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Built {output_path} (hash={client_hash})")
    return output_path


if __name__ == "__main__":
    build()
