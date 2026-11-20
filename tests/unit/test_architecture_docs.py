from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("002")

ROOT = Path(__file__).resolve().parents[2]

ADRS = (
    "docs/adr/0002-verification-pipeline.md",
    "docs/adr/0003-subprocess-tool-execution.md",
    "docs/adr/0004-verification-contract-and-statuses.md",
    "docs/adr/0005-type-checker-selection.md",
    "docs/adr/0006-pytest-integration.md",
    "docs/adr/0007-trust-boundary-and-timeouts.md",
)


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


@pytest.mark.ac("AC-1")
def test_system_overview_has_required_sections() -> None:
    overview = text("docs/architecture/system-overview.md")
    for heading in (
        "## Scope",
        "## C4 Level 1 — Context",
        "## C4 Level 2 — Components",
        "## Module boundaries",
        "## Data flow",
        "## Tier model",
        "## Status and exit model",
        "## Tool execution",
        "## Type-checker selection",
        "## Pytest integration",
        "## Trust boundary",
        "## Performance model",
        "## Failure modes",
        "## Security and redaction",
        "## Testing",
        "## Extension seams",
        "## Out of scope",
        "## ADR index",
    ):
        assert heading in overview, heading


@pytest.mark.ac("AC-1")
def test_module_boundaries_and_data_flow() -> None:
    overview = text("docs/architecture/system-overview.md")
    assert "core" in overview
    assert "Must not import" in overview
    assert "Tier 0" in overview
    assert "Tier 1a" in overview
    assert "Tier 1b" in overview
    assert "Tier 2" in overview
    assert "Fail-fast" in overview
    assert "git ls-files" in overview


@pytest.mark.ac("AC-2")
def test_contract_has_required_sections() -> None:
    contract = text("docs/architecture/verification-contract.md")
    for heading in (
        "## Top-level envelope",
        "## Status model",
        "## Scope ledger",
        "## Diagnostic object",
        "## Tier result",
        "## Truncation and limits",
        "## Ordering",
        "## Human output",
        "## JSON output",
        "## Versioning",
        "## Trust metadata",
        "## Examples",
    ):
        assert heading in contract, heading


@pytest.mark.ac("AC-2")
def test_contract_status_and_exit_model() -> None:
    contract = text("docs/architecture/verification-contract.md")
    assert "schema_version" in contract
    assert "`pass`" in contract
    assert "`fail`" in contract
    assert "`partial`" in contract
    assert "`error`" in contract
    assert "Exit code" in contract
    assert "trust.sandboxed" in contract
    assert "2,000 characters" in contract
    assert "20" in contract


@pytest.mark.ac("AC-3")
def test_six_adrs_exist_with_required_sections() -> None:
    assert len(ADRS) == 6
    for relative in ADRS:
        document = text(relative)
        for heading in ("## Context", "## Decision", "## Consequences", "## Confirmation"):
            assert heading in document, f"{relative} missing {heading}"


@pytest.mark.ac("AC-3")
def test_architecture_links_adrs() -> None:
    overview = text("docs/architecture/system-overview.md")
    for relative in ADRS:
        assert relative.rsplit("/", 1)[-1] in overview, relative


@pytest.mark.ac("AC-4")
def test_execution_policies_documented() -> None:
    overview = text("docs/architecture/system-overview.md")
    contract = text("docs/architecture/verification-contract.md")
    for phrase in (
        "subprocess",
        "mypy",
        "pyright",
        "JUnit",
        "timeout",
        "process tree",
        "Windows",
    ):
        assert phrase in overview, phrase
    assert "not a sandbox" in overview
    assert "sandboxed" in contract


@pytest.mark.ac("AC-5")
def test_entry_points_link_architecture_docs() -> None:
    agents = text("AGENTS.md")
    readme = text("README.md")
    for document in (agents, readme):
        assert "docs/architecture/verification-contract.md" in document
        assert "docs/adr/" in document
