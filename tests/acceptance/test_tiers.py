from __future__ import annotations

import importlib.util
import json
from typing import Any

import pytest

pytestmark = pytest.mark.spec("003")

MYPY_AVAILABLE = importlib.util.find_spec("mypy") is not None


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def tier_by_id(document: dict[str, Any], tier_id: str) -> dict[str, Any]:
    return next(tier for tier in document["tiers"] if tier["id"] == tier_id)


@pytest.mark.skipif(not MYPY_AVAILABLE, reason="mypy is not installed")
@pytest.mark.ac("AC-7")
@pytest.mark.ac("AC-8")
@pytest.mark.ac("AC-10")
@pytest.mark.ac("AC-11")
def test_clean_project_passes_all_four_tiers(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("clean")

    completed = run_cli(root, "check", "--json", "--type-checker", "mypy")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "pass"
    assert [tier["id"] for tier in document["tiers"]] == [
        "tier0",
        "tier1-ruff",
        "tier1-types",
        "tier2-pytest",
    ]
    assert [tier["status"] for tier in document["tiers"]] == [
        "pass",
        "pass",
        "pass",
        "pass",
    ]
    for tier_id, tool_name in (
        ("tier1-ruff", "ruff"),
        ("tier1-types", "mypy"),
        ("tier2-pytest", "pytest"),
    ):
        tool = tier_by_id(document, tier_id)["tool"]
        assert tool["name"] == tool_name
        assert tool["version"]
    assert document["scope"]["files_checked"] == 2
    assert document["scope"]["tests_collected"] == 1
    assert document["scope"]["tests_run"] == 1
    assert document["scope"]["tests_skipped"] == 0


@pytest.mark.ac("AC-7")
def test_syntax_error_fails_tier0_and_skips_later_tiers(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("syntax-error")

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    tier0 = tier_by_id(document, "tier0")
    assert tier0["status"] == "fail"
    diagnostic = tier0["diagnostics"][0]
    assert diagnostic["path"] == "broken.py"
    assert diagnostic["line"] >= 1
    assert diagnostic["column"] >= 1
    assert diagnostic["code"] == "syntax-error"
    assert diagnostic["severity"] == "error"
    assert diagnostic["message"]
    for tier in document["tiers"][1:]:
        assert tier["status"] == "skipped"
        assert tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.ac("AC-8")
def test_ruff_failure_reports_normalized_diagnostics(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("ruff-error")

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert tier_by_id(document, "tier0")["status"] == "pass"
    ruff = tier_by_id(document, "tier1-ruff")
    assert ruff["status"] == "fail"
    assert ruff["tool"]["name"] == "ruff"
    assert ruff["tool"]["version"]
    diagnostic = ruff["diagnostics"][0]
    assert diagnostic["source"] == "ruff"
    assert diagnostic["path"] == "app.py"
    assert diagnostic["line"] == 1
    assert diagnostic["code"] == "F401"
    assert diagnostic["severity"] == "error"
    for tier in document["tiers"][2:]:
        assert tier["status"] == "skipped"
        assert tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.skipif(not MYPY_AVAILABLE, reason="mypy is not installed")
@pytest.mark.ac("AC-10")
def test_type_error_fails_with_mypy(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("type-error")

    completed = run_cli(root, "check", "--json", "--type-checker", "mypy")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert tier_by_id(document, "tier0")["status"] == "pass"
    assert tier_by_id(document, "tier1-ruff")["status"] == "pass"
    types = tier_by_id(document, "tier1-types")
    assert types["status"] == "fail"
    assert types["tool"]["name"] == "mypy"
    assert types["meta"]["checker"] == "mypy"
    assert types["meta"]["selection"] == "explicit"
    diagnostic = types["diagnostics"][0]
    assert diagnostic["source"] == "mypy"
    assert diagnostic["path"] == "app.py"
    assert diagnostic["line"] == 2
    assert diagnostic["code"] == "return-value"
    assert diagnostic["severity"] == "error"
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "skipped"
    assert pytest_tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.ac("AC-11")
def test_pytest_failure_reports_test_evidence(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("test-failure")

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert tier_by_id(document, "tier0")["status"] == "pass"
    assert tier_by_id(document, "tier1-ruff")["status"] == "pass"
    assert tier_by_id(document, "tier1-types")["status"] == "skipped"
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "fail"
    diagnostic = pytest_tier["diagnostics"][0]
    assert diagnostic["source"] == "pytest"
    assert diagnostic["path"] == "tests/test_math.py"
    assert diagnostic["line"] == 2
    assert diagnostic["code"] == "test-failure"
    assert diagnostic["test"] == "tests/test_math.py::test_addition"
    assert diagnostic["exception"] == "AssertionError"
    assert diagnostic["severity"] == "error"
    assert document["scope"]["tests_collected"] == 1
    assert document["scope"]["tests_run"] == 1
    assert document["scope"]["tests_skipped"] == 0


@pytest.mark.ac("AC-11")
def test_no_tests_is_a_skip_not_a_failure(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("no-tests")

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "pass"
    assert tier_by_id(document, "tier0")["status"] == "pass"
    assert tier_by_id(document, "tier1-ruff")["status"] == "pass"
    assert tier_by_id(document, "tier1-types")["status"] == "skipped"
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "skipped"
    assert pytest_tier["skipped_reason"] == "no tests collected"
    assert document["scope"]["tests_collected"] == 0
    assert document["scope"]["tests_run"] == 0
    assert document["scope"]["tests_skipped"] == 0


@pytest.mark.ac("AC-11")
def test_pytest_collection_error_is_an_error(make_project: Any, run_cli: Any) -> None:
    root = make_project({"tests/test_broken.py": 'raise RuntimeError("collection boom")\n'})

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "error"
    assert pytest_tier["skipped_reason"] == "tool failed"
    assert pytest_tier["meta"].get("error") or pytest_tier["diagnostics"]
