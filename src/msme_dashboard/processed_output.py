"""Generate processed Gujarat district data and audit metadata."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from msme_dashboard.district_metrics import (
    DERIVED_COLUMNS,
    add_district_analytical_metrics,
)
from msme_dashboard.district_pipeline import (
    build_gujarat_district_dataset,
    validate_district_dataset,
)
from msme_dashboard.file_inventory import sha256_file

SCHEMA_VERSION = "1.0"
DEFAULT_SOURCE_ID = "OGD_UDYAM_DISTRICT"


def summarise_gujarat_dataset(
    frame: pd.DataFrame,
) -> dict[str, Any]:
    """Return summary statistics for a Gujarat district dataset."""

    validate_district_dataset(frame)

    state_names = {str(value).strip().casefold() for value in frame["state_name"]}

    if state_names != {"gujarat"}:
        raise ValueError("Processed output must contain only Gujarat records.")

    totals = {column: int(frame[column].sum()) for column in ("micro", "small", "medium", "total")}

    return {
        "row_count": len(frame),
        "district_count": int(frame["lg_dt_code"].nunique()),
        "registration_totals": totals,
    }


def create_output_metadata(
    *,
    frame: pd.DataFrame,
    source_path: Path,
    output_path: Path,
    source_id: str = DEFAULT_SOURCE_ID,
    source_as_of_date: str | None = None,
) -> dict[str, Any]:
    """Create provenance and summary metadata for processed output."""

    summary = summarise_gujarat_dataset(frame)

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_name": "Gujarat District MSME Aggregate Dataset",
        "source_id": source_id,
        "source_file_name": source_path.name,
        "source_sha256": sha256_file(source_path),
        "source_as_of_date": source_as_of_date,
        "generated_at_utc": generated_at,
        "output_file_name": output_path.name,
        "columns": list(frame.columns),
        "derived_columns": [column for column in DERIVED_COLUMNS if column in frame.columns],
        **summary,
        "transformations": [
            "Loaded the official national district aggregate CSV.",
            "Trimmed column names and required text fields.",
            "Converted registration count columns to integers.",
            "Validated non-negative registration counts.",
            "Validated unique state and district-code keys.",
            "Validated total equals micro plus small plus medium.",
            "Filtered records to Gujarat only.",
            "Calculated district rankings and category shares.",
            "Calculated each district's contribution to the Gujarat total.",
            "Assigned dominant-category and Top/Bottom 10 indicators.",
            "Sorted records by descending total registrations.",
        ],
        "limitations": [
            "Registration counts do not prove that enterprises are currently active.",
            "Registration counts do not represent revenue or profitability.",
            "The output reflects the reporting date of the source dataset.",
        ],
    }


def write_processed_district_outputs(
    *,
    source_path: Path,
    output_csv_path: Path,
    metadata_json_path: Path,
    source_id: str = DEFAULT_SOURCE_ID,
    source_as_of_date: str | None = None,
) -> dict[str, Any]:
    """Generate the processed Gujarat CSV and metadata JSON."""

    frame = build_gujarat_district_dataset(source_path)
    frame = add_district_analytical_metrics(frame)

    output_csv_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    metadata_json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output_csv_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    metadata = create_output_metadata(
        frame=frame,
        source_path=source_path,
        output_path=output_csv_path,
        source_id=source_id,
        source_as_of_date=source_as_of_date,
    )

    metadata_json_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return metadata
