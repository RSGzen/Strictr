"""Pure ruff JSON output normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strictr.core.errors import InvalidToolOutput
from strictr.core.models import Diagnostic
from strictr.core.paths import relative_posix

_FALLBACK_CODE = "ruff-error"


def parse_ruff_json(stdout: str, root: Path) -> tuple[Diagnostic, ...]:
    """Normalize ruff `--output-format=json` output into contract diagnostics.

    Returned paths are relative to *root* and use `/`, and the result is ordered
    by the contract's diagnostic key. Raises `InvalidToolOutput` when *stdout*
    is not the documented JSON shape.
    """
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise InvalidToolOutput(f"invalid ruff JSON: {error}") from error
    if not isinstance(payload, list):
        raise InvalidToolOutput("invalid ruff JSON: expected an array")

    diagnostics = [_parse_entry(entry, root) for entry in payload]
    diagnostics.sort(key=lambda item: (item.path, item.line, item.column, item.code, item.message))
    return tuple(diagnostics)


def _parse_entry(entry: Any, root: Path) -> Diagnostic:
    if not isinstance(entry, dict):
        raise InvalidToolOutput("invalid ruff JSON: finding is not an object")

    filename = entry.get("filename")
    if not isinstance(filename, str) or not filename:
        raise InvalidToolOutput("invalid ruff JSON: finding has no filename")

    location = entry.get("location")
    if not isinstance(location, dict):
        raise InvalidToolOutput("invalid ruff JSON: finding has no location")
    line = _position(location, "row")
    column = _position(location, "column")

    message = entry.get("message")
    if not isinstance(message, str) or not message:
        raise InvalidToolOutput("invalid ruff JSON: finding has no message")

    code = entry.get("code")
    if not isinstance(code, str) or not code:
        code = _FALLBACK_CODE

    end_line, end_column = _end_location(entry.get("end_location"))
    url = entry.get("url")
    path = Path(filename)
    if not path.is_absolute():
        path = root / path

    return Diagnostic(
        tier="tier1-ruff",
        source="ruff",
        path=relative_posix(path, root),
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        code=code,
        severity="error",
        message=message,
        url=url if isinstance(url, str) and url else None,
    )


def _position(location: dict[Any, Any], key: str) -> int:
    value = location.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidToolOutput(f"invalid ruff JSON: {key} must be a positive integer")
    return value


def _end_location(value: Any) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    if not isinstance(value, dict):
        raise InvalidToolOutput("invalid ruff JSON: end_location is not an object")
    return _position(value, "row"), _position(value, "column")
