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
        raise NotImplementedError


def exit_code_for(status: OverallStatus) -> int:
    """Map an overall status to the CLI exit code."""
    raise NotImplementedError
