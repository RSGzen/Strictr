from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

pytestmark = pytest.mark.spec("003")

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "architecture" / "verification-contract.schema.json"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "contract"
GOLDEN_FIXTURES = ("pass", "fail", "partial", "error")
TIER_IDS = ("tier0", "tier1-ruff", "tier1-types", "tier2-pytest")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(SCHEMA_PATH))


def validation_errors(document: Any) -> list[str]:
    return [error.message for error in validator().iter_errors(document)]


@pytest.mark.ac("AC-15")
@pytest.mark.parametrize("name", GOLDEN_FIXTURES)
def test_golden_fixtures_validate(name: str) -> None:
    document = load_json(FIXTURE_DIR / f"{name}.json")
    assert validation_errors(document) == []


@pytest.mark.ac("AC-15")
def test_schema_version_is_one() -> None:
    document = load_json(FIXTURE_DIR / "pass.json")
    assert document["schema_version"] == "1"

    document["schema_version"] = "2"
    assert validation_errors(document)


@pytest.mark.ac("AC-15")
def test_tier_ids_are_stable() -> None:
    document = load_json(FIXTURE_DIR / "pass.json")
    assert [tier["id"] for tier in document["tiers"]] == list(TIER_IDS)


@pytest.mark.ac("AC-15")
def test_schema_allows_additive_fields() -> None:
    document = load_json(FIXTURE_DIR / "pass.json")
    document["future_field"] = {"anything": True}
    document["scope"]["future_count"] = 1
    assert validation_errors(document) == []


@pytest.mark.ac("AC-15")
def test_schema_rejects_missing_required_fields() -> None:
    document = load_json(FIXTURE_DIR / "pass.json")
    del document["trust"]
    assert validation_errors(document)

    document = load_json(FIXTURE_DIR / "pass.json")
    del document["scope"]["files_checked"]
    assert validation_errors(document)

    document = load_json(FIXTURE_DIR / "pass.json")
    del document["tiers"][0]["diagnostics"]
    assert validation_errors(document)


@pytest.mark.ac("AC-15")
def test_schema_rejects_invalid_statuses_and_trust() -> None:
    document = load_json(FIXTURE_DIR / "pass.json")
    document["status"] = "ok"
    assert validation_errors(document)

    document = load_json(FIXTURE_DIR / "pass.json")
    document["trust"]["sandboxed"] = True
    assert validation_errors(document)

    document = load_json(FIXTURE_DIR / "pass.json")
    document["tiers"][0]["status"] = "unknown"
    assert validation_errors(document)


@pytest.mark.ac("AC-15")
def test_schema_requires_a_path_for_diagnostics() -> None:
    document = load_json(FIXTURE_DIR / "fail.json")
    diagnostic = copy.deepcopy(document["tiers"][1]["diagnostics"][0])
    del diagnostic["path"]
    document["tiers"][1]["diagnostics"] = [diagnostic]
    assert validation_errors(document)


@pytest.mark.ac("AC-15")
def test_golden_files_are_portable() -> None:
    for name in GOLDEN_FIXTURES:
        raw = (FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8")
        assert not re.search(r"[A-Za-z]:\\\\", raw), name
        assert not re.search(r"/(?:Users|home|tmp)/", raw), name
        assert '"version": "0.' not in raw, name
