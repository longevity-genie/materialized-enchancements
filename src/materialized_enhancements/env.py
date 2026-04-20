"""Environment configuration: .env loading + derived constants.

``MATERIALIZED_DEV_MODE`` is set by ``run.py`` when invoked with ``--dev``.
``ARTEX_API_URL`` / ``ARTEX_API_TOKEN`` match the variables used by ARTEX's
own ``run-new-project.ts`` sample.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _positive_int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


DEV_MODE: bool = os.getenv("MATERIALIZED_DEV_MODE", "").lower() in ("1", "true", "yes", "on")

# Minimum enhancement credits (cr) in Choice required to run Materialize (STL pipeline).
MIN_CREDITS_TO_MATERIALIZE: int = _positive_int_from_env("MIN_CREDITS_TO_MATERIALIZE", 25)

# ARTEX Platform API — credentials & instance target
ARTEX_API_URL: str = os.getenv("ARTEX_API_URL", "http://localhost:8080/v1")
ARTEX_API_TOKEN: str = os.getenv("ARTEX_API_TOKEN", "")
ARTEX_INSTANCE_ID: str = os.getenv("ARTEX_INSTANCE_ID", "default")

# Redirects after "Create ARTEX Project" success / kiosk idle timeout
# ARTEX_PROJECT_URL_TEMPLATE gets {project_id} substituted; ARTEX_IDLE_URL is plain.
# In dev mode both redirects go to ARTEX_DEV_REDIRECT_URL for visual verification.
ARTEX_PROJECT_URL_TEMPLATE: str = os.getenv(
    "ARTEX_PROJECT_URL_TEMPLATE", "https://artex.live/project/{project_id}"
)
ARTEX_IDLE_URL: str = os.getenv("ARTEX_IDLE_URL", "https://artex.live/")
ARTEX_DEV_REDIRECT_URL: str = os.getenv(
    "ARTEX_DEV_REDIRECT_URL", "https://example.com/artex-dev-redirect"
)

# Kiosk idle timer (only rendered in prod). Seconds.
IDLE_TIMEOUT_SECONDS: int = int(os.getenv("IDLE_TIMEOUT_SECONDS", "60"))
IDLE_WARNING_SECONDS: int = int(os.getenv("IDLE_WARNING_SECONDS", "5"))


def project_redirect_url(project_id: str, override: str = "") -> str:
    """URL to send the user to after a successful ARTEX project creation.

    Resolution order: ``override`` (e.g. from a ``?redirect=`` query arg) →
    prod template → dev fallback. All three support ``{project_id}``
    substitution, so a kiosk operator can point at
    ``?redirect=https://artex.live/wall/{project_id}`` and the project ID
    gets spliced in.
    """
    template = override or (ARTEX_DEV_REDIRECT_URL if DEV_MODE else ARTEX_PROJECT_URL_TEMPLATE)
    return template.format(project_id=project_id)


def idle_redirect_url() -> str:
    """URL the kiosk returns to when the inactivity timer expires."""
    if DEV_MODE:
        return ARTEX_DEV_REDIRECT_URL
    return ARTEX_IDLE_URL
