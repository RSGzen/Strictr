"""Ordered tier execution, fail-fast, and result assembly."""

from __future__ import annotations

import platform
import sys
import time
from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from strictr import __version__

from .models import (
    CheckContext,
    CheckResult,
    Diagnostic,
    Environment,
    OverallStatus,
    Scope,
    TierResult,
    Timings,
    ToolInfo,
)
from .protocols import Tier
from .text import DIAGNOSTIC_LIMIT, ERROR_LIMIT, cap_text

_EARLIER_TIER_FAILED = "earlier_tier_failed"
_INTERNAL_ERROR = "internal error"
_OPTIONAL_SKIP_REASONS = frozenset({"disabled_by_user", "no tests collected", _EARLIER_TIER_FAILED})


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
    started = time.perf_counter()
    results: list[TierResult] = []
    stop = False

    for tier in tiers:
        if stop:
            results.append(
                TierResult(
                    id=tier.id,
                    name=tier.name,
                    status="skipped",
                    skipped_reason=_EARLIER_TIER_FAILED,
                )
            )
            continue

        tier_started = time.perf_counter()
        try:
            result = tier.run(context)
        except Exception as error:
            result = TierResult(
                id=tier.id,
                name=tier.name,
                status="error",
                duration_ms=_elapsed_ms(tier_started),
                skipped_reason=_INTERNAL_ERROR,
                meta={"error": f"{type(error).__name__}: {error}"},
            )
        result = _finalize(result)
        results.append(result)
        if result.status in ("fail", "error"):
            stop = True

    warnings = list(initial_warnings)
    for result in results:
        warnings.extend(result.warnings)

    return CheckResult(
        tool=ToolInfo(name="strictr", version=__version__),
        status=_overall_status(results),
        scope=_copy_test_counts(scope, results),
        tiers=tuple(results),
        timings=Timings(total_ms=_elapsed_ms(started)),
        environment=Environment(
            python=platform.python_version(),
            platform=sys.platform,
            root=scope.root,
        ),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _finalize(result: TierResult) -> TierResult:
    truncated = False
    diagnostics: list[Diagnostic] = []
    for diagnostic in result.diagnostics:
        message, message_truncated = cap_text(diagnostic.message)
        truncated = truncated or message_truncated
        diagnostics.append(replace(diagnostic, message=message))

    diagnostics.sort(key=lambda item: (item.path, item.line, item.column, item.code, item.message))
    total = len(diagnostics)
    if total > DIAGNOSTIC_LIMIT:
        diagnostics = diagnostics[:DIAGNOSTIC_LIMIT]
        truncated = True

    meta = dict(result.meta)
    if "error" in meta:
        error_text, error_truncated = cap_text(str(meta["error"]), ERROR_LIMIT)
        meta["error"] = error_text
        truncated = truncated or error_truncated
    if truncated:
        meta["truncated"] = True
    if total > DIAGNOSTIC_LIMIT:
        meta["total_diagnostics"] = total

    return replace(result, diagnostics=tuple(diagnostics), meta=meta)


def _overall_status(results: Sequence[TierResult]) -> OverallStatus:
    statuses = {result.status for result in results}
    if "error" in statuses:
        return "error"
    if "fail" in statuses:
        return "fail"
    if any(_is_required_skip(result) for result in results):
        return "partial"
    return "pass"


def _is_required_skip(result: TierResult) -> bool:
    return result.status == "skipped" and result.skipped_reason not in _OPTIONAL_SKIP_REASONS


def _copy_test_counts(scope: Scope, results: Sequence[TierResult]) -> Scope:
    pytest_result = next((result for result in results if result.id == "tier2-pytest"), None)
    if pytest_result is None:
        return scope
    return replace(
        scope,
        tests_collected=_meta_int(pytest_result.meta, "tests_collected"),
        tests_run=_meta_int(pytest_result.meta, "tests_run"),
        tests_skipped=_meta_int(pytest_result.meta, "tests_skipped"),
    )


def _meta_int(meta: dict[str, Any], key: str) -> int:
    value = meta.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
