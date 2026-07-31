"""Generate and validate the real Gujarat MSME dashboard release."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from msme_dashboard.district_metrics import (
    DERIVED_COLUMNS,
    add_district_analytical_metrics,
    validate_analytical_metrics,
)
from msme_dashboard.district_pipeline import REQUIRED_COLUMNS
from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.powerbi_bundle import (
    DATA_DICTIONARY_FILE,
    DISTRICT_DATA_FILE,
    DISTRICT_METADATA_FILE,
    EXECUTIVE_SUMMARY_FILE,
    RANKING_VIEW_FILE,
    build_data_dictionary,
    build_executive_summary,
    build_ranking_views,
)
from msme_dashboard.powerbi_bundle import (
    MANIFEST_FILE as DATA_PACKAGE_MANIFEST_FILE,
)
from msme_dashboard.powerbi_implementation_package import (
    PACKAGE_MANIFEST_FILE as IMPLEMENTATION_MANIFEST_FILE,
)
from msme_dashboard.powerbi_implementation_package import (
    validate_written_implementation_package,
    write_powerbi_implementation_package,
)
from msme_dashboard.processed_output import create_output_metadata
from msme_dashboard.scoped_source import (
    build_gujarat_scoped_dataset,
    build_scope_qualification_summary,
)

RELEASE_SCHEMA_VERSION = "1.0"

RELEASE_MANIFEST_FILE = "gujarat_msme_real_data_release_manifest.json"
RELEASE_SUMMARY_FILE = "M3_REAL_DATA_RELEASE_SUMMARY.md"
RELEASE_VALIDATION_FILE = "gujarat_msme_real_data_validation.json"
QUALIFICATION_COPY_FILE = "source_qualification.json"

DATA_PACKAGE_DIRECTORY = "data_package"
DASHBOARD_DIRECTORY = "dashboard_implementation"


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


def load_source_qualification(
    path: Path,
) -> dict[str, Any]:
    """Load and validate the Gujarat-scope qualification."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Source qualification does not exist: {path}")

    qualification = json.loads(path.read_text(encoding="utf-8"))

    required_fields = {
        "source_id",
        "source_url",
        "licence",
        "retrieval_date",
        "source_sha256",
        "qualification_status",
        "privacy_classification",
    }

    missing = sorted(required_fields - set(qualification))

    if missing:
        raise ValueError("Qualification is missing required fields: " + ", ".join(missing))

    if qualification["qualification_status"] != ("qualified_for_gujarat_scope_only"):
        raise ValueError("Source is not qualified for Gujarat scope.")

    if qualification["privacy_classification"] != ("public_aggregate_district_data"):
        raise ValueError("Source privacy classification is not approved.")

    return qualification


def _write_data_package(
    *,
    analytical_frame: pd.DataFrame,
    source_path: Path,
    qualification: dict[str, Any],
    output_directory: Path,
    ranking_limit: int,
) -> dict[str, Any]:
    """Write the real Gujarat Power BI data package."""

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    district_path = output_directory / DISTRICT_DATA_FILE
    metadata_path = output_directory / DISTRICT_METADATA_FILE
    executive_path = output_directory / EXECUTIVE_SUMMARY_FILE
    rankings_path = output_directory / RANKING_VIEW_FILE
    dictionary_path = output_directory / DATA_DICTIONARY_FILE
    manifest_path = output_directory / DATA_PACKAGE_MANIFEST_FILE

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
        source_id=qualification["source_id"],
        source_as_of_date=qualification.get("source_as_of_date"),
    )

    metadata.update(
        {
            "retrieval_date": qualification["retrieval_date"],
            "qualification_status": qualification["qualification_status"],
            "source_url": qualification["source_url"],
            "licence": qualification["licence"],
            "national_scope_limitation": (
                "The source contains conflicting national "
                "state/district-code keys and is qualified "
                "only for Gujarat district analysis."
            ),
        }
    )

    _write_json(metadata_path, metadata)

    executive_summary = build_executive_summary(analytical_frame)

    executive_summary.update(
        {
            "source_id": qualification["source_id"],
            "source_file_name": source_path.name,
            "source_sha256": sha256_file(source_path),
            "source_as_of_date": qualification.get("source_as_of_date"),
            "retrieval_date": qualification["retrieval_date"],
            "qualification_status": qualification["qualification_status"],
            "generated_at_utc": metadata["generated_at_utc"],
        }
    )

    _write_json(
        executive_path,
        executive_summary,
    )

    rankings = build_ranking_views(
        analytical_frame,
        limit=ranking_limit,
    )

    rankings.to_csv(
        rankings_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    dictionary = build_data_dictionary()

    dictionary.to_csv(
        dictionary_path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    files = {
        "district_data": district_path,
        "district_metadata": metadata_path,
        "executive_summary": executive_path,
        "district_rankings": rankings_path,
        "data_dictionary": dictionary_path,
    }

    manifest = {
        "bundle_schema_version": "1.0",
        "bundle_name": ("Gujarat MSME Real Data Power BI Package"),
        "generated_at_utc": metadata["generated_at_utc"],
        "source": {
            "source_id": qualification["source_id"],
            "file_name": source_path.name,
            "sha256": sha256_file(source_path),
            "source_as_of_date": qualification.get("source_as_of_date"),
            "retrieval_date": qualification["retrieval_date"],
            "qualification_status": qualification["qualification_status"],
        },
        "district_row_count": len(analytical_frame),
        "ranking_row_count": len(rankings),
        "data_dictionary_row_count": len(dictionary),
        "base_columns": list(REQUIRED_COLUMNS),
        "derived_columns": list(DERIVED_COLUMNS),
        "files": {
            key: {
                "file_name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for key, path in files.items()
        },
        "limitations": [
            ("The source is qualified only for Gujarat district-level aggregate analysis."),
            ("The national source contains nine conflicting state/district-code key groups."),
            ("The source provides no confirmed fixed reporting date."),
            ("The retrieval date must not be represented as the source reporting date."),
            (
                "Registration counts do not represent active "
                "businesses, revenue, profitability or employment."
            ),
        ],
    }

    _write_json(manifest_path, manifest)

    return manifest


def build_release_summary(
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    """Return the real-data release summary document."""

    totals = validation["registration_totals"]
    highest = validation["highest_registered_district"]
    lowest = validation["lowest_registered_district"]

    return f"""# M3 — Gujarat MSME Real Data Candidate Release

## Release status

**Candidate for internal Power BI implementation and validation.**

This release is not approved for public dashboard publication until
the final human review and acceptance checklist are completed.

## Source qualification

- Source ID: `{manifest["source"]["source_id"]}`
- Source file: `{manifest["source"]["file_name"]}`
- Source SHA-256: `{manifest["source"]["sha256"]}`
- Retrieval date: `{manifest["source"]["retrieval_date"]}`
- Fixed source reporting date: **Not provided**
- Qualification: `qualified_for_gujarat_scope_only`

The source contains conflicting national state/district-code keys.
No conflicting keys occur within the Gujarat subset.

The complete national file is preserved without automatic deletion,
merging or reconciliation of conflicting records.

## Gujarat release totals

- Districts: **{validation["district_count"]}**
- Micro registrations: **{totals["micro"]:,}**
- Small registrations: **{totals["small"]:,}**
- Medium registrations: **{totals["medium"]:,}**
- Total registrations: **{totals["total"]:,}**

## Highest and lowest districts

- Highest: **{highest["district_name"]}**
  ({highest["total"]:,})
- Lowest: **{lowest["district_name"]}**
  ({lowest["total"]:,})

## Release contents

### Data package

- Main analytical district CSV
- Dataset metadata JSON
- Gujarat executive summary JSON
- Top and Bottom district ranking CSV
- Power BI data dictionary
- Data-package manifest and checksums

### Dashboard implementation package

- Five visible dashboard page specifications
- Two hidden technical pages
- DAX measure library
- Prototype StackOre theme
- Pixel-level page layouts
- Visual interaction rules
- Tooltip and drill-through specification
- Acceptance criteria
- Implementation guide
- Implementation manifest and checksums

## Restrictions

- Do not use this source for national district ranking.
- Do not describe registrations as active businesses.
- Do not infer employment, activity type, revenue or profitability.
- Do not represent the retrieval date as a reporting date.
- Do not introduce enterprise-level identifiable records.
- Do not publish until the M3 acceptance checklist is complete.
"""


def write_real_dashboard_release(
    *,
    source_path: Path,
    qualification_path: Path,
    output_directory: Path,
    ranking_limit: int = 10,
) -> dict[str, Any]:
    """Generate the complete real-data dashboard candidate release."""

    if ranking_limit < 1:
        raise ValueError("Ranking limit must be at least 1.")

    source_path = Path(source_path)
    qualification_path = Path(qualification_path)
    output_directory = Path(output_directory)

    qualification = load_source_qualification(qualification_path)

    source_checksum = sha256_file(source_path)

    if source_checksum != qualification["source_sha256"]:
        raise ValueError("Source checksum does not match the qualification.")

    scope_summary = build_scope_qualification_summary(source_path)

    if not scope_summary["qualified_for_gujarat_scope"]:
        raise ValueError("Source failed Gujarat-scope qualification.")

    gujarat = build_gujarat_scoped_dataset(source_path)

    analytical = add_district_analytical_metrics(gujarat)

    validate_analytical_metrics(analytical)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_directory = output_directory / DATA_PACKAGE_DIRECTORY
    dashboard_directory = output_directory / DASHBOARD_DIRECTORY

    data_manifest = _write_data_package(
        analytical_frame=analytical,
        source_path=source_path,
        qualification=qualification,
        output_directory=data_directory,
        ranking_limit=ranking_limit,
    )

    dashboard_manifest = write_powerbi_implementation_package(dashboard_directory)

    qualification_copy = output_directory / QUALIFICATION_COPY_FILE

    shutil.copyfile(
        qualification_path,
        qualification_copy,
    )

    highest = analytical.sort_values(
        by=[
            "district_rank_total",
        ],
        kind="stable",
    ).iloc[0]

    lowest = analytical.sort_values(
        by=[
            "district_rank_total_ascending",
        ],
        kind="stable",
    ).iloc[0]

    validation = {
        "validation_schema_version": "1.0",
        "source_sha256_verified": True,
        "qualified_for_gujarat_scope": True,
        "national_conflicting_key_group_count": (
            scope_summary["national_conflicting_key_group_count"]
        ),
        "national_conflicting_key_row_count": (scope_summary["national_conflicting_key_row_count"]),
        "gujarat_conflicting_key_group_count": (
            scope_summary["gujarat_conflicting_key_group_count"]
        ),
        "district_count": len(analytical),
        "registration_totals": {
            "medium": int(analytical["medium"].sum()),
            "micro": int(analytical["micro"].sum()),
            "small": int(analytical["small"].sum()),
            "total": int(analytical["total"].sum()),
        },
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
        "category_share_total_pct": round(
            float(
                analytical[
                    [
                        "micro_share_pct",
                        "small_share_pct",
                        "medium_share_pct",
                    ]
                ]
                .sum(axis=1)
                .mean()
            ),
            4,
        ),
        "source_as_of_date": qualification.get("source_as_of_date"),
        "retrieval_date": qualification["retrieval_date"],
        "publication_allowed": False,
    }

    validation_path = output_directory / RELEASE_VALIDATION_FILE
    _write_json(validation_path, validation)

    release_summary = build_release_summary(
        manifest=data_manifest,
        validation=validation,
    )

    release_summary_path = output_directory / RELEASE_SUMMARY_FILE
    release_summary_path.write_text(
        release_summary,
        encoding="utf-8",
        newline="\n",
    )

    generated_files = {
        "source_qualification": qualification_copy,
        "release_validation": validation_path,
        "release_summary": release_summary_path,
        "data_package_manifest": (data_directory / DATA_PACKAGE_MANIFEST_FILE),
        "dashboard_implementation_manifest": (dashboard_directory / IMPLEMENTATION_MANIFEST_FILE),
    }

    release_manifest = {
        "release_schema_version": (RELEASE_SCHEMA_VERSION),
        "release_name": ("Gujarat MSME Real Dashboard Candidate"),
        "generated_at_utc": (datetime.now(UTC).replace(microsecond=0).isoformat()),
        "release_status": ("candidate_for_internal_powerbi_validation"),
        "publication_allowed": False,
        "source": data_manifest["source"],
        "scope_validation": scope_summary,
        "district_count": len(analytical),
        "registration_totals": validation["registration_totals"],
        "data_package": {
            "directory": DATA_PACKAGE_DIRECTORY,
            "manifest_file": (DATA_PACKAGE_MANIFEST_FILE),
            "file_count": len(data_manifest["files"]),
        },
        "dashboard_implementation": {
            "directory": DASHBOARD_DIRECTORY,
            "manifest_file": (IMPLEMENTATION_MANIFEST_FILE),
            "visible_page_count": (dashboard_manifest["visible_page_count"]),
            "technical_page_count": (dashboard_manifest["technical_page_count"]),
            "visual_count": dashboard_manifest["visual_count"],
        },
        "files": {
            key: {
                "relative_path": str(path.relative_to(output_directory)),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for key, path in generated_files.items()
        },
    }

    manifest_path = output_directory / RELEASE_MANIFEST_FILE
    _write_json(manifest_path, release_manifest)

    return release_manifest


def validate_written_real_dashboard_release(
    output_directory: Path,
) -> dict[str, Any]:
    """Validate a generated real-data dashboard release."""

    output_directory = Path(output_directory)
    manifest_path = output_directory / RELEASE_MANIFEST_FILE

    if not manifest_path.exists():
        raise FileNotFoundError(f"Release manifest does not exist: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for details in manifest["files"].values():
        path = output_directory / details["relative_path"]

        if not path.exists():
            raise FileNotFoundError(f"Release file does not exist: {path}")

        if path.stat().st_size != details["size_bytes"]:
            raise ValueError(f"File size mismatch for {path.name}.")

        if sha256_file(path) != details["sha256"]:
            raise ValueError(f"Checksum mismatch for {path.name}.")

    data_directory = output_directory / DATA_PACKAGE_DIRECTORY

    data = pd.read_csv(
        data_directory / DISTRICT_DATA_FILE,
        dtype={
            "state_id": str,
            "lg_dt_code": str,
        },
    )

    validate_analytical_metrics(data)

    if len(data) != manifest["district_count"]:
        raise ValueError("Release district count does not match.")

    totals = {
        "medium": int(data["medium"].sum()),
        "micro": int(data["micro"].sum()),
        "small": int(data["small"].sum()),
        "total": int(data["total"].sum()),
    }

    if totals != manifest["registration_totals"]:
        raise ValueError("Release registration totals do not match.")

    validate_written_implementation_package(output_directory / DASHBOARD_DIRECTORY)

    if manifest["publication_allowed"]:
        raise ValueError("Candidate release must not permit publication.")

    return manifest
