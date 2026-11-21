"""Command-line interface for `strictr check`."""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Parse *argv*, run the check, write output, and return the exit code."""
    raise NotImplementedError
