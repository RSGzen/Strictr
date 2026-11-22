from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from strictr.core.models import (
    CheckResult,
    Diagnostic,
    Environment,
    Scope,
    TierResult,
    Timings,
    ToolInfo,
)
from strictr.output.human import render_human
from strictr.output.json_output import render_json

pytestmark = pytest.mark.spec("004")

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "verification-contract.schema.json"
)

# Surrogateescape decodes undecodable POSIX filename bytes to lone surrogates.
UNDECODABLE_PATH = "broken_\udcff.py"
UNICODE_PATH = "src/módulo.py"


def make_result() -> CheckResult:
    diagnostic = Diagnostic(
        tier="tier0",
        source="python",
        path=UNDECODABLE_PATH,
        line=1,
        column=1,
        code="syntax-error",
        severity="error",
        message="invalid syntax",
    )
    return CheckResult(
        tool=ToolInfo(name="strictr", version="0.0.0"),
        status="fail",
        scope=Scope(
            root=".",
            targets=(UNDECODABLE_PATH, UNICODE_PATH),
            files_checked=2,
        ),
        tiers=(
            TierResult(
                id="tier0",
                name="syntax",
                status="fail",
                diagnostics=(diagnostic,),
            ),
        ),
        timings=Timings(total_ms=10),
        environment=Environment(python="3.12", platform="linux", root="."),
    )


def validation_errors(document: Any) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(document)]


@pytest.mark.ac("AC-3")
def test_non_utf8_json_render() -> None:
    text = render_json(make_result())

    assert text.endswith("\n")
    assert text.count("\n") == 1
    payload = text.encode("utf-8")
    assert b"\\udcff" in payload.lower()
    assert UNICODE_PATH in text
    assert "\\u00f3" not in text.lower()

    document = json.loads(payload.decode("utf-8"))
    assert document["scope"]["targets"] == [UNDECODABLE_PATH, UNICODE_PATH]
    assert document["tiers"][0]["diagnostics"][0]["path"] == UNDECODABLE_PATH
    assert validation_errors(document) == []


@pytest.mark.ac("AC-3")
def test_non_utf8_human_render() -> None:
    payload = render_human(make_result()).encode("utf-8")

    assert b"syntax-error" in payload
