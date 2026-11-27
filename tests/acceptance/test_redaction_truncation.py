from __future__ import annotations

import json
from typing import Any

import pytest

pytestmark = pytest.mark.spec("004")

RUFF_CONFIG = '[tool.ruff.lint]\nselect = ["E", "F"]\n'
SECRET = "sk-A1B2C3D4E5F6G7H8I9J0K1L2"
FINDING_COUNT = 21
DIAGNOSTIC_CAP = 20
PREVIEW_LIMIT = 5
UNUSED_MODULES = (
    "abc",
    "argparse",
    "ast",
    "asyncio",
    "base64",
    "bisect",
    "calendar",
    "collections",
    "contextlib",
    "csv",
    "dataclasses",
    "datetime",
    "decimal",
    "difflib",
    "enum",
    "fnmatch",
    "fractions",
    "functools",
    "getpass",
    "glob",
    "hashlib",
)


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def tier_by_id(document: dict[str, Any], tier_id: str) -> dict[str, Any]:
    return next(tier for tier in document["tiers"] if tier["id"] == tier_id)


@pytest.mark.ac("AC-7")
def test_real_pytest_secret_is_redacted(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": RUFF_CONFIG,
            "tests/test_secret.py": (
                f'SECRET = "{SECRET}"\n'
                "\n"
                "def test_secret_failure() -> None:\n"
                '    raise AssertionError(f"token {SECRET} leaked")\n'
            ),
        }
    )

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 1, completed.stderr
    document = json_envelope(completed)
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "fail"
    [diagnostic] = pytest_tier["diagnostics"]
    assert "[REDACTED]" in diagnostic["message"]
    assert SECRET not in completed.stdout
    assert diagnostic["path"] == "tests/test_secret.py"
    assert diagnostic["test"] == "tests/test_secret.py::test_secret_failure"


@pytest.mark.ac("AC-7")
def test_real_pytest_message_is_capped(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": RUFF_CONFIG,
            "tests/test_long.py": (
                'def test_long_failure() -> None:\n    raise AssertionError("A" * 3000)\n'
            ),
        }
    )

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 1, completed.stderr
    document = json_envelope(completed)
    pytest_tier = tier_by_id(document, "tier2-pytest")
    assert pytest_tier["status"] == "fail"
    assert pytest_tier["meta"]["truncated"] is True
    longest = max(diagnostic["message"] for diagnostic in pytest_tier["diagnostics"])
    assert len(longest) <= 2_000
    assert longest.endswith(" [truncated]")


@pytest.mark.ac("AC-7")
def test_ruff_count_cap(make_project: Any, run_cli: Any) -> None:
    root = make_project(
        {
            "pyproject.toml": RUFF_CONFIG,
            "findings.py": "".join(f"import {module}\n" for module in UNUSED_MODULES),
        }
    )

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 1, completed.stderr
    document = json_envelope(completed)
    ruff_tier = tier_by_id(document, "tier1-ruff")
    assert len(ruff_tier["diagnostics"]) == DIAGNOSTIC_CAP
    assert ruff_tier["meta"]["total_diagnostics"] == FINDING_COUNT
    assert ruff_tier["meta"]["truncated"] is True

    human = run_cli(root, "check", "--type-checker", "none")

    assert human.returncode == 1
    hidden = FINDING_COUNT - PREVIEW_LIMIT
    assert f"... {hidden} more diagnostics (use --json)" in human.stdout
