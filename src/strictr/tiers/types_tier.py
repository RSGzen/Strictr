"""Tier 1b: project type verification with mypy or pyright."""

from __future__ import annotations

from strictr.core.models import CheckContext, TierResult
from strictr.core.protocols import ToolRunner

DEFAULT_TIMEOUT_SECONDS = 180.0
NO_CHECKER_REASON = "no type checker found"
DISABLED_REASON = "disabled_by_user"
NO_CHECKER_WARNING = "No type checker found; install mypy or pyright for a full pass."
BOTH_CONFIGURED_WARNING = (
    "Both mypy and pyright are configured; using mypy. Pass --type-checker pyright to override."
)


class TypesTier:
    """Select the project's type checker, run it, and normalize its findings."""

    id = "tier1-types"
    name = "types"

    def __init__(self, runner: ToolRunner) -> None:
        self._runner = runner

    def run(self, context: CheckContext) -> TierResult:
        """Return the type tier result for *context*.

        Selection follows ADR 0005. A configured or explicitly requested checker
        that cannot be probed is an error; no checker at all is a required skip
        that makes the run `partial`. `--type-checker none` is a deliberate skip
        that does not. The selected checker and its selection reason are recorded
        in `meta`; the checker name and version go in `tool`.
        """
        raise NotImplementedError


def _pyright_module_available() -> bool:
    """Whether the PyPI pyright wrapper is importable in this interpreter."""
    raise NotImplementedError
