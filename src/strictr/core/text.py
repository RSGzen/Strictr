"""Message redaction and truncation for the verification envelope."""

from __future__ import annotations

import re

MESSAGE_LIMIT = 2_000
ERROR_LIMIT = 500
DIAGNOSTIC_LIMIT = 20
TRUNCATION_MARKER = " [truncated]"
REDACTED = "[REDACTED]"

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{16,}=*"),
    re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret"
        r"|password|passwd|secret)\b\s*[:=]\s*[\"']?([A-Za-z0-9_./+=-]{8,})"
    ),
    re.compile(r"(?i)\bhttps?://[^/\s:@]+:[^/\s@]+@"),
)


def redact(text: str) -> str:
    """Replace the fixed v0.1 secret patterns with `[REDACTED]`."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


def cap_text(text: str, limit: int = MESSAGE_LIMIT) -> tuple[str, bool]:
    """Redact *text*, then cap it at *limit* characters including the marker.

    Returns the capped text and whether the cap was applied. Redaction runs
    first so truncation cannot split a secret.
    """
    text = redact(text)
    if len(text) <= limit:
        return text, False
    return text[: limit - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER, True
