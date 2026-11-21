"""Subprocess execution for external verification tools."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from strictr.core.models import ToolResult


class SubprocessRunner:
    """Run tools without a shell and capture their output under a hard timeout."""

    def run(self, command: Sequence[str], *, cwd: Path, timeout: float) -> ToolResult:
        """Run *command* in *cwd* and capture UTF-8 stdout and stderr.

        Raises `ToolNotFoundError` when the executable cannot be started and
        `ToolTimeoutError` after terminating the process tree when *timeout*
        expires.
        """
        raise NotImplementedError

    def which(self, name: str) -> str | None:
        """Return the executable path for *name*, or `None` when absent."""
        raise NotImplementedError
