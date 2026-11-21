"""Tier 2: full-suite test verification with pytest."""

from __future__ import annotations

import re
import sys
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any

from strictr.core.errors import (
    InvalidToolOutput,
    ToolError,
    ToolNotFoundError,
    ToolTimeoutError,
)
from strictr.core.models import CheckContext, Diagnostic, TierResult, ToolInfo, ToolResult
from strictr.core.protocols import ToolRunner
from strictr.core.text import ERROR_LIMIT, cap_text
from strictr.tools.parsers.pytest_junit import PytestReport, parse_junit_xml

DEFAULT_TIMEOUT_SECONDS = 300.0
NO_TESTS_REASON = "no tests collected"
PYTEST_NOT_FOUND_REASON = "pytest not found"

_TOOL_FAILED_REASON = "tool failed"
_TOOL_TIMEOUT_REASON = "tool timeout"
_INVALID_OUTPUT_REASON = "invalid tool output"
_MISSING_PYTEST_MESSAGE = "pytest is not installed or not importable"
_VERSION_UNKNOWN = "unknown"
_VERSION_PATTERN = re.compile(r"\d+(?:\.\d+)+")


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
        started = time.perf_counter()
        timeout = DEFAULT_TIMEOUT_SECONDS if context.timeout is None else context.timeout
        probe = (sys.executable, "-m", "pytest", "--version")
        try:
            version_result = self._runner.run(probe, cwd=context.root, timeout=timeout)
        except ToolNotFoundError as error:
            return self._missing_pytest(started, context, str(error))
        except ToolTimeoutError as error:
            return self._error(started, _TOOL_TIMEOUT_REASON, str(error))
        except ToolError as error:
            return self._error(started, _TOOL_FAILED_REASON, str(error))

        if version_result.returncode != 0:
            return self._missing_pytest(started, context, version_result.stderr)
        tool = ToolInfo(name="pytest", version=_parse_version(version_result.stdout))

        with tempfile.TemporaryDirectory(prefix="strictr-pytest-") as directory:
            xml_path = Path(directory) / "junit.xml"
            command = (
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-o",
                "junit_family=xunit1",
                f"--junitxml={xml_path}",
            )
            try:
                suite_result = self._runner.run(command, cwd=context.root, timeout=timeout)
            except ToolNotFoundError as error:
                return self._missing_pytest(started, context, str(error), tool=tool)
            except ToolTimeoutError as error:
                return self._error(started, _TOOL_TIMEOUT_REASON, str(error), tool=tool)
            except ToolError as error:
                return self._error(started, _TOOL_FAILED_REASON, str(error), tool=tool)

            return self._result(started, suite_result, xml_path, context.root, tool)

    def _result(
        self,
        started: float,
        result: ToolResult,
        xml_path: Path,
        root: Path,
        tool: ToolInfo,
    ) -> TierResult:
        report = self._report(xml_path, root)

        if result.returncode == 5:
            return self._skip(
                started,
                NO_TESTS_REASON,
                tool=tool,
                meta=_counts(report),
            )
        if result.returncode in (0, 1):
            if report is None:
                return self._error(
                    started,
                    _INVALID_OUTPUT_REASON,
                    _output_text(result) or "pytest produced no usable JUnit XML",
                    tool=tool,
                    meta=_counts(None),
                )
            if report.error is not None:
                return self._error(
                    started,
                    _INVALID_OUTPUT_REASON,
                    report.error,
                    tool=tool,
                    meta=_counts(report),
                )
            failed = any(item.severity == "error" for item in report.diagnostics)
            if result.returncode == 1 and not failed:
                return self._error(
                    started,
                    _INVALID_OUTPUT_REASON,
                    "pytest exited with 1 but produced no error diagnostics",
                    tool=tool,
                    meta=_counts(report),
                )
            return TierResult(
                id=self.id,
                name=self.name,
                status="fail" if failed or result.returncode == 1 else "pass",
                tool=tool,
                duration_ms=_elapsed_ms(started),
                diagnostics=report.diagnostics,
                meta=_counts(report),
            )

        message = (
            _output_text(result)
            or (report.error if report is not None else None)
            or f"pytest exited with {result.returncode}"
        )
        return self._error(
            started,
            _TOOL_FAILED_REASON,
            message,
            tool=tool,
            diagnostics=report.diagnostics if report is not None else (),
            meta=_counts(report),
        )

    def _report(self, xml_path: Path, root: Path) -> PytestReport | None:
        try:
            xml = xml_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        try:
            return parse_junit_xml(xml, root)
        except InvalidToolOutput:
            return None

    def _missing_pytest(
        self,
        started: float,
        context: CheckContext,
        detail: str | None = None,
        *,
        tool: ToolInfo | None = None,
    ) -> TierResult:
        if _has_test_candidates(context) or _has_pytest_config(context.root):
            return self._error(
                started,
                PYTEST_NOT_FOUND_REASON,
                detail or _MISSING_PYTEST_MESSAGE,
                tool=tool,
            )
        return self._skip(started, NO_TESTS_REASON, tool=tool)

    def _error(
        self,
        started: float,
        reason: str,
        message: str,
        *,
        tool: ToolInfo | None = None,
        diagnostics: tuple[Diagnostic, ...] = (),
        meta: dict[str, Any] | None = None,
    ) -> TierResult:
        error_text, _ = cap_text(message, ERROR_LIMIT)
        result_meta = dict(meta or {})
        result_meta["error"] = error_text
        return TierResult(
            id=self.id,
            name=self.name,
            status="error",
            tool=tool,
            duration_ms=_elapsed_ms(started),
            diagnostics=diagnostics,
            skipped_reason=reason,
            meta=result_meta,
        )

    def _skip(
        self,
        started: float,
        reason: str,
        *,
        tool: ToolInfo | None = None,
        meta: dict[str, Any] | None = None,
    ) -> TierResult:
        return TierResult(
            id=self.id,
            name=self.name,
            status="skipped",
            tool=tool,
            duration_ms=_elapsed_ms(started),
            skipped_reason=reason,
            meta=dict(meta or {}),
        )


def _counts(report: PytestReport | None) -> dict[str, int]:
    if report is None:
        return {"tests_collected": 0, "tests_run": 0, "tests_skipped": 0}
    return {
        "tests_collected": report.tests_collected,
        "tests_run": report.tests_run,
        "tests_skipped": report.tests_skipped,
    }


def _has_test_candidates(context: CheckContext) -> bool:
    for path in context.files:
        if path.suffix != ".py":
            continue
        if path.name.startswith("test_") or path.name.endswith("_test.py"):
            return True
    return False


def _has_pytest_config(root: Path) -> bool:
    if (root / "pytest.ini").is_file():
        return True
    if _ini_section(root / "tox.ini", "pytest"):
        return True
    if _ini_section(root / "setup.cfg", "tool:pytest"):
        return True
    return _pyproject_has_pytest_config(root / "pyproject.toml")


def _ini_section(path: Path, section: str) -> bool:
    if not path.is_file():
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    return any(line.strip() == f"[{section}]" for line in lines)


def _pyproject_has_pytest_config(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    tool = data.get("tool")
    if not isinstance(tool, dict):
        return False
    pytest_table = tool.get("pytest")
    return isinstance(pytest_table, dict) and isinstance(pytest_table.get("ini_options"), dict)


def _parse_version(stdout: str) -> str:
    match = _VERSION_PATTERN.search(stdout)
    return match.group(0) if match else _VERSION_UNKNOWN


def _output_text(result: ToolResult) -> str:
    return result.stderr.strip() or result.stdout.strip()


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
