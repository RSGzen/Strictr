"""Tier 1b: project type verification with mypy or pyright."""

from __future__ import annotations

import importlib.util
import re
import sys
import time
import tomllib
from pathlib import Path
from typing import Any, Literal

from strictr.core.errors import (
    InvalidToolOutput,
    ToolError,
    ToolNotFoundError,
    ToolTimeoutError,
)
from strictr.core.models import CheckContext, TierResult, ToolInfo, ToolResult
from strictr.core.protocols import ToolRunner
from strictr.core.text import ERROR_LIMIT, cap_text
from strictr.tools.parsers.mypy import parse_mypy_json
from strictr.tools.parsers.pyright import parse_pyright_json

DEFAULT_TIMEOUT_SECONDS = 180.0
NO_CHECKER_REASON = "no type checker found"
DISABLED_REASON = "disabled_by_user"
NO_CHECKER_WARNING = "No type checker found; install mypy or pyright for a full pass."
BOTH_CONFIGURED_WARNING = (
    "Both mypy and pyright are configured; using mypy. Pass --type-checker pyright to override."
)

type _CheckerName = Literal["mypy", "pyright"]
type _SelectionMode = Literal["explicit", "config", "available"]

_CHECKERS: tuple[_CheckerName, ...] = ("mypy", "pyright")
_MYPY_CONFIG_FILES = ("mypy.ini", ".mypy.ini")
_PYRIGHT_CONFIG_FILE = "pyrightconfig.json"
_VERSION_UNKNOWN = "unknown"
_VERSION_PATTERN = re.compile(r"\d+(?:\.\d+)+")


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
        started = time.perf_counter()
        choice = context.type_checker
        if choice == "none":
            return self._skip(
                started, DISABLED_REASON, {"checker": "none", "selection": "explicit"}
            )

        timeout = DEFAULT_TIMEOUT_SECONDS if context.timeout is None else context.timeout
        mypy_config = _has_mypy_config(context.root)
        pyright_config = _has_pyright_config(context.root)

        if choice == "mypy":
            return self._run_required(started, "mypy", "explicit", context, timeout)
        if choice == "pyright":
            return self._run_required(started, "pyright", "explicit", context, timeout)
        if mypy_config or pyright_config:
            checker: _CheckerName = "mypy" if mypy_config else "pyright"
            warnings = (BOTH_CONFIGURED_WARNING,) if mypy_config and pyright_config else ()
            return self._run_required(started, checker, "config", context, timeout, warnings)
        return self._run_available(started, context, timeout)

    def _run_required(
        self,
        started: float,
        checker: _CheckerName,
        mode: _SelectionMode,
        context: CheckContext,
        timeout: float,
        warnings: tuple[str, ...] = (),
    ) -> TierResult:
        try:
            probed = self._probe(checker, context.root, timeout)
        except ToolError as error:
            return self._error(started, checker, mode, error, warnings=warnings)

        if probed is None:
            return self._error(
                started,
                checker,
                mode,
                ToolNotFoundError(f"{checker} is configured but not available"),
                warnings=warnings,
            )

        launch, version = probed
        return self._execute(started, checker, mode, launch, version, context, timeout, warnings)

    def _run_available(self, started: float, context: CheckContext, timeout: float) -> TierResult:
        for checker in _CHECKERS:
            try:
                probed = self._probe(checker, context.root, timeout)
            except ToolError as error:
                return self._error(started, checker, "available", error)
            if probed is not None:
                launch, version = probed
                return self._execute(
                    started, checker, "available", launch, version, context, timeout
                )
        return self._skip(started, NO_CHECKER_REASON, {}, warnings=(NO_CHECKER_WARNING,))

    def _probe(
        self, checker: _CheckerName, root: Path, timeout: float
    ) -> tuple[tuple[str, ...], str] | None:
        launch = _launch_for(checker, self._runner)
        if launch is None:
            return None
        try:
            result = self._runner.run((*launch, "--version"), cwd=root, timeout=timeout)
        except ToolNotFoundError:
            return None
        if result.returncode != 0:
            return None
        return launch, _parse_version(result.stdout)

    def _execute(
        self,
        started: float,
        checker: _CheckerName,
        mode: _SelectionMode,
        launch: tuple[str, ...],
        version: str,
        context: CheckContext,
        timeout: float,
        warnings: tuple[str, ...] = (),
    ) -> TierResult:
        tool = ToolInfo(name=checker, version=version)
        if checker == "mypy":
            command = (*launch, "--output=json", "--", *context.targets)
            parser = parse_mypy_json
        else:
            command = (*launch, "--outputjson", *context.targets)
            parser = parse_pyright_json

        try:
            result = self._runner.run(command, cwd=context.root, timeout=timeout)
        except ToolError as error:
            return self._error(started, checker, mode, error, warnings=warnings, tool=tool)

        if result.returncode not in (0, 1):
            return self._error(
                started,
                checker,
                mode,
                ToolError(_tool_error_text(result, checker)),
                warnings=warnings,
                tool=tool,
            )

        try:
            diagnostics = parser(result.stdout, context.root)
        except InvalidToolOutput as error:
            return self._error(started, checker, mode, error, warnings=warnings, tool=tool)

        failed = result.returncode == 1 or any(
            diagnostic.severity == "error" for diagnostic in diagnostics
        )
        return TierResult(
            id=self.id,
            name=self.name,
            status="fail" if failed else "pass",
            tool=tool,
            duration_ms=_elapsed_ms(started),
            diagnostics=diagnostics,
            meta={"checker": checker, "selection": mode},
            warnings=warnings,
        )

    def _error(
        self,
        started: float,
        checker: _CheckerName,
        mode: _SelectionMode,
        error: ToolError,
        *,
        warnings: tuple[str, ...] = (),
        tool: ToolInfo | None = None,
    ) -> TierResult:
        error_text, _ = cap_text(str(error), ERROR_LIMIT)
        return TierResult(
            id=self.id,
            name=self.name,
            status="error",
            tool=tool,
            duration_ms=_elapsed_ms(started),
            skipped_reason=_reason_for(error, checker),
            meta={"checker": checker, "selection": mode, "error": error_text},
            warnings=warnings,
        )

    def _skip(
        self,
        started: float,
        reason: str,
        meta: dict[str, Any],
        *,
        warnings: tuple[str, ...] = (),
    ) -> TierResult:
        return TierResult(
            id=self.id,
            name=self.name,
            status="skipped",
            duration_ms=_elapsed_ms(started),
            skipped_reason=reason,
            meta=meta,
            warnings=warnings,
        )


def _launch_for(checker: _CheckerName, runner: ToolRunner) -> tuple[str, ...] | None:
    if checker == "mypy":
        return (sys.executable, "-m", "mypy")
    if _pyright_module_available():
        return (sys.executable, "-m", "pyright")
    executable = runner.which("pyright")
    return None if executable is None else (executable,)


def _pyright_module_available() -> bool:
    """Whether the PyPI pyright wrapper is importable in this interpreter."""
    return importlib.util.find_spec("pyright") is not None


def _reason_for(error: ToolError, checker: str) -> str:
    if isinstance(error, ToolNotFoundError):
        return f"{checker} not found"
    if isinstance(error, ToolTimeoutError):
        return "tool timeout"
    if isinstance(error, InvalidToolOutput):
        return "invalid tool output"
    return "tool failed"


def _tool_error_text(result: ToolResult, checker: str) -> str:
    return (
        result.stderr.strip()
        or result.stdout.strip()
        or f"{checker} exited with {result.returncode}"
    )


def _parse_version(stdout: str) -> str:
    match = _VERSION_PATTERN.search(stdout)
    return match.group(0) if match else _VERSION_UNKNOWN


def _has_mypy_config(root: Path) -> bool:
    if any((root / name).is_file() for name in _MYPY_CONFIG_FILES):
        return True
    if _toml_table(root / "pyproject.toml", "mypy"):
        return True
    return _ini_section(root / "setup.cfg", "mypy")


def _has_pyright_config(root: Path) -> bool:
    return (root / _PYRIGHT_CONFIG_FILE).is_file() or _toml_table(
        root / "pyproject.toml", "pyright"
    )


def _toml_table(path: Path, name: str) -> bool:
    if not path.is_file():
        return False
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    tool = data.get("tool")
    return isinstance(tool, dict) and isinstance(tool.get(name), dict)


def _ini_section(path: Path, section: str) -> bool:
    if not path.is_file():
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    return any(line.strip() == f"[{section}]" for line in lines)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
