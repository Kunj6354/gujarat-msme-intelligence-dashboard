"""Tests for the complete Power BI implementation package."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.powerbi_dashboard_assets import (
    PAGE_IDS,
    THEME_FILE,
    build_dashboard_spec,
)
from msme_dashboard.powerbi_implementation_package import (
    IMPLEMENTATION_GUIDE_FILE,
    INTERACTION_RULES_FILE,
    MODEL_SPEC_FILE,
    PACKAGE_MANIFEST_FILE,
    PAGE_LAYOUT_FILE,
    TECHNICAL_PAGE_IDS,
    TOOLTIP_DRILLTHROUGH_FILE,
    build_implementation_guide,
    build_interaction_rules,
    build_model_spec,
    build_page_layouts,
    build_tooltip_drillthrough_spec,
    validate_implementation_assets,
    validate_written_implementation_package,
    write_powerbi_implementation_package,
)


def test_model_spec_defines_expected_tables_and_pages() -> None:
    model = build_model_spec()

    assert tuple(model["visible_report_pages"]) == PAGE_IDS

    technical_ids = tuple(page["page_id"] for page in model["technical_pages"])

    assert technical_ids == TECHNICAL_PAGE_IDS
    assert model["storage_mode"] == "Import"
    assert model["relationships"] == []

    assert set(model["tables"]) == {
        "district_fact",
        "dataset_metadata",
        "bundle_manifest",
        "field_dictionary",
        "measures",
    }

    assert model["tables"]["district_fact"]["grain"].startswith("One row per Gujarat district")


def test_page_layouts_cover_all_visible_visuals() -> None:
    spec = build_dashboard_spec()
    layouts = build_page_layouts(spec)

    visual_ids = {visual["visual_id"] for page in spec["pages"] for visual in page["visuals"]}

    assert set(layouts["visual_id"]) == visual_ids
    assert layouts["visual_id"].is_unique
    assert layouts["visible"].all()

    assert (layouts["x"] + layouts["width"] <= layouts["canvas_width"]).all()

    assert (layouts["y"] + layouts["height"] <= layouts["canvas_height"]).all()


def test_interaction_rules_reference_known_visuals() -> None:
    spec = build_dashboard_spec()
    interactions = build_interaction_rules(spec)

    visual_ids = {visual["visual_id"] for page in spec["pages"] for visual in page["visuals"]}

    assert not interactions.empty
    assert set(interactions["source_visual_id"]).issubset(visual_ids)
    assert set(interactions["target_visual_id"]).issubset(visual_ids)
    assert set(interactions["interaction"]) == {
        "filter",
        "cross_highlight",
    }


def test_tooltip_and_drillthrough_pages_are_hidden() -> None:
    tooltip_spec = build_tooltip_drillthrough_spec()

    technical_pages = tooltip_spec["technical_pages"]

    assert tuple(page["page_id"] for page in technical_pages) == TECHNICAL_PAGE_IDS

    assert all(page["hidden"] for page in technical_pages)

    drillthrough = technical_pages[1]

    assert drillthrough["keep_all_filters"] is True
    assert drillthrough["drillthrough_fields"] == [
        "district_name",
        "lg_dt_code",
    ]


def test_implementation_guide_contains_required_sections() -> None:
    guide = build_implementation_guide()

    assert "# M2" in guide
    assert "## Semantic model" in guide
    assert "## Build sequence" in guide
    assert "## Tooltip page" in guide
    assert "## Drill-through page" in guide
    assert "## Data governance" in guide
    assert "approved M0 source" in guide


def test_validation_rejects_missing_layout_visual() -> None:
    spec = build_dashboard_spec()
    model = build_model_spec()
    layouts = build_page_layouts(spec).iloc[:-1].copy()
    interactions = build_interaction_rules(spec)
    tooltip_spec = build_tooltip_drillthrough_spec()

    with pytest.raises(
        ValueError,
        match="Layout coverage",
    ):
        validate_implementation_assets(
            dashboard_spec=spec,
            model_spec=model,
            layouts=layouts,
            interactions=interactions,
            tooltip_spec=tooltip_spec,
        )


def test_writer_generates_and_validates_complete_package(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "implementation"

    returned_manifest = write_powerbi_implementation_package(
        output_directory,
    )

    required_files = [
        THEME_FILE,
        MODEL_SPEC_FILE,
        PAGE_LAYOUT_FILE,
        INTERACTION_RULES_FILE,
        TOOLTIP_DRILLTHROUGH_FILE,
        IMPLEMENTATION_GUIDE_FILE,
        PACKAGE_MANIFEST_FILE,
    ]

    for file_name in required_files:
        assert (output_directory / file_name).exists()

    saved_manifest = json.loads(
        (output_directory / PACKAGE_MANIFEST_FILE).read_text(encoding="utf-8")
    )

    assert saved_manifest == returned_manifest
    assert saved_manifest["visible_page_count"] == 5
    assert saved_manifest["technical_page_count"] == 2
    assert saved_manifest["visual_count"] >= 25
    assert saved_manifest["interaction_rule_count"] > 0

    for details in saved_manifest["files"].values():
        path = output_directory / details["file_name"]

        assert sha256_file(path) == details["sha256"]
        assert path.stat().st_size == details["size_bytes"]

    validated_manifest = validate_written_implementation_package(
        output_directory,
    )

    assert validated_manifest == saved_manifest

    layouts = pd.read_csv(output_directory / PAGE_LAYOUT_FILE)
    interactions = pd.read_csv(output_directory / INTERACTION_RULES_FILE)

    assert len(layouts) == saved_manifest["visual_count"]
    assert len(interactions) == saved_manifest["interaction_rule_count"]


def test_validator_detects_modified_asset(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "implementation"

    write_powerbi_implementation_package(
        output_directory,
    )

    theme_path = output_directory / THEME_FILE
    theme_path.write_text(
        theme_path.read_text(encoding="utf-8") + "\nmodified",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="size mismatch|Checksum mismatch",
    ):
        validate_written_implementation_package(
            output_directory,
        )
