"""Tier 0: in-process syntax verification."""

from __future__ import annotations

import ast
import time

from strictr.core.models import CheckContext, Diagnostic, TierResult
from strictr.core.paths import relative_posix

DEFAULT_TIMEOUT_SECONDS = 10.0
_BUDGET_REASON = "tool timeout"


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
        budget = DEFAULT_TIMEOUT_SECONDS if context.timeout is None else context.timeout
        started = time.perf_counter()
        deadline = started + budget
        diagnostics: list[Diagnostic] = []

        for path in context.files:
            if time.perf_counter() >= deadline:
                return self._budget_error(started, diagnostics, budget)
            try:
                ast.parse(path.read_bytes(), filename=str(path))
            except SyntaxError as error:
                diagnostics.append(
                    Diagnostic(
                        tier=self.id,
                        source="python",
                        path=relative_posix(path, context.root),
                        line=max(error.lineno or 1, 1),
                        column=max(error.offset or 1, 1),
                        code="syntax-error",
                        severity="error",
                        message=error.msg,
                    )
                )

        # A budget consumed by the last file must not become a pass.
        if time.perf_counter() >= deadline:
            return self._budget_error(started, diagnostics, budget)

        return TierResult(
            id=self.id,
            name=self.name,
            status="fail" if diagnostics else "pass",
            duration_ms=_elapsed_ms(started),
            diagnostics=tuple(diagnostics),
        )

    def _budget_error(
        self, started: float, diagnostics: list[Diagnostic], budget: float
    ) -> TierResult:
        return TierResult(
            id=self.id,
            name=self.name,
            status="error",
            duration_ms=_elapsed_ms(started),
            diagnostics=tuple(diagnostics),
            skipped_reason=_BUDGET_REASON,
            meta={"error": f"Tier 0 budget exceeded after {budget:g} seconds"},
        )


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
