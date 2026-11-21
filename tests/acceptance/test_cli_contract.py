from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

pytestmark = pytest.mark.spec("003")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "verification-contract.schema.json"
)
TRUST_WARNING = "Local execution; not a security boundary."
CLEAN = {"src/example.py": "def add(a: int, b: int) -> int:\n    return a + b\n"}
RUFF_ERROR = {"app.py": "import os\n\n\nVALUE = 1\n"}


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def validation_errors(document: Any) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(document)]


@pytest.mark.ac("AC-1")
def test_check_defaults_paths_to_dot(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["scope"]["targets"] == ["."]
    assert document["scope"]["files_checked"] == 1


@pytest.mark.ac("AC-1")
def test_python_m_prints_the_package_version(make_project: Any, run_cli: Any) -> None:
    root = make_project({})

    completed = run_cli(root, "--version")

    assert completed.returncode == 0
    assert completed.stdout.strip() == "0.0.0"
    assert completed.stderr == ""


@pytest.mark.ac("AC-1")
def test_console_script_prints_the_package_version(make_project: Any, run_console: Any) -> None:
    root = make_project({})

    completed = run_console(root, "--version")

    assert completed.returncode == 0
    assert completed.stdout.strip() == "0.0.0"
    assert completed.stderr == ""


@pytest.mark.ac("AC-1")
def test_console_script_runs_check(make_project: Any, run_console: Any) -> None:
    root = make_project(CLEAN)

    completed = run_console(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    assert json_envelope(completed)["scope"]["targets"] == ["."]


@pytest.mark.ac("AC-1")
def test_check_parser_rejects_version(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--version")

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "usage" in completed.stderr.lower()


@pytest.mark.ac("AC-1")
@pytest.mark.parametrize("choice", ["mypy", "pyright", "none"])
def test_type_checker_choices_are_accepted(choice: str, make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", choice)

    assert "usage" not in completed.stderr.lower(), completed.stderr
    document = json_envelope(completed)
    assert document["schema_version"] == "1"
    assert completed.returncode in (0, 1, 2)


@pytest.mark.ac("AC-1")
def test_invalid_type_checker_is_a_usage_error(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", "pytype")

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "usage" in completed.stderr.lower()


@pytest.mark.ac("AC-1")
def test_timeout_option_is_accepted(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--timeout", "60", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    json_envelope(completed)


@pytest.mark.ac("AC-1")
@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "abc"])
def test_invalid_timeout_is_a_usage_error(value: str, make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--timeout", value)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr


@pytest.mark.ac("AC-2")
def test_json_mode_writes_one_newline_terminated_object(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.endswith("\n")
    assert completed.stdout.count("\n") == 1
    document = json.loads(completed.stdout)
    assert document["status"] == "pass"


@pytest.mark.ac("AC-2")
def test_json_mode_validates_against_the_contract_schema(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert validation_errors(json_envelope(completed)) == []


@pytest.mark.ac("AC-2")
def test_json_mode_keeps_stdout_to_json_on_failure(make_project: Any, run_cli: Any) -> None:
    root = make_project(RUFF_ERROR)

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert "files checked" not in completed.stdout
    assert TRUST_WARNING not in completed.stderr


@pytest.mark.ac("AC-2")
def test_usage_error_writes_stderr_without_an_envelope(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--unknown-option")

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "usage" in completed.stderr.lower()


@pytest.mark.ac("AC-2")
def test_json_mode_writes_warnings_to_stderr_without_trust(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN, git_marker=True)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert any("git file discovery failed" in warning for warning in document["warnings"])
    assert "git file discovery failed" in completed.stderr
    assert TRUST_WARNING not in completed.stderr
    assert document["trust"] == {"sandboxed": False, "warning": TRUST_WARNING}
