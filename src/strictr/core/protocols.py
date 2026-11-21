"""Ports between the pipeline, tiers, and the subprocess runner."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from .models import CheckContext, TierResult, ToolResult


class ToolRunner(Protocol):
    """Execute an external tool without a shell."""

    def run(self, command: Sequence[str], *, cwd: Path, timeout: float) -> ToolResult:
        """Run *command* in *cwd* and return captured output."""
        ...

    def which(self, name: str) -> str | None:
        """Return the executable path for *name*, or `None` when absent."""
        ...


class Tier(Protocol):
    """One verification stage in pipeline order."""

    id: str
    name: str

    def run(self, context: CheckContext) -> TierResult:
        """Run the tier and return its contract result."""
        ...
