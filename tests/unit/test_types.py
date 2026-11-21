from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

import strictr.tiers.types_tier as types_tier
from strictr.core.errors import InvalidToolOutput, ToolNotFoundError, ToolTimeoutError
from strictr.core.models import (
    CheckContext,
    Scope,
    TierResult,
    ToolInfo,
    ToolResult,
    TypeCheckerChoice,
)
from strictr.core.pipeline import run_pipeline
from strictr.tiers.types_tier import TypesTier
from strictr.tools.parsers.mypy import parse_mypy_json
from strictr.tools.parsers.pyright import parse_pyright_json

pytestmark = pytest.mark.spec("003")

MYPY = (sys.executable, "-m", "mypy")
PYRIGHT = (sys.executable, "-m", "pyright")
PYRIGHT_EXE = "C:/tools/pyright.exe"
CHECK_TARGETS = ("src", "tests")


@dataclass
class FakeRunner:
    """ToolRunner double keyed by checker, mode, and command."""

    mypy_version_returncode: int | None = 0
    mypy_version_error: Exception | None = None
    mypy_version_stdout: str = "mypy 1.19.0 (compiled: yes)\n"
    mypy_check_returncode: int = 0
    mypy_check_error: Exception | None = None
    mypy_check_stdout: str = ""
    mypy_check_stderr: str = ""
    pyright_version_returncode: int | None = 0
    pyright_version_error: Exception | None = None
    pyright_version_stdout: str = "pyright 1.1.400\n"
    pyright_check_returncode: int = 0
    pyright_check_error: Exception | None = None
    pyright_check_stdout: str = '{"generalDiagnostics": []}'
    pyright_check_stderr: str = ""
    pyright_exe: str | None = None
    calls: list[tuple[tuple[str, ...], Path, float]] = field(default_factory=list)
    which_calls: list[str] = field(default_factory=list)

    def which(self, name: str) -> str | None:
        self.which_calls.append(name)
        return self.pyright_exe if name == "pyright" else None

    def run(self, command: Sequence[str], *, cwd: Path, timeout: float) -> ToolResult:
        recorded = tuple(command)
        self.calls.append((recorded, cwd, timeout))
        if self._is_mypy(recorded):
            if recorded[-1] == "--version":
                if self.mypy_version_error is not None:
                    raise self.mypy_version_error
                if self.mypy_version_returncode is None:
                    raise ToolNotFoundError("mypy not found")
                return _tool_result(
                    recorded, self.mypy_version_returncode, self.mypy_version_stdout
                )
            if self.mypy_check_error is not None:
                raise self.mypy_check_error
            return _tool_result(
                recorded,
                self.mypy_check_returncode,
                self.mypy_check_stdout,
                self.mypy_check_stderr,
            )

        if recorded[-1] == "--version":
            if self.pyright_version_error is not None:
                raise self.pyright_version_error
            if self.pyright_version_returncode is None:
                raise ToolNotFoundError("pyright not found")
            return _tool_result(
                recorded, self.pyright_version_returncode, self.pyright_version_stdout
            )
        if self.pyright_check_error is not None:
            raise self.pyright_check_error
        return _tool_result(
            recorded,
            self.pyright_check_returncode,
            self.pyright_check_stdout,
            self.pyright_check_stderr,
        )

    def _is_mypy(self, command: tuple[str, ...]) -> bool:
        return command[0] == sys.executable and command[1:3] == ("-m", "mypy")


@dataclass
class LaterTier:
    id: str = "tier2-pytest"
    name: str = "tests"
    calls: list[CheckContext] = field(default_factory=list)

    def run(self, context: CheckContext) -> TierResult:
        self.calls.append(context)
        return TierResult(id=self.id, name=self.name, status="pass")


def _tool_result(
    command: tuple[str, ...], returncode: int, stdout: str, stderr: str = ""
) -> ToolResult:
    return ToolResult(
        command=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=1,
    )


@pytest.fixture(autouse=True)
def pyright_wrapper_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(types_tier, "_pyright_module_available", lambda: True)


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def context_for(
    root: Path,
    *,
    targets: tuple[str, ...] = (".",),
    timeout: float | None = None,
    type_checker: TypeCheckerChoice | None = None,
) -> CheckContext:
    return CheckContext(
        root=root,
        targets=targets,
        files=(root / "app.py",),
        timeout=timeout,
        type_checker=type_checker,
    )


def scope_for(files: tuple[Path, ...]) -> Scope:
    return Scope(root=".", targets=(".",), files_checked=len(files))


def mypy_line(**overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "file": "src/app.py",
        "line": 2,
        "column": 8,
        "end_line": 2,
        "end_column": 11,
        "message": 'Unsupported operand types for + ("int" and "str")',
        "hint": None,
        "code": "operator",
        "severity": "error",
    }
    entry.update(overrides)
    return entry


def mypy_lines(*entries: dict[str, Any]) -> str:
    return "\n".join(json.dumps(entry) for entry in entries) + "\n"


def pyright_diagnostic(**overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "file": "src/app.py",
        "severity": "error",
        "message": 'Operator "+" not supported for types "int" and "str"',
        "range": {
            "start": {"line": 1, "character": 8},
            "end": {"line": 1, "character": 11},
        },
        "rule": "reportOperatorIssue",
    }
    entry.update(overrides)
    return entry


def pyright_payload(*diagnostics: dict[str, Any]) -> str:
    return json.dumps(
        {
            "version": "1.1.400",
            "generalDiagnostics": list(diagnostics),
            "summary": {
                "filesAnalyzed": 1,
                "errorCount": 0,
                "warningCount": 0,
                "informationCount": 0,
            },
        }
    )


@pytest.mark.ac("AC-9")
def test_explicit_mypy_wins_over_pyright_config(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    write(root / "pyrightconfig.json", "{}")
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root, type_checker="mypy"))

    assert result.id == "tier1-types"
    assert result.name == "types"
    assert result.status == "pass"
    assert result.meta == {"checker": "mypy", "selection": "explicit"}
    assert result.tool == ToolInfo(name="mypy", version="1.19.0")
    assert [command for command, _, _ in runner.calls] == [
        (*MYPY, "--version"),
        (*MYPY, "--output=json", "--", "."),
    ]


@pytest.mark.ac("AC-9")
def test_explicit_pyright_wins_over_mypy_config(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    write(root / "mypy.ini", "[mypy]\nstrict = True\n")
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root, type_checker="pyright"))

    assert result.status == "pass"
    assert result.meta == {"checker": "pyright", "selection": "explicit"}
    assert result.tool == ToolInfo(name="pyright", version="1.1.400")
    assert [command for command, _, _ in runner.calls] == [
        (*PYRIGHT, "--version"),
        (*PYRIGHT, "--outputjson", "."),
    ]


@pytest.mark.ac("AC-9")
@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("mypy.ini", "[mypy]\nstrict = True\n"),
        (".mypy.ini", "[mypy]\nstrict = True\n"),
        ("pyproject.toml", "[tool.mypy]\nstrict = true\n"),
        ("setup.cfg", "[mypy]\nstrict = True\n"),
    ],
)
def test_mypy_configuration_selects_mypy(tmp_path: Path, name: str, text: str) -> None:
    root = tmp_path.resolve()
    write(root / name, text)
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "pass"
    assert result.meta == {"checker": "mypy", "selection": "config"}
    assert result.warnings == ()
    assert runner.calls[1][0] == (*MYPY, "--output=json", "--", ".")


@pytest.mark.ac("AC-9")
@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("pyrightconfig.json", "{}"),
        ("pyproject.toml", '[tool.pyright]\ninclude = ["src"]\n'),
    ],
)
def test_pyright_configuration_selects_pyright(tmp_path: Path, name: str, text: str) -> None:
    root = tmp_path.resolve()
    write(root / name, text)
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "pass"
    assert result.meta == {"checker": "pyright", "selection": "config"}
    assert runner.calls[1][0] == (*PYRIGHT, "--outputjson", ".")


@pytest.mark.ac("AC-9")
def test_both_configured_uses_mypy_and_warns(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    write(root / "mypy.ini", "[mypy]\n")
    write(root / "pyrightconfig.json", "{}")
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root))

    assert result.meta == {"checker": "mypy", "selection": "config"}
    assert result.warnings == (types_tier.BOTH_CONFIGURED_WARNING,)
    assert runner.calls[1][0] == (*MYPY, "--output=json", "--", ".")


@pytest.mark.ac("AC-9")
def test_available_mypy_is_selected_without_configuration(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "pass"
    assert result.meta == {"checker": "mypy", "selection": "available"}
    assert result.warnings == ()
    assert runner.which_calls == []


@pytest.mark.ac("AC-9")
def test_pyright_is_selected_when_mypy_is_unavailable(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_version_returncode=1)

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "pass"
    assert result.meta == {"checker": "pyright", "selection": "available"}
    assert result.tool == ToolInfo(name="pyright", version="1.1.400")
    assert [command for command, _, _ in runner.calls] == [
        (*MYPY, "--version"),
        (*PYRIGHT, "--version"),
        (*PYRIGHT, "--outputjson", "."),
    ]


@pytest.mark.ac("AC-9")
def test_pyright_executable_is_used_when_the_wrapper_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(types_tier, "_pyright_module_available", lambda: False)
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_version_returncode=1, pyright_exe=PYRIGHT_EXE)

    result = TypesTier(runner).run(context_for(root))

    assert result.meta == {"checker": "pyright", "selection": "available"}
    assert runner.which_calls == ["pyright"]
    assert [command for command, _, _ in runner.calls] == [
        (*MYPY, "--version"),
        (PYRIGHT_EXE, "--version"),
        (PYRIGHT_EXE, "--outputjson", "."),
    ]


@pytest.mark.ac("AC-9")
def test_no_checker_found_is_a_required_skip_with_a_warning(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_version_returncode=1, pyright_version_returncode=1)

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "skipped"
    assert result.skipped_reason == "no type checker found"
    assert result.tool is None
    assert result.diagnostics == ()
    assert result.meta == {}
    assert result.warnings == ("No type checker found; install mypy or pyright for a full pass.",)


@pytest.mark.ac("AC-9")
def test_configured_checker_that_is_unavailable_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    write(root / "mypy.ini", "[mypy]\n")
    runner = FakeRunner(mypy_version_returncode=1)

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "mypy not found"
    assert result.meta["checker"] == "mypy"
    assert result.meta["selection"] == "config"
    assert "mypy" in result.meta["error"].lower()
    assert result.tool is None
    assert result.diagnostics == ()
    # A configured checker never silently falls back to the other one.
    assert [command for command, _, _ in runner.calls] == [(*MYPY, "--version")]


@pytest.mark.ac("AC-9")
def test_explicit_checker_that_is_unavailable_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_version_returncode=1)

    result = TypesTier(runner).run(context_for(root, type_checker="mypy"))

    assert result.status == "error"
    assert result.skipped_reason == "mypy not found"
    assert result.meta["selection"] == "explicit"
    assert [command for command, _, _ in runner.calls] == [(*MYPY, "--version")]


@pytest.mark.ac("AC-9")
def test_none_is_skipped_as_disabled_by_user_without_warnings(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    result = TypesTier(runner).run(context_for(root, type_checker="none"))

    assert result.status == "skipped"
    assert result.skipped_reason == "disabled_by_user"
    assert result.meta == {"checker": "none", "selection": "explicit"}
    assert result.tool is None
    assert result.diagnostics == ()
    assert result.warnings == ()
    assert runner.calls == []
    assert runner.which_calls == []


@pytest.mark.ac("AC-10")
def test_checker_runs_requested_targets_from_the_root(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    TypesTier(runner).run(context_for(root, targets=CHECK_TARGETS))

    assert runner.calls[1][0] == (*MYPY, "--output=json", "--", *CHECK_TARGETS)
    assert all(cwd == root for _, cwd, _ in runner.calls)


@pytest.mark.ac("AC-10")
def test_default_timeout_is_180_seconds(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    TypesTier(runner).run(context_for(root))

    assert [timeout for _, _, timeout in runner.calls] == [180.0, 180.0]


@pytest.mark.ac("AC-10")
def test_timeout_override_applies_to_version_and_check(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner()

    TypesTier(runner).run(context_for(root, timeout=1.5))

    assert [timeout for _, _, timeout in runner.calls] == [1.5, 1.5]


@pytest.mark.ac("AC-10")
def test_mypy_diagnostics_are_normalized(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    stdout = mypy_lines(
        mypy_line(),
        mypy_line(
            line=5,
            column=1,
            end_line=5,
            end_column=6,
            code="assignment",
            severity="warning",
            message="unused ignore",
        ),
        mypy_line(
            line=7,
            column=16,
            end_line=7,
            end_column=17,
            code="misc",
            severity="note",
            message='Revealed type is "Any"',
        ),
    )
    runner = FakeRunner(mypy_check_stdout=stdout, mypy_check_returncode=1)

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "fail"
    assert result.tool == ToolInfo(name="mypy", version="1.19.0")
    assert result.skipped_reason is None
    assert [diagnostic.severity for diagnostic in result.diagnostics] == [
        "error",
        "warning",
        "note",
    ]
    first = result.diagnostics[0]
    assert first.tier == "tier1-types"
    assert first.source == "mypy"
    assert first.path == "src/app.py"
    assert first.line == 2
    assert first.column == 8
    assert first.end_line == 2
    assert first.end_column == 11
    assert first.code == "operator"
    assert first.message == 'Unsupported operand types for + ("int" and "str")'


@pytest.mark.ac("AC-10")
def test_mypy_absolute_paths_become_root_relative(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    absolute = str(root / "src" / "app.py")

    diagnostics = parse_mypy_json(mypy_lines(mypy_line(file=absolute)), root)

    assert [diagnostic.path for diagnostic in diagnostics] == ["src/app.py"]


@pytest.mark.ac("AC-10")
def test_mypy_diagnostics_are_ordered_deterministically(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    stdout = mypy_lines(
        mypy_line(file="src/z.py", line=2, code="F401", message="z"),
        mypy_line(file="src/a.py", line=9, code="E501", message="b"),
        mypy_line(file="src/a.py", line=2, code="E501", message="c"),
        mypy_line(file="src/a.py", line=2, code="E501", message="a"),
    )

    diagnostics = parse_mypy_json(stdout, root)

    assert [(d.path, d.line, d.code, d.message) for d in diagnostics] == [
        ("src/a.py", 2, "E501", "a"),
        ("src/a.py", 2, "E501", "c"),
        ("src/a.py", 9, "E501", "b"),
        ("src/z.py", 2, "F401", "z"),
    ]


@pytest.mark.ac("AC-10")
def test_mypy_missing_code_and_end_positions_are_nullable(tmp_path: Path) -> None:
    root = tmp_path.resolve()

    diagnostics = parse_mypy_json(
        mypy_lines(mypy_line(code=None, end_line=None, end_column=None)), root
    )

    assert diagnostics[0].code == "mypy-error"
    assert diagnostics[0].end_line is None
    assert diagnostics[0].end_column is None


@pytest.mark.ac("AC-10")
@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        "[]",
        json.dumps(mypy_line(file="")),
        json.dumps(mypy_line(line=0)),
        json.dumps(mypy_line(column=0)),
        json.dumps(mypy_line(severity="fatal")),
        json.dumps(mypy_line(message="")),
        json.dumps({key: value for key, value in mypy_line().items() if key != "file"}),
    ],
)
def test_invalid_mypy_output_raises_invalid_tool_output(tmp_path: Path, stdout: str) -> None:
    with pytest.raises(InvalidToolOutput):
        parse_mypy_json(stdout, tmp_path.resolve())


@pytest.mark.ac("AC-10")
def test_invalid_mypy_output_is_a_tier_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_check_stdout="not json")

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "invalid tool output"
    assert result.tool == ToolInfo(name="mypy", version="1.19.0")
    assert result.diagnostics == ()
    assert "json" in result.meta["error"].lower()


@pytest.mark.ac("AC-10")
def test_mypy_crash_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_check_returncode=2, mypy_check_stderr="mypy crashed")

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "tool failed"
    assert result.diagnostics == ()
    assert "mypy crashed" in result.meta["error"]


@pytest.mark.ac("AC-10")
def test_mypy_timeout_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_check_error=ToolTimeoutError("tool timed out"))

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "tool timeout"
    assert result.diagnostics == ()


@pytest.mark.ac("AC-10")
def test_mypy_missing_at_execution_maps_to_not_found(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_check_error=ToolNotFoundError("tool not found: mypy"))

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "mypy not found"


@pytest.mark.ac("AC-10")
def test_pyright_diagnostics_are_normalized(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    stdout = pyright_payload(
        pyright_diagnostic(),
        pyright_diagnostic(
            severity="warning",
            range={
                "start": {"line": 4, "character": 0},
                "end": {"line": 4, "character": 3},
            },
            rule="reportUnusedVariable",
            message="Variable is unused",
        ),
        pyright_diagnostic(
            severity="information",
            range={
                "start": {"line": 6, "character": 15},
                "end": {"line": 6, "character": 16},
            },
            rule="reportAny",
            message='Type of "x" is Any',
        ),
    )
    runner = FakeRunner(
        mypy_version_returncode=1,
        pyright_check_stdout=stdout,
        pyright_check_returncode=1,
    )

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "fail"
    assert result.tool == ToolInfo(name="pyright", version="1.1.400")
    assert [diagnostic.severity for diagnostic in result.diagnostics] == [
        "error",
        "warning",
        "note",
    ]
    first = result.diagnostics[0]
    assert first.tier == "tier1-types"
    assert first.source == "pyright"
    assert first.path == "src/app.py"
    assert first.line == 2
    assert first.column == 9
    assert first.end_line == 2
    assert first.end_column == 12
    assert first.code == "reportOperatorIssue"
    assert first.message == 'Operator "+" not supported for types "int" and "str"'


@pytest.mark.ac("AC-10")
def test_pyright_warning_only_does_not_fail(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    stdout = pyright_payload(
        pyright_diagnostic(
            severity="warning",
            range={
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 1},
            },
        )
    )
    runner = FakeRunner(mypy_version_returncode=1, pyright_check_stdout=stdout)

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "pass"
    assert [diagnostic.severity for diagnostic in result.diagnostics] == ["warning"]


@pytest.mark.ac("AC-10")
def test_pyright_missing_rule_uses_a_stable_fallback(tmp_path: Path) -> None:
    root = tmp_path.resolve()

    diagnostics = parse_pyright_json(pyright_payload(pyright_diagnostic(rule=None)), root)

    assert diagnostics[0].code == "pyright-error"


@pytest.mark.ac("AC-10")
@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        "[]",
        "{}",
        '{"generalDiagnostics": {}}',
        '{"generalDiagnostics": [1]}',
        json.dumps({"generalDiagnostics": [pyright_diagnostic(file="")]}),
        json.dumps({"generalDiagnostics": [pyright_diagnostic(severity="fatal")]}),
        json.dumps({"generalDiagnostics": [pyright_diagnostic(message="")]}),
        json.dumps({"generalDiagnostics": [pyright_diagnostic(range=None)]}),
        json.dumps(
            {
                "generalDiagnostics": [
                    pyright_diagnostic(range={"start": {"line": -1, "character": 0}})
                ]
            }
        ),
    ],
)
def test_invalid_pyright_output_raises_invalid_tool_output(tmp_path: Path, stdout: str) -> None:
    with pytest.raises(InvalidToolOutput):
        parse_pyright_json(stdout, tmp_path.resolve())


@pytest.mark.ac("AC-10")
def test_invalid_pyright_output_is_a_tier_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(mypy_version_returncode=1, pyright_check_stdout="not json")

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "invalid tool output"
    assert result.tool == ToolInfo(name="pyright", version="1.1.400")
    assert result.diagnostics == ()
    assert "json" in result.meta["error"].lower()


@pytest.mark.ac("AC-10")
def test_pyright_crash_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(
        mypy_version_returncode=1,
        pyright_check_returncode=2,
        pyright_check_stderr="pyright crashed",
    )

    result = TypesTier(runner).run(context_for(root))

    assert result.status == "error"
    assert result.skipped_reason == "tool failed"
    assert "pyright crashed" in result.meta["error"]


@pytest.mark.ac("AC-9")
def test_no_checker_makes_the_pipeline_partial(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    files = (root / "app.py",)
    runner = FakeRunner(mypy_version_returncode=1, pyright_version_returncode=1)

    check = run_pipeline((TypesTier(runner),), context_for(root), scope_for(files))

    assert check.status == "partial"
    assert check.tiers[0].status == "skipped"
    assert check.tiers[0].skipped_reason == "no type checker found"
    assert check.warnings == ("No type checker found; install mypy or pyright for a full pass.",)


@pytest.mark.ac("AC-9")
def test_none_keeps_the_pipeline_pass(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    files = (root / "app.py",)

    check = run_pipeline(
        (TypesTier(FakeRunner()),),
        context_for(root, type_checker="none"),
        scope_for(files),
    )

    assert check.status == "pass"
    assert check.tiers[0].status == "skipped"
    assert check.tiers[0].skipped_reason == "disabled_by_user"


@pytest.mark.ac("AC-10")
def test_type_failure_stops_later_tiers(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    files = (root / "app.py",)
    runner = FakeRunner(
        mypy_check_stdout=mypy_lines(mypy_line()),
        mypy_check_returncode=1,
    )
    later = LaterTier()

    check = run_pipeline((TypesTier(runner), later), context_for(root), scope_for(files))

    assert check.status == "fail"
    assert [tier.status for tier in check.tiers] == ["fail", "skipped"]
    assert check.tiers[1].skipped_reason == "earlier_tier_failed"
    assert later.calls == []
