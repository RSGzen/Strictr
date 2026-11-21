"""Tier 2: full-suite test verification with pytest."""

from __future__ import annotations

from strictr.core.models import CheckContext, TierResult
from strictr.core.protocols import ToolRunner

DEFAULT_TIMEOUT_SECONDS = 300.0
NO_TESTS_REASON = "no tests collected"
PYTEST_NOT_FOUND_REASON = "pytest not found"


class PytestTier:
    """Run the project's full pytest suite and normalize its JUnit evidence."""

    id = "tier2-pytest"
    name = "tests"

    def __init__(self, runner: ToolRunner) -> None:
        self._runner = runner

    def run(self, context: CheckContext) -> TierResult:
        """Return the pytest tier result for *context*.

        Always runs the full suite from the project root; targets do not narrow
        pytest. JUnit XML goes to a temporary directory outside the repository
        and is removed after parsing. Missing pytest is an error when test files
        or pytest configuration exist, and a deliberate `no tests collected`
        skip otherwise. Counts are recorded in `meta`; failures carry pytest
        node IDs and failure evidence in the diagnostic message.
        """
        raise NotImplementedError
