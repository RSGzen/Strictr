from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from strictr.core.models import (
    TRUST_WARNING,
    CheckContext,
    CheckResult,
    Diagnostic,
    Environment,
    OverallStatus,
    Scope,
    Severity,
    TierResult,
    TierStatus,
    Timings,
    ToolInfo,
    exit_code_for,
)
from strictr.core.paths import relative_posix
from strictr.core.pipeline import run_pipeline
from strictr.core.text import ERROR_LIMIT, MESSAGE_LIMIT, TRUNCATION_MARKER, cap_text, redact

pytestmark = pytest.mark.spec("003")


@dataclass
class FakeTier:
    id: str
    name: str
    result: TierResult | None = None
    error: BaseException | None = None
    calls: list[CheckContext] = field(default_factory=list)

    def run(self, context: CheckContext) -> TierResult:
        self.calls.append(context)
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("fake tier needs a result or an error")
        return self.result


def make_scope() -> Scope:
    return Scope(root=".", targets=(".",))


def diagnostic(
    path: str = "a.py",
    line: int = 1,
    column: int = 1,
    code: str = "E001",
    message: str = "message",
    *,
    tier: str = "tier0",
    severity: Severity = "error",
) -> Diagnostic:
    return Diagnostic(
        tier=tier,
        source="test",
        path=path,
        line=line,
        column=column,
        code=code,
        severity=severity,
        message=message,
    )


def fake(
    tier_id: str,
    name: str,
    status: TierStatus = "pass",
    *,
    diagnostics: tuple[Diagnostic, ...] = (),
    skipped_reason: str | None = None,
    meta: dict[str, Any] | None = None,
    warnings: tuple[str, ...] = (),
) -> FakeTier:
    return FakeTier(
        id=tier_id,
        name=name,
        result=TierResult(
            id=tier_id,
            name=name,
            status=status,
            diagnostics=diagnostics,
            skipped_reason=skipped_reason,
            meta={} if meta is None else meta,
            warnings=warnings,
        ),
    )


@pytest.fixture
def context(tmp_path: Path) -> CheckContext:
    return CheckContext(root=tmp_path, targets=(".",), files=())


@pytest.mark.ac("AC-4")
@pytest.mark.parametrize(
    ("status", "expected"),
    [("pass", 0), ("fail", 1), ("partial", 2), ("error", 2)],
)
def test_exit_code_follows_status(status: OverallStatus, expected: int) -> None:
    assert exit_code_for(status) == expected


@pytest.mark.ac("AC-12")
def test_pipeline_runs_every_tier_in_order(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint"),
        fake("tier1-types", "types"),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert [tier.id for tier in check.tiers] == [tier.id for tier in tiers]
    assert [tier.status for tier in check.tiers] == ["pass", "pass", "pass", "pass"]
    assert check.status == "pass"
    assert all(len(tier.calls) == 1 for tier in tiers)


@pytest.mark.ac("AC-12")
def test_pipeline_stops_after_first_fail(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake(
            "tier1-ruff",
            "lint",
            "fail",
            diagnostics=(diagnostic(path="src/app.py", tier="tier1-ruff"),),
        ),
        fake("tier1-types", "types"),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert [tier.status for tier in check.tiers] == ["pass", "fail", "skipped", "skipped"]
    assert check.status == "fail"
    assert [tier.skipped_reason for tier in check.tiers[2:]] == [
        "earlier_tier_failed",
        "earlier_tier_failed",
    ]
    assert tiers[2].calls == []
    assert tiers[3].calls == []


@pytest.mark.ac("AC-12")
def test_pipeline_stops_after_first_error(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint", "error", skipped_reason="ruff not found"),
        fake("tier1-types", "types"),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert [tier.status for tier in check.tiers] == ["pass", "error", "skipped", "skipped"]
    assert check.status == "error"
    assert [tier.skipped_reason for tier in check.tiers[2:]] == [
        "earlier_tier_failed",
        "earlier_tier_failed",
    ]
    assert tiers[2].calls == []
    assert tiers[3].calls == []


@pytest.mark.ac("AC-12")
def test_pipeline_required_skip_is_partial(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint"),
        fake("tier1-types", "types", "skipped", skipped_reason="no type checker found"),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert check.status == "partial"
    assert check.tiers[2].skipped_reason == "no type checker found"
    assert len(tiers[3].calls) == 1


@pytest.mark.ac("AC-12")
def test_pipeline_disabled_by_user_is_not_partial(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint"),
        fake("tier1-types", "types", "skipped", skipped_reason="disabled_by_user"),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert check.status == "pass"


@pytest.mark.ac("AC-12")
def test_pipeline_no_tests_collected_is_not_partial(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint"),
        fake("tier1-types", "types"),
        fake("tier2-pytest", "tests", "skipped", skipped_reason="no tests collected"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert check.status == "pass"


@pytest.mark.ac("AC-12")
def test_pipeline_keeps_fail_above_partial(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint"),
        fake("tier1-types", "types", "skipped", skipped_reason="no type checker found"),
        fake(
            "tier2-pytest",
            "tests",
            "fail",
            diagnostics=(diagnostic(path="tests/test_app.py", tier="tier2-pytest"),),
        ),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert check.status == "fail"


@pytest.mark.ac("AC-12")
def test_pipeline_internal_exception_is_error(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax"),
        fake("tier1-ruff", "lint"),
        FakeTier("tier1-types", "types", error=RuntimeError("boom")),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert [tier.status for tier in check.tiers] == ["pass", "pass", "error", "skipped"]
    assert check.status == "error"
    assert check.tiers[2].skipped_reason == "internal error"
    assert "boom" in str(check.tiers[2].meta["error"])
    assert check.tiers[3].skipped_reason == "earlier_tier_failed"
    assert tiers[3].calls == []


@pytest.mark.ac("AC-12")
def test_pipeline_does_not_catch_base_exception(context: CheckContext) -> None:
    tiers = [FakeTier("tier0", "syntax", error=KeyboardInterrupt())]

    with pytest.raises(KeyboardInterrupt):
        run_pipeline(tiers, context, make_scope())


@pytest.mark.ac("AC-12")
def test_pipeline_copies_only_pytest_test_counts(context: CheckContext) -> None:
    tiers = [
        fake(
            "tier0",
            "syntax",
            meta={"tests_collected": 99, "tests_run": 99, "tests_skipped": 99},
        ),
        fake("tier1-ruff", "lint"),
        fake("tier1-types", "types"),
        fake(
            "tier2-pytest",
            "tests",
            meta={"tests_collected": 5, "tests_run": 4, "tests_skipped": 1},
        ),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert (
        check.scope.tests_collected,
        check.scope.tests_run,
        check.scope.tests_skipped,
    ) == (5, 4, 1)
    assert check.scope.root == "."
    assert check.scope.targets == (".",)


@pytest.mark.ac("AC-12")
def test_pipeline_aggregates_warnings_in_order(context: CheckContext) -> None:
    tiers = [
        fake("tier0", "syntax", warnings=("shared", "tier0 warning")),
        fake("tier1-ruff", "lint", warnings=("ruff warning",)),
        fake("tier1-types", "types"),
        fake("tier2-pytest", "tests"),
    ]

    check = run_pipeline(
        tiers,
        context,
        make_scope(),
        initial_warnings=("discovery warning", "shared"),
    )

    assert check.warnings == (
        "discovery warning",
        "shared",
        "tier0 warning",
        "ruff warning",
    )
    assert check.status == "pass"


@pytest.mark.ac("AC-14")
def test_diagnostics_ordered_deterministically(context: CheckContext) -> None:
    tiers = [
        fake(
            "tier0",
            "syntax",
            "fail",
            diagnostics=(
                diagnostic(path="b.py", code="E", message="b1"),
                diagnostic(path="a.py", line=2, code="E", message="a2"),
                diagnostic(path="a.py", line=1, column=2, code="E", message="a1c2"),
                diagnostic(path="a.py", line=1, column=1, code="Z", message="z"),
                diagnostic(path="a.py", line=1, column=1, code="A", message="b"),
                diagnostic(path="a.py", line=1, column=1, code="A", message="a"),
            ),
        ),
    ]

    check = run_pipeline(tiers, context, make_scope())

    assert [item.message for item in check.tiers[0].diagnostics] == [
        "a",
        "b",
        "z",
        "a1c2",
        "a2",
        "b1",
    ]


@pytest.mark.ac("AC-14")
def test_diagnostics_capped_at_twenty(context: CheckContext) -> None:
    diagnostics = tuple(
        diagnostic(path=f"{index:02d}.py", message=f"m{index}") for index in reversed(range(25))
    )
    tiers = [fake("tier0", "syntax", "fail", diagnostics=diagnostics)]

    result = run_pipeline(tiers, context, make_scope()).tiers[0]

    assert len(result.diagnostics) == 20
    assert [item.path for item in result.diagnostics] == [f"{index:02d}.py" for index in range(20)]
    assert result.meta["truncated"] is True
    assert result.meta["total_diagnostics"] == 25


@pytest.mark.ac("AC-14")
def test_message_capped_with_marker(context: CheckContext) -> None:
    tiers = [
        fake(
            "tier0",
            "syntax",
            "fail",
            diagnostics=(diagnostic(message="x" * (MESSAGE_LIMIT + 500)),),
        ),
    ]

    result = run_pipeline(tiers, context, make_scope()).tiers[0]

    message = result.diagnostics[0].message
    assert len(message) == MESSAGE_LIMIT
    assert message.endswith(TRUNCATION_MARKER)
    assert result.meta["truncated"] is True
    assert "total_diagnostics" not in result.meta


@pytest.mark.ac("AC-14")
def test_meta_error_capped_with_marker(context: CheckContext) -> None:
    tiers = [
        fake(
            "tier0",
            "syntax",
            "error",
            skipped_reason="tool failed",
            meta={"error": "e" * (ERROR_LIMIT + 200)},
        ),
    ]

    result = run_pipeline(tiers, context, make_scope()).tiers[0]

    error = result.meta["error"]
    assert isinstance(error, str)
    assert len(error) == ERROR_LIMIT
    assert error.endswith(TRUNCATION_MARKER)
    assert result.meta["truncated"] is True


@pytest.mark.ac("AC-14")
def test_pipeline_redacts_messages_and_meta_error(context: CheckContext) -> None:
    secret = "sk-" + "a" * 40
    tiers = [
        fake(
            "tier0",
            "syntax",
            "error",
            diagnostics=(diagnostic(message=f"token {secret}"),),
            skipped_reason="tool failed",
            meta={"error": f"token {secret}"},
        ),
    ]

    result = run_pipeline(tiers, context, make_scope()).tiers[0]

    assert secret not in result.diagnostics[0].message
    assert secret not in str(result.meta["error"])
    assert "[REDACTED]" in result.diagnostics[0].message
    assert "[REDACTED]" in str(result.meta["error"])


@pytest.mark.ac("AC-14")
@pytest.mark.parametrize(
    "secret",
    [
        "-----BEGIN RSA PRIVATE KEY-----\nsecret\n-----END RSA PRIVATE KEY-----",
        "AKIAABCDEFGHIJKLMNOP",
        "ghp_" + "a" * 36,
        "github_pat_" + "a" * 20,
        "sk-" + "a" * 20,
        "xoxb-" + "a" * 10,
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
        "Bearer " + "a" * 20,
        "password=hunter2hunter2",
        "https://user:pass@example.com/repo",
    ],
)
def test_known_secret_patterns_are_redacted(secret: str) -> None:
    redacted = redact(f"before {secret} after")

    assert "[REDACTED]" in redacted
    assert secret not in redacted


@pytest.mark.ac("AC-14")
@pytest.mark.parametrize("text", ["token budget", "password policy", "sk-learn"])
def test_redaction_ignores_ordinary_text(text: str) -> None:
    assert redact(text) == text


@pytest.mark.ac("AC-14")
def test_redaction_precedes_capping() -> None:
    text = "x" * 1980 + "sk-" + "a" * 40

    capped, truncated = cap_text(text)

    assert truncated is False
    assert capped == "x" * 1980 + "[REDACTED]"


@pytest.mark.ac("AC-14")
def test_envelope_carries_trust_and_omits_internal_warnings() -> None:
    tier = TierResult(id="tier0", name="syntax", status="pass", warnings=("internal",))
    check = CheckResult(
        tool=ToolInfo(name="strictr", version="0.0.0"),
        status="pass",
        scope=make_scope(),
        tiers=(tier,),
        timings=Timings(total_ms=1),
        environment=Environment(python="3.12", platform="test", root="."),
    )

    envelope = check.to_envelope()

    assert set(envelope) >= {
        "schema_version",
        "tool",
        "status",
        "scope",
        "tiers",
        "timings",
        "environment",
        "trust",
        "warnings",
    }
    assert envelope["schema_version"] == "1"
    assert envelope["status"] == "pass"
    assert envelope["trust"] == {"sandboxed": False, "warning": TRUST_WARNING}
    assert envelope["warnings"] == []
    assert envelope["tiers"][0]["id"] == "tier0"
    assert "warnings" not in envelope["tiers"][0]


@pytest.mark.ac("AC-5")
def test_relative_posix_uses_forward_slashes() -> None:
    root = Path("project")

    assert relative_posix(root / "src" / "app.py", root) == "src/app.py"


@pytest.mark.ac("AC-5")
def test_relative_posix_root_is_dot() -> None:
    root = Path("project")

    assert relative_posix(root, root) == "."


@pytest.mark.ac("AC-5")
def test_relative_posix_does_not_reject_outside_paths() -> None:
    assert relative_posix(Path("other") / "app.py", Path("project")) == "../other/app.py"
