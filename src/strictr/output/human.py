"""Concise human-readable rendering for check results."""

from __future__ import annotations

from strictr.core.models import CheckResult, Diagnostic, TierResult
from strictr.core.text import escape_surrogates

_DIAGNOSTIC_PREVIEW_LIMIT = 5


def render_human(result: CheckResult) -> str:
    """Return the stdout report: status, scope, tier lines, and first failures.

    Warnings and the trust warning are returned by `render_stderr`, not here.
    """
    lines = [
        f"{result.status.upper()}  {result.scope.files_checked} files checked in "
        f"{result.timings.total_ms} ms"
    ]
    lines.extend(_tier_line(tier) for tier in result.tiers)

    for tier in result.tiers:
        if tier.status != "fail":
            continue
        lines.extend(
            _diagnostic_line(item) for item in tier.diagnostics[:_DIAGNOSTIC_PREVIEW_LIMIT]
        )
        notice = _truncation_notice(tier)
        if notice is not None:
            lines.append(notice)

    return escape_surrogates("\n".join(lines)) + "\n"


def render_stderr(result: CheckResult, *, include_trust: bool) -> str:
    """Return newline-terminated warning lines for stderr.

    *include_trust* is true in human mode; `--json` passes false because the
    envelope already carries the trust object.
    """
    warnings = list(result.warnings)
    if include_trust:
        warnings.append(result.trust.warning)
    return "".join(f"warning: {warning}\n" for warning in warnings)


def _tier_line(tier: TierResult) -> str:
    line = f"  {tier.id:<12} {tier.status:<9}{tier.duration_ms:>3} ms"
    if tier.skipped_reason is not None:
        line += f"  {tier.skipped_reason}"
    return line


def _diagnostic_line(item: Diagnostic) -> str:
    return f"  {item.path}:{item.line}:{item.column}: {item.code}: {item.message}"


def _truncation_notice(tier: TierResult) -> str | None:
    shown = min(len(tier.diagnostics), _DIAGNOSTIC_PREVIEW_LIMIT)
    hidden = _hidden_diagnostics(tier, shown)
    if hidden:
        return f"  ... {hidden} more diagnostics (use --json)"
    if tier.meta.get("truncated"):
        return "  ... some text truncated"
    return None


def _hidden_diagnostics(tier: TierResult, shown: int) -> int:
    total = tier.meta.get("total_diagnostics")
    if isinstance(total, int) and not isinstance(total, bool):
        return max(total - shown, 0)
    return max(len(tier.diagnostics) - shown, 0)
