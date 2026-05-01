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
from pathlib import Path

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

def public_app_url() -> str:
    """Return the canonical public base URL, read fresh from env vars on every call.

    Priority: DEPLOY_URL → PUBLIC_APP_URL → http://localhost:3000

    Called as a function (not a module-level constant) so the value is always
    current — avoids the module-import-time freeze that caused localhost:3000
    to appear in emails when env vars weren't visible at import time.
    """
    deploy = os.getenv("DEPLOY_URL", "").strip().rstrip("/")
    if deploy:
        return deploy
    public = os.getenv("PUBLIC_APP_URL", "").strip().rstrip("/")
    if public:
        return public
    return "http://localhost:3000"


# Module-level constant kept for the report-canonical-base hidden input rendered
# by pages/index.py (Reflex renders it at compile time, not per-request).
PUBLIC_APP_URL: str = public_app_url()

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED_PUBLIC_DIR: Path = Path(
    os.getenv("GENERATED_PUBLIC_DIR", str(REPO_ROOT / "data" / "output" / "public"))
).expanduser()
GENERATED_URL_PREFIX: str = "/" + os.getenv("GENERATED_URL_PREFIX", "/generated").strip().strip("/")


def ensure_generated_public_dirs() -> None:
    """Create generated public output folders for fresh clones and runtime use."""
    (GENERATED_PUBLIC_DIR / "reports").mkdir(parents=True, exist_ok=True)


def generated_public_path(*parts: str) -> Path:
    """Return a path under the public generated output root."""
    return GENERATED_PUBLIC_DIR.joinpath(*parts)


def generated_public_url(relative_path: str) -> str:
    """Return an absolute public URL for a generated artifact."""
    path = relative_path.strip().lstrip("/")
    return f"{public_app_url()}{GENERATED_URL_PREFIX}/{path}"

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

# Umami analytics — both must be set for the tracking script to be injected.
# UMAMI_SCRIPT_URL: full URL to /script.js on your Umami instance.
# UMAMI_WEBSITE_ID: the UUID shown in Umami Settings → Websites.
UMAMI_SCRIPT_URL: str = os.getenv("UMAMI_SCRIPT_URL", "")
UMAMI_WEBSITE_ID: str = os.getenv("UMAMI_WEBSITE_ID", "")


def idle_redirect_url() -> str:
    """URL the kiosk returns to when the inactivity timer expires.

    The ?redirect= query param at runtime takes priority over this value
    (handled entirely in client JS inside the idle band).
    """
    if DEV_MODE:
        return ARTEX_DEV_REDIRECT_URL
    return ARTEX_IDLE_URL
