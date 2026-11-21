"""Tier 1a: project lint verification with ruff."""

from __future__ import annotations

from strictr.core.models import CheckContext, TierResult
from strictr.core.protocols import ToolRunner

DEFAULT_TIMEOUT_SECONDS = 30.0


class RuffTier:
    """Run the project's ruff from the project root and normalize its findings."""

    id = "tier1-ruff"
    name = "lint"

    def __init__(self, runner: ToolRunner) -> None:
        self._runner = runner

    def run(self, context: CheckContext) -> TierResult:
        """Return the ruff tier result for *context*."""
        raise NotImplementedError
