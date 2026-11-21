from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from strictr.core.errors import InvalidToolOutput, ToolNotFoundError, ToolTimeoutError
from strictr.core.models import (
    CheckContext,
    Scope,
    TierResult,
    ToolInfo,
    ToolResult,
)
from strictr.core.pipeline import run_pipeline
from strictr.tiers.ruff_tier import RuffTier
from strictr.tools.parsers.ruff import parse_ruff_json

pytestmark = pytest.mark.spec("003")

RUFF = "C:/tools/ruff.exe"


@dataclass
class FakeRunner:
    """ToolRunner double keyed by the version and check commands."""

    available: bool = True
    executable: str = RUFF
    version_stdout: str = "ruff 0.11.2\n"
    version_error: Exception | None = None
    check_stdout: str = "[]"
    check_stderr: str = ""
    check_returncode: int = 0
    check_error: Exception | None = None
    calls: list[tuple[tuple[str, ...], Path, float]] = field(default_factory=list)
    which_calls: list[str] = field(default_factory=list)

    def which(self, name: str) -> str | None:
        self.which_calls.append(name)
        return self.executable if self.available else None

    def run(self, command: Sequence[str], *, cwd: Path, timeout: float) -> ToolResult:
        recorded = tuple(command)
        self.calls.append((recorded, cwd, timeout))
        if recorded == (self.executable, "--version"):
            if self.version_error is not None:
                raise self.version_error
            return ToolResult(
                command=recorded,
                returncode=0,
                stdout=self.version_stdout,
                stderr="",
                duration_ms=1,
            )
        if self.check_error is not None:
            raise self.check_error
        return ToolResult(
            command=recorded,
            returncode=self.check_returncode,
            stdout=self.check_stdout,
            stderr=self.check_stderr,
            duration_ms=1,
        )


@dataclass
class LaterTier:
    id: str
    name: str
    calls: list[CheckContext] = field(default_factory=list)

    def run(self, context: CheckContext) -> TierResult:
        self.calls.append(context)
        return TierResult(id=self.id, name=self.name, status="pass")


def context_for(
    root: Path,
    *,
    targets: tuple[str, ...] = (".",),
    timeout: float | None = None,
) -> CheckContext:
    return CheckContext(root=root, targets=targets, files=(root / "app.py",), timeout=timeout)


def scope_for(files: tuple[Path, ...]) -> Scope:
    return Scope(root=".", targets=(".",), files_checked=len(files))


def ruff_finding(
    filename: str = "src/app.py",
    *,
    line: int = 3,
    column: int = 1,
    end_line: int = 3,
    end_column: int = 5,
    code: str | None = "F401",
    message: str = "`os` imported but unused",
    url: str | None = "https://docs.astral.sh/ruff/rules/unused-import",
) -> dict[str, Any]:
    return {
        "cell": None,
        "code": code,
        "end_location": {"column": end_column, "row": end_line},
        "filename": filename,
        "fix": None,
        "location": {"column": column, "row": line},
        "message": message,
        "noqa_row": line,
        "url": url,
    }


@pytest.mark.ac("AC-8")
def test_pass_records_ruff_version_and_runs_from_the_root(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    result = RuffTier(runner).run(context_for(root))

    assert result.id == "tier1-ruff"
    assert result.name == "lint"
    assert result.status == "pass"
    assert result.diagnostics == ()
    assert result.skipped_reason is None
    assert result.tool == ToolInfo(name="ruff", version="0.11.2")
    assert runner.which_calls == ["ruff"]
    assert [command for command, _, _ in runner.calls] == [
        (RUFF, "--version"),
        (RUFF, "check", "--output-format=json", "--no-fix", "--", "."),
    ]
    assert all(cwd == root for _, cwd, _ in runner.calls)
    assert all(timeout == 30.0 for _, _, timeout in runner.calls)


@pytest.mark.ac("AC-8")
def test_command_uses_requested_targets_and_timeout_override(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    RuffTier(runner).run(context_for(root, targets=("src", "tests"), timeout=1.5))

    assert runner.calls[1][0] == (
        RUFF,
        "check",
        "--output-format=json",
        "--no-fix",
        "--",
        "src",
        "tests",
    )
    assert [timeout for _, _, timeout in runner.calls] == [1.5, 1.5]


@pytest.mark.ac("AC-8")
def test_findings_are_normalized_to_contract_diagnostics(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(check_stdout=json.dumps([ruff_finding()]), check_returncode=1)

    result = RuffTier(runner).run(context_for(root))

    assert result.status == "fail"
    assert result.tool == ToolInfo(name="ruff", version="0.11.2")
    assert result.skipped_reason is None
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.tier == "tier1-ruff"
    assert diagnostic.source == "ruff"
    assert diagnostic.path == "src/app.py"
    assert diagnostic.line == 3
    assert diagnostic.column == 1
    assert diagnostic.end_line == 3
    assert diagnostic.end_column == 5
    assert diagnostic.code == "F401"
    assert diagnostic.severity == "error"
    assert diagnostic.message == "`os` imported but unused"
    assert diagnostic.url == "https://docs.astral.sh/ruff/rules/unused-import"


@pytest.mark.ac("AC-8")
def test_absolute_filenames_become_root_relative_posix_paths(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    filename = str(root / "src" / "app.py")

    diagnostics = parse_ruff_json(json.dumps([ruff_finding(filename=filename)]), root)

    assert [diagnostic.path for diagnostic in diagnostics] == ["src/app.py"]


@pytest.mark.ac("AC-8")
def test_findings_are_ordered_deterministically(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    entries = [
        ruff_finding("src/z.py", line=2, code="F401", message="z"),
        ruff_finding("src/a.py", line=9, code="E501", message="b"),
        ruff_finding("src/a.py", line=2, code="E501", message="c"),
        ruff_finding("src/a.py", line=2, code="E501", message="a"),
    ]

    diagnostics = parse_ruff_json(json.dumps(entries), root)

    assert [(d.path, d.line, d.code, d.message) for d in diagnostics] == [
        ("src/a.py", 2, "E501", "a"),
        ("src/a.py", 2, "E501", "c"),
        ("src/a.py", 9, "E501", "b"),
        ("src/z.py", 2, "F401", "z"),
    ]


@pytest.mark.ac("AC-8")
@pytest.mark.parametrize("code", [None, ""])
def test_missing_rule_code_uses_a_stable_fallback(tmp_path: Path, code: str | None) -> None:
    root = tmp_path.resolve()

    diagnostics = parse_ruff_json(json.dumps([ruff_finding(code=code)]), root)

    assert diagnostics[0].code == "ruff-error"


@pytest.mark.ac("AC-8")
@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        "{}",
        '[{"filename": "app.py"}]',
        '[{"filename": "app.py", "location": {"row": 0, "column": 1}}]',
    ],
)
def test_invalid_ruff_json_raises_invalid_tool_output(tmp_path: Path, stdout: str) -> None:
    with pytest.raises(InvalidToolOutput):
        parse_ruff_json(stdout, tmp_path.resolve())


@pytest.mark.ac("AC-8")
def test_invalid_ruff_json_is_a_tier_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(check_stdout="not json")

    result = RuffTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "invalid tool output"
    assert result.diagnostics == ()
    assert result.tool == ToolInfo(name="ruff", version="0.11.2")
    assert "json" in result.meta["error"].lower()


@pytest.mark.ac("AC-8")
def test_missing_ruff_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(available=False)

    result = RuffTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "ruff not found"
    assert result.tool is None
    assert result.diagnostics == ()
    assert "ruff" in result.meta["error"].lower()
    assert runner.which_calls == ["ruff"]
    assert runner.calls == []


@pytest.mark.ac("AC-8")
@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (ToolNotFoundError("tool not found: ruff"), "ruff not found"),
        (ToolTimeoutError("tool timed out after 30 seconds"), "tool timeout"),
    ],
)
def test_runner_failures_map_to_error_reasons(
    tmp_path: Path, error: Exception, reason: str
) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(check_error=error)

    result = RuffTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == reason
    assert result.diagnostics == ()
    assert result.tool == ToolInfo(name="ruff", version="0.11.2")
    assert result.meta["error"]


@pytest.mark.ac("AC-8")
def test_version_check_failure_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(version_error=ToolTimeoutError("tool timed out after 30 seconds"))

    result = RuffTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "tool timeout"
    assert result.diagnostics == ()
    assert result.meta["error"]


@pytest.mark.ac("AC-8")
def test_ruff_crash_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(check_returncode=2, check_stderr="ruff crashed")

    result = RuffTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "tool failed"
    assert result.diagnostics == ()
    assert result.tool == ToolInfo(name="ruff", version="0.11.2")
    assert "ruff crashed" in result.meta["error"]


@pytest.mark.ac("AC-8")
def test_ruff_failure_stops_later_tiers(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    files = (root / "app.py",)
    runner = FakeRunner(check_stdout=json.dumps([ruff_finding()]), check_returncode=1)
    later = LaterTier("tier1-types", "types")

    check = run_pipeline((RuffTier(runner), later), context_for(root), scope_for(files))

    assert check.status == "fail"
    assert [tier.status for tier in check.tiers] == ["fail", "skipped"]
    assert check.tiers[1].skipped_reason == "earlier_tier_failed"
    assert later.calls == []
