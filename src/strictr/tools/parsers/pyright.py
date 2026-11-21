"""Pure pyright `--outputjson` normalization."""

from __future__ import annotations

from pathlib import Path

from strictr.core.models import Diagnostic


def parse_pyright_json(stdout: str, root: Path) -> tuple[Diagnostic, ...]:
    """Normalize pyright JSON into contract diagnostics for `tier1-types`.

    `generalDiagnostics` entries carry a 0-based `range`; contract positions are
    1-based. `information` maps to the contract's `note`, and `rule` becomes the
    code when present. Paths are relative to *root* and use `/`. The result is
    ordered by path, line, column, code, and message. Raises `InvalidToolOutput`
    when *stdout* is not the documented shape.
    """
    raise NotImplementedError
