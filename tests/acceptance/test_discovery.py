from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.spec("003")


def json_envelope(completed: Any) -> dict[str, Any]:
    assert completed.stdout.endswith("\n"), completed.stderr
    document = json.loads(completed.stdout)
    assert isinstance(document, dict)
    return document


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.mark.ac("AC-5")
def test_targets_are_normalized_and_counted(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("clean")

    completed = run_cli(root, "check", "--json", "--type-checker", "none", "src", "tests")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["scope"]["targets"] == ["src", "tests"]
    assert document["scope"]["files_checked"] == 2
    assert document["scope"]["files_skipped"] == 0
    assert [tier["status"] for tier in document["tiers"]] == [
        "pass",
        "pass",
        "skipped",
        "pass",
    ]


@pytest.mark.ac("AC-5")
def test_missing_target_is_a_discovery_error(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("clean")

    completed = run_cli(root, "check", "--json", "missing.py")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    assert document["scope"]["files_checked"] == 0
    tier0 = document["tiers"][0]
    assert tier0["status"] == "error"
    assert tier0["skipped_reason"] == "discovery failed"
    assert "does not exist" in tier0["meta"]["error"]


@pytest.mark.ac("AC-5")
def test_target_outside_root_is_a_discovery_error(
    copy_fixture: Any, tmp_path: Path, run_cli: Any
) -> None:
    root = copy_fixture("clean")
    (tmp_path / "outside.py").write_text("VALUE = 1\n", encoding="utf-8")

    completed = run_cli(root, "check", "--json", "../outside.py")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    tier0 = document["tiers"][0]
    assert tier0["status"] == "error"
    assert tier0["skipped_reason"] == "discovery failed"
    assert "outside project root" in tier0["meta"]["error"]
    for tier in document["tiers"][1:]:
        assert tier["status"] == "skipped"
        assert tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.ac("AC-6")
def test_empty_project_is_an_error(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("empty")

    completed = run_cli(root, "check", "--json")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    tier0 = document["tiers"][0]
    assert tier0["status"] == "error"
    assert tier0["skipped_reason"] == "no Python files found"
    for tier in document["tiers"][1:]:
        assert tier["status"] == "skipped"
        assert tier["skipped_reason"] == "earlier_tier_failed"


@pytest.mark.ac("AC-5")
def test_gitignored_files_are_outside_the_candidate_set(tmp_path: Path, run_cli: Any) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not available")
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True)
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    (root / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    (root / "src" / "kept.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "src" / "ignored.py").write_text("VALUE = 2\n", encoding="utf-8")
    git(root, "init", "--quiet")

    completed = run_cli(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["scope"]["files_checked"] == 1
    assert document["scope"]["files_skipped"] == 0
    assert document["scope"]["targets"] == ["."]


@pytest.mark.ac("AC-5")
def test_symlink_escaping_the_root_is_an_error(
    copy_fixture: Any, tmp_path: Path, run_cli: Any
) -> None:
    root = copy_fixture("clean")
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 1\n", encoding="utf-8")
    link = root / "src" / "escape.py"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not available")

    completed = run_cli(root, "check", "--json", "src")

    assert completed.returncode == 2
    document = json_envelope(completed)
    assert document["status"] == "error"
    tier0 = document["tiers"][0]
    assert tier0["status"] == "error"
    assert tier0["skipped_reason"] == "discovery failed"
    assert "outside project root" in tier0["meta"]["error"]


@pytest.mark.ac("AC-5")
def test_path_with_spaces_and_unicode(copy_fixture: Any, run_cli: Any) -> None:
    root = copy_fixture("path with space-ü")

    completed = run_cli(root, "check", "--json", "--type-checker", "none", "src/módulo.py")

    assert completed.returncode == 0, completed.stderr
    document = json_envelope(completed)
    assert document["scope"]["targets"] == ["src/módulo.py"]
    assert document["scope"]["files_checked"] == 1
    assert document["status"] == "pass"
