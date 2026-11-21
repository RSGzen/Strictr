from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from strictr.core.models import CheckContext, Scope, TierResult
from strictr.core.pipeline import run_pipeline
from strictr.tiers.ast_tier import AstTier

pytestmark = pytest.mark.spec("003")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def context_for(
    root: Path, files: tuple[Path, ...], *, timeout: float | None = None
) -> CheckContext:
    return CheckContext(root=root, targets=(".",), files=files, timeout=timeout)


def scope_for(files: tuple[Path, ...]) -> Scope:
    return Scope(root=".", targets=(".",), files_checked=len(files))


@dataclass
class LaterTier:
    id: str
    name: str
    calls: list[CheckContext] = field(default_factory=list)

    def run(self, context: CheckContext) -> TierResult:
        self.calls.append(context)
        return TierResult(id=self.id, name=self.name, status="pass")


@pytest.mark.ac("AC-7")
def test_clean_python_files_pass(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source = write(root / "src" / "app.py", "x = 1\n")
    stub = write(root / "src" / "app.pyi", "def f() -> int: ...\n")

    result = AstTier().run(context_for(root, (source, stub)))

    assert result.id == "tier0"
    assert result.name == "syntax"
    assert result.status == "pass"
    assert result.diagnostics == ()
    assert result.skipped_reason is None
    assert result.tool is None
    assert result.duration_ms >= 0


@pytest.mark.ac("AC-7")
def test_syntax_error_reports_location_and_message(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source = write(root / "src" / "pkg" / "broken.py", "x = 1\ny = )\n")

    result = AstTier().run(context_for(root, (source,)))

    assert result.status == "fail"
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.tier == "tier0"
    assert diagnostic.source == "python"
    assert diagnostic.path == "src/pkg/broken.py"
    assert diagnostic.line == 2
    assert diagnostic.column == 5
    assert diagnostic.code == "syntax-error"
    assert diagnostic.severity == "error"
    assert diagnostic.message


@pytest.mark.ac("AC-7")
def test_every_file_is_parsed_after_a_syntax_error(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    first = write(root / "a.py", "def broken(:\n")
    ok = write(root / "ok.py", "x = 1\n")
    second = write(root / "z.py", "y = )\n")

    result = AstTier().run(context_for(root, (first, ok, second)))

    assert result.status == "fail"
    assert {diagnostic.path for diagnostic in result.diagnostics} == {"a.py", "z.py"}


@pytest.mark.ac("AC-7")
@pytest.mark.parametrize("filename", ["broken.py", "broken.pyi"])
def test_syntax_errors_cover_both_python_suffixes(tmp_path: Path, filename: str) -> None:
    root = tmp_path.resolve()
    source = write(root / filename, "def broken(:\n")

    result = AstTier().run(context_for(root, (source,)))

    assert result.status == "fail"
    assert [diagnostic.path for diagnostic in result.diagnostics] == [filename]


@pytest.mark.ac("AC-7")
def test_syntax_failure_stops_later_tiers(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    broken = write(root / "broken.py", "def broken(:\n")
    files = (broken,)
    later = LaterTier("tier1-ruff", "lint")

    check = run_pipeline((AstTier(), later), context_for(root, files), scope_for(files))

    assert check.status == "fail"
    assert [tier.status for tier in check.tiers] == ["fail", "skipped"]
    assert check.tiers[1].skipped_reason == "earlier_tier_failed"
    assert later.calls == []


@pytest.mark.ac("AC-7")
def test_exceeded_budget_is_an_error_and_stops_later_tiers(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source = write(root / "app.py", "x = 1\n")
    files = (source,)
    later = LaterTier("tier1-ruff", "lint")

    check = run_pipeline(
        (AstTier(), later), context_for(root, files, timeout=0.0), scope_for(files)
    )

    result = check.tiers[0]
    assert result.status == "error"
    assert result.skipped_reason == "tool timeout"
    assert result.diagnostics == ()
    assert "budget" in result.meta["error"].lower()
    assert check.status == "error"
    assert check.tiers[1].status == "skipped"
    assert check.tiers[1].skipped_reason == "earlier_tier_failed"
    assert later.calls == []
