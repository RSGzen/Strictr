from __future__ import annotations

import importlib.util
import json
import os
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
MYPY_AVAILABLE = importlib.util.find_spec("mypy") is not None


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def validation_errors(document: Any) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(document)]


@pytest.mark.ac("AC-15")
@pytest.mark.parametrize(
    ("fixture", "expected_status", "expected_exit"),
    [
        ("ruff-error", "fail", 1),
        ("syntax-error", "fail", 1),
        ("test-failure", "fail", 1),
        ("empty", "error", 2),
    ],
)
def test_non_pass_envelopes_validate_against_the_schema(
    fixture: str,
    expected_status: str,
    expected_exit: int,
    copy_fixture: Any,
    run_cli: Any,
) -> None:
    root = copy_fixture(fixture)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == expected_exit, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == expected_status
    assert validation_errors(document) == []


@pytest.mark.skipif(not MYPY_AVAILABLE, reason="mypy is not installed")
@pytest.mark.ac("AC-10")
@pytest.mark.ac("AC-15")
def test_type_error_envelope_validates_against_the_schema(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("type-error")

    completed = run_cli(root, "check", "--json", "--type-checker", "mypy")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert validation_errors(document) == []


@pytest.mark.ac("AC-4")
@pytest.mark.ac("AC-9")
@pytest.mark.ac("AC-15")
def test_no_type_checker_is_partial_and_schema_valid(
    tmp_path_factory: pytest.TempPathFactory, make_project: Any, run_cli: Any
) -> None:
    root = make_project({"src/example.py": "VALUE = 1\n"})
    fake_checkers = tmp_path_factory.mktemp("no-checkers")
    (fake_checkers / "mypy.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    (fake_checkers / "pyright.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(fake_checkers), environment.get("PYTHONPATH", "")) if part
    )

    completed = run_cli(root, "check", "--json", env=environment)

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "partial"
    types_tier = next(tier for tier in document["tiers"] if tier["id"] == "tier1-types")
    assert types_tier["status"] == "skipped"
    assert types_tier["skipped_reason"] == "no type checker found"
    assert any("No type checker found" in warning for warning in document["warnings"])
    assert "No type checker found" in completed.stderr
    assert validation_errors(document) == []


@pytest.mark.ac("AC-11")
@pytest.mark.ac("AC-15")
def test_pytest_collection_error_envelope_validates(make_project: Any, run_cli: Any) -> None:
    root = make_project({"tests/test_broken.py": 'raise RuntimeError("collection boom")\n'})

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    assert validation_errors(document) == []
