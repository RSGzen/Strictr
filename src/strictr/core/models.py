"""Contract models shared by the pipeline, tiers, tools, and output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = "1"
TRUST_WARNING = "Local execution; not a security boundary."

type TierStatus = Literal["pass", "fail", "skipped", "error"]
type OverallStatus = Literal["pass", "fail", "partial", "error"]
type Severity = Literal["error", "warning", "note"]
type TypeCheckerChoice = Literal["mypy", "pyright", "none"]


@dataclass(frozen=True, slots=True)
class ToolInfo:
    name: str
    version: str


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Captured subprocess output. Missing executables and timeouts raise."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One normalized finding. `path` is root-relative POSIX; positions are 1-based."""

    tier: str
    source: str
    path: str
    line: int
    column: int
    code: str
    severity: Severity
    message: str
    end_line: int | None = None
    end_column: int | None = None
    test: str | None = None
    exception: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class TierResult:
    """One tier's contract fields. `warnings` is internal and never serialized."""

    id: str
    name: str
    status: TierStatus
    tool: ToolInfo | None = None
    duration_ms: int = 0
    diagnostics: tuple[Diagnostic, ...] = ()
    skipped_reason: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Scope:
    """What was and was not inspected; unrun test counts stay at zero."""

    root: str
    targets: tuple[str, ...]
    files_checked: int = 0
    files_skipped: int = 0
    tests_collected: int = 0
    tests_run: int = 0
    tests_skipped: int = 0


@dataclass(frozen=True, slots=True)
class Timings:
    total_ms: int


@dataclass(frozen=True, slots=True)
class Environment:
    python: str
    platform: str
    root: str


@dataclass(frozen=True, slots=True)
class Trust:
    sandboxed: bool = False
    warning: str = TRUST_WARNING


@dataclass(frozen=True, slots=True)
class CheckContext:
    root: Path
    targets: tuple[str, ...]
    files: tuple[Path, ...]
    timeout: float | None = None
    type_checker: TypeCheckerChoice | None = None


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    root: Path
    targets: tuple[str, ...]
    files: tuple[Path, ...]
    files_skipped: int = 0
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CheckResult:
    """A completed run. The pipeline owns status, warnings, and test counts."""

    tool: ToolInfo
    status: OverallStatus
    scope: Scope
    tiers: tuple[TierResult, ...]
    timings: Timings
    environment: Environment
    warnings: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
    trust: Trust = field(default_factory=Trust)

    def to_envelope(self) -> dict[str, Any]:
        """Serialize to the contract shape; tier warnings stay internal."""
        return {
            "schema_version": self.schema_version,
            "tool": {"name": self.tool.name, "version": self.tool.version},
            "status": self.status,
            "scope": {
                "root": self.scope.root,
                "targets": list(self.scope.targets),
                "files_checked": self.scope.files_checked,
                "files_skipped": self.scope.files_skipped,
                "tests_collected": self.scope.tests_collected,
                "tests_run": self.scope.tests_run,
                "tests_skipped": self.scope.tests_skipped,
            },
            "tiers": [
                {
                    "id": tier.id,
                    "name": tier.name,
                    "status": tier.status,
                    "tool": (
                        None
                        if tier.tool is None
                        else {"name": tier.tool.name, "version": tier.tool.version}
                    ),
                    "duration_ms": tier.duration_ms,
                    "diagnostics": [
                        {
                            "tier": diagnostic.tier,
                            "source": diagnostic.source,
                            "path": diagnostic.path,
                            "line": diagnostic.line,
                            "column": diagnostic.column,
                            "end_line": diagnostic.end_line,
                            "end_column": diagnostic.end_column,
                            "code": diagnostic.code,
                            "severity": diagnostic.severity,
                            "message": diagnostic.message,
                            "test": diagnostic.test,
                            "exception": diagnostic.exception,
                            "url": diagnostic.url,
                        }
                        for diagnostic in tier.diagnostics
                    ],
                    "skipped_reason": tier.skipped_reason,
                    "meta": dict(tier.meta),
                }
                for tier in self.tiers
            ],
            "timings": {"total_ms": self.timings.total_ms},
            "environment": {
                "python": self.environment.python,
                "platform": self.environment.platform,
                "root": self.environment.root,
            },
            "trust": {"sandboxed": self.trust.sandboxed, "warning": self.trust.warning},
            "warnings": list(self.warnings),
        }


def exit_code_for(status: OverallStatus) -> int:
    """Map an overall status to the CLI exit code."""
    if status == "pass":
        return 0
    if status == "fail":
        return 1
    return 2
