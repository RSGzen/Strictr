from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

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
from strictr.tiers.pytest_tier import PytestTier
from strictr.tools.parsers.pytest_junit import parse_junit_xml

pytestmark = pytest.mark.spec("003")

PYTEST = (sys.executable, "-m", "pytest")
COLLECTION_ERROR = (
    '<error message="collection failure">ImportError while importing test module</error>'
)


@dataclass
class FakeRunner:
    """ToolRunner double for the version probe and the suite invocation."""

    version_returncode: int = 0
    version_stdout: str = "pytest 8.4.2\n"
    version_stderr: str = ""
    version_error: Exception | None = None
    suite_returncode: int = 0
    suite_stdout: str = ""
    suite_stderr: str = ""
    suite_error: Exception | None = None
    junit_xml: str | None = None
    calls: list[tuple[tuple[str, ...], Path, float]] = field(default_factory=list)
    junit_paths: list[Path] = field(default_factory=list)

    def run(self, command: Sequence[str], *, cwd: Path, timeout: float) -> ToolResult:
        recorded = tuple(command)
        self.calls.append((recorded, cwd, timeout))
        if recorded[-1] == "--version":
            if self.version_error is not None:
                raise self.version_error
            return ToolResult(
                command=recorded,
                returncode=self.version_returncode,
                stdout=self.version_stdout,
                stderr=self.version_stderr,
                duration_ms=1,
            )

        if self.suite_error is not None:
            raise self.suite_error

        xml_argument = next((item for item in recorded if item.startswith("--junitxml=")), None)
        if xml_argument is not None:
            xml_path = Path(xml_argument.split("=", 1)[1])
            self.junit_paths.append(xml_path)
            if self.junit_xml is not None:
                xml_path.write_text(self.junit_xml, encoding="utf-8")
        return ToolResult(
            command=recorded,
            returncode=self.suite_returncode,
            stdout=self.suite_stdout,
            stderr=self.suite_stderr,
            duration_ms=1,
        )


@dataclass
class LaterTier:
    id: str = "tier3-later"
    name: str = "later"
    calls: list[CheckContext] = field(default_factory=list)

    def run(self, context: CheckContext) -> TierResult:
        self.calls.append(context)
        return TierResult(id=self.id, name=self.name, status="pass")


def context_for(
    root: Path,
    *,
    files: tuple[str, ...] = ("app.py",),
    targets: tuple[str, ...] = (".",),
    timeout: float | None = None,
) -> CheckContext:
    return CheckContext(
        root=root,
        targets=targets,
        files=tuple(root / name for name in files),
        timeout=timeout,
    )


def scope_for(files: tuple[Path, ...]) -> Scope:
    return Scope(root=".", targets=(".",), files_checked=len(files))


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def case(
    name: str = "test_ok",
    *,
    classname: str = "tests.test_app",
    file: str | None = "tests/test_app.py",
    line: int | None = 3,
    body: str = "",
) -> str:
    attributes = f'classname="{classname}" name="{name}"'
    if file is not None:
        attributes += f' file="{file}"'
    if line is not None:
        attributes += f' line="{line}"'
    attributes += ' time="0.001"'
    if body:
        return f"<testcase {attributes}>{body}</testcase>"
    return f"<testcase {attributes} />"


def failure(message: str = "assert 1 == 2", text: str = "") -> str:
    return f'<failure message="{message}">{text}</failure>'


def suite(
    *cases: str,
    tests: int | None = None,
    skipped: int | None = 0,
    errors: int = 0,
    failures: int = 0,
) -> str:
    attributes = ['name="pytest"', f'errors="{errors}"', f'failures="{failures}"']
    if skipped is not None:
        attributes.append(f'skipped="{skipped}"')
    if tests is not None:
        attributes.append(f'tests="{tests}"')
    return (
        '<?xml version="1.0" encoding="utf-8"?><testsuites>'
        f"<testsuite {' '.join(attributes)}>{''.join(cases)}</testsuite></testsuites>"
    )


@pytest.mark.ac("AC-11")
def test_pass_and_skip_counts_are_parsed_without_diagnostics(tmp_path: Path) -> None:
    xml = suite(
        case("test_pass"),
        case("test_skip", body='<skipped type="pytest.skip" message="later" />'),
        tests=2,
        skipped=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics == ()
    assert (report.tests_collected, report.tests_run, report.tests_skipped) == (2, 1, 1)
    assert report.error is None


@pytest.mark.ac("AC-11")
def test_counts_fall_back_to_testcases_when_attributes_are_missing(tmp_path: Path) -> None:
    xml = suite(
        case("test_pass"),
        case("test_skip", body='<skipped type="pytest.skip" message="later" />'),
        tests=None,
        skipped=None,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert (report.tests_collected, report.tests_run, report.tests_skipped) == (2, 1, 1)


@pytest.mark.ac("AC-11")
def test_failure_is_reported_with_failure_evidence(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    xml = suite(
        case(
            "test_fails",
            line=5,
            body=failure(
                "assert 1 == 2",
                "E   assert 1 == 2\n\ntests/test_app.py:7: AssertionError",
            ),
        ),
        tests=1,
        failures=1,
    )

    report = parse_junit_xml(xml, root)

    assert len(report.diagnostics) == 1
    diagnostic = report.diagnostics[0]
    assert diagnostic.tier == "tier2-pytest"
    assert diagnostic.source == "pytest"
    assert diagnostic.path == "tests/test_app.py"
    assert diagnostic.line == 7
    assert diagnostic.column == 1
    assert diagnostic.end_line is None
    assert diagnostic.end_column is None
    assert diagnostic.code == "test-failure"
    assert diagnostic.severity == "error"
    assert diagnostic.test == "tests/test_app.py::test_fails"
    assert diagnostic.exception == "AssertionError"
    assert "assert 1 == 2" in diagnostic.message
    assert "AssertionError" in diagnostic.message
    assert (report.tests_collected, report.tests_run, report.tests_skipped) == (1, 1, 0)


@pytest.mark.ac("AC-11")
def test_failure_uses_the_testcase_line_when_the_text_has_no_location(tmp_path: Path) -> None:
    xml = suite(case("test_fails", line=9, body=failure("boom", "boom")), tests=1)

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics[0].line == 9


@pytest.mark.ac("AC-11")
def test_missing_line_is_normalized_to_one(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_fails",
            classname="tests.test_app",
            file=None,
            line=None,
            body=failure("boom", "boom"),
        ),
        tests=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics[0].path == "tests/test_app.py"
    assert report.diagnostics[0].line == 1


@pytest.mark.ac("AC-11")
def test_xunit2_classname_derives_the_test_file_path(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_fails",
            classname="tests.test_app.TestThing",
            file=None,
            line=None,
            body=failure("boom", "boom"),
        ),
        tests=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    diagnostic = report.diagnostics[0]
    assert diagnostic.path == "tests/test_app.py"
    assert diagnostic.test == "tests/test_app.py::TestThing::test_fails"


@pytest.mark.ac("AC-11")
def test_error_is_reported_with_its_exception_class(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_boom",
            classname="tests.test_app.TestThing",
            line=4,
            body='<error message="RuntimeError: boom">RuntimeError: boom</error>',
        ),
        tests=1,
        errors=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    diagnostic = report.diagnostics[0]
    assert diagnostic.code == "test-error"
    assert diagnostic.exception == "RuntimeError"
    assert diagnostic.test == "tests/test_app.py::TestThing::test_boom"


@pytest.mark.ac("AC-11")
def test_collection_error_uses_the_collection_error_code(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_bad",
            classname="",
            file="tests/test_bad.py",
            line=None,
            body=COLLECTION_ERROR,
        ),
        tests=1,
        errors=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    diagnostic = report.diagnostics[0]
    assert diagnostic.code == "collection-error"
    assert diagnostic.path == "tests/test_bad.py"
    assert diagnostic.line == 1
    assert diagnostic.test == "tests/test_bad.py"


@pytest.mark.ac("AC-11")
def test_pathless_collection_error_is_reported_in_report_error(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_bad",
            classname="",
            file=None,
            line=None,
            body=COLLECTION_ERROR,
        ),
        tests=1,
        errors=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics == ()
    assert report.error is not None
    assert "collection failure" in report.error
    assert (report.tests_collected, report.tests_run, report.tests_skipped) == (1, 1, 0)


@pytest.mark.ac("AC-11")
def test_node_id_uses_the_nested_class_path(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_fails",
            classname="tests.test_app.Outer.Inner",
            body=failure("boom", "boom"),
        ),
        tests=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics[0].test == "tests/test_app.py::Outer::Inner::test_fails"


@pytest.mark.ac("AC-11")
def test_node_id_falls_back_to_the_classname_when_it_is_unrelated(tmp_path: Path) -> None:
    xml = suite(
        case(
            "test_fails",
            classname="other.module.Thing",
            body=failure("boom", "boom"),
        ),
        tests=1,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics[0].test == "other.module.Thing::test_fails"


@pytest.mark.ac("AC-11")
def test_absolute_testcase_paths_become_root_relative(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    xml = suite(
        case(
            "test_fails",
            file=str(root / "tests" / "test_app.py"),
            body=failure("boom", "boom"),
        ),
        tests=1,
    )

    report = parse_junit_xml(xml, root)

    assert report.diagnostics[0].path == "tests/test_app.py"


@pytest.mark.ac("AC-11")
def test_diagnostics_are_ordered_by_the_contract_key(tmp_path: Path) -> None:
    xml = suite(
        case("test_z", file="tests/test_z.py", body=failure("z", "z")),
        case("test_b", file="tests/test_a.py", line=9, body=failure("b", "b")),
        case("test_a", file="tests/test_a.py", line=2, body=failure("a", "a")),
        tests=3,
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert [(item.path, item.line) for item in report.diagnostics] == [
        ("tests/test_a.py", 2),
        ("tests/test_a.py", 9),
        ("tests/test_z.py", 3),
    ]


@pytest.mark.ac("AC-11")
def test_empty_suite_is_valid_with_zero_counts(tmp_path: Path) -> None:
    xml = suite(tests=0, skipped=0)

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics == ()
    assert (report.tests_collected, report.tests_run, report.tests_skipped) == (0, 0, 0)
    assert report.error is None


@pytest.mark.ac("AC-11")
def test_testsuite_root_is_accepted(tmp_path: Path) -> None:
    xml = (
        '<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="1">'
        f"{case('test_pass')}</testsuite>"
    )

    report = parse_junit_xml(xml, tmp_path.resolve())

    assert report.diagnostics == ()
    assert report.tests_collected == 1


@pytest.mark.ac("AC-11")
@pytest.mark.parametrize(
    "xml",
    [
        "not xml",
        "<testsuites><testsuite tests='1'>",
        "<other />",
        '<testsuites><testsuite name="pytest" tests="many" /></testsuites>',
        '<testsuites><testsuite name="pytest" tests="1" skipped="-1" /></testsuites>',
        '<testsuites><testsuite name="pytest" tests="1">'
        '<testcase classname="tests.test_app" file="tests/test_app.py" line="1" />'
        "</testsuite></testsuites>",
    ],
)
def test_invalid_junit_xml_raises_invalid_tool_output(tmp_path: Path, xml: str) -> None:
    with pytest.raises(InvalidToolOutput):
        parse_junit_xml(xml, tmp_path.resolve())


@pytest.mark.ac("AC-11")
def test_pass_records_pytest_version_and_test_counts(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(
        junit_xml=suite(
            case("test_pass"),
            case("test_skip", body='<skipped type="pytest.skip" message="later" />'),
            tests=2,
            skipped=1,
        )
    )

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.id == "tier2-pytest"
    assert result.name == "tests"
    assert result.status == "pass"
    assert result.skipped_reason is None
    assert result.diagnostics == ()
    assert result.tool == ToolInfo(name="pytest", version="8.4.2")
    assert result.meta == {"tests_collected": 2, "tests_run": 1, "tests_skipped": 1}


@pytest.mark.ac("AC-11")
def test_runs_the_full_suite_from_the_root_without_narrowing_targets(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(junit_xml=suite(case("test_pass")))

    PytestTier(runner).run(context_for(root, targets=("src",), files=("tests/test_app.py",)))

    assert runner.calls[0][0] == (*PYTEST, "--version")
    command = runner.calls[1][0]
    assert command[:6] == (*PYTEST, "-q", "-o", "junit_family=xunit1")
    assert command[6].startswith("--junitxml=")
    assert len(command) == 7
    assert all(cwd == root for _, cwd, _ in runner.calls)
    assert all(timeout == 300.0 for _, _, timeout in runner.calls)


@pytest.mark.ac("AC-11")
def test_junit_file_is_outside_the_repository_and_removed_after_parsing(
    tmp_path: Path,
) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(junit_xml=suite(case("test_pass")))

    PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert len(runner.junit_paths) == 1
    xml_path = runner.junit_paths[0]
    assert not xml_path.is_relative_to(root)
    assert not xml_path.exists()


@pytest.mark.ac("AC-11")
def test_timeout_override_applies_to_the_probe_and_the_suite(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(junit_xml=suite(case("test_pass")))

    PytestTier(runner).run(context_for(root, files=("tests/test_app.py",), timeout=2.5))

    assert [timeout for _, _, timeout in runner.calls] == [2.5, 2.5]


@pytest.mark.ac("AC-11")
def test_failure_is_a_fail_with_a_test_failure_diagnostic(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(
        suite_returncode=1,
        junit_xml=suite(
            case(
                "test_fails",
                line=5,
                body=failure(
                    "assert 1 == 2",
                    "E   assert 1 == 2\n\ntests/test_app.py:7: AssertionError",
                ),
            ),
            tests=1,
            failures=1,
        ),
    )

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "fail"
    assert result.skipped_reason is None
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "test-failure"
    assert diagnostic.path == "tests/test_app.py"
    assert diagnostic.line == 7
    assert diagnostic.test == "tests/test_app.py::test_fails"
    assert result.meta == {"tests_collected": 1, "tests_run": 1, "tests_skipped": 0}


@pytest.mark.ac("AC-11")
def test_exit_one_without_error_evidence_is_invalid_output(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(
        suite_returncode=1,
        junit_xml=suite(case("test_pass"), tests=1),
    )

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "invalid tool output"
    assert result.diagnostics == ()


@pytest.mark.ac("AC-11")
def test_exit_five_is_a_skip_with_no_tests_collected(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(suite_returncode=5, junit_xml=suite(tests=0, skipped=0))

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "skipped"
    assert result.skipped_reason == "no tests collected"
    assert result.tool == ToolInfo(name="pytest", version="8.4.2")
    assert result.diagnostics == ()
    assert result.meta == {"tests_collected": 0, "tests_run": 0, "tests_skipped": 0}


@pytest.mark.ac("AC-11")
def test_exit_two_is_an_error_and_keeps_collection_evidence(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(
        suite_returncode=2,
        suite_stderr="collection failed",
        junit_xml=suite(
            case(
                "test_bad",
                classname="",
                file="tests/test_bad.py",
                line=None,
                body=COLLECTION_ERROR,
            ),
            tests=1,
            errors=1,
        ),
    )

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "tool failed"
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "collection-error"
    assert result.meta["tests_collected"] == 1
    assert result.meta["tests_run"] == 1
    assert result.meta["tests_skipped"] == 0
    assert "collection failed" in result.meta["error"]


@pytest.mark.ac("AC-11")
def test_exit_two_without_xml_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(suite_returncode=2, suite_stderr="usage error")

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "tool failed"
    assert result.diagnostics == ()
    assert "usage error" in result.meta["error"]


@pytest.mark.ac("AC-11")
@pytest.mark.parametrize("returncode", [3, 4])
def test_exit_three_and_four_are_errors(tmp_path: Path, returncode: int) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(suite_returncode=returncode, junit_xml=suite(tests=0, skipped=0))

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "tool failed"


@pytest.mark.ac("AC-11")
def test_invalid_junit_xml_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(junit_xml="not xml")

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "invalid tool output"
    assert result.diagnostics == ()
    assert result.tool == ToolInfo(name="pytest", version="8.4.2")


@pytest.mark.ac("AC-11")
def test_missing_junit_xml_is_an_error_when_pytest_ran(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(junit_xml=None)

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "invalid tool output"
    assert result.diagnostics == ()


@pytest.mark.ac("AC-11")
def test_missing_pytest_with_test_files_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(version_returncode=1, version_stderr="No module named pytest")

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "pytest not found"
    assert result.tool is None
    assert result.diagnostics == ()
    assert "pytest" in result.meta["error"].lower()
    assert len(runner.calls) == 1


@pytest.mark.ac("AC-11")
def test_missing_pytest_without_tests_is_a_skip(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(version_returncode=1, version_stderr="No module named pytest")

    result = PytestTier(runner).run(context_for(root, files=("app.py",)))

    assert result.status == "skipped"
    assert result.skipped_reason == "no tests collected"
    assert result.tool is None
    assert result.diagnostics == ()
    assert len(runner.calls) == 1


@pytest.mark.ac("AC-11")
@pytest.mark.parametrize("name", ["test_app.py", "pkg/app_test.py"])
def test_missing_pytest_detects_both_test_file_patterns(tmp_path: Path, name: str) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(version_returncode=1)

    result = PytestTier(runner).run(context_for(root, files=(name,)))

    assert result.status == "error"
    assert result.skipped_reason == "pytest not found"


@pytest.mark.ac("AC-11")
@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("pytest.ini", "[pytest]\n"),
        ("tox.ini", "[pytest]\n"),
        ("setup.cfg", "[tool:pytest]\n"),
        ("pyproject.toml", "[tool.pytest.ini_options]\n"),
    ],
)
def test_missing_pytest_with_pytest_config_is_an_error(
    tmp_path: Path, name: str, text: str
) -> None:
    root = tmp_path.resolve()
    write(root / name, text)
    runner = FakeRunner(version_returncode=1)

    result = PytestTier(runner).run(context_for(root, files=("app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "pytest not found"


@pytest.mark.ac("AC-11")
def test_missing_pytest_from_the_runner_is_an_error_when_tests_exist(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(version_error=ToolNotFoundError("tool not found: pytest"))

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "pytest not found"


@pytest.mark.ac("AC-11")
def test_version_probe_timeout_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(version_error=ToolTimeoutError("tool timed out"))

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "tool timeout"
    assert len(runner.calls) == 1


@pytest.mark.ac("AC-11")
def test_suite_timeout_is_an_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(suite_error=ToolTimeoutError("tool timed out"))

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "tool timeout"
    assert result.tool == ToolInfo(name="pytest", version="8.4.2")


@pytest.mark.ac("AC-11")
def test_suite_missing_at_execution_is_an_error_when_tests_exist(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    runner = FakeRunner(suite_error=ToolNotFoundError("tool not found: pytest"))

    result = PytestTier(runner).run(context_for(root, files=("tests/test_app.py",)))

    assert result.status == "error"
    assert result.skipped_reason == "pytest not found"


@pytest.mark.ac("AC-11")
def test_pipeline_copies_test_counts_from_the_pytest_tier(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    files = (root / "tests" / "test_app.py",)
    runner = FakeRunner(
        junit_xml=suite(
            case("test_pass"),
            case("test_skip", body='<skipped type="pytest.skip" message="later" />'),
            tests=2,
            skipped=1,
        )
    )

    check = run_pipeline(
        (PytestTier(runner),),
        context_for(root, files=("tests/test_app.py",)),
        scope_for(files),
    )

    assert check.status == "pass"
    assert (check.scope.tests_collected, check.scope.tests_run, check.scope.tests_skipped) == (
        2,
        1,
        1,
    )


@pytest.mark.ac("AC-11")
def test_no_tests_collected_keeps_the_pipeline_pass(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    files = (root / "tests" / "test_app.py",)
    runner = FakeRunner(suite_returncode=5, junit_xml=suite(tests=0, skipped=0))

    check = run_pipeline(
        (PytestTier(runner), LaterTier()),
        context_for(root, files=("tests/test_app.py",)),
        scope_for(files),
    )

    assert check.status == "pass"
    assert [tier.status for tier in check.tiers] == ["skipped", "pass"]
    assert check.tiers[0].skipped_reason == "no tests collected"
