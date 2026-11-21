"""Pure pyright `--outputjson` normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strictr.core.errors import InvalidToolOutput
from strictr.core.models import Diagnostic, Severity
from strictr.core.paths import relative_posix

_FALLBACK_CODE = "pyright-error"
_SEVERITIES: dict[str, Severity] = {
    "error": "error",
    "warning": "warning",
    "information": "note",
}


def parse_pyright_json(stdout: str, root: Path) -> tuple[Diagnostic, ...]:
    """Normalize pyright JSON into contract diagnostics for `tier1-types`.

    `generalDiagnostics` entries carry a 0-based `range`; contract positions are
    1-based. `information` maps to the contract's `note`, and `rule` becomes the
    code when present. Paths are relative to *root* and use `/`. The result is
    ordered by path, line, column, code, and message. Raises `InvalidToolOutput`
    when *stdout* is not the documented shape.
    """
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise InvalidToolOutput(f"invalid pyright JSON: {error}") from error
    if not isinstance(payload, dict):
        raise InvalidToolOutput("invalid pyright JSON: expected an object")

    entries = payload.get("generalDiagnostics")
    if not isinstance(entries, list):
        raise InvalidToolOutput("invalid pyright JSON: generalDiagnostics must be an array")

    diagnostics = [_parse_entry(entry, root) for entry in entries]
    diagnostics.sort(key=lambda item: (item.path, item.line, item.column, item.code, item.message))
    return tuple(diagnostics)


def _parse_entry(entry: Any, root: Path) -> Diagnostic:
    if not isinstance(entry, dict):
        raise InvalidToolOutput("invalid pyright JSON: diagnostic is not an object")

    filename = entry.get("file")
    if not isinstance(filename, str) or not filename:
        raise InvalidToolOutput("invalid pyright JSON: diagnostic has no file")

    message = entry.get("message")
    if not isinstance(message, str) or not message:
        raise InvalidToolOutput("invalid pyright JSON: diagnostic has no message")

    severity = _severity(entry.get("severity"))
    line, column, end_line, end_column = _positions(entry.get("range"))

    rule = entry.get("rule")
    code = rule if isinstance(rule, str) and rule else _FALLBACK_CODE
    path = Path(filename)
    if not path.is_absolute():
        path = root / path

    return Diagnostic(
        tier="tier1-types",
        source="pyright",
        path=relative_posix(path, root),
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        code=code,
        severity=severity,
        message=message,
    )


def _severity(value: Any) -> Severity:
    if not isinstance(value, str) or value not in _SEVERITIES:
        raise InvalidToolOutput("invalid pyright JSON: unknown severity")
    return _SEVERITIES[value]


def _positions(value: Any) -> tuple[int, int, int | None, int | None]:
    if not isinstance(value, dict):
        raise InvalidToolOutput("invalid pyright JSON: diagnostic has no range")
    start = value.get("start")
    if not isinstance(start, dict):
        raise InvalidToolOutput("invalid pyright JSON: range has no start")
    line = _zero_based(start, "line")
    column = _zero_based(start, "character")

    end = value.get("end")
    if end is None:
        return line, column, None, None
    if not isinstance(end, dict):
        raise InvalidToolOutput("invalid pyright JSON: range end is not an object")
    return line, column, _zero_based(end, "line"), _zero_based(end, "character")


def _zero_based(position: dict[str, Any], key: str) -> int:
    value = position.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidToolOutput(f"invalid pyright JSON: {key} must be a non-negative integer")
    return value + 1
