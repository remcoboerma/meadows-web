from __future__ import annotations

from invoke import Context, task

try:
    from edwh import tasks as edwh_tasks
    from edwh import task as edwh_task
except ImportError:  # pragma: no cover
    edwh_tasks = None
    edwh_task = task


def _check_env(key: str, default: str = "", comment: str = "") -> str:
    """BUSINESS RULE (MEADOWS §4 line 114): env-beheer blijft via de edwh/check_env-conventie.

    Configuratie per service is niet los in code gezet; de bron van waarheid is de
    setup-taak die check_env aanroept. Hier registreren we de variabelen die deze
    domme host nodig heeft: bind-adres, server-URL (voor template-injectie) en de
    Traefik-routing parameters.
    """
    if edwh_tasks is not None:
        return edwh_tasks.check_env(key, default=default, comment=comment)
    import os

    val = os.environ.get(key, default)
    print(f"[check_env fallback] {key}={val!r}  # {comment}")
    return val


@task
def setup(c: Context) -> None:
    """Configure environment for meadows-web (the dumb HTTP host)."""
    if hasattr(c, "sudo"):
        c.sudo("chmod +x captain-hooks/*.sh")

    # Bind config for uvicorn (TLS is terminated by Traefik; this is plain HTTP).
    _check_env("MEADOWS_WEB_HOST", default="0.0.0.0", comment="Bind address for the web host (Traefik fronts it)")
    _check_env("MEADOWS_WEB_PORT", default="8081", comment="Bind port for the web host")

    # Template-injection config: the browser Socket.IO client connects to the server, not to us.
    _check_env(
        "MEADOWS_SERVER_URL",
        default="http://localhost:8080",
        comment="URL of meadows-server injected into index.html (browser is the Socket.IO client)",
    )
    _check_env("MEADOWS_SYSTEM_NAME", default="MEADOWS Chat", comment="Display name injected into the page")

    # Traefik routing parameters (section 4 line 115: TLS via Traefik labels).
    _check_env("PROJECT", default="meadows", comment="Traefik router prefix")
    _check_env("HOSTINGDOMAIN", default="localhost", comment="Traefik host domain")


@task
def test(c: Context) -> None:
    c.run("uv run pytest -q")


@task
def lint(c: Context) -> None:
    c.run("uv run ruff check src tests")


@task
def fmt(c: Context) -> None:
    c.run("uv run ruff format src tests")
    c.run("uv run ruff check --fix src tests")


__all__ = ["setup", "test", "lint", "fmt"]
