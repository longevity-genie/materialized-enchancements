"""Environment configuration: .env loading + derived constants.

``MATERIALIZED_DEV_MODE`` is set by ``run.py`` when invoked with ``--dev``.
``ARTEX_API_URL`` / ``ARTEX_API_TOKEN`` are the platform API base URL and the
admin token (``ARTEX_PLATFORM_ADMIN_TOKEN`` on the server side) used to exchange
for a short-lived session token at publish time.
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

# ARTEX Platform API — credentials & venue display target
ARTEX_API_URL: str = os.getenv("ARTEX_API_URL", "http://127.0.0.1:8787")
ARTEX_API_TOKEN: str = os.getenv("ARTEX_API_TOKEN", "")
ARTEX_DISPLAY_ID: str = os.getenv("ARTEX_DISPLAY_ID", "test-wall")

# Kiosk inactivity redirect — where the idle timer sends the visitor.
# The ?redirect= query param at runtime overrides this.
ARTEX_IDLE_URL: str = os.getenv("ARTEX_IDLE_URL", "https://artex.live/")
ARTEX_DEV_REDIRECT_URL: str = os.getenv(
    "ARTEX_DEV_REDIRECT_URL", "http://127.0.0.1:8787/public/projects/{slug}"
)

# Public frontend URL used for share/report links.
PUBLIC_APP_URL: str = os.getenv("PUBLIC_APP_URL", "http://localhost:3000").rstrip("/")

# Kiosk idle timer (only rendered in prod). Seconds.
IDLE_TIMEOUT_SECONDS: int = int(os.getenv("IDLE_TIMEOUT_SECONDS", "60"))
IDLE_WARNING_SECONDS: int = int(os.getenv("IDLE_WARNING_SECONDS", "5"))


def idle_redirect_url() -> str:
    """URL the kiosk returns to when the inactivity timer expires.

    The ?redirect= query param at runtime takes priority over this value
    (handled entirely in client JS inside the idle band).
    """
    if DEV_MODE:
        return ARTEX_DEV_REDIRECT_URL
    return ARTEX_IDLE_URL
