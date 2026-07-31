"""Generate implementation assets for the Gujarat MSME Power BI report."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from msme_dashboard.file_inventory import sha256_file

ASSET_SCHEMA_VERSION = "1.0"
POWERBI_TABLE_NAME = "Gujarat MSME Districts"

THEME_FILE = "stackore_gujarat_msme_theme.json"
MEASURES_FILE = "gujarat_msme_measures.dax"
SPEC_FILE = "gujarat_msme_dashboard_spec.json"
VISUAL_INVENTORY_FILE = "gujarat_msme_visual_inventory.csv"
ACCEPTANCE_CRITERIA_FILE = "gujarat_msme_acceptance_criteria.csv"
MANIFEST_FILE = "gujarat_msme_dashboard_assets_manifest.json"

PAGE_IDS = (
    "executive_overview",
    "district_comparison",
    "category_analysis",
    "data_availability",
    "sources_methodology",
)

BASE_FIELDS = (
    "state_name",
    "state_id",
    "district_name",
    "lg_dt_code",
    "medium",
    "micro",
    "small",
    "total",
)

DERIVED_FIELDS = (
    "district_rank_total",
    "district_rank_total_ascending",
    "micro_share_pct",
    "small_share_pct",
    "medium_share_pct",
    "gujarat_total_share_pct",
    "dominant_category",
    "top_10_flag",
    "bottom_10_flag",
)

METADATA_FIELDS = (
    "source_id",
    "source_file_name",
    "source_sha256",
    "source_as_of_date",
    "generated_at_utc",
    "row_count",
    "district_count",
)

MANIFEST_FIELDS = (
    "bundle_schema_version",
    "district_row_count",
    "ranking_row_count",
    "data_dictionary_row_count",
)

DATASET_FIELDS = {
    "district_fact": {*BASE_FIELDS, *DERIVED_FIELDS},
    "metadata": set(METADATA_FIELDS),
    "manifest": set(MANIFEST_FIELDS),
    "static": set(),
}

MEASURE_NAMES = (
    "Total Registered Enterprises",
    "Micro Registered Enterprises",
    "Small Registered Enterprises",
    "Medium Registered Enterprises",
    "District Count",
    "Average Registrations per District",
    "Micro Share %",
    "Small Share %",
    "Medium Share %",
    "Selected District Contribution %",
    "Highest Registered District",
    "Lowest Registered District",
    "Top 10 District Flag",
    "Bottom 10 District Flag",
)


def build_powerbi_theme() -> dict[str, Any]:
    """Return the prototype StackOre Power BI theme."""

    return {
        "name": "StackOre Prototype - Gujarat MSME",
        "description": (
            "Prototype dashboard theme pending confirmation against the final StackOre brand kit."
        ),
        "dataColors": [
            "#2563EB",
            "#F59E0B",
            "#10B981",
            "#7C3AED",
            "#0EA5E9",
            "#EF4444",
            "#64748B",
            "#14B8A6",
        ],
        "background": "#F8FAFC",
        "foreground": "#0F172A",
        "tableAccent": "#2563EB",
        "good": "#10B981",
        "neutral": "#F59E0B",
        "bad": "#EF4444",
        "maximum": "#1D4ED8",
        "center": "#F8FAFC",
        "minimum": "#DBEAFE",
        "visualStyles": {
            "*": {
                "*": {
                    "background": [
                        {
                            "color": {
                                "solid": {
                                    "color": "#FFFFFF",
                                }
                            },
                            "transparency": 0,
                        }
                    ],
                    "border": [
                        {
                            "show": True,
                            "color": {
                                "solid": {
                                    "color": "#E2E8F0",
                                }
                            },
                            "radius": 6,
                        }
                    ],
                    "title": [
                        {
                            "show": True,
                            "fontFamily": "Segoe UI Semibold",
                            "fontSize": 12,
                            "color": {
                                "solid": {
                                    "color": "#0F172A",
                                }
                            },
                        }
                    ],
                    "visualHeader": [
                        {
                            "show": True,
                            "foreground": {
                                "solid": {
                                    "color": "#64748B",
                                }
                            },
                        }
                    ],
                }
            },
            "card": {
                "*": {
                    "labels": [
                        {
                            "fontFamily": "Segoe UI Semibold",
                            "fontSize": 22,
                            "color": {
                                "solid": {
                                    "color": "#0F172A",
                                }
                            },
                        }
                    ],
                    "categoryLabels": [
                        {
                            "fontFamily": "Segoe UI",
                            "fontSize": 10,
                            "color": {
                                "solid": {
                                    "color": "#64748B",
                                }
                            },
                        }
                    ],
                }
            },
            "slicer": {
                "*": {
                    "general": [
                        {
                            "outlineColor": {
                                "solid": {
                                    "color": "#CBD5E1",
                                }
                            }
                        }
                    ]
                }
            },
        },
    }


def build_dax_measures() -> str:
    """Return the dashboard DAX measure library."""

    table = f"'{POWERBI_TABLE_NAME}'"

    return f"""// Gujarat MSME Intelligence Dashboard
// Power BI measure library
// Main table: {POWERBI_TABLE_NAME}

Total Registered Enterprises =
SUM({table}[total])

Micro Registered Enterprises =
SUM({table}[micro])

Small Registered Enterprises =
SUM({table}[small])

Medium Registered Enterprises =
SUM({table}[medium])

District Count =
DISTINCTCOUNT({table}[lg_dt_code])

Average Registrations per District =
DIVIDE(
    [Total Registered Enterprises],
    [District Count],
    0
)

Micro Share % =
DIVIDE(
    [Micro Registered Enterprises],
    [Total Registered Enterprises],
    0
)

Small Share % =
DIVIDE(
    [Small Registered Enterprises],
    [Total Registered Enterprises],
    0
)

Medium Share % =
DIVIDE(
    [Medium Registered Enterprises],
    [Total Registered Enterprises],
    0
)

Selected District Contribution % =
DIVIDE(
    SUM({table}[total]),
    CALCULATE(
        [Total Registered Enterprises],
        REMOVEFILTERS(
            {table}[district_name],
            {table}[lg_dt_code]
        )
    ),
    0
)

Highest Registered District =
MAXX(
    TOPN(
        1,
        ALLSELECTED({table}),
        {table}[total],
        DESC,
        {table}[district_name],
        ASC
    ),
    {table}[district_name]
)

Lowest Registered District =
MAXX(
    TOPN(
        1,
        ALLSELECTED({table}),
        {table}[total],
        ASC,
        {table}[district_name],
        ASC
    ),
    {table}[district_name]
)

Top 10 District Flag =
IF(
    MIN({table}[district_rank_total]) <= 10,
    1,
    0
)

Bottom 10 District Flag =
IF(
    MIN({table}[district_rank_total_ascending]) <= 10,
    1,
    0
)
"""


def _visual(
    *,
    visual_id: str,
    title: str,
    visual_type: str,
    dataset: str,
    fields: list[str] | None = None,
    measures: list[str] | None = None,
    purpose: str,
    interactions: str = "",
) -> dict[str, Any]:
    """Create one dashboard visual specification."""

    return {
        "visual_id": visual_id,
        "title": title,
        "visual_type": visual_type,
        "dataset": dataset,
        "fields": fields or [],
        "measures": measures or [],
        "purpose": purpose,
        "interactions": interactions,
    }


def build_dashboard_spec() -> dict[str, Any]:
    """Return the five-page Gujarat-focused dashboard specification."""

    pages = [
        {
            "page_id": "executive_overview",
            "page_number": 1,
            "page_name": "Gujarat Executive Overview",
            "objective": (
                "Present the main Gujarat UDYAM registration KPIs "
                "and the leading district-level patterns."
            ),
            "page_filters": [
                "district_name",
            ],
            "visuals": [
                _visual(
                    visual_id="p1_total_card",
                    title="Total Registered Enterprises",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Total Registered Enterprises"],
                    purpose="Display the Gujarat registration total.",
                ),
                _visual(
                    visual_id="p1_micro_card",
                    title="Micro Enterprises",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Micro Registered Enterprises"],
                    purpose="Display total Micro registrations.",
                ),
                _visual(
                    visual_id="p1_small_card",
                    title="Small Enterprises",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Small Registered Enterprises"],
                    purpose="Display total Small registrations.",
                ),
                _visual(
                    visual_id="p1_medium_card",
                    title="Medium Enterprises",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Medium Registered Enterprises"],
                    purpose="Display total Medium registrations.",
                ),
                _visual(
                    visual_id="p1_district_count",
                    title="Districts Covered",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["District Count"],
                    purpose="Display the number of Gujarat districts.",
                ),
                _visual(
                    visual_id="p1_top_district",
                    title="Highest Registered District",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Highest Registered District"],
                    purpose="Identify the highest-registration district.",
                ),
                _visual(
                    visual_id="p1_top10_chart",
                    title="Top 10 Gujarat Districts",
                    visual_type="clustered_bar_chart",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "total",
                        "district_rank_total",
                    ],
                    purpose="Compare the ten highest-registration districts.",
                    interactions="Filtered where top_10_flag is true.",
                ),
                _visual(
                    visual_id="p1_category_share",
                    title="Enterprise Category Share",
                    visual_type="donut_chart",
                    dataset="district_fact",
                    measures=[
                        "Micro Registered Enterprises",
                        "Small Registered Enterprises",
                        "Medium Registered Enterprises",
                    ],
                    purpose="Show Gujarat registration composition.",
                ),
            ],
        },
        {
            "page_id": "district_comparison",
            "page_number": 2,
            "page_name": "District Comparison",
            "objective": (
                "Rank and compare Gujarat districts using total "
                "registrations and Gujarat contribution."
            ),
            "page_filters": [
                "district_name",
                "dominant_category",
                "top_10_flag",
                "bottom_10_flag",
            ],
            "visuals": [
                _visual(
                    visual_id="p2_district_slicer",
                    title="Select District",
                    visual_type="slicer",
                    dataset="district_fact",
                    fields=["district_name"],
                    purpose="Filter the page to selected districts.",
                ),
                _visual(
                    visual_id="p2_rank_chart",
                    title="District Registration Ranking",
                    visual_type="clustered_bar_chart",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "total",
                        "district_rank_total",
                    ],
                    purpose="Compare districts by total registrations.",
                ),
                _visual(
                    visual_id="p2_contribution_chart",
                    title="Contribution to Gujarat Total",
                    visual_type="bar_chart",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "gujarat_total_share_pct",
                    ],
                    purpose="Show each district's Gujarat contribution.",
                ),
                _visual(
                    visual_id="p2_rank_table",
                    title="District Ranking Table",
                    visual_type="table",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "lg_dt_code",
                        "micro",
                        "small",
                        "medium",
                        "total",
                        "district_rank_total",
                        "gujarat_total_share_pct",
                    ],
                    purpose="Provide sortable district-level detail.",
                ),
                _visual(
                    visual_id="p2_average_card",
                    title="Average Registrations per District",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Average Registrations per District"],
                    purpose="Display the Gujarat district average.",
                ),
                _visual(
                    visual_id="p2_selected_share",
                    title="Selected District Contribution",
                    visual_type="card",
                    dataset="district_fact",
                    measures=["Selected District Contribution %"],
                    purpose="Display selected district contribution.",
                ),
            ],
        },
        {
            "page_id": "category_analysis",
            "page_number": 3,
            "page_name": "Enterprise Category Analysis",
            "objective": (
                "Compare Micro, Small and Medium registration composition across Gujarat districts."
            ),
            "page_filters": [
                "district_name",
                "dominant_category",
            ],
            "visuals": [
                _visual(
                    visual_id="p3_category_cards",
                    title="Category Totals",
                    visual_type="multi_row_card",
                    dataset="district_fact",
                    measures=[
                        "Micro Registered Enterprises",
                        "Small Registered Enterprises",
                        "Medium Registered Enterprises",
                    ],
                    purpose="Display Gujarat category totals.",
                ),
                _visual(
                    visual_id="p3_stacked_chart",
                    title="District Category Composition",
                    visual_type="stacked_bar_chart",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "micro",
                        "small",
                        "medium",
                    ],
                    purpose="Compare category volumes by district.",
                ),
                _visual(
                    visual_id="p3_share_matrix",
                    title="District Category Shares",
                    visual_type="matrix",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "micro_share_pct",
                        "small_share_pct",
                        "medium_share_pct",
                        "dominant_category",
                    ],
                    purpose="Compare category percentages.",
                ),
                _visual(
                    visual_id="p3_medium_share",
                    title="Districts by Medium Share",
                    visual_type="bar_chart",
                    dataset="district_fact",
                    fields=[
                        "district_name",
                        "medium_share_pct",
                    ],
                    purpose="Identify districts with higher Medium share.",
                ),
                _visual(
                    visual_id="p3_dominant_slicer",
                    title="Dominant Category",
                    visual_type="slicer",
                    dataset="district_fact",
                    fields=["dominant_category"],
                    purpose="Filter districts by dominant category.",
                ),
            ],
        },
        {
            "page_id": "data_availability",
            "page_number": 4,
            "page_name": "Data Availability and Limitations",
            "objective": (
                "Explain data coverage, validation status and fields "
                "that are not available at district level."
            ),
            "page_filters": [],
            "visuals": [
                _visual(
                    visual_id="p4_source_status",
                    title="Source Validation Status",
                    visual_type="reference_table",
                    dataset="metadata",
                    fields=[
                        "source_id",
                        "source_as_of_date",
                        "generated_at_utc",
                        "row_count",
                        "district_count",
                    ],
                    purpose="Show source and output status.",
                ),
                _visual(
                    visual_id="p4_checksum",
                    title="Source Integrity",
                    visual_type="reference_card",
                    dataset="metadata",
                    fields=[
                        "source_file_name",
                        "source_sha256",
                    ],
                    purpose="Display source-file traceability.",
                ),
                _visual(
                    visual_id="p4_activity_notice",
                    title="Activity-Type Data",
                    visual_type="static_notice",
                    dataset="static",
                    purpose=(
                        "State that district-level Manufacturing, "
                        "Service and Trading fields are unavailable."
                    ),
                ),
                _visual(
                    visual_id="p4_employment_notice",
                    title="Employment Data",
                    visual_type="static_notice",
                    dataset="static",
                    purpose=(
                        "State that compliant district-level employment "
                        "data is unavailable and is not inferred."
                    ),
                ),
                _visual(
                    visual_id="p4_interpretation_notice",
                    title="Interpretation Warning",
                    visual_type="static_notice",
                    dataset="static",
                    purpose=(
                        "Clarify that registrations are not equivalent "
                        "to active businesses, revenue or profitability."
                    ),
                ),
            ],
        },
        {
            "page_id": "sources_methodology",
            "page_number": 5,
            "page_name": "Sources and Methodology",
            "objective": (
                "Document source provenance, output generation, "
                "field definitions and governance rules."
            ),
            "page_filters": [],
            "visuals": [
                _visual(
                    visual_id="p5_source_details",
                    title="Primary Source",
                    visual_type="reference_table",
                    dataset="metadata",
                    fields=[
                        "source_id",
                        "source_file_name",
                        "source_as_of_date",
                        "source_sha256",
                    ],
                    purpose="Document the approved source snapshot.",
                ),
                _visual(
                    visual_id="p5_bundle_details",
                    title="Generated Package",
                    visual_type="reference_table",
                    dataset="manifest",
                    fields=[
                        "bundle_schema_version",
                        "district_row_count",
                        "ranking_row_count",
                        "data_dictionary_row_count",
                    ],
                    purpose="Document generated Power BI assets.",
                ),
                _visual(
                    visual_id="p5_methodology",
                    title="Transformation Methodology",
                    visual_type="static_text",
                    dataset="static",
                    purpose=(
                        "Explain filtering, validation, ranking, "
                        "percentage calculations and checksum generation."
                    ),
                ),
                _visual(
                    visual_id="p5_field_dictionary",
                    title="Field Dictionary",
                    visual_type="reference_table",
                    dataset="static",
                    purpose=(
                        "Display field name, type, origin, description "
                        "and calculation from the generated dictionary."
                    ),
                ),
                _visual(
                    visual_id="p5_governance",
                    title="Data Governance",
                    visual_type="static_text",
                    dataset="static",
                    purpose=(
                        "Document aggregate-only usage, date preservation "
                        "and prohibition of identifiable records."
                    ),
                ),
            ],
        },
    ]

    spec = {
        "asset_schema_version": ASSET_SCHEMA_VERSION,
        "dashboard_name": "Gujarat MSME Intelligence Dashboard",
        "prepared_for": "StackOre Technologies",
        "main_table_name": POWERBI_TABLE_NAME,
        "page_count": len(pages),
        "supported_datasets": {key: sorted(value) for key, value in DATASET_FIELDS.items()},
        "measure_names": list(MEASURE_NAMES),
        "pages": pages,
        "global_rules": [
            "Dashboard scope is Gujarat district aggregate data.",
            "No identifiable enterprise-level data is permitted.",
            "Source reporting dates must be displayed and preserved.",
            "Unsupported activity and employment data must not be inferred.",
            "Registration counts must not be described as active businesses.",
            "LGD district codes must remain text identifiers.",
        ],
    }

    validate_dashboard_spec(spec)

    return spec


def validate_dashboard_spec(
    spec: dict[str, Any],
) -> None:
    """Validate dashboard pages, visuals, fields and measures."""

    pages = spec.get("pages")

    if not isinstance(pages, list):
        raise TypeError("Dashboard specification must contain pages.")

    if len(pages) != 5:
        raise ValueError("Dashboard specification must contain five pages.")

    page_ids = [page.get("page_id") for page in pages]

    if tuple(page_ids) != PAGE_IDS:
        raise ValueError("Dashboard page order or identifiers are invalid.")

    if len(page_ids) != len(set(page_ids)):
        raise ValueError("Dashboard page identifiers must be unique.")

    visual_ids: list[str] = []

    for page in pages:
        visuals = page.get("visuals")

        if not isinstance(visuals, list) or not visuals:
            raise ValueError(f"Page {page['page_id']!r} must contain visuals.")

        for visual in visuals:
            visual_id = str(visual.get("visual_id", "")).strip()

            if not visual_id:
                raise ValueError("Every visual must have an identifier.")

            visual_ids.append(visual_id)

            dataset = visual.get("dataset")

            if dataset not in DATASET_FIELDS:
                raise ValueError(f"Visual {visual_id!r} has an invalid dataset.")

            fields = set(visual.get("fields", []))
            unsupported_fields = fields - DATASET_FIELDS[dataset]

            if unsupported_fields:
                raise ValueError(
                    f"Visual {visual_id!r} contains unsupported fields: "
                    + ", ".join(sorted(unsupported_fields))
                )

            measures = set(visual.get("measures", []))
            unsupported_measures = measures - set(MEASURE_NAMES)

            if unsupported_measures:
                raise ValueError(
                    f"Visual {visual_id!r} contains unsupported measures: "
                    + ", ".join(sorted(unsupported_measures))
                )

    if len(visual_ids) != len(set(visual_ids)):
        raise ValueError("Dashboard visual identifiers must be unique.")

    prohibited_fields = {
        "activity_type",
        "employment",
        "gender",
        "social_category",
        "enterprise_name",
        "udyam_number",
        "owner_name",
        "address",
        "mobile_number",
        "email",
    }

    all_configured_fields = {
        field for page in pages for visual in page["visuals"] for field in visual.get("fields", [])
    }

    invalid = all_configured_fields & prohibited_fields

    if invalid:
        raise ValueError(
            "Dashboard contains prohibited or unsupported fields: " + ", ".join(sorted(invalid))
        )


def build_visual_inventory(
    spec: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Flatten the dashboard specification into a visual inventory."""

    resolved_spec = spec or build_dashboard_spec()
    validate_dashboard_spec(resolved_spec)

    rows: list[dict[str, Any]] = []

    for page in resolved_spec["pages"]:
        for visual in page["visuals"]:
            rows.append(
                {
                    "page_number": page["page_number"],
                    "page_id": page["page_id"],
                    "page_name": page["page_name"],
                    "visual_id": visual["visual_id"],
                    "visual_title": visual["title"],
                    "visual_type": visual["visual_type"],
                    "dataset": visual["dataset"],
                    "fields": " | ".join(visual["fields"]),
                    "measures": " | ".join(visual["measures"]),
                    "purpose": visual["purpose"],
                    "interactions": visual["interactions"],
                }
            )

    return pd.DataFrame(rows)


def build_acceptance_criteria() -> pd.DataFrame:
    """Return page-level Power BI acceptance criteria."""

    rows = [
        (
            "M2-001",
            "executive_overview",
            "KPI",
            "All five Gujarat headline KPI cards display without blanks.",
            "Compare visual values with the executive summary JSON.",
        ),
        (
            "M2-002",
            "executive_overview",
            "Chart",
            "The Top 10 chart shows no more than ten Gujarat districts.",
            "Filter and count displayed district categories.",
        ),
        (
            "M2-003",
            "executive_overview",
            "Interpretation",
            "The page uses registration terminology consistently.",
            "Review all titles, subtitles and tooltips.",
        ),
        (
            "M2-004",
            "district_comparison",
            "Ranking",
            "District ranking is ordered from highest to lowest total.",
            "Compare with district_rank_total.",
        ),
        (
            "M2-005",
            "district_comparison",
            "Interaction",
            "District selection filters all comparison visuals.",
            "Select one district and inspect cross-filtering.",
        ),
        (
            "M2-006",
            "district_comparison",
            "Contribution",
            "District contribution percentages use the Gujarat total.",
            "Compare visual values with gujarat_total_share_pct.",
        ),
        (
            "M2-007",
            "category_analysis",
            "Composition",
            "Micro, Small and Medium shares total approximately 100%.",
            "Validate selected district category percentages.",
        ),
        (
            "M2-008",
            "category_analysis",
            "Dominance",
            "Dominant-category filters match the generated field.",
            "Compare slicer results with dominant_category.",
        ),
        (
            "M2-009",
            "category_analysis",
            "Zero handling",
            "Zero-registration districts show zero shares.",
            "Test a zero-registration fixture when available.",
        ),
        (
            "M2-010",
            "data_availability",
            "Limitations",
            "Activity and employment gaps are displayed explicitly.",
            "Review static notices on Page 4.",
        ),
        (
            "M2-011",
            "data_availability",
            "Traceability",
            "Source date and SHA-256 checksum are visible.",
            "Compare with the metadata JSON.",
        ),
        (
            "M2-012",
            "data_availability",
            "Governance",
            "The page states that missing fields are not inferred.",
            "Review limitation text.",
        ),
        (
            "M2-013",
            "sources_methodology",
            "Source",
            "Primary source ID, file name and reporting date are shown.",
            "Compare with the approved source registry entry.",
        ),
        (
            "M2-014",
            "sources_methodology",
            "Methodology",
            "Validation and transformation steps are documented.",
            "Compare with generated metadata transformations.",
        ),
        (
            "M2-015",
            "sources_methodology",
            "Dictionary",
            "All fact-table fields appear in the field dictionary.",
            "Compare with gujarat_msme_data_dictionary.csv.",
        ),
        (
            "M2-016",
            "all_pages",
            "Branding",
            "The prototype theme is applied consistently.",
            "Inspect fonts, backgrounds, borders and accent colours.",
        ),
        (
            "M2-017",
            "all_pages",
            "Privacy",
            "No identifiable enterprise-level fields are present.",
            "Inspect the Power BI model and all visuals.",
        ),
        (
            "M2-018",
            "all_pages",
            "Performance",
            "Page visuals render without avoidable duplicate datasets.",
            "Use Power BI Performance Analyzer.",
        ),
    ]

    return pd.DataFrame(
        rows,
        columns=[
            "criterion_id",
            "page_id",
            "category",
            "acceptance_criterion",
            "validation_method",
        ],
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


def write_dashboard_assets(
    output_directory: Path,
) -> dict[str, Any]:
    """Generate the complete Power BI dashboard implementation package."""

    output_directory = Path(output_directory)
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    theme_path = output_directory / THEME_FILE
    measures_path = output_directory / MEASURES_FILE
    spec_path = output_directory / SPEC_FILE
    inventory_path = output_directory / VISUAL_INVENTORY_FILE
    criteria_path = output_directory / ACCEPTANCE_CRITERIA_FILE
    manifest_path = output_directory / MANIFEST_FILE

    theme = build_powerbi_theme()
    measures = build_dax_measures()
    spec = build_dashboard_spec()
    inventory = build_visual_inventory(spec)
    criteria = build_acceptance_criteria()

    _write_json(theme_path, theme)

    measures_path.write_text(
        measures,
        encoding="utf-8",
        newline="\n",
    )

    _write_json(spec_path, spec)

    inventory.to_csv(
        inventory_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    criteria.to_csv(
        criteria_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    generated_files = {
        "theme": theme_path,
        "measures": measures_path,
        "dashboard_specification": spec_path,
        "visual_inventory": inventory_path,
        "acceptance_criteria": criteria_path,
    }

    manifest = {
        "asset_schema_version": ASSET_SCHEMA_VERSION,
        "asset_package_name": ("Gujarat MSME Power BI Dashboard Implementation Assets"),
        "generated_at_utc": (datetime.now(UTC).replace(microsecond=0).isoformat()),
        "dashboard_name": spec["dashboard_name"],
        "page_count": spec["page_count"],
        "visual_count": len(inventory),
        "measure_count": len(MEASURE_NAMES),
        "acceptance_criteria_count": len(criteria),
        "theme_status": ("Prototype theme pending final StackOre brand-kit confirmation."),
        "files": {
            key: {
                "file_name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for key, path in generated_files.items()
        },
        "governance": [
            "The assets consume the validated M1 aggregate data package.",
            "No identifiable enterprise-level fields are permitted.",
            "Unsupported activity and employment fields are not inferred.",
            "Final publication requires an approved M0 source snapshot.",
        ],
    }

    _write_json(manifest_path, manifest)

    return manifest
