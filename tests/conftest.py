from __future__ import annotations

import json
from pathlib import Path

import pytest

# Fixture projects contain intentional failures and a hung test; never collect them.
collect_ignore = ["fixtures/projects"]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Write a spec-scoped AC-to-test map for the traceability checker."""
    del config
    report: dict[str, dict[str, list[str]]] = {}
    for item in items:
        spec_marker = next(item.iter_markers(name="spec"), None)
        spec_id = (
            str(spec_marker.args[0]) if spec_marker is not None and spec_marker.args else "unscoped"
        )
        for mark in item.iter_markers(name="ac"):
            if mark.args:
                report.setdefault(spec_id, {}).setdefault(str(mark.args[0]), []).append(item.nodeid)

    out = Path(__file__).resolve().parents[1] / "build" / "ac-tests.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
