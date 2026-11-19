from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.mark.ac("AC-1")
def test_governance_documents_exist_and_have_required_sections() -> None:
    for relative in (
        "AGENTS.md",
        "docs/constitution.md",
        "docs/architecture/system-overview.md",
        "docs/adr/0001-python-toolchain.md",
    ):
        assert (ROOT / relative).is_file(), relative

    assert "## Workflow" in text("AGENTS.md")
    assert "## Definition of Done" in text("AGENTS.md")
    assert "## I. Specification before code" in text("docs/constitution.md")
    assert "## Amendment process" in text("docs/constitution.md")
    assert "## Trust boundaries" in text("docs/architecture/system-overview.md")
    assert "## Decision" in text("docs/adr/0001-python-toolchain.md")


@pytest.mark.ac("AC-2")
def test_spec_templates_and_bootstrap_spec_exist() -> None:
    for relative in ("specs/_templates/spec.md", "specs/_templates/blueprint.md"):
        assert (ROOT / relative).is_file(), relative

    spec = next(
        (
            path
            for path in (
                ROOT / "specs/active/000-sdd-bootstrap/spec.md",
                ROOT / "specs/archive/000-sdd-bootstrap/spec.md",
            )
            if path.is_file()
        ),
        None,
    )
    blueprint = next(
        (
            path
            for path in (
                ROOT / "specs/active/000-sdd-bootstrap/blueprint.md",
                ROOT / "specs/archive/000-sdd-bootstrap/blueprint.md",
            )
            if path.is_file()
        ),
        None,
    )

    assert spec is not None
    assert blueprint is not None
    assert "AC-1" in spec.read_text(encoding="utf-8")
    assert "## Test plan" in blueprint.read_text(encoding="utf-8")


@pytest.mark.ac("AC-4")
def test_project_config_and_ci_exist() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    assert project["project"]["name"] == "strictr"
    assert (ROOT / "uv.lock").is_file()

    workflow = text(".github/workflows/ci.yml")
    assert "quality" in workflow
    assert "traceability" in workflow
    assert "windows-latest" in workflow
    assert "uv sync --locked" in workflow
    assert "pull_request_target" not in workflow


@pytest.mark.ac("AC-5")
def test_pr_template_hook_and_setup_checklist_exist() -> None:
    assert (ROOT / ".github/pull_request_template.md").is_file()
    assert "## Spec" in text(".github/pull_request_template.md")
    assert "Spec:" in text(".githooks/commit-msg")
    assert "interpret-trailers" in text(".githooks/commit-msg")
    assert "Require a pull request" in text("docs/repo-setup.md")
    assert "Dependabot" in text("docs/repo-setup.md")


@pytest.mark.ac("AC-6")
def test_testing_guide_covers_required_topics() -> None:
    guide = text("docs/testing.md")
    assert "## Layers" in guide
    assert "AC" in guide
    assert "## Fixtures" in guide
    assert "## Failure modes" in guide
    assert "## Determinism" in guide


@pytest.mark.ac("AC-7")
def test_readme_describes_status_and_quickstart() -> None:
    readme = text("README.md")
    assert "## Status" in readme
    assert "## Quick start" in readme
    assert "## Repository map" in readme
    assert "docs/testing.md" in readme
