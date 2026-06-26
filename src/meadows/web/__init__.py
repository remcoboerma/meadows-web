"""MEADOWS web host — a dumb HTTP host (MEADOWS §2 line 40).

This package serves index.html and static assets. It is deliberately the
simplest of the five MEADOWS distributions: no Socket.IO, no auth, no domain
logic. The browser is the Socket.IO client; the connection runs browser→
meadows-server, NOT via this Python webserver. TLS is terminated by Traefik
(section 4 line 115).

The only touch of meadows.protocol is in build.py, and only for EventName
(architecture invariant #3: protocol constants only).

PEP 420 (section 3.1): there is intentionally NO `src/meadows/__init__.py`.
Only this leaf package's __init__ exists.
"""

from meadows.web.__about__ import __version__

__all__ = ["__version__"]
