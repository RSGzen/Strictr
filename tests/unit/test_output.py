from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from strictr.core.models import (
    TRUST_WARNING,
    CheckResult,
    Diagnostic,
    Environment,
    OverallStatus,
    Scope,
    TierResult,
    TierStatus,
    Timings,
    ToolInfo,
)
from strictr.output.human import render_human, render_stderr
from strictr.output.json_output import render_json

pytestmark = pytest.mark.spec("003")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "verification-contract.schema.json"
)


def make_diagnostic(
    path: str = "src/app.py",
    *,
    line: int = 1,
    column: int = 1,
    code: str = "E001",
    message: str = "finding",
) -> Diagnostic:
    return Diagnostic(
        tier="tier1-ruff",
        source="ruff",
        path=path,
        line=line,
        column=column,
        code=code,
        severity="error",
        message=message,
    )


def make_tier(
    tier_id: str = "tier0",
    name: str = "syntax",
    status: TierStatus = "pass",
    *,
    duration_ms: int = 0,
    diagnostics: tuple[Diagnostic, ...] = (),
    skipped_reason: str | None = None,
    meta: dict[str, Any] | None = None,
) -> TierResult:
    return TierResult(
        id=tier_id,
        name=name,
        status=status,
        duration_ms=duration_ms,
        diagnostics=diagnostics,
        skipped_reason=skipped_reason,
        meta={} if meta is None else meta,
    )


def make_result(
    *tiers: TierResult,
    status: OverallStatus = "pass",
    warnings: tuple[str, ...] = (),
    targets: tuple[str, ...] = (".",),
    files_checked: int = 3,
    total_ms: int = 1200,
) -> CheckResult:
    return CheckResult(
        tool=ToolInfo(name="strictr", version="0.0.0"),
        status=status,
        scope=Scope(root=".", targets=targets, files_checked=files_checked),
        tiers=tiers,
        timings=Timings(total_ms=total_ms),
        environment=Environment(python="3.12", platform="test", root="."),
        warnings=warnings,
    )


def pipeline_result() -> CheckResult:
    return make_result(
        make_tier(duration_ms=12),
        make_tier("tier1-ruff", "lint", duration_ms=84),
    )


def failing_tiers() -> tuple[TierResult, ...]:
    diagnostics = tuple(
        make_diagnostic(line=index, code=f"E00{index}", message=f"finding {index}")
        for index in range(1, 8)
    )
    return (
        make_tier(duration_ms=10),
        make_tier(
            "tier1-ruff",
            "lint",
            "fail",
            duration_ms=80,
            diagnostics=diagnostics,
        ),
        make_tier(
            "tier1-types",
            "types",
            "skipped",
            skipped_reason="earlier_tier_failed",
        ),
        make_tier(
            "tier2-pytest",
            "tests",
            "skipped",
            skipped_reason="earlier_tier_failed",
        ),
    )


@pytest.mark.ac("AC-2")
def test_json_output_is_one_compact_newline_terminated_object() -> None:
    result = pipeline_result()

    text = render_json(result)

    assert (
        text == json.dumps(result.to_envelope(), ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    assert text.count("\n") == 1


@pytest.mark.ac("AC-2")
def test_json_output_round_trips_utf8_paths() -> None:
    result = make_result(make_tier(), targets=("src/ü",), files_checked=1)

    text = render_json(result)

    document = json.loads(text.encode("utf-8").decode("utf-8"))
    assert document["scope"]["targets"] == ["src/ü"]


@pytest.mark.ac("AC-2")
def test_json_output_validates_against_the_contract_schema() -> None:
    result = make_result(
        make_tier(duration_ms=12),
        make_tier("tier1-ruff", "lint", duration_ms=84),
        make_tier("tier1-types", "types"),
        make_tier("tier2-pytest", "tests"),
    )
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    document = json.loads(render_json(result))

    errors = [error.message for error in Draft202012Validator(schema).iter_errors(document)]
    assert errors == []


@pytest.mark.ac("AC-3")
def test_human_pass_shows_status_scope_and_tier_lines() -> None:
    text = render_human(pipeline_result())

    assert text == (
        "PASS  3 files checked in 1200 ms\n"
        "  tier0        pass      12 ms\n"
        "  tier1-ruff   pass      84 ms\n"
    )
    assert TRUST_WARNING not in text


@pytest.mark.ac("AC-3")
def test_human_failure_shows_at_most_five_diagnostics() -> None:
    result = make_result(*failing_tiers(), status="fail", total_ms=900)

    lines = render_human(result).splitlines()

    assert lines[:4] == [
        "FAIL  3 files checked in 900 ms",
        "  tier0        pass      10 ms",
        "  tier1-ruff   fail      80 ms",
        "  tier1-types  skipped    0 ms  earlier_tier_failed",
    ]
    assert lines[4] == "  tier2-pytest skipped    0 ms  earlier_tier_failed"
    assert lines[5:10] == [
        "  src/app.py:1:1: E001: finding 1",
        "  src/app.py:2:1: E002: finding 2",
        "  src/app.py:3:1: E003: finding 3",
        "  src/app.py:4:1: E004: finding 4",
        "  src/app.py:5:1: E005: finding 5",
    ]
    assert lines[10] == "  ... 2 more diagnostics (use --json)"


@pytest.mark.ac("AC-3")
def test_human_partial_shows_the_skipped_reason() -> None:
    result = make_result(
        make_tier(duration_ms=10),
        make_tier("tier1-ruff", "lint", duration_ms=20),
        make_tier(
            "tier1-types",
            "types",
            "skipped",
            skipped_reason="no type checker found",
        ),
        status="partial",
        total_ms=500,
    )

    text = render_human(result)

    assert text == (
        "PARTIAL  3 files checked in 500 ms\n"
        "  tier0        pass      10 ms\n"
        "  tier1-ruff   pass      20 ms\n"
        "  tier1-types  skipped    0 ms  no type checker found\n"
    )


@pytest.mark.ac("AC-3")
def test_human_warnings_and_trust_warning_go_to_stderr() -> None:
    result = make_result(
        make_tier(),
        make_tier("tier1-ruff", "lint"),
        warnings=("discovery warning", "tier warning"),
    )

    stderr = render_stderr(result, include_trust=True)

    assert stderr == (
        "warning: discovery warning\n"
        "warning: tier warning\n"
        "warning: Local execution; not a security boundary.\n"
    )
    assert stderr.count(TRUST_WARNING) == 1
    assert "discovery warning" not in render_human(result)
    assert TRUST_WARNING not in render_human(result)


@pytest.mark.ac("AC-2")
def test_json_mode_writes_warnings_to_stderr_without_the_trust_warning() -> None:
    result = make_result(
        make_tier(),
        make_tier("tier1-ruff", "lint"),
        warnings=("discovery warning", "tier warning"),
    )

    stderr = render_stderr(result, include_trust=False)

    assert stderr == "warning: discovery warning\nwarning: tier warning\n"
    assert TRUST_WARNING not in stderr
    assert render_stderr(make_result(), include_trust=False) == ""


@pytest.mark.ac("AC-14")
def test_json_output_keeps_trust_and_truncation_metadata() -> None:
    diagnostics = tuple(make_diagnostic(path=f"{index:02d}.py") for index in range(20))
    result = make_result(
        make_tier(duration_ms=10),
        make_tier(
            "tier1-ruff",
            "lint",
            "fail",
            diagnostics=diagnostics,
            meta={"truncated": True, "total_diagnostics": 25},
        ),
        make_tier(
            "tier1-types",
            "types",
            "skipped",
            skipped_reason="earlier_tier_failed",
        ),
        make_tier(
            "tier2-pytest",
            "tests",
            "skipped",
            skipped_reason="earlier_tier_failed",
        ),
        status="fail",
        warnings=("warning one",),
    )

    document = json.loads(render_json(result))

    assert document["status"] == "fail"
    assert document["trust"] == {"sandboxed": False, "warning": TRUST_WARNING}
    assert document["warnings"] == ["warning one"]
    assert len(document["tiers"][1]["diagnostics"]) == 20
    assert document["tiers"][1]["meta"] == {"truncated": True, "total_diagnostics": 25}


@pytest.mark.ac("AC-14")
def test_human_count_truncation_names_the_hidden_diagnostics() -> None:
    diagnostics = tuple(make_diagnostic(path=f"{index:02d}.py") for index in range(20))
    result = make_result(
        make_tier(duration_ms=10),
        make_tier(
            "tier1-ruff",
            "lint",
            "fail",
            diagnostics=diagnostics,
            meta={"truncated": True, "total_diagnostics": 25},
        ),
        status="fail",
        total_ms=900,
    )

    lines = render_human(result).splitlines()

    assert lines[-1] == "  ... 20 more diagnostics (use --json)"
    assert not any("some text truncated" in line for line in lines)


@pytest.mark.ac("AC-14")
def test_human_text_truncation_is_visible() -> None:
    result = make_result(
        make_tier(duration_ms=10),
        make_tier(
            "tier1-ruff",
            "lint",
            "fail",
            diagnostics=(make_diagnostic(message="short [truncated]"),),
            meta={"truncated": True},
        ),
        status="fail",
        total_ms=900,
    )

    lines = render_human(result).splitlines()

    assert lines[-1] == "  ... some text truncated"
    assert not any("more diagnostics" in line for line in lines)
