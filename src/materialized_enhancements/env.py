"""Environment configuration: .env loading + derived constants.

``MATERIALIZED_DEV_MODE`` is set by ``run.py`` when invoked with ``--dev``.
``DEPLOY_URL`` (when set) is the canonical public base for share links, report
exports, and sculpture email permalinks; see ``PUBLIC_APP_URL`` below.
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

def _canonical_public_app_url() -> str:
    """Base URL for share links, report QR/PDF, and sculpture email permalinks.

    ``DEPLOY_URL`` (the Reflex app URL in production) is preferred so deploy and
    public links stay aligned. ``PUBLIC_APP_URL`` applies when ``DEPLOY_URL`` is
    unset, for example when the marketing or share hostname differs from the app.
    """
    deploy = os.getenv("DEPLOY_URL", "").strip().rstrip("/")
    if deploy:
        return deploy
    public = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    if public:
        return public
    return "http://localhost:3000"


# Canonical public site root (from DEPLOY_URL, else PUBLIC_APP_URL, else localhost).
PUBLIC_APP_URL: str = _canonical_public_app_url()

# Resend transactional email — used by the "Send to email" buttons on the
# sculpture and jigsaw pages. RESEND_FROM_EMAIL must be a verified sender
# (use Resend's "onboarding@resend.dev" while iterating; switch to a domain
# you own once SPF/DKIM are set up). RESEND_REPLY_TO is optional.
RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL: str = os.getenv(
    "RESEND_FROM_EMAIL",
    "Materialized Enhancements <no-reply@longevity-genie.info>",
)
RESEND_REPLY_TO: str = os.getenv("RESEND_REPLY_TO", "")

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
