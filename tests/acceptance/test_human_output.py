from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.spec("003")

TRUST_WARNING = "Local execution; not a security boundary."
CLEAN = {"src/example.py": "def add(a: int, b: int) -> int:\n    return a + b\n"}
RUFF_ERROR = {"app.py": "import os\n\n\nVALUE = 1\n"}


@pytest.mark.ac("AC-3")
def test_human_pass_writes_status_scope_and_tiers_to_stdout(
    make_project: Any, run_cli: Any
) -> None:
    root = make_project(CLEAN)

    completed = run_cli(root, "check", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("PASS")
    assert "1 files checked" in completed.stdout
    assert "tier0" in completed.stdout
    assert "tier1-ruff" in completed.stdout
    assert TRUST_WARNING not in completed.stdout
    assert completed.stderr.count(TRUST_WARNING) == 1


@pytest.mark.ac("AC-3")
def test_human_failure_shows_the_first_failures(make_project: Any, run_cli: Any) -> None:
    root = make_project(RUFF_ERROR)

    completed = run_cli(root, "check")

    assert completed.returncode == 1
    assert completed.stdout.startswith("FAIL")
    assert "tier1-ruff" in completed.stdout
    assert "app.py" in completed.stdout
    assert "F401" in completed.stdout
    assert TRUST_WARNING not in completed.stdout
    assert completed.stderr.count(TRUST_WARNING) == 1


@pytest.mark.ac("AC-3")
def test_human_warnings_and_trust_warning_go_to_stderr(make_project: Any, run_cli: Any) -> None:
    root = make_project(CLEAN, git_marker=True)

    completed = run_cli(root, "check", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    assert "git file discovery failed" in completed.stderr
    assert "git file discovery failed" not in completed.stdout
    assert TRUST_WARNING not in completed.stdout
    assert completed.stderr.count(TRUST_WARNING) == 1


@pytest.mark.ac("AC-3")
def test_human_error_shows_skipped_reasons(make_project: Any, run_cli: Any) -> None:
    root = make_project({})

    completed = run_cli(root, "check")

    assert completed.returncode == 2
    assert completed.stdout.startswith("ERROR")
    assert "no Python files found" in completed.stdout
    assert TRUST_WARNING not in completed.stdout
    assert completed.stderr.count(TRUST_WARNING) == 1


@pytest.mark.ac("AC-3")
def test_human_output_has_no_ansi_colors(make_project: Any, run_cli: Any) -> None:
    root = make_project(RUFF_ERROR)

    completed = run_cli(root, "check")

    assert completed.returncode == 1
    assert "FAIL" in completed.stdout
    assert "\x1b[" not in completed.stdout + completed.stderr
