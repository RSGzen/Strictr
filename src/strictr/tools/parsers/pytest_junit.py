"""Pure pytest JUnit XML normalization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from strictr.core.models import Diagnostic


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
    raise NotImplementedError
