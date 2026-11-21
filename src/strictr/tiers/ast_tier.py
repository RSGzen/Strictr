"""Tier 0: in-process syntax verification."""

from __future__ import annotations

from strictr.core.models import CheckContext, TierResult

DEFAULT_TIMEOUT_SECONDS = 10.0


class AstTier:
    """Parse every discovered Python file within an in-process time budget.

    Files are parsed in discovery order. A syntax error produces a diagnostic
    with the root-relative path and a 1-based position, and the tier is `fail`.
    An exhausted budget is an `error`, never a pass or a fail.
    """

    id = "tier0"
    name = "syntax"

    def run(self, context: CheckContext) -> TierResult:
        """Return the Tier 0 result for *context*.

        The budget is `context.timeout`, falling back to
        `DEFAULT_TIMEOUT_SECONDS`. It is checked between files; an exhausted
        budget reports `tool timeout` with the reason in `meta.error`.
        """
        raise NotImplementedError
