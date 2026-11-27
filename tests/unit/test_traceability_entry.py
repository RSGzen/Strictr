from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from strictr import traceability

pytestmark = pytest.mark.spec("004")

COMMIT = "feat(demo): demo\n\nSpec: 004"
CHANGED_FILE = "src/strictr/demo.py"
PR_TITLE = "feat(demo): demo [004]"
VALID_SPEC = """---
id: "004"
status: approved
---

# Demo

## Acceptance criteria

- **AC-1:** demo
"""


def write_repo(root: Path, spec_text: str = VALID_SPEC) -> None:
    spec = root / "specs" / "active" / "004-demo" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(spec_text, encoding="utf-8")
    report = root / "build" / "ac-tests.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps({"004": {"AC-1": ["tests/unit/test_demo.py::test_demo"]}}),
        encoding="utf-8",
    )


def set_environment(monkeypatch: pytest.MonkeyPatch, title: str = PR_TITLE) -> None:
    monkeypatch.setenv("HEAD_REF", "feat/004-demo")
    monkeypatch.setenv("PR_TITLE", title)
    monkeypatch.setenv("BASE_REF", "main")


def patch_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(traceability, "collect_commits", lambda root, base_ref: [COMMIT])
    monkeypatch.setattr(
        traceability, "collect_changed_files", lambda root, base_ref: [CHANGED_FILE]
    )


@pytest.mark.ac("AC-8")
@pytest.mark.parametrize("missing", [("HEAD_REF",), ("PR_TITLE",), ("HEAD_REF", "PR_TITLE")])
def test_main_requires_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    missing: tuple[str, ...],
) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("HEAD_REF", "PR_TITLE", "BASE_REF"):
        monkeypatch.delenv(key, raising=False)
    for key, value in {"HEAD_REF": "feat/004-demo", "PR_TITLE": PR_TITLE}.items():
        if key not in missing:
            monkeypatch.setenv(key, value)

    assert traceability.main() == 1
    captured = capsys.readouterr()
    assert "HEAD_REF and PR_TITLE are required" in captured.err


@pytest.mark.ac("AC-8")
def test_main_accepts_valid_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_repo(tmp_path)
    set_environment(monkeypatch)
    patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)

    assert traceability.main() == 0
    captured = capsys.readouterr()
    assert "traceability: ok" in captured.out
    assert captured.err == ""


@pytest.mark.ac("AC-8")
def test_main_reports_git_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(root: Path, base_ref: str) -> list[str]:
        raise subprocess.CalledProcessError(128, ["git", "log"])

    write_repo(tmp_path)
    set_environment(monkeypatch)
    patch_git(monkeypatch)
    monkeypatch.setattr(traceability, "collect_commits", fail)
    monkeypatch.chdir(tmp_path)

    assert traceability.main() == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("traceability:")


@pytest.mark.ac("AC-8")
def test_main_reports_malformed_spec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_repo(tmp_path, VALID_SPEC.replace("status: approved", "status: bogus"))
    set_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)

    assert traceability.main() == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("traceability:")
    assert "invalid status" in captured.err


@pytest.mark.ac("AC-8")
def test_main_reports_malformed_ac_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_repo(tmp_path)
    (tmp_path / "build" / "ac-tests.json").write_text("{not json", encoding="utf-8")
    set_environment(monkeypatch)
    monkeypatch.chdir(tmp_path)

    assert traceability.main() == 1
    captured = capsys.readouterr()
    assert "invalid AC report" in captured.err


@pytest.mark.ac("AC-8")
def test_main_reports_policy_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_repo(tmp_path)
    set_environment(monkeypatch, title="fix(demo): demo [004]")
    patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)

    assert traceability.main() == 1
    captured = capsys.readouterr()
    assert "PR title type 'fix' does not match branch type 'feat'" in captured.err
