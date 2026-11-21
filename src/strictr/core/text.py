"""Message redaction and truncation for the verification envelope."""

from __future__ import annotations

MESSAGE_LIMIT = 2_000
ERROR_LIMIT = 500
TRUNCATION_MARKER = " [truncated]"


def redact(text: str) -> str:
    """Replace the fixed v0.1 secret patterns with `[REDACTED]`."""
    raise NotImplementedError


def cap_text(text: str, limit: int = MESSAGE_LIMIT) -> tuple[str, bool]:
    """Redact *text*, then cap it at *limit* characters including the marker.

    Returns the capped text and whether the cap was applied. Redaction runs
    first so truncation cannot split a secret.
    """
    raise NotImplementedError
