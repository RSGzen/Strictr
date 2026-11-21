from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from strictr.core.discovery import discover
from strictr.core.models import (
    CheckContext,
    Diagnostic,
    DiscoveryResult,
    Scope,
    TierResult,
    exit_code_for,
)
from strictr.core.paths import relative_posix
from strictr.core.pipeline import run_pipeline
from strictr.tools.runner import SubprocessRunner

pytestmark = pytest.mark.spec("003")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "verification-contract.schema.json"
)
MISSING_TOOL = "strictr-no-such-tool-3f9a"


def validation_errors(document: Any) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(document)]


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    write(root / "pyproject.toml")
    return root


def python(code: str) -> tuple[str, ...]:
    return (sys.executable, "-c", code)


def context_for(discovery: DiscoveryResult) -> CheckContext:
    return CheckContext(
        root=discovery.root,
        targets=discovery.targets,
        files=discovery.files,
    )


def scope_for(discovery: DiscoveryResult) -> Scope:
    return Scope(
        root=relative_posix(discovery.root, Path.cwd()),
        targets=discovery.targets,
        files_checked=len(discovery.files),
        files_skipped=discovery.files_skipped,
    )


@dataclass
class PassingTier:
    id: str
    name: str
    warnings: tuple[str, ...] = ()
    calls: list[CheckContext] = field(default_factory=list)

    def run(self, context: CheckContext) -> TierResult:
        self.calls.append(context)
        return TierResult(id=self.id, name=self.name, status="pass", warnings=self.warnings)


@dataclass
class ToolTier:
    """A tier boundary backed by the real runner, without a product tier."""

    id: str
    command: tuple[str, ...]
    timeout: float
    name: str = "tool"

    def run(self, context: CheckContext) -> TierResult:
        result = SubprocessRunner().run(self.command, cwd=context.root, timeout=self.timeout)
        if result.returncode == 0:
            return TierResult(
                id=self.id,
                name=self.name,
                status="pass",
                duration_ms=result.duration_ms,
            )
        diagnostic = Diagnostic(
            tier=self.id,
            source="test-tool",
            path=relative_posix(context.files[0], context.root),
            line=1,
            column=1,
            code="T001",
            severity="error",
            message=result.stdout.strip() or result.stderr.strip(),
        )
        return TierResult(
            id=self.id,
            name=self.name,
            status="fail",
            duration_ms=result.duration_ms,
            diagnostics=(diagnostic,),
        )


@pytest.mark.ac("AC-5")
@pytest.mark.ac("AC-12")
@pytest.mark.ac("AC-15")
def test_discovery_scope_and_pass_envelope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = make_project(tmp_path.resolve())
    write(root / "src" / "app.py", "x = 1\n")
    write(root / "tests" / "test_app.py", "def test_ok(): assert True\n")
    monkeypatch.chdir(root)
    discovery = discover(("src", "tests"))

    check = run_pipeline(
        (PassingTier("tier0", "syntax"), PassingTier("tier1-ruff", "lint")),
        context_for(discovery),
        scope_for(discovery),
    )

    envelope = check.to_envelope()
    assert check.status == "pass"
    assert exit_code_for(check.status) == 0
    assert envelope["scope"]["root"] == "."
    assert envelope["scope"]["targets"] == ["src", "tests"]
    assert envelope["scope"]["files_checked"] == 2
    assert envelope["scope"]["files_skipped"] == 0
    assert validation_errors(envelope) == []


@pytest.mark.ac("AC-12")
@pytest.mark.ac("AC-13")
@pytest.mark.ac("AC-15")
def test_real_subprocess_failure_stops_the_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_project(tmp_path.resolve())
    write(root / "app.py", "x = 1\n")
    monkeypatch.chdir(root)
    discovery = discover()
    later = PassingTier("tier1-ruff", "lint")

    check = run_pipeline(
        (
            ToolTier("tier0", python("print('boom'); raise SystemExit(1)"), timeout=30),
            later,
        ),
        context_for(discovery),
        scope_for(discovery),
    )

    envelope = check.to_envelope()
    assert check.status == "fail"
    assert exit_code_for(check.status) == 1
    assert [tier.status for tier in check.tiers] == ["fail", "skipped"]
    assert check.tiers[1].skipped_reason == "earlier_tier_failed"
    assert later.calls == []
    assert envelope["tiers"][0]["diagnostics"][0]["path"] == "app.py"
    assert envelope["tiers"][0]["diagnostics"][0]["message"] == "boom"
    assert validation_errors(envelope) == []


@pytest.mark.ac("AC-12")
@pytest.mark.ac("AC-13")
@pytest.mark.ac("AC-15")
def test_real_subprocess_timeout_becomes_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_project(tmp_path.resolve())
    write(root / "app.py", "x = 1\n")
    monkeypatch.chdir(root)
    discovery = discover()
    later = PassingTier("tier1-ruff", "lint")
    started = time.perf_counter()

    check = run_pipeline(
        (
            ToolTier("tier0", python("import threading; threading.Event().wait(10)"), timeout=0.5),
            later,
        ),
        context_for(discovery),
        scope_for(discovery),
    )

    elapsed = time.perf_counter() - started
    assert elapsed < 5
    assert check.status == "error"
    assert exit_code_for(check.status) == 2
    assert check.tiers[0].status == "error"
    assert check.tiers[0].skipped_reason == "internal error"
    assert "ToolTimeoutError" in check.tiers[0].meta["error"]
    assert later.calls == []
    assert validation_errors(check.to_envelope()) == []


@pytest.mark.ac("AC-12")
@pytest.mark.ac("AC-13")
@pytest.mark.ac("AC-15")
def test_missing_executable_becomes_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_project(tmp_path.resolve())
    write(root / "app.py", "x = 1\n")
    monkeypatch.chdir(root)
    discovery = discover()
    later = PassingTier("tier1-ruff", "lint")

    check = run_pipeline(
        (ToolTier("tier0", (MISSING_TOOL,), timeout=5), later),
        context_for(discovery),
        scope_for(discovery),
    )

    assert check.status == "error"
    assert exit_code_for(check.status) == 2
    assert check.tiers[0].status == "error"
    assert check.tiers[0].skipped_reason == "internal error"
    assert "ToolNotFoundError" in check.tiers[0].meta["error"]
    assert MISSING_TOOL in check.tiers[0].meta["error"]
    assert later.calls == []
    assert validation_errors(check.to_envelope()) == []


@pytest.mark.ac("AC-5")
@pytest.mark.ac("AC-13")
@pytest.mark.ac("AC-15")
def test_unicode_paths_survive_discovery_and_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_project(tmp_path.resolve() / "path with space-ü")
    write(root / "módulo.py", "x = 1\n")
    monkeypatch.chdir(root)
    discovery = discover()

    check = run_pipeline(
        (ToolTier("tier0", python("print('boom'); raise SystemExit(1)"), timeout=30),),
        context_for(discovery),
        scope_for(discovery),
    )

    envelope = check.to_envelope()
    assert envelope["scope"]["targets"] == ["."]
    assert envelope["tiers"][0]["diagnostics"][0]["path"] == "módulo.py"
    assert validation_errors(envelope) == []
    assert "\\" not in json.dumps(envelope, ensure_ascii=False)


def test_discovery_and_tier_warnings_are_aggregated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_project(tmp_path.resolve())
    (root / ".git").mkdir()
    write(root / "app.py", "x = 1\n")
    monkeypatch.chdir(root)
    discovery = discover()
    assert len(discovery.warnings) == 1
    warning = discovery.warnings[0]

    check = run_pipeline(
        (
            PassingTier("tier0", "syntax", warnings=(warning, "tier warning")),
            PassingTier("tier1-ruff", "lint", warnings=("tier warning",)),
        ),
        context_for(discovery),
        scope_for(discovery),
        initial_warnings=discovery.warnings,
    )

    assert check.status == "pass"
    assert check.warnings == (warning, "tier warning")
    assert check.to_envelope()["warnings"] == [warning, "tier warning"]
