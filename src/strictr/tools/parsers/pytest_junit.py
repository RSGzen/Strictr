"""Pure pytest JUnit XML normalization."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from strictr.core.errors import InvalidToolOutput
from strictr.core.models import Diagnostic
from strictr.core.paths import relative_posix

_FILE_LINE_PATTERN = re.compile(r"(?m)^\s*(.+?\.py):(\d+):")
_EXCEPTION_PATTERN = re.compile(
    r"([A-Z][A-Za-z0-9_.]*(?:Error|Exception|Warning|Interrupt|Exit|Failure|Failed))(?::|$)"
)


@dataclass(frozen=True, slots=True)
class PytestReport:
    """Parsed JUnit evidence for `tier2-pytest`.

    `error` carries a failure or collection error that has no usable path, so
    the tier can report it in `meta.error` without inventing a pathless
    diagnostic.
    """

    diagnostics: tuple[Diagnostic, ...] = ()
    tests_collected: int = 0
    tests_run: int = 0
    tests_skipped: int = 0
    error: str | None = None


def parse_junit_xml(xml: str, root: Path) -> PytestReport:
    """Normalize JUnit XML into contract diagnostics and pytest counts.

    Supports xunit1 and xunit2 shapes, including missing `file` and `line`
    attributes. Paths are relative to *root* and use `/`. A testcase line of 0
    or missing is normalized to 1; a better `file:line` in the failure text
    wins. Node IDs are reconstructed from the test file and `classname`. A
    failure or collection error without a usable path is reported in `error`,
    never as a pathless diagnostic. Raises `InvalidToolOutput` when *xml* is not
    a usable JUnit document.
    """
    try:
        document = ET.fromstring(xml)
    except ET.ParseError as error:
        raise InvalidToolOutput(f"invalid JUnit XML: {error}") from error

    diagnostics: list[Diagnostic] = []
    pathless_errors: list[str] = []
    tests_collected = 0
    tests_skipped = 0

    for suite in _suites(document):
        cases = suite.findall("testcase")
        collected = _count(suite, "tests")
        if collected is None:
            collected = len(cases)
        skipped = _count(suite, "skipped")
        if skipped is None:
            skipped = sum(1 for case in cases if case.find("skipped") is not None)
        tests_collected += collected
        tests_skipped += skipped

        for case in cases:
            diagnostic, pathless = _parse_case(case, root)
            if diagnostic is not None:
                diagnostics.append(diagnostic)
            if pathless is not None:
                pathless_errors.append(pathless)

    diagnostics.sort(key=lambda item: (item.path, item.line, item.column, item.code, item.message))
    return PytestReport(
        diagnostics=tuple(diagnostics),
        tests_collected=tests_collected,
        tests_run=max(tests_collected - tests_skipped, 0),
        tests_skipped=tests_skipped,
        error="\n".join(pathless_errors) if pathless_errors else None,
    )


def _suites(document: ET.Element) -> list[ET.Element]:
    if document.tag == "testsuite":
        return [document]
    if document.tag == "testsuites":
        return document.findall("testsuite")
    raise InvalidToolOutput("invalid JUnit XML: expected a testsuite root")


def _count(suite: ET.Element, name: str) -> int | None:
    value = suite.get(name)
    if value is None:
        return None
    try:
        count = int(value)
    except ValueError as error:
        raise InvalidToolOutput(f"invalid JUnit XML: {name} is not an integer") from error
    if count < 0:
        raise InvalidToolOutput(f"invalid JUnit XML: {name} must not be negative")
    return count


def _parse_case(case: ET.Element, root: Path) -> tuple[Diagnostic | None, str | None]:
    name = case.get("name")
    if not isinstance(name, str) or not name:
        raise InvalidToolOutput("invalid JUnit XML: testcase has no name")

    classname = case.get("classname") or ""
    failure = case.find("failure")
    error = case.find("error")
    element = failure if failure is not None else error
    if element is None:
        return None, None

    if failure is not None:
        code = "test-failure"
    elif not classname:
        code = "collection-error"
    else:
        code = "test-error"

    message = _message(element)
    path, line = _location(case, element, classname, root)
    if path is None:
        return None, message

    test = path if code == "collection-error" else _node_id(path, classname, name)
    return (
        Diagnostic(
            tier="tier2-pytest",
            source="pytest",
            path=path,
            line=line,
            column=1,
            code=code,
            severity="error",
            message=message,
            test=test,
            exception=_exception(message),
        ),
        None,
    )


def _location(
    case: ET.Element, element: ET.Element, classname: str, root: Path
) -> tuple[str | None, int]:
    matches = _FILE_LINE_PATTERN.findall(element.text or "")
    if matches:
        filename, line_text = matches[-1]
        line = int(line_text)
        if line >= 1:
            path = Path(filename)
            if not path.is_absolute():
                path = root / path
            return relative_posix(path, root), line

    line = _line(case)
    file_value = case.get("file")
    if isinstance(file_value, str) and file_value:
        path = Path(file_value)
        if not path.is_absolute():
            path = root / path
        return relative_posix(path, root), line
    return _path_from_classname(classname), line


def _line(case: ET.Element) -> int:
    value = case.get("line")
    if value is None:
        return 1
    try:
        line = int(value)
    except ValueError:
        return 1
    return line if line >= 1 else 1


def _path_from_classname(classname: str) -> str | None:
    """Derive an xunit2-style test path by dropping trailing class names."""
    parts = [part for part in classname.split(".") if part]
    while parts and parts[-1][:1].isupper():
        parts.pop()
    if not parts:
        return None
    return "/".join(parts) + ".py"


def _node_id(path: str, classname: str, name: str) -> str:
    module = path.removesuffix(".pyi").removesuffix(".py").replace("/", ".")
    if not classname or classname == module:
        return f"{path}::{name}"
    if classname.startswith(f"{module}."):
        class_path = classname[len(module) + 1 :].replace(".", "::")
        return f"{path}::{class_path}::{name}"
    return f"{classname}::{name}"


def _message(element: ET.Element) -> str:
    message = element.get("message")
    text = (element.text or "").strip()
    parts: list[str] = []
    if isinstance(message, str) and message.strip():
        parts.append(message.strip())
    if text and (not parts or not text.startswith(parts[0])):
        parts.append(text)
    if not parts:
        raise InvalidToolOutput("invalid JUnit XML: failure has no message")
    return "\n".join(parts)


def _exception(message: str) -> str | None:
    matches = _EXCEPTION_PATTERN.findall(message)
    return matches[-1] if matches else None
