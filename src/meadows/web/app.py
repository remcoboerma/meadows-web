"""
BUSINESS RULE (MEADOWS §2 line 40 + §4 line 115): meadows-web is a dumb HTTP
host. It serves index.html and static assets, injects protocol constants into
the template, and does nothing else. The browser is the Socket.IO client; the
connection runs browser→meadows-server, NOT via this Python webserver.

This module deliberately has no socketio, no auth, no domain logic, no JWT, no
message parsing (architecture invariant #1). TLS is terminated by Traefik
(section 4 line 115), so this host speaks plain HTTP (invariant #2).
"""

from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse, Response
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from meadows.web.build import build

# Resolved relative to this file so the app works regardless of CWD (container
# WORKDIR is /app; the package lives at /app/src/meadows/web).
_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_INDEX = _PACKAGE_DIR / "dist" / "index.html"
_DEFAULT_STATIC = _PACKAGE_DIR / "static"


class WebHost:
    """
    BUSINESS RULE (MEADOWS §2 line 40): meadows-web is a dumb HTTP host.
    It serves files. The browser is the Socket.IO client, connecting directly
    to meadows-server. This Python webserver never touches Socket.IO. TLS is
    terminated by Traefik (MEADOWS §4 line 115).

    This class wires three routes and nothing more:
      - `GET /`          -> the built dist/index.html (template-injected by build.py)
      - `/static/*`      -> static assets, if any (404 when absent)
      - anything else    -> 404

    No auth, no sockets, no domain logic. If dist/index.html is missing on
    startup, the template is built once so the host is usable without a manual
    build step — this is static-asset preparation, not domain logic.
    """

    def __init__(self, index_path: Path = _DEFAULT_INDEX, static_dir: Path = _DEFAULT_STATIC) -> None:
        self.index_path = index_path
        self.static_dir = static_dir

    def _ensure_built(self) -> None:
        """BUSINESS RULE: guarantee the served index.html exists before serving.

        build.py is the single place that injects protocol constants (invariant
        #3). If the dist file is absent (fresh checkout / container start without
        a prior build), render it once from the template + env. This keeps the
        host a pure file server at request time while still being runnable
        standalone.
        """
        if not self.index_path.exists():
            build()

    def serve_index(self, request) -> Response:
        """BUSINESS RULE: serve the pre-built index.html at `/`. Dumb file host —
        no templating per request, no auth, no session. The page already carries
        the injected protocol constants + server URL from build.py."""
        del request  # request is unused: this route is a fixed file response (dumb host).
        self._ensure_built()
        if not self.index_path.exists():
            return Response("index.html not found", status_code=404)
        return FileResponse(self.index_path, media_type="text/html")

    def not_found(self, request) -> Response:
        """BUSINESS RULE: anything that isn't `/` or `/static/*` is a 404. The
        host serves only the chat page and static assets — no API surface."""
        del request  # unused: a dumb host has no per-request routing logic here.
        return Response("Not found", status_code=404)

    def create_app(self) -> Starlette:
        """BUSINESS RULE: assemble the ASGI app. Two real routes + a 404 catch-all.
        StaticFiles is mounted (directory created empty if missing so missing
        assets 404 instead of crashing the mount)."""
        self.static_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_built()

        routes = [
            Mount(
                "/static",
                app=StaticFiles(directory=str(self.static_dir), html=False),
                name="static",
            ),
        ]
        app = Starlette(routes=routes)
        app.router.add_route("/", self.serve_index, methods=["GET"])
        app.router.add_route("/{path:path}", self.not_found, methods=["GET"])
        return app


def create_app() -> Starlette:
    """Module-level factory for `uvicorn meadows.web.app:app`."""
    return WebHost().create_app()


# BUSINESS RULE: a module-level `app` so `uvicorn meadows.web.app:app` works
# without the caller invoking create_app() explicitly (matches the original
# monolith's `webchat` ASGI exposure pattern).
app = create_app()

__all__ = ["WebHost", "app", "create_app"]
