"""Pure mypy `--output=json` normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strictr.core.errors import InvalidToolOutput
from strictr.core.models import Diagnostic, Severity
from strictr.core.paths import relative_posix

_FALLBACK_CODE = "mypy-error"
_SEVERITIES: dict[str, Severity] = {
    "error": "error",
    "warning": "warning",
    "note": "note",
}


def parse_mypy_json(stdout: str, root: Path) -> tuple[Diagnostic, ...]:
    """Normalize mypy JSON Lines into contract diagnostics for `tier1-types`.

    Each non-blank line is one diagnostic object with `file`, `line`, `column`,
    `message`, and `severity`; `end_line`, `end_column`, and `code` are optional.
    Severities map to the contract's `error`, `warning`, and `note`. Paths are
    relative to *root* and use `/`. The result is ordered by path, line, column,
    code, and message. Raises `InvalidToolOutput` when *stdout* is not the
    documented shape.
    """
    diagnostics: list[Diagnostic] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as error:
            raise InvalidToolOutput(f"invalid mypy JSON: {error}") from error
        if not isinstance(entry, dict):
            raise InvalidToolOutput("invalid mypy JSON: line is not an object")
        diagnostics.append(_parse_entry(entry, root))

    diagnostics.sort(key=lambda item: (item.path, item.line, item.column, item.code, item.message))
    return tuple(diagnostics)


def _parse_entry(entry: dict[str, Any], root: Path) -> Diagnostic:
    filename = entry.get("file")
    if not isinstance(filename, str) or not filename:
        raise InvalidToolOutput("invalid mypy JSON: finding has no file")

    message = entry.get("message")
    if not isinstance(message, str) or not message:
        raise InvalidToolOutput("invalid mypy JSON: finding has no message")

    severity = _severity(entry.get("severity"))
    code = entry.get("code")
    if not isinstance(code, str) or not code:
        code = _FALLBACK_CODE

    path = Path(filename)
    if not path.is_absolute():
        path = root / path

    return Diagnostic(
        tier="tier1-types",
        source="mypy",
        path=relative_posix(path, root),
        line=_position(entry, "line"),
        column=_position(entry, "column"),
        end_line=_optional_position(entry, "end_line"),
        end_column=_optional_position(entry, "end_column"),
        code=code,
        severity=severity,
        message=message,
    )


def _severity(value: Any) -> Severity:
    if not isinstance(value, str) or value not in _SEVERITIES:
        raise InvalidToolOutput("invalid mypy JSON: unknown severity")
    return _SEVERITIES[value]


def _position(entry: dict[str, Any], key: str) -> int:
    value = entry.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidToolOutput(f"invalid mypy JSON: {key} must be a positive integer")
    return value


def _optional_position(entry: dict[str, Any], key: str) -> int | None:
    if entry.get(key) is None:
        return None
    return _position(entry, key)
