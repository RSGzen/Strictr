"""Machine-readable verification envelope rendering."""

from __future__ import annotations

from strictr.core.models import CheckResult


def render_json(result: CheckResult) -> str:
    """Return *result* as one compact, newline-terminated JSON object.

    Warnings stay inside the envelope; the caller still writes them to stderr.
    """
    raise NotImplementedError
