"""Ordered tier execution, fail-fast, and result assembly."""

from __future__ import annotations

from collections.abc import Sequence

from .models import CheckContext, CheckResult, Scope
from .protocols import Tier


def run_pipeline(
    tiers: Sequence[Tier],
    context: CheckContext,
    scope: Scope,
    initial_warnings: Sequence[str] = (),
) -> CheckResult:
    """Run *tiers* in order until the first fail or error.

    Later tiers are recorded as skipped rather than omitted. The returned result
    owns the aggregated warnings and the finalized diagnostics.
    """
    raise NotImplementedError
