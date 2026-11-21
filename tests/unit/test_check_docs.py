from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("003")

ROOT = Path(__file__).resolve().parents[2]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.mark.ac("AC-16")
def test_readme_documents_check_command() -> None:
    readme = text("README.md")
    for phrase in (
        "strictr check",
        "python -m strictr check",
        "strictr --version",
        "--json",
        "--type-checker",
        "--timeout",
    ):
        assert phrase in readme, phrase
    assert "Exit code" in readme


@pytest.mark.ac("AC-16")
def test_changelog_records_check_command() -> None:
    changelog = text("CHANGELOG.md")
    assert "strictr check" in changelog
    assert "003-check-command" in changelog


@pytest.mark.ac("AC-16")
def test_agents_documents_check_command() -> None:
    agents = text("AGENTS.md")
    assert "strictr check" in agents
    assert "There is no `strictr` CLI yet" not in agents


@pytest.mark.ac("AC-16")
def test_system_overview_records_spec_003_implementation() -> None:
    overview = text("docs/architecture/system-overview.md")
    assert "003-check-command" in overview
    assert "implements the architecture" in overview
