from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

pytestmark = pytest.mark.spec("004")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "verification-contract.schema.json"
)


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    assert completed.stdout.count("\n") == 1, completed.stdout
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    assert (
        completed.stdout == json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    assert validation_errors(document) == []
    return document


def validation_errors(document: Any) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(document)]


def assert_discovery_error(completed: Any, expected_targets: list[str]) -> dict[str, Any]:
    assert completed.returncode == 2, completed.stderr
    document = json_envelope(completed)
    assert document["status"] == "error"
    assert document["scope"]["root"] == "."
    assert document["scope"]["targets"] == expected_targets
    assert document["scope"]["files_checked"] == 0
    tier0 = document["tiers"][0]
    assert tier0["status"] == "error"
    assert tier0["skipped_reason"] == "discovery failed"
    return document


@pytest.mark.ac("AC-9")
def test_discovery_error_targets_are_sorted_and_deduplicated(
    make_project: Any, run_cli: Any
) -> None:
    root = make_project({"src/ok.py": "VALUE = 1\n"})

    completed = run_cli(
        root,
        "check",
        "--json",
        "--type-checker",
        "none",
        "missing/b.py",
        "missing/a.py",
        "missing/a.py",
    )

    document = assert_discovery_error(completed, ["missing/a.py", "missing/b.py"])
    assert "does not exist" in document["tiers"][0]["meta"]["error"]


@pytest.mark.ac("AC-9")
def test_discovery_error_normalizes_windows_separators(make_project: Any, run_cli: Any) -> None:
    root = make_project({"src/ok.py": "VALUE = 1\n"})
    expected = ["missing/dir/x.py"] if os.name == "nt" else ["missing\\dir\\x.py"]

    completed = run_cli(
        root,
        "check",
        "--json",
        "--type-checker",
        "none",
        "missing\\dir\\x.py",
    )

    document = assert_discovery_error(completed, expected)
    assert "does not exist" in document["tiers"][0]["meta"]["error"]


@pytest.mark.ac("AC-9")
def test_discovery_error_outside_target_normalizes_relative_to_root(
    tmp_path: Path, run_cli: Any
) -> None:
    # make_project always builds at tmp_path, so build the project explicitly to
    # get a sibling outside its marker root.
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "pyproject.toml").write_text("", encoding="utf-8")
    (project / "src" / "ok.py").write_text("VALUE = 1\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "evil.py").write_text("VALUE = 2\n", encoding="utf-8")

    completed = run_cli(
        project,
        "check",
        "--json",
        "--type-checker",
        "none",
        os.path.join("..", "outside", "evil.py"),
    )

    document = assert_discovery_error(completed, ["../outside/evil.py"])
    assert "outside project root" in document["tiers"][0]["meta"]["error"]


@pytest.mark.ac("AC-9")
def test_discovery_error_deduplicates_mixed_separators(make_project: Any, run_cli: Any) -> None:
    root = make_project({"src/ok.py": "VALUE = 1\n"})
    expected = ["missing/a.py"] if os.name == "nt" else ["missing/a.py", "missing\\a.py"]

    completed = run_cli(
        root,
        "check",
        "--json",
        "--type-checker",
        "none",
        "missing\\a.py",
        "missing/a.py",
    )

    assert_discovery_error(completed, expected)
