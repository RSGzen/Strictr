"""Tier 1a: project lint verification with ruff."""

from __future__ import annotations

import time

from strictr.core.errors import (
    InvalidToolOutput,
    ToolError,
    ToolNotFoundError,
    ToolTimeoutError,
)
from strictr.core.models import CheckContext, TierResult, ToolInfo, ToolResult
from strictr.core.protocols import ToolRunner
from strictr.core.text import ERROR_LIMIT, cap_text
from strictr.tools.parsers.ruff import parse_ruff_json

DEFAULT_TIMEOUT_SECONDS = 30.0

_VERSION_UNKNOWN = "unknown"


class RuffTier:
    """Run the project's ruff from the project root and normalize its findings."""

    id = "tier1-ruff"
    name = "lint"

    def __init__(self, runner: ToolRunner) -> None:
        self._runner = runner

    def run(self, context: CheckContext) -> TierResult:
        """Return the ruff tier result for *context*."""
        started = time.perf_counter()
        timeout = DEFAULT_TIMEOUT_SECONDS if context.timeout is None else context.timeout
        executable = self._runner.which("ruff")
        if executable is None:
            return self._error(started, None, "ruff not found", "Ruff executable not found")

        try:
            version_result = self._runner.run(
                (executable, "--version"), cwd=context.root, timeout=timeout
            )
        except ToolError as error:
            return self._error(started, None, _reason_for(error), str(error))

        version = _parse_version(version_result.stdout)
        tool = ToolInfo(name="ruff", version=version)
        if version_result.returncode != 0:
            return self._error(started, tool, "tool failed", _tool_error_text(version_result))

        command = (
            executable,
            "check",
            "--output-format=json",
            "--no-fix",
            "--",
            *context.targets,
        )
        try:
            check_result = self._runner.run(command, cwd=context.root, timeout=timeout)
        except ToolError as error:
            return self._error(started, tool, _reason_for(error), str(error))

        if check_result.returncode not in (0, 1):
            return self._error(started, tool, "tool failed", _tool_error_text(check_result))

        try:
            diagnostics = parse_ruff_json(check_result.stdout, context.root)
        except InvalidToolOutput as error:
            return self._error(started, tool, "invalid tool output", str(error))

        return TierResult(
            id=self.id,
            name=self.name,
            status="fail" if check_result.returncode == 1 or diagnostics else "pass",
            tool=tool,
            duration_ms=_elapsed_ms(started),
            diagnostics=diagnostics,
        )

    def _error(
        self,
        started: float,
        tool: ToolInfo | None,
        reason: str,
        message: str,
    ) -> TierResult:
        error_text, _ = cap_text(message, ERROR_LIMIT)
        return TierResult(
            id=self.id,
            name=self.name,
            status="error",
            tool=tool,
            duration_ms=_elapsed_ms(started),
            skipped_reason=reason,
            meta={"error": error_text},
        )


def _reason_for(error: ToolError) -> str:
    if isinstance(error, ToolNotFoundError):
        return "ruff not found"
    if isinstance(error, ToolTimeoutError):
        return "tool timeout"
    if isinstance(error, InvalidToolOutput):
        return "invalid tool output"
    return "tool failed"


def _parse_version(stdout: str) -> str:
    parts = stdout.split()
    return parts[-1] if parts else _VERSION_UNKNOWN


def _tool_error_text(result: ToolResult) -> str:
    return result.stderr.strip() or result.stdout.strip() or f"ruff exited with {result.returncode}"


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
