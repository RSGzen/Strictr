from __future__ import annotations

import json
from typing import Any

import pytest

pytestmark = pytest.mark.spec("004")

OUTSIDE_SYNTAX_ERROR = "def broken(:\n    pass\n"


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


@pytest.mark.ac("AC-1")
def test_nested_cwd_ledger(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "src/ok.py": "VALUE = 1\n",
            "outside_broken.py": OUTSIDE_SYNTAX_ERROR,
        }
    )

    completed = run_cli(root / "src", "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "pass"
    assert document["scope"]["root"] == ".."
    assert document["scope"]["targets"] == ["src"]
    assert document["scope"]["files_checked"] == 1


@pytest.mark.ac("AC-1")
def test_nested_cwd_explicit_dot_checks_only_the_subtree(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "src/ok.py": "VALUE = 1\n",
            "outside_broken.py": OUTSIDE_SYNTAX_ERROR,
        }
    )

    completed = run_cli(root / "src", "check", "--json", "--type-checker", "none", ".")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["scope"]["root"] == ".."
    assert document["scope"]["targets"] == ["src"]
    assert document["scope"]["files_checked"] == 1


@pytest.mark.ac("AC-1")
def test_absolute_target_normalizes_relative_to_root(make_project: Any, run_cli: Any) -> None:
    root = make_project({"src/ok.py": "VALUE = 1\n"})

    completed = run_cli(root, "check", "--json", "--type-checker", "none", str(root / "src"))

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["scope"]["root"] == "."
    assert document["scope"]["targets"] == ["src"]
    assert document["scope"]["files_checked"] == 1
