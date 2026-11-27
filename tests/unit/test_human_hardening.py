from __future__ import annotations

import pytest

from strictr.core.models import (
    CheckResult,
    Diagnostic,
    Environment,
    OverallStatus,
    Scope,
    TierResult,
    Timings,
    ToolInfo,
)
from strictr.output.human import render_human

pytestmark = pytest.mark.spec("004")


def make_result(
    *,
    status: OverallStatus = "pass",
    files_checked: int = 1,
    files_skipped: int = 0,
    tiers: tuple[TierResult, ...] = (),
) -> CheckResult:
    return CheckResult(
        tool=ToolInfo(name="strictr", version="0.0.0"),
        status=status,
        scope=Scope(
            root=".",
            targets=("app.py",),
            files_checked=files_checked,
            files_skipped=files_skipped,
        ),
        tiers=tiers,
        timings=Timings(total_ms=1200),
        environment=Environment(python="3.12", platform="linux", root="."),
    )


def make_diagnostic(*, code: str = "TYPE001", message: str = "bad type") -> Diagnostic:
    return Diagnostic(
        tier="tier1-types",
        source="pyright",
        path="app.py",
        line=1,
        column=1,
        code=code,
        severity="error",
        message=message,
    )


@pytest.mark.ac("AC-4")
def test_human_reports_skipped_files() -> None:
    text = render_human(make_result(files_checked=3, files_skipped=1))

    assert text.splitlines()[0] == "PASS  3 files checked, 1 skipped in 1200 ms"


@pytest.mark.ac("AC-4")
def test_human_zero_skipped_keeps_status_line() -> None:
    status_line = render_human(make_result(files_checked=3, files_skipped=0)).splitlines()[0]

    assert status_line == "PASS  3 files checked in 1200 ms"
    assert "skipped" not in status_line


@pytest.mark.ac("AC-4")
def test_human_error_shows_meta_error() -> None:
    tier = TierResult(
        id="tier1-types",
        name="types",
        status="error",
        skipped_reason="pyright not found",
        meta={"error": "pyright is configured but not available\nsecond line"},
    )

    text = render_human(make_result(status="error", tiers=(tier,)))

    assert "  tier1-types: pyright is configured but not available" in text.splitlines()
    assert "second line" not in text


@pytest.mark.ac("AC-4")
def test_human_error_meta_error_equal_to_reason_is_not_duplicated() -> None:
    tier = TierResult(
        id="tier1-types",
        name="types",
        status="error",
        skipped_reason="pyright not found",
        meta={"error": "pyright not found"},
    )

    text = render_human(make_result(status="error", tiers=(tier,)))
    lines = text.splitlines()

    assert "  tier1-types: pyright not found" not in lines
    assert sum(line.count("pyright not found") for line in lines) == 1


@pytest.mark.ac("AC-4")
def test_human_error_with_diagnostics_shows_diagnostics() -> None:
    tier = TierResult(
        id="tier1-types",
        name="types",
        status="error",
        skipped_reason="tool failed",
        diagnostics=(make_diagnostic(),),
        meta={"error": "tool failed details"},
    )

    lines = render_human(make_result(status="error", tiers=(tier,))).splitlines()

    assert "  app.py:1:1: TYPE001: bad type" in lines
    assert "  tier1-types: tool failed details" not in lines


@pytest.mark.ac("AC-4")
def test_human_error_truncation_notice() -> None:
    many = tuple(
        make_diagnostic(code=f"TYPE00{index}", message=f"bad type {index}") for index in range(6)
    )
    count_tier = TierResult(
        id="tier1-types",
        name="types",
        status="error",
        diagnostics=many,
    )

    count_lines = render_human(make_result(status="error", tiers=(count_tier,))).splitlines()

    assert "  ... 1 more diagnostics (use --json)" in count_lines

    truncated_tier = TierResult(
        id="tier1-types",
        name="types",
        status="error",
        diagnostics=(make_diagnostic(),),
        meta={"truncated": True},
    )

    truncated_lines = render_human(
        make_result(status="error", tiers=(truncated_tier,))
    ).splitlines()

    assert "  ... some text truncated" in truncated_lines
