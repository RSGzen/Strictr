from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("001")

ROOT = Path(__file__).resolve().parents[2]


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.mark.ac("AC-1")
def test_vision_has_required_sections() -> None:
    vision = text("docs/product/vision.md")
    for heading in (
        "## Positioning",
        "## Problem",
        "## Evidence and assumptions",
        "## Target users",
        "## Current alternatives and gap",
        "## Product principles",
        "## Decisions locked",
        "## Goals",
        "## Non-goals (locked for v0.1)",
        "## Scope and phases",
        "## Adoption path",
        "## Risks",
        "## Open questions",
        "## Success and kill criteria",
    ):
        assert heading in vision, heading


@pytest.mark.ac("AC-1")
def test_vision_locks_user_trust_and_scope() -> None:
    vision = text("docs/product/vision.md")
    assert "Agent harness builders and AI-heavy solo developers" in vision
    assert "local-only execution" in vision
    assert "not a sandbox" in vision
    assert "Tier 0" in vision
    assert "Tier 1" in vision
    assert "compact pytest" in vision
    assert "No LLM-as-a-judge" in vision
    assert "No auto-fix" in vision
    assert "No multi-language support" in vision
    assert "No test selection" in vision
    assert "No MCP server in v0.1" in vision


@pytest.mark.ac("AC-2")
def test_evaluation_has_required_sections() -> None:
    evaluation = text("docs/product/evaluation.md")
    for heading in (
        "## Evaluation questions",
        "## Metrics",
        "## Baseline configurations",
        "## Workloads and corpus",
        "## Measurement protocol",
        "## Conditional targets",
        "## Kill criteria",
        "## Public benchmark caveats",
        "## Reporting template",
    ):
        assert heading in evaluation, heading


@pytest.mark.ac("AC-2")
def test_targets_are_conditional() -> None:
    evaluation = text("docs/product/evaluation.md")
    assert "conditional hypothesis" in evaluation
    assert "These are initial hypotheses" in evaluation
    assert "p95" in evaluation
    assert "mutation" in evaluation
    assert "false pass" in evaluation.lower()


@pytest.mark.ac("AC-3")
def test_entry_points_use_new_numbering() -> None:
    agents = text("AGENTS.md")
    architecture = text("docs/architecture/system-overview.md")
    readme = text("README.md")

    for document in (agents, architecture):
        assert "003-check-command" in document
        assert "001-check-command" not in document

    assert "003-check-command" in readme or "first product slice" in readme


@pytest.mark.ac("AC-3")
def test_entry_points_link_product_docs() -> None:
    agents = text("AGENTS.md")
    readme = text("README.md")

    for document in (agents, readme):
        assert "docs/product/vision.md" in document
        assert "docs/product/evaluation.md" in document


@pytest.mark.ac("AC-4")
def test_changelog_records_product_discovery() -> None:
    changelog = text("CHANGELOG.md")
    assert "product discovery" in changelog.lower()
    assert "docs/product/vision.md" in changelog
    assert "docs/product/evaluation.md" in changelog


@pytest.mark.ac("AC-4")
def test_product_doc_links_resolve() -> None:
    for relative in ("docs/product/vision.md", "docs/product/evaluation.md"):
        document = ROOT / relative
        body = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (document.parent / target.split("#", 1)[0]).resolve()
            assert resolved.exists(), f"{relative} -> {target}"
