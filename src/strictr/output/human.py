"""Concise human-readable rendering for check results."""

from __future__ import annotations

from strictr.core.models import CheckResult

_DIAGNOSTIC_PREVIEW_LIMIT = 5


def render_human(result: CheckResult) -> str:
    """Return the stdout report: status, scope, tier lines, and first failures.

    Warnings and the trust warning are returned by `render_stderr`, not here.
    """
    raise NotImplementedError


def render_stderr(result: CheckResult, *, include_trust: bool) -> str:
    """Return newline-terminated warning lines for stderr.

    *include_trust* is true in human mode; `--json` passes false because the
    envelope already carries the trust object.
    """
    raise NotImplementedError
