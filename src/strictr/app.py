"""Wiring from CLI arguments to one check result."""

from __future__ import annotations

from collections.abc import Sequence

from strictr.core.models import CheckResult, TypeCheckerChoice


def run_check(
    targets: Sequence[str] = (),
    *,
    type_checker: TypeCheckerChoice | None = None,
    timeout: float | None = None,
) -> CheckResult:
    """Discover *targets*, run the pipeline, and return the assembled result.

    Discovery failures become an error result so the caller always has an
    envelope; the caller owns rendering and exit codes.
    """
    raise NotImplementedError
