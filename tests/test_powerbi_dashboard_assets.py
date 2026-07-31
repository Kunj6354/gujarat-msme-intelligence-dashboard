"""Tests for Power BI dashboard implementation assets."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.powerbi_dashboard_assets import (
    ACCEPTANCE_CRITERIA_FILE,
    MANIFEST_FILE,
    MEASURE_NAMES,
    MEASURES_FILE,
    PAGE_IDS,
    SPEC_FILE,
    THEME_FILE,
    VISUAL_INVENTORY_FILE,
    build_acceptance_criteria,
    build_dashboard_spec,
    build_dax_measures,
    build_powerbi_theme,
    build_visual_inventory,
    validate_dashboard_spec,
    write_dashboard_assets,
)


def test_theme_contains_required_powerbi_properties() -> None:
    theme = build_powerbi_theme()

    assert theme["name"] == ("StackOre Prototype - Gujarat MSME")
    assert len(theme["dataColors"]) >= 6
    assert theme["background"].startswith("#")
    assert theme["foreground"].startswith("#")
    assert "visualStyles" in theme
    assert "Prototype" in theme["description"]


def test_dax_library_contains_all_declared_measures() -> None:
    measures = build_dax_measures()

    for measure_name in MEASURE_NAMES:
        assert f"{measure_name} =" in measures

    assert "DIVIDE(" in measures
    assert "REMOVEFILTERS(" in measures
    assert "ALLSELECTED(" in measures
    assert "active businesses" not in measures.lower()


def test_dashboard_spec_contains_five_valid_pages() -> None:
    spec = build_dashboard_spec()

    validate_dashboard_spec(spec)

    assert spec["page_count"] == 5
    assert tuple(page["page_id"] for page in spec["pages"]) == PAGE_IDS

    visual_ids = [visual["visual_id"] for page in spec["pages"] for visual in page["visuals"]]

    assert len(visual_ids) >= 25
    assert len(visual_ids) == len(set(visual_ids))


def test_dashboard_spec_excludes_prohibited_fields() -> None:
    spec = build_dashboard_spec()

    configured_fields = {
        field for page in spec["pages"] for visual in page["visuals"] for field in visual["fields"]
    }

    prohibited = {
        "activity_type",
        "employment",
        "enterprise_name",
        "udyam_number",
        "owner_name",
        "address",
        "mobile_number",
        "email",
    }

    assert configured_fields.isdisjoint(prohibited)


def test_validation_rejects_duplicate_page_id() -> None:
    spec = build_dashboard_spec()
    spec["pages"][1]["page_id"] = spec["pages"][0]["page_id"]

    with pytest.raises(
        ValueError,
        match="page order|identifiers",
    ):
        validate_dashboard_spec(spec)


def test_visual_inventory_covers_every_page() -> None:
    spec = build_dashboard_spec()
    inventory = build_visual_inventory(spec)

    assert set(inventory["page_id"]) == set(PAGE_IDS)
    assert inventory["visual_id"].is_unique
    assert inventory["purpose"].str.len().gt(0).all()
    assert len(inventory) >= 25


def test_acceptance_criteria_cover_all_pages() -> None:
    criteria = build_acceptance_criteria()

    covered_pages = set(criteria["page_id"])

    assert set(PAGE_IDS).issubset(covered_pages)
    assert "all_pages" in covered_pages
    assert criteria["criterion_id"].is_unique
    assert len(criteria) >= 15


def test_write_dashboard_assets_generates_complete_package(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "dashboard_assets"

    returned_manifest = write_dashboard_assets(
        output_directory,
    )

    expected_files = [
        THEME_FILE,
        MEASURES_FILE,
        SPEC_FILE,
        VISUAL_INVENTORY_FILE,
        ACCEPTANCE_CRITERIA_FILE,
        MANIFEST_FILE,
    ]

    for file_name in expected_files:
        assert (output_directory / file_name).exists()

    saved_manifest = json.loads((output_directory / MANIFEST_FILE).read_text(encoding="utf-8"))

    assert saved_manifest == returned_manifest
    assert saved_manifest["page_count"] == 5
    assert saved_manifest["measure_count"] == len(MEASURE_NAMES)
    assert saved_manifest["visual_count"] >= 25
    assert saved_manifest["acceptance_criteria_count"] >= 15

    for details in saved_manifest["files"].values():
        generated_path = output_directory / details["file_name"]

        assert details["sha256"] == sha256_file(generated_path)
        assert details["size_bytes"] == (generated_path.stat().st_size)

    inventory = pd.read_csv(output_directory / VISUAL_INVENTORY_FILE)
    criteria = pd.read_csv(output_directory / ACCEPTANCE_CRITERIA_FILE)

    assert len(inventory) == saved_manifest["visual_count"]
    assert len(criteria) == saved_manifest["acceptance_criteria_count"]
