"""Generate and validate the complete Power BI implementation package."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.powerbi_dashboard_assets import (
    ACCEPTANCE_CRITERIA_FILE,
    MEASURES_FILE,
    PAGE_IDS,
    SPEC_FILE,
    THEME_FILE,
    VISUAL_INVENTORY_FILE,
    build_dashboard_spec,
    build_visual_inventory,
    validate_dashboard_spec,
    write_dashboard_assets,
)
from msme_dashboard.powerbi_dashboard_assets import (
    MANIFEST_FILE as DASHBOARD_ASSETS_MANIFEST_FILE,
)

IMPLEMENTATION_SCHEMA_VERSION = "1.0"

MODEL_SPEC_FILE = "gujarat_msme_model_spec.json"
PAGE_LAYOUT_FILE = "gujarat_msme_page_layouts.csv"
INTERACTION_RULES_FILE = "gujarat_msme_interaction_rules.csv"
TOOLTIP_DRILLTHROUGH_FILE = "gujarat_msme_tooltip_drillthrough.json"
IMPLEMENTATION_GUIDE_FILE = "M2_POWERBI_IMPLEMENTATION_GUIDE.md"
PACKAGE_MANIFEST_FILE = "gujarat_msme_powerbi_implementation_manifest.json"

TECHNICAL_PAGE_IDS = (
    "district_tooltip",
    "district_drillthrough",
)

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

PROHIBITED_FIELDS = {
    "enterprise_name",
    "udyam_number",
    "owner_name",
    "mobile_number",
    "email",
    "address",
    "pin_code",
    "activity_type",
    "employment",
    "gender",
    "social_category",
}


def build_model_spec() -> dict[str, Any]:
    """Return the Power BI semantic-model implementation plan."""

    return {
        "implementation_schema_version": (IMPLEMENTATION_SCHEMA_VERSION),
        "model_name": "Gujarat MSME Intelligence Model",
        "storage_mode": "Import",
        "visible_report_pages": list(PAGE_IDS),
        "technical_pages": [
            {
                "page_id": "district_tooltip",
                "display_name": "District Tooltip",
                "page_type": "tooltip",
                "hidden": True,
            },
            {
                "page_id": "district_drillthrough",
                "display_name": "District Detail",
                "page_type": "drillthrough",
                "hidden": True,
            },
        ],
        "tables": {
            "district_fact": {
                "powerbi_name": "Gujarat MSME Districts",
                "source_file": "gujarat_district_msme.csv",
                "table_role": "fact",
                "grain": ("One row per Gujarat district for one approved source snapshot."),
                "load_enabled": True,
                "key_columns": [
                    "state_id",
                    "lg_dt_code",
                ],
                "default_sort": [
                    {
                        "column": "district_name",
                        "sort_by": "district_rank_total",
                    }
                ],
                "hidden_columns": [
                    "state_name",
                    "state_id",
                    "district_rank_total_ascending",
                    "top_10_flag",
                    "bottom_10_flag",
                ],
            },
            "dataset_metadata": {
                "powerbi_name": "Dataset Metadata",
                "source_file": ("gujarat_district_msme.metadata.json"),
                "table_role": "disconnected_reference",
                "grain": "One record per generated dataset.",
                "load_enabled": True,
                "hidden": True,
            },
            "bundle_manifest": {
                "powerbi_name": "Bundle Manifest",
                "source_file": ("gujarat_powerbi_bundle_manifest.json"),
                "table_role": "disconnected_reference",
                "grain": "One record per generated bundle.",
                "load_enabled": True,
                "hidden": True,
            },
            "field_dictionary": {
                "powerbi_name": "Field Dictionary",
                "source_file": ("gujarat_msme_data_dictionary.csv"),
                "table_role": "reference",
                "grain": "One row per output field.",
                "load_enabled": True,
                "hidden": False,
            },
            "measures": {
                "powerbi_name": "_Measures",
                "source_file": None,
                "table_role": "measure_table",
                "grain": "No analytical rows.",
                "load_enabled": True,
                "hidden": False,
            },
        },
        "relationships": [],
        "formatting": {
            "whole_number_columns": [
                "medium",
                "micro",
                "small",
                "total",
                "district_rank_total",
                "district_rank_total_ascending",
            ],
            "percentage_columns": [
                "micro_share_pct",
                "small_share_pct",
                "medium_share_pct",
                "gujarat_total_share_pct",
            ],
            "percentage_decimal_places": 2,
            "identifier_columns_as_text": [
                "state_id",
                "lg_dt_code",
            ],
            "display_units": "None",
            "thousands_separator": True,
        },
        "refresh": {
            "mode": "Manual during prototype phase",
            "source_integrity_check": "SHA-256 checksum",
            "required_before_refresh": [
                "Source remains approved in the registry.",
                "Source reporting date is confirmed.",
                "Source schema passes pipeline validation.",
                "Generated bundle manifest passes validation.",
            ],
        },
        "governance": [
            "No enterprise-level identifiable data is loaded.",
            "Registration counts are not active-business counts.",
            "Unsupported fields are not inferred.",
            "LGD codes remain text identifiers.",
            "Different reporting snapshots are not silently combined.",
        ],
    }


def _layout_rows() -> list[dict[str, Any]]:
    """Return explicit positions for all visible report visuals."""

    layouts = {
        "executive_overview": [
            ("p1_total_card", 24, 80, 236, 110),
            ("p1_micro_card", 270, 80, 180, 110),
            ("p1_small_card", 460, 80, 180, 110),
            ("p1_medium_card", 650, 80, 180, 110),
            ("p1_district_count", 840, 80, 180, 110),
            ("p1_top_district", 1030, 80, 226, 110),
            ("p1_top10_chart", 24, 210, 820, 486),
            ("p1_category_share", 864, 210, 392, 486),
        ],
        "district_comparison": [
            ("p2_district_slicer", 24, 80, 260, 90),
            ("p2_average_card", 304, 80, 300, 90),
            ("p2_selected_share", 624, 80, 300, 90),
            ("p2_rank_chart", 24, 190, 600, 300),
            ("p2_contribution_chart", 644, 190, 612, 300),
            ("p2_rank_table", 24, 510, 1232, 186),
        ],
        "category_analysis": [
            ("p3_category_cards", 24, 80, 1232, 100),
            ("p3_stacked_chart", 24, 200, 600, 300),
            ("p3_medium_share", 644, 200, 612, 300),
            ("p3_dominant_slicer", 24, 520, 300, 176),
            ("p3_share_matrix", 344, 520, 912, 176),
        ],
        "data_availability": [
            ("p4_source_status", 24, 80, 760, 220),
            ("p4_checksum", 804, 80, 452, 220),
            ("p4_activity_notice", 24, 320, 392, 376),
            ("p4_employment_notice", 436, 320, 392, 376),
            ("p4_interpretation_notice", 848, 320, 408, 376),
        ],
        "sources_methodology": [
            ("p5_source_details", 24, 80, 600, 220),
            ("p5_bundle_details", 644, 80, 612, 220),
            ("p5_methodology", 24, 320, 392, 376),
            ("p5_field_dictionary", 436, 320, 500, 376),
            ("p5_governance", 956, 320, 300, 376),
        ],
    }

    rows: list[dict[str, Any]] = []

    for page_id, placements in layouts.items():
        for z_order, placement in enumerate(
            placements,
            start=1,
        ):
            visual_id, x, y, width, height = placement

            rows.append(
                {
                    "page_id": page_id,
                    "visual_id": visual_id,
                    "canvas_width": CANVAS_WIDTH,
                    "canvas_height": CANVAS_HEIGHT,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "z_order": z_order,
                    "visible": True,
                }
            )

    return rows


def build_page_layouts(
    spec: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Return pixel-level layouts for all visible visuals."""

    resolved_spec = spec or build_dashboard_spec()
    validate_dashboard_spec(resolved_spec)

    layouts = pd.DataFrame(_layout_rows())
    inventory = build_visual_inventory(resolved_spec)

    expected_visuals = set(inventory["visual_id"])
    actual_visuals = set(layouts["visual_id"])

    if expected_visuals != actual_visuals:
        missing = expected_visuals - actual_visuals
        unexpected = actual_visuals - expected_visuals

        raise ValueError(
            "Page layouts do not match the visual inventory. "
            f"Missing={sorted(missing)}; "
            f"Unexpected={sorted(unexpected)}"
        )

    if layouts["visual_id"].duplicated().any():
        raise ValueError("Every visual must have one layout row.")

    invalid_bounds = (
        layouts["x"].lt(0)
        | layouts["y"].lt(0)
        | (layouts["x"] + layouts["width"]).gt(layouts["canvas_width"])
        | (layouts["y"] + layouts["height"]).gt(layouts["canvas_height"])
    )

    if invalid_bounds.any():
        invalid_ids = layouts.loc[
            invalid_bounds,
            "visual_id",
        ].tolist()

        raise ValueError("Visuals exceed the configured page canvas: " + ", ".join(invalid_ids))

    return layouts


def build_interaction_rules(
    spec: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Return explicit same-page visual interaction rules."""

    resolved_spec = spec or build_dashboard_spec()
    validate_dashboard_spec(resolved_spec)

    data_visual_types = {
        "card",
        "multi_row_card",
        "clustered_bar_chart",
        "bar_chart",
        "stacked_bar_chart",
        "donut_chart",
        "table",
        "matrix",
    }

    interactive_source_types = {
        "slicer",
        "clustered_bar_chart",
        "bar_chart",
        "stacked_bar_chart",
        "donut_chart",
        "table",
        "matrix",
    }

    rows: list[dict[str, str]] = []

    for page in resolved_spec["pages"]:
        visuals = page["visuals"]

        for source in visuals:
            if source["visual_type"] not in interactive_source_types:
                continue

            for target in visuals:
                if source["visual_id"] == target["visual_id"]:
                    continue

                if target["visual_type"] not in data_visual_types:
                    continue

                if source["dataset"] != "district_fact" or target["dataset"] != "district_fact":
                    continue

                interaction = "filter" if source["visual_type"] == "slicer" else "cross_highlight"

                rows.append(
                    {
                        "page_id": page["page_id"],
                        "source_visual_id": source["visual_id"],
                        "target_visual_id": target["visual_id"],
                        "interaction": interaction,
                        "rationale": (
                            "Keep analytical visuals synchronized within the current report page."
                        ),
                    }
                )

    return pd.DataFrame(rows)


def build_tooltip_drillthrough_spec() -> dict[str, Any]:
    """Return hidden tooltip and drill-through page requirements."""

    return {
        "technical_pages": [
            {
                "page_id": "district_tooltip",
                "display_name": "District Tooltip",
                "page_type": "tooltip",
                "hidden": True,
                "page_size": {
                    "width": 360,
                    "height": 280,
                },
                "trigger_fields": [
                    "district_name",
                ],
                "display_fields": [
                    "district_name",
                    "lg_dt_code",
                    "district_rank_total",
                    "dominant_category",
                ],
                "display_measures": [
                    "Total Registered Enterprises",
                    "Micro Registered Enterprises",
                    "Small Registered Enterprises",
                    "Medium Registered Enterprises",
                    "Selected District Contribution %",
                ],
                "source_visual_types": [
                    "clustered_bar_chart",
                    "bar_chart",
                    "stacked_bar_chart",
                    "donut_chart",
                ],
            },
            {
                "page_id": "district_drillthrough",
                "display_name": "District Detail",
                "page_type": "drillthrough",
                "hidden": True,
                "page_size": {
                    "width": CANVAS_WIDTH,
                    "height": CANVAS_HEIGHT,
                },
                "drillthrough_fields": [
                    "district_name",
                    "lg_dt_code",
                ],
                "keep_all_filters": True,
                "visuals": [
                    {
                        "visual_id": "dt_total_card",
                        "visual_type": "card",
                        "measure": ("Total Registered Enterprises"),
                    },
                    {
                        "visual_id": "dt_category_chart",
                        "visual_type": "clustered_column_chart",
                        "measures": [
                            "Micro Registered Enterprises",
                            "Small Registered Enterprises",
                            "Medium Registered Enterprises",
                        ],
                    },
                    {
                        "visual_id": "dt_share_table",
                        "visual_type": "table",
                        "fields": [
                            "micro_share_pct",
                            "small_share_pct",
                            "medium_share_pct",
                            "gujarat_total_share_pct",
                        ],
                    },
                    {
                        "visual_id": "dt_back_button",
                        "visual_type": "back_button",
                    },
                ],
            },
        ],
        "assignment_rules": [
            {
                "source_page_id": "executive_overview",
                "source_visual_id": "p1_top10_chart",
                "tooltip_page_id": "district_tooltip",
                "drillthrough_page_id": "district_drillthrough",
            },
            {
                "source_page_id": "district_comparison",
                "source_visual_id": "p2_rank_chart",
                "tooltip_page_id": "district_tooltip",
                "drillthrough_page_id": "district_drillthrough",
            },
            {
                "source_page_id": "district_comparison",
                "source_visual_id": "p2_contribution_chart",
                "tooltip_page_id": "district_tooltip",
                "drillthrough_page_id": "district_drillthrough",
            },
            {
                "source_page_id": "category_analysis",
                "source_visual_id": "p3_stacked_chart",
                "tooltip_page_id": "district_tooltip",
                "drillthrough_page_id": "district_drillthrough",
            },
            {
                "source_page_id": "category_analysis",
                "source_visual_id": "p3_medium_share",
                "tooltip_page_id": "district_tooltip",
                "drillthrough_page_id": "district_drillthrough",
            },
        ],
    }


def build_implementation_guide() -> str:
    """Return the complete Power BI developer handover guide."""

    return """# M2 — Power BI Dashboard Implementation Guide

## Purpose

This guide converts the generated M1 Gujarat district data package
into the five-page Gujarat MSME Intelligence Dashboard.

The dashboard is a StackOre Technologies proof of concept based on
public aggregate data. It is not an official government product.

## Required inputs

Load these files from the generated M1 package:

- `gujarat_district_msme.csv`
- `gujarat_district_msme.metadata.json`
- `gujarat_powerbi_bundle_manifest.json`
- `gujarat_msme_data_dictionary.csv`

Use these M2 implementation assets:

- `stackore_gujarat_msme_theme.json`
- `gujarat_msme_measures.dax`
- `gujarat_msme_dashboard_spec.json`
- `gujarat_msme_visual_inventory.csv`
- `gujarat_msme_acceptance_criteria.csv`
- `gujarat_msme_model_spec.json`
- `gujarat_msme_page_layouts.csv`
- `gujarat_msme_interaction_rules.csv`
- `gujarat_msme_tooltip_drillthrough.json`

## Semantic model

Rename the main fact table to `Gujarat MSME Districts`.

Keep `state_id` and `lg_dt_code` as Text. Registration counts and
district ranks use Whole Number. Percentage fields use Decimal Number
with two displayed decimal places.

Create a dedicated `_Measures` table and place all DAX measures there.

Metadata and manifest tables are disconnected reference tables. No
relationship is required because the current model has one analytical
fact table and no separate dimensions.

## Build sequence

1. Load the validated M1 data package.
2. Apply the supplied Power BI theme.
3. Rename tables according to the model specification.
4. Assign data types and hidden-column settings.
5. Create the `_Measures` table.
6. copy the supplied DAX measures.
7. Create the five visible pages in specification order.
8. Apply the pixel layouts from the layout CSV.
9. Configure visual interactions from the interaction-rules CSV.
10. Create the hidden tooltip and drill-through pages.
11. Apply page-level and visual-level filters.
12. Validate values against the M1 JSON and CSV outputs.
13. Run the acceptance checklist.
14. Save the PBIX using a source-date-aware file name.

## Visible pages

### 1. Gujarat Executive Overview

Use cards for Gujarat totals, category totals, district count and the
highest-registration district. Use a Top-10 bar chart and category
share donut chart.

Do not describe total registrations as active enterprises.

### 2. District Comparison

Provide district selection, district ranking, Gujarat contribution,
average registrations and a sortable district table.

The selected district contribution measure must remove only district
filters when calculating the Gujarat denominator.

### 3. Enterprise Category Analysis

Compare Micro, Small and Medium registrations and shares across
districts. Include the dominant-category slicer and Medium-share
ranking.

Category shares should total approximately 100 percent for nonzero
districts.

### 4. Data Availability and Limitations

Display source ID, source reporting date, generated timestamp and
source checksum.

Clearly state that district-level activity type and employment data
are unavailable and are not inferred.

### 5. Sources and Methodology

Display source provenance, bundle details, transformation methodology,
field dictionary and governance warnings.

The primary reporting date must match the approved source snapshot.

## Tooltip page

Create a hidden report-tooltip page named `District Tooltip`.

The tooltip displays district name, LGD code, district rank, dominant
category, category totals and contribution to the Gujarat total.

Assign it to the supported analytical charts listed in the tooltip
specification.

## Drill-through page

Create a hidden page named `District Detail`.

Use `district_name` and `lg_dt_code` as drill-through fields and enable
Keep all filters.

Include a Back button, total card, category chart and percentage table.

## Visual interactions

Slicers filter all same-page analytical visuals.

Charts, tables and matrices cross-highlight compatible same-page
visuals. Reference text, methodology blocks and limitation notices do
not participate in cross-filtering.

## Theme

The supplied theme is a StackOre prototype theme. It uses clean
light-background cards, dark typography, blue as the primary accent,
and distinct category colours.

Before client delivery, compare it with the final StackOre brand kit
and update colours, fonts and logo treatment when necessary.

## Data governance

- Only aggregate district data is permitted.
- Enterprise names, registration numbers, owner details and contact
  details must never be loaded.
- Missing values must not be inferred from state totals.
- Different reporting snapshots must not be silently combined.
- Registration counts are not revenue, profitability or employment.
- The source reporting date and checksum must remain visible.
- Final publication requires an approved M0 source.

## Validation

Run the generated acceptance-criteria checklist and verify:

- KPI values against the executive summary JSON
- District order against the analytical CSV
- Category shares against derived columns
- Source information against metadata
- File integrity against the package manifest
- Absence of identifiable enterprise-level fields
- Page rendering with Power BI Performance Analyzer

## Delivery naming

Use a PBIX file name such as:

`StackOre_Gujarat_MSME_Dashboard_<SOURCE_DATE>_v1.pbix`

Do not place an unconfirmed date in the PBIX file name.
"""


def validate_implementation_assets(
    *,
    dashboard_spec: dict[str, Any],
    model_spec: dict[str, Any],
    layouts: pd.DataFrame,
    interactions: pd.DataFrame,
    tooltip_spec: dict[str, Any],
) -> None:
    """Validate the complete implementation design."""

    validate_dashboard_spec(dashboard_spec)

    if tuple(model_spec["visible_report_pages"]) != PAGE_IDS:
        raise ValueError("Model visible pages do not match the dashboard.")

    technical_page_ids = tuple(page["page_id"] for page in model_spec["technical_pages"])

    if technical_page_ids != TECHNICAL_PAGE_IDS:
        raise ValueError("Model technical pages are incomplete or misordered.")

    inventory = build_visual_inventory(dashboard_spec)
    inventory_ids = set(inventory["visual_id"])
    layout_ids = set(layouts["visual_id"])

    if inventory_ids != layout_ids:
        raise ValueError("Layout coverage does not match dashboard visuals.")

    if interactions.empty:
        raise ValueError("Dashboard interaction rules must not be empty.")

    interaction_sources = set(interactions["source_visual_id"])
    interaction_targets = set(interactions["target_visual_id"])

    invalid_interactions = (interaction_sources | interaction_targets) - inventory_ids

    if invalid_interactions:
        raise ValueError(
            "Interaction rules reference unknown visuals: "
            + ", ".join(sorted(invalid_interactions))
        )

    tooltip_pages = tooltip_spec.get("technical_pages", [])
    tooltip_page_ids = tuple(page["page_id"] for page in tooltip_pages)

    if tooltip_page_ids != TECHNICAL_PAGE_IDS:
        raise ValueError("Tooltip and drill-through pages are incomplete.")

    assigned_visuals = {rule["source_visual_id"] for rule in tooltip_spec["assignment_rules"]}

    invalid_assignments = assigned_visuals - inventory_ids

    if invalid_assignments:
        raise ValueError(
            "Tooltip rules reference unknown visuals: " + ", ".join(sorted(invalid_assignments))
        )

    serialized = json.dumps(
        {
            "dashboard_spec": dashboard_spec,
            "model_spec": model_spec,
            "tooltip_spec": tooltip_spec,
        }
    ).casefold()

    prohibited = {field for field in PROHIBITED_FIELDS if f'"{field}"' in serialized}

    if prohibited:
        raise ValueError(
            "Implementation package contains prohibited fields: " + ", ".join(sorted(prohibited))
        )


def _write_json(
    path: Path,
    value: dict[str, Any],
) -> None:
    """Write formatted UTF-8 JSON."""

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_powerbi_implementation_package(
    output_directory: Path,
) -> dict[str, Any]:
    """Generate all dashboard and implementation assets."""

    output_directory = Path(output_directory)
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    dashboard_manifest = write_dashboard_assets(
        output_directory,
    )

    dashboard_spec = build_dashboard_spec()
    model_spec = build_model_spec()
    layouts = build_page_layouts(dashboard_spec)
    interactions = build_interaction_rules(
        dashboard_spec,
    )
    tooltip_spec = build_tooltip_drillthrough_spec()
    guide = build_implementation_guide()

    validate_implementation_assets(
        dashboard_spec=dashboard_spec,
        model_spec=model_spec,
        layouts=layouts,
        interactions=interactions,
        tooltip_spec=tooltip_spec,
    )

    model_path = output_directory / MODEL_SPEC_FILE
    layout_path = output_directory / PAGE_LAYOUT_FILE
    interactions_path = output_directory / INTERACTION_RULES_FILE
    tooltip_path = output_directory / TOOLTIP_DRILLTHROUGH_FILE
    guide_path = output_directory / IMPLEMENTATION_GUIDE_FILE
    package_manifest_path = output_directory / PACKAGE_MANIFEST_FILE

    _write_json(model_path, model_spec)

    layouts.to_csv(
        layout_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    interactions.to_csv(
        interactions_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    _write_json(tooltip_path, tooltip_spec)

    guide_path.write_text(
        guide,
        encoding="utf-8",
        newline="\n",
    )

    file_names = [
        THEME_FILE,
        MEASURES_FILE,
        SPEC_FILE,
        VISUAL_INVENTORY_FILE,
        ACCEPTANCE_CRITERIA_FILE,
        DASHBOARD_ASSETS_MANIFEST_FILE,
        MODEL_SPEC_FILE,
        PAGE_LAYOUT_FILE,
        INTERACTION_RULES_FILE,
        TOOLTIP_DRILLTHROUGH_FILE,
        IMPLEMENTATION_GUIDE_FILE,
    ]

    generated_files = {file_name: output_directory / file_name for file_name in file_names}

    manifest = {
        "implementation_schema_version": (IMPLEMENTATION_SCHEMA_VERSION),
        "package_name": ("Gujarat MSME Power BI Implementation Package"),
        "generated_at_utc": (datetime.now(UTC).replace(microsecond=0).isoformat()),
        "dashboard_asset_manifest": dashboard_manifest["files"],
        "visible_page_count": len(PAGE_IDS),
        "technical_page_count": len(TECHNICAL_PAGE_IDS),
        "visual_count": len(layouts),
        "interaction_rule_count": len(interactions),
        "files": {
            file_name: {
                "file_name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for file_name, path in generated_files.items()
        },
        "publication_status": (
            "Prototype implementation assets. Final publication "
            "requires an approved M0 source snapshot."
        ),
    }

    _write_json(
        package_manifest_path,
        manifest,
    )

    return manifest


def validate_written_implementation_package(
    output_directory: Path,
) -> dict[str, Any]:
    """Validate generated files, checksums and design consistency."""

    output_directory = Path(output_directory)
    manifest_path = output_directory / PACKAGE_MANIFEST_FILE

    if not manifest_path.exists():
        raise FileNotFoundError(f"Implementation manifest does not exist: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for details in manifest.get("files", {}).values():
        path = output_directory / details["file_name"]

        if not path.exists():
            raise FileNotFoundError(f"Implementation asset does not exist: {path}")

        if path.stat().st_size != details["size_bytes"]:
            raise ValueError(f"File size mismatch for {path.name}.")

        if sha256_file(path) != details["sha256"]:
            raise ValueError(f"Checksum mismatch for {path.name}.")

    dashboard_spec = json.loads((output_directory / SPEC_FILE).read_text(encoding="utf-8"))
    model_spec = json.loads((output_directory / MODEL_SPEC_FILE).read_text(encoding="utf-8"))
    layouts = pd.read_csv(output_directory / PAGE_LAYOUT_FILE)
    interactions = pd.read_csv(output_directory / INTERACTION_RULES_FILE)
    tooltip_spec = json.loads(
        (output_directory / TOOLTIP_DRILLTHROUGH_FILE).read_text(encoding="utf-8")
    )

    validate_implementation_assets(
        dashboard_spec=dashboard_spec,
        model_spec=model_spec,
        layouts=layouts,
        interactions=interactions,
        tooltip_spec=tooltip_spec,
    )

    return manifest
