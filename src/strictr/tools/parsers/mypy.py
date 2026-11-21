"""Pure mypy `--output=json` normalization."""

from __future__ import annotations

from pathlib import Path

from strictr.core.models import Diagnostic


def parse_mypy_json(stdout: str, root: Path) -> tuple[Diagnostic, ...]:
    """Normalize mypy JSON Lines into contract diagnostics for `tier1-types`.

    Each non-blank line is one diagnostic object with `file`, `line`, `column`,
    `message`, and `severity`; `end_line`, `end_column`, and `code` are optional.
    Severities map to the contract's `error`, `warning`, and `note`. Paths are
    relative to *root* and use `/`. The result is ordered by path, line, column,
    code, and message. Raises `InvalidToolOutput` when *stdout* is not the
    documented shape.
    """
    raise NotImplementedError
