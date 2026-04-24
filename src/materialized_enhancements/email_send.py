"""Resend transactional email client + helpers shared by the sculpture and
jigsaw pages.

The "Send to email" buttons call into this module to deliver the same payload
the Download buttons would write to the user's disk, but as a Resend message.

Endpoint reference: https://resend.com/docs/api-reference/emails/send-email
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Any

from materialized_enhancements.env import (
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    RESEND_REPLY_TO,
)

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"

# Single-attachment soft cap. Resend itself accepts up to 40 MB total per
# message, but we zip earlier than that so a multi-MB STL doesn't blow up
# the recipient's inbox quota or land in spam.
ATTACHMENT_ZIP_THRESHOLD_BYTES = 1_500_000

# Hard cap on total attachment payload (raw, before base64). Slightly under
# Resend's 40 MB to leave headroom for base64 + JSON overhead.
MAX_TOTAL_ATTACHMENT_BYTES = 30_000_000

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class EmailAttachment:
    """One file to attach. ``content`` is raw bytes; we base64-encode at send time."""

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class EmailSendError(RuntimeError):
    """Raised when the Resend API rejects the message or transport fails."""


def is_valid_email(value: str) -> bool:
    """Cheap syntactic check — Resend will do the real validation."""
    return bool(EMAIL_RE.match(value.strip()))


def maybe_zip_attachments(
    attachments: list[EmailAttachment],
    zip_name: str,
    *,
    threshold: int = ATTACHMENT_ZIP_THRESHOLD_BYTES,
) -> list[EmailAttachment]:
    """Bundle attachments into one zip when their combined size exceeds ``threshold``.

    Smaller payloads stay as separate attachments so the user can grab the STL
    or SVG directly from the message preview without unzipping.
    """
    if not attachments:
        return []
    total = sum(len(a.content) for a in attachments)
    if total <= threshold:
        return list(attachments)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for a in attachments:
            zf.writestr(a.filename, a.content)
    return [EmailAttachment(filename=zip_name, content=buf.getvalue(), content_type="application/zip")]


def send_email_via_resend(
    to: str,
    subject: str,
    html: str,
    *,
    attachments: list[EmailAttachment] | None = None,
    text: str | None = None,
    reply_to: str | None = None,
) -> str:
    """Send a single transactional email via Resend.

    Returns the Resend message id on success. Raises ``EmailSendError`` on any
    transport or API error so callers can surface a single failure message.
    """
    if not RESEND_API_KEY:
        raise EmailSendError("RESEND_API_KEY is not configured.")
    recipient = to.strip()
    if not is_valid_email(recipient):
        raise EmailSendError(f"Invalid recipient email: {recipient!r}")

    attachments = attachments or []
    total_bytes = sum(len(a.content) for a in attachments)
    if total_bytes > MAX_TOTAL_ATTACHMENT_BYTES:
        raise EmailSendError(
            f"Attachments total {total_bytes:,} bytes, exceeds {MAX_TOTAL_ATTACHMENT_BYTES:,} byte limit."
        )

    payload: dict[str, Any] = {
        "from": RESEND_FROM_EMAIL,
        "to": [recipient],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    final_reply_to = (reply_to or RESEND_REPLY_TO).strip()
    if final_reply_to:
        payload["reply_to"] = final_reply_to
    if attachments:
        payload["attachments"] = [
            {
                "filename": a.filename,
                "content": base64.b64encode(a.content).decode("ascii"),
                "content_type": a.content_type,
            }
            for a in attachments
        ]

    body = json.dumps(payload).encode("utf-8")
    # Cloudflare in front of api.resend.com 403s the default `Python-urllib/*`
    # User-Agent (error 1010 — banned browser signature). Use a neutral UA so
    # the request reaches Resend.
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "materialized-enhancements/0.2 (+https://longevity-genie.info)",
    }
    req = urllib.request.Request(RESEND_API_URL, data=body, headers=headers, method="POST")
    logger.info(
        "Resend send: to=%s subject=%r attachments=%d bytes=%d",
        recipient, subject, len(attachments), total_bytes,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise EmailSendError(f"Resend HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise EmailSendError(f"Resend connection failed: {exc.reason}") from exc

    try:
        parsed: dict[str, Any] = json.loads(data) if data else {}
    except json.JSONDecodeError as exc:
        raise EmailSendError(f"Resend returned non-JSON body: {data!r}") from exc

    message_id = str(parsed.get("id", ""))
    if not message_id:
        raise EmailSendError(f"Resend response missing id: {parsed!r}")
    logger.info("Resend send ok: id=%s", message_id)
    return message_id
