"""Pure ruff JSON output normalization."""

from __future__ import annotations

from pathlib import Path

from strictr.core.models import Diagnostic


def parse_ruff_json(stdout: str, root: Path) -> tuple[Diagnostic, ...]:
    """Normalize ruff `--output-format=json` output into contract diagnostics.

    Returned paths are relative to *root* and use `/`, and the result is ordered
    by the contract's diagnostic key. Raises `InvalidToolOutput` when *stdout*
    is not the documented JSON shape.
    """
    raise NotImplementedError
