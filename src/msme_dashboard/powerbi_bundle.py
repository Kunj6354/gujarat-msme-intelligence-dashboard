"""Generate the complete Power BI-ready Gujarat MSME data package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from msme_dashboard.district_metrics import (
    DERIVED_COLUMNS,
    add_district_analytical_metrics,
    validate_analytical_metrics,
)
from msme_dashboard.district_pipeline import (
    REQUIRED_COLUMNS,
    build_gujarat_district_dataset,
)
from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.processed_output import create_output_metadata

BUNDLE_SCHEMA_VERSION = "1.0"

DISTRICT_DATA_FILE = "gujarat_district_msme.csv"
DISTRICT_METADATA_FILE = "gujarat_district_msme.metadata.json"
EXECUTIVE_SUMMARY_FILE = "gujarat_executive_summary.json"
RANKING_VIEW_FILE = "gujarat_district_rankings.csv"
DATA_DICTIONARY_FILE = "gujarat_msme_data_dictionary.csv"
MANIFEST_FILE = "gujarat_powerbi_bundle_manifest.json"


def build_executive_summary(
    frame: pd.DataFrame,
) -> dict[str, Any]:
    """Build Gujarat-level KPIs from analytical district data."""

    validate_analytical_metrics(frame)

    district_count = len(frame)
    total_registrations = int(frame["total"].sum())
    micro_total = int(frame["micro"].sum())
    small_total = int(frame["small"].sum())
    medium_total = int(frame["medium"].sum())

    highest = frame.sort_values(
        by=["district_rank_total"],
        kind="stable",
    ).iloc[0]

    lowest = frame.sort_values(
        by=["district_rank_total_ascending"],
        kind="stable",
    ).iloc[0]

    def percentage(value: int) -> float:
        if total_registrations == 0:
            return 0.0

        return round(
            value / total_registrations * 100,
            4,
        )

    return {
        "geography": "Gujarat",
        "district_count": district_count,
        "total_registered_enterprises": total_registrations,
        "micro_registered_enterprises": micro_total,
        "small_registered_enterprises": small_total,
        "medium_registered_enterprises": medium_total,
        "micro_share_pct": percentage(micro_total),
        "small_share_pct": percentage(small_total),
        "medium_share_pct": percentage(medium_total),
        "average_registrations_per_district": round(
            total_registrations / district_count,
            2,
        ),
        "highest_registered_district": {
            "district_name": str(highest["district_name"]),
            "lg_dt_code": str(highest["lg_dt_code"]),
            "total": int(highest["total"]),
        },
        "lowest_registered_district": {
            "district_name": str(lowest["district_name"]),
            "lg_dt_code": str(lowest["lg_dt_code"]),
            "total": int(lowest["total"]),
        },
        "kpi_definitions": {
            "total_registered_enterprises": (
                "Sum of Micro, Small and Medium UDYAM registration counts across Gujarat districts."
            ),
            "average_registrations_per_district": (
                "Gujarat registration total divided by the "
                "number of districts in the source dataset."
            ),
            "category_share_pct": (
                "Category registration count divided by the "
                "Gujarat registration total, multiplied by 100."
            ),
        },
        "interpretation_warning": (
            "Registration counts do not establish whether an "
            "enterprise is active, profitable or currently employing staff."
        ),
    }


def build_ranking_views(
    frame: pd.DataFrame,
    *,
    limit: int = 10,
) -> pd.DataFrame:
    """Build Top-N and Bottom-N district ranking views."""

    validate_analytical_metrics(frame)

    if limit < 1:
        raise ValueError("Ranking limit must be at least 1.")

    effective_limit = min(limit, len(frame))

    top = (
        frame.sort_values(
            by=["district_rank_total"],
            kind="stable",
        )
        .head(effective_limit)
        .copy()
    )
    top.insert(
        0,
        "ranking_group",
        "TOP",
    )
    top.insert(
        1,
        "ranking_position",
        range(1, len(top) + 1),
    )

    bottom = (
        frame.sort_values(
            by=["district_rank_total_ascending"],
            kind="stable",
        )
        .head(effective_limit)
        .copy()
    )
    bottom.insert(
        0,
        "ranking_group",
        "BOTTOM",
    )
    bottom.insert(
        1,
        "ranking_position",
        range(1, len(bottom) + 1),
    )

    return pd.concat(
        [top, bottom],
        ignore_index=True,
    )


def build_data_dictionary() -> pd.DataFrame:
    """Return the Power BI field dictionary."""

    rows = [
        (
            "state_name",
            "text",
            "source",
            "State or union territory name.",
            "",
        ),
        (
            "state_id",
            "text",
            "source",
            "State identifier supplied by the source.",
            "",
        ),
        (
            "district_name",
            "text",
            "source",
            "District name supplied by the source.",
            "",
        ),
        (
            "lg_dt_code",
            "text",
            "source",
            "Local Government Directory district code.",
            "",
        ),
        (
            "micro",
            "whole_number",
            "source",
            "Registered Micro enterprises.",
            "",
        ),
        (
            "small",
            "whole_number",
            "source",
            "Registered Small enterprises.",
            "",
        ),
        (
            "medium",
            "whole_number",
            "source",
            "Registered Medium enterprises.",
            "",
        ),
        (
            "total",
            "whole_number",
            "source",
            "Total registered enterprises.",
            "micro + small + medium",
        ),
        (
            "district_rank_total",
            "whole_number",
            "derived",
            "District rank from highest to lowest total.",
            "Descending rank of total",
        ),
        (
            "district_rank_total_ascending",
            "whole_number",
            "derived",
            "District rank from lowest to highest total.",
            "Ascending rank of total",
        ),
        (
            "micro_share_pct",
            "decimal_number",
            "derived",
            "Micro registrations as a percentage of district total.",
            "micro / total * 100",
        ),
        (
            "small_share_pct",
            "decimal_number",
            "derived",
            "Small registrations as a percentage of district total.",
            "small / total * 100",
        ),
        (
            "medium_share_pct",
            "decimal_number",
            "derived",
            "Medium registrations as a percentage of district total.",
            "medium / total * 100",
        ),
        (
            "gujarat_total_share_pct",
            "decimal_number",
            "derived",
            "District contribution to Gujarat registrations.",
            "district total / Gujarat total * 100",
        ),
        (
            "dominant_category",
            "text",
            "derived",
            "Largest registration category in the district.",
            "Maximum of Micro, Small and Medium",
        ),
        (
            "top_10_flag",
            "boolean",
            "derived",
            "Whether the district is in the Gujarat Top 10.",
            "district_rank_total <= 10",
        ),
        (
            "bottom_10_flag",
            "boolean",
            "derived",
            "Whether the district is in the Gujarat Bottom 10.",
            "district_rank_total_ascending <= 10",
        ),
    ]

    dictionary = pd.DataFrame(
        rows,
        columns=[
            "field_name",
            "powerbi_data_type",
            "field_origin",
            "description",
            "calculation",
        ],
    )

    field_order = [
        *REQUIRED_COLUMNS,
        *DERIVED_COLUMNS,
    ]

    return dictionary.set_index("field_name").loc[field_order].reset_index()


def _write_json(
    path: Path,
    value: dict[str, Any],
) -> None:
    """Write deterministic formatted JSON."""

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_powerbi_bundle(
    *,
    source_path: Path,
    output_directory: Path,
    source_id: str,
    source_as_of_date: str | None = None,
    ranking_limit: int = 10,
) -> dict[str, Any]:
    """Generate the complete Gujarat Power BI data package."""

    if ranking_limit < 1:
        raise ValueError("Ranking limit must be at least 1.")

    source_path = Path(source_path)
    output_directory = Path(output_directory)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    district_path = output_directory / DISTRICT_DATA_FILE
    metadata_path = output_directory / DISTRICT_METADATA_FILE
    summary_path = output_directory / EXECUTIVE_SUMMARY_FILE
    ranking_path = output_directory / RANKING_VIEW_FILE
    dictionary_path = output_directory / DATA_DICTIONARY_FILE
    manifest_path = output_directory / MANIFEST_FILE

    district_frame = build_gujarat_district_dataset(
        source_path,
    )
    analytical_frame = add_district_analytical_metrics(
        district_frame,
    )

    analytical_frame.to_csv(
        district_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    metadata = create_output_metadata(
        frame=analytical_frame,
        source_path=source_path,
        output_path=district_path,
        source_id=source_id,
        source_as_of_date=source_as_of_date,
    )
    _write_json(
        metadata_path,
        metadata,
    )

    executive_summary = build_executive_summary(
        analytical_frame,
    )
    executive_summary.update(
        {
            "source_id": source_id,
            "source_file_name": source_path.name,
            "source_sha256": sha256_file(source_path),
            "source_as_of_date": source_as_of_date,
            "generated_at_utc": metadata["generated_at_utc"],
        }
    )
    _write_json(
        summary_path,
        executive_summary,
    )

    ranking_frame = build_ranking_views(
        analytical_frame,
        limit=ranking_limit,
    )
    ranking_frame.to_csv(
        ranking_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    dictionary_frame = build_data_dictionary()
    dictionary_frame.to_csv(
        dictionary_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    generated_files = {
        "district_data": district_path,
        "district_metadata": metadata_path,
        "executive_summary": summary_path,
        "district_rankings": ranking_path,
        "data_dictionary": dictionary_path,
    }

    manifest = {
        "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_name": "Gujarat MSME Power BI Data Package",
        "generated_at_utc": metadata["generated_at_utc"],
        "source": {
            "source_id": source_id,
            "file_name": source_path.name,
            "sha256": sha256_file(source_path),
            "as_of_date": source_as_of_date,
        },
        "district_row_count": len(analytical_frame),
        "ranking_row_count": len(ranking_frame),
        "data_dictionary_row_count": len(dictionary_frame),
        "base_columns": list(REQUIRED_COLUMNS),
        "derived_columns": list(DERIVED_COLUMNS),
        "files": {
            key: {
                "file_name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for key, path in generated_files.items()
        },
        "limitations": [
            "The package contains aggregate district registration counts.",
            "It contains no enterprise-level identifiable records.",
            "Registration counts do not represent active-business counts.",
            "Registration counts do not represent revenue or profitability.",
            "Source snapshots with incompatible dates must not be combined.",
        ],
    }

    _write_json(
        manifest_path,
        manifest,
    )

    return manifest
