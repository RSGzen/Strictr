from __future__ import annotations

import json
import os
from typing import Any

import pytest

pytestmark = pytest.mark.spec("003")

CLEAN = {"src/example.py": "def add(a: int, b: int) -> int:\n    return a + b\n"}
RUFF_ERROR = {"app.py": "import os\n\n\nVALUE = 1\n"}
SYNTAX_ERROR = {"broken.py": "def broken(:\n    pass\n"}


def json_envelope(completed: Any) -> dict[str, Any]:
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


@pytest.mark.ac("AC-4")
def test_pass_exits_zero(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    assert json_envelope(completed)["status"] == "pass"


@pytest.mark.ac("AC-4")
def test_syntax_error_exits_one(make_project: Any, run_cli: Any) -> None:
    root = make_project(SYNTAX_ERROR)

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert document["tiers"][0]["diagnostics"][0]["code"] == "syntax-error"
    assert document["tiers"][1]["status"] == "skipped"


@pytest.mark.ac("AC-4")
def test_ruff_failure_exits_one(make_project: Any, run_cli: Any) -> None:
    root = make_project(RUFF_ERROR)

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 1
    document = json_envelope(completed)
    assert document["status"] == "fail"
    assert document["tiers"][1]["id"] == "tier1-ruff"
    assert document["tiers"][1]["status"] == "fail"


@pytest.mark.ac("AC-4")
def test_missing_target_exits_two_with_a_discovery_error(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "missing.py")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    assert document["tiers"][0]["status"] == "error"
    assert document["tiers"][0]["skipped_reason"] == "discovery failed"
    for tier in document["tiers"][1:]:
        assert tier["status"] == "skipped"
        assert tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.ac("AC-4")
def test_empty_project_exits_two(make_project: Any, run_cli: Any) -> None:
    root = make_project({})

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    assert document["tiers"][0]["status"] == "error"
    assert document["tiers"][0]["skipped_reason"] == "no Python files found"


@pytest.mark.ac("AC-4")
def test_missing_ruff_exits_two_instead_of_passing(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)
    empty_bin = root / "empty-bin"
    empty_bin.mkdir()
    environment = os.environ.copy()
    environment["PATH"] = str(empty_bin)

    completed = run_cli(root, "check", "--json", env=environment)

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    ruff_tier = next(tier for tier in document["tiers"] if tier["id"] == "tier1-ruff")
    assert ruff_tier["status"] == "error"
    assert ruff_tier["skipped_reason"] == "ruff not found"


@pytest.mark.ac("AC-4")
def test_type_checker_none_does_not_make_the_run_partial(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0
    assert json_envelope(completed)["status"] == "pass"
