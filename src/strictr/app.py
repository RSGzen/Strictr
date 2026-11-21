"""Wiring from CLI arguments to one check result."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from strictr.core.discovery import discover
from strictr.core.errors import DiscoveryError
from strictr.core.models import (
    CheckContext,
    CheckResult,
    Scope,
    TierResult,
    TypeCheckerChoice,
)
from strictr.core.paths import relative_posix
from strictr.core.pipeline import run_pipeline
from strictr.core.protocols import Tier, ToolRunner
from strictr.tiers.ast_tier import AstTier
from strictr.tiers.ruff_tier import RuffTier
from strictr.tiers.types_tier import TypesTier
from strictr.tools.runner import SubprocessRunner

_NO_FILES_MESSAGE = "no Python files found"
_DISCOVERY_REASON = "discovery failed"


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
    runner = SubprocessRunner()
    try:
        discovery = discover(targets)
    except DiscoveryError as error:
        return _discovery_result(
            error,
            targets,
            runner,
            type_checker=type_checker,
            timeout=timeout,
        )

    context = CheckContext(
        root=discovery.root,
        targets=discovery.targets,
        files=discovery.files,
        timeout=timeout,
        type_checker=type_checker,
    )
    scope = Scope(
        root=relative_posix(discovery.root, Path.cwd()),
        targets=discovery.targets,
        files_checked=len(discovery.files),
        files_skipped=discovery.files_skipped,
    )
    return run_pipeline(
        _pipeline_tiers(AstTier(), runner),
        context,
        scope,
        initial_warnings=discovery.warnings,
    )


def _pipeline_tiers(tier0: Tier, runner: ToolRunner) -> tuple[Tier, ...]:
    """Run Tier 0, ruff, then the type checker; T-9 appends pytest."""
    return (tier0, RuffTier(runner), TypesTier(runner))


def _discovery_result(
    error: DiscoveryError,
    targets: Sequence[str],
    runner: ToolRunner,
    *,
    type_checker: TypeCheckerChoice | None,
    timeout: float | None,
) -> CheckResult:
    recorded = tuple(target for target in targets if target) or (".",)
    context = CheckContext(
        root=Path.cwd(),
        targets=recorded,
        files=(),
        timeout=timeout,
        type_checker=type_checker,
    )
    scope = Scope(root=".", targets=recorded)
    reason = _NO_FILES_MESSAGE if str(error) == _NO_FILES_MESSAGE else _DISCOVERY_REASON
    return run_pipeline(
        _pipeline_tiers(_ErrorTier(reason, str(error)), runner),
        context,
        scope,
    )


@dataclass(slots=True)
class _ErrorTier:
    """Report a failure that happened before any tier could run."""

    reason: str
    message: str
    id: str = "tier0"
    name: str = "syntax"

    def run(self, context: CheckContext) -> TierResult:
        del context
        return TierResult(
            id=self.id,
            name=self.name,
            status="error",
            skipped_reason=self.reason,
            meta={"error": self.message},
        )
