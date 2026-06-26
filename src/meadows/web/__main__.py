"""BUSINESS RULE (MEADOWS §2 line 40): `python -m meadows.web` runs the dumb
HTTP host via uvicorn. Plain HTTP — TLS is terminated by Traefik (§4 line 115),
so no cert logic here (invariant #2). Defaults match tasks.py:check_env so the
container and local dev behave identically.
"""

from __future__ import annotations

import os

import uvicorn

from meadows.web.app import create_app

app = create_app()


def main() -> None:
    """BUSINESS RULE: serve files on the configured host/port. Nothing else —
    the browser opens its own Socket.IO connection to meadows-server using the
    URL injected into index.html by build.py."""
    host = os.environ.get("MEADOWS_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("MEADOWS_WEB_PORT", "8081"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
