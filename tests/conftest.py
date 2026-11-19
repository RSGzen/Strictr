from __future__ import annotations

import json
from pathlib import Path

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Write the AC-to-test map for the traceability checker."""
    del config
    report: dict[str, list[str]] = {}
    for item in items:
        for mark in item.iter_markers(name="ac"):
            if mark.args:
                report.setdefault(str(mark.args[0]), []).append(item.nodeid)

    out = Path(__file__).resolve().parents[1] / "build" / "ac-tests.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
