"""Machine-readable verification envelope rendering."""

from __future__ import annotations

import json

from strictr.core.models import CheckResult
from strictr.core.text import escape_surrogates


def render_json(result: CheckResult) -> str:
    """Return *result* as one compact, newline-terminated JSON object.

    Warnings stay inside the envelope; the caller still writes them to stderr.
    Surrogates are escaped after serialization so the encoded byte stream stays
    valid UTF-8.
    """
    document = json.dumps(result.to_envelope(), ensure_ascii=False, separators=(",", ":"))
    return escape_surrogates(document) + "\n"
