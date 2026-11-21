"""Command-line interface for `strictr check`."""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence

from strictr import __version__
from strictr.app import run_check
from strictr.core.models import exit_code_for
from strictr.output.human import render_human, render_stderr
from strictr.output.json_output import render_json

_TYPE_CHECKERS = ("mypy", "pyright", "none")


def main(argv: Sequence[str] | None = None) -> int:
    """Parse *argv*, run the check, write output, and return the exit code."""
    _configure_stdio()
    args = _build_parser().parse_args(argv)
    try:
        result = run_check(
            args.targets,
            type_checker=args.type_checker,
            timeout=args.timeout,
        )
    except KeyboardInterrupt:
        print("strictr: interrupted", file=sys.stderr)
        return 130

    if args.json_output:
        sys.stdout.write(render_json(result))
        sys.stderr.write(render_stderr(result, include_trust=False))
    else:
        sys.stdout.write(render_human(result))
        sys.stderr.write(render_stderr(result, include_trust=True))
    return exit_code_for(result.status)


def _configure_stdio() -> None:
    """Emit UTF-8 regardless of the platform locale.

    Paths and diagnostics are arbitrary Unicode, and the JSON contract requires
    UTF-8; the Windows locale encoding would replace characters instead.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="strictr")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="verify Python files")
    check.add_argument("targets", nargs="*")
    check.add_argument("--json", action="store_true", dest="json_output")
    check.add_argument("--type-checker", choices=_TYPE_CHECKERS)
    check.add_argument("--timeout", type=_positive_finite_float)
    return parser


def _positive_finite_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid timeout: {text!r}") from None
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("timeout must be a finite positive number")
    return value
