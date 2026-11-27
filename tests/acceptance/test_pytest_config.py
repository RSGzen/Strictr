from __future__ import annotations

import json
from typing import Any

import pytest

pytestmark = pytest.mark.spec("004")

DECOY_FAILURE_TEXT = "decoy should never run"


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def tier_by_id(document: dict[str, Any], tier_id: str) -> dict[str, Any]:
    return next(tier for tier in document["tiers"] if tier["id"] == tier_id)


@pytest.mark.ac("AC-6")
def test_pytest_testpaths_is_honored(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": (
                '[tool.pytest.ini_options]\ntestpaths = ["checks"]\n\n'
                '[tool.ruff.lint]\nselect = ["E", "F"]\n'
            ),
            "checks/test_ok.py": "def test_ok() -> None:\n    assert True\n",
            "tests/test_decoy.py": (
                f'def test_decoy() -> None:\n    assert False, "{DECOY_FAILURE_TEXT}"\n'
            ),
        }
    )

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "pass"
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "pass"
    assert pytest_tier["meta"]["tests_collected"] == 1
    assert pytest_tier["meta"]["tests_run"] == 1
    assert document["scope"]["tests_collected"] == 1
    assert document["scope"]["tests_run"] == 1
    assert document["scope"]["tests_skipped"] == 0
    assert DECOY_FAILURE_TEXT not in completed.stdout
