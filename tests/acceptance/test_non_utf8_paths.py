from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "architecture"
    / "verification-contract.schema.json"
)

UNDECODABLE_PATH = "broken_\udcff.py"
UNICODE_PATH = "módulo.py"
SYNTAX_ERROR = "def broken(:\n    pass\n"


def _supports_non_utf8_names() -> bool:
    if os.name != "posix":
        return False
    try:
        return os.fsdecode(b"broken_\xff.py") == UNDECODABLE_PATH
    except UnicodeDecodeError:
        return False


pytestmark = [
    pytest.mark.spec("004"),
    pytest.mark.skipif(
        not _supports_non_utf8_names(),
        reason="non-UTF8 filenames require a POSIX UTF-8 filesystem",
    ),
]


def make_project(root: Path) -> Path:
    root = root.resolve()
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    (root / UNDECODABLE_PATH).write_text(SYNTAX_ERROR, encoding="utf-8")
    (root / UNICODE_PATH).write_text(SYNTAX_ERROR, encoding="utf-8")
    return root


def run_cli_bytes(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (sys.executable, "-m", "strictr", *args),
        cwd=root,
        capture_output=True,
        check=False,
    )


def validation_errors(document: Any) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(schema).iter_errors(document)]


@pytest.mark.ac("AC-3")
def test_non_utf8_path_json(tmp_path: Path) -> None:
    root = make_project(tmp_path)

    completed = run_cli_bytes(root, "check", "--json", "--type-checker", "none")

    assert completed.returncode == 1, completed.stderr
    assert completed.stdout.endswith(b"\n")
    assert completed.stdout.count(b"\n") == 1
    assert re.search(rb"\\udcff", completed.stdout, re.IGNORECASE)
    assert UNICODE_PATH.encode("utf-8") in completed.stdout

    document = json.loads(completed.stdout.decode("utf-8"))
    diagnostic_paths = {
        diagnostic["path"] for tier in document["tiers"] for diagnostic in tier["diagnostics"]
    }
    assert diagnostic_paths == {UNDECODABLE_PATH, UNICODE_PATH}
    assert validation_errors(document) == []


@pytest.mark.ac("AC-3")
def test_non_utf8_path_human(tmp_path: Path) -> None:
    root = make_project(tmp_path)

    completed = run_cli_bytes(root, "check", "--type-checker", "none")

    assert completed.returncode == 1, completed.stderr
    stdout = completed.stdout.decode("utf-8")
    stderr = completed.stderr.decode("utf-8", "replace")
    assert stdout.startswith("FAIL")
    assert "broken_" in stdout
    assert UNICODE_PATH in stdout
    assert "UnicodeEncodeError" not in stderr
    assert "Traceback" not in stderr
