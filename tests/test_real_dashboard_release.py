"""Tests for the real Gujarat dashboard release package."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.real_dashboard_release import (
    DASHBOARD_DIRECTORY,
    DATA_PACKAGE_DIRECTORY,
    RELEASE_MANIFEST_FILE,
    RELEASE_SUMMARY_FILE,
    RELEASE_VALIDATION_FILE,
    load_source_qualification,
    validate_written_real_dashboard_release,
    write_real_dashboard_release,
)


def make_source(path: Path) -> None:
    """Write Gujarat rows plus an out-of-scope conflict."""

    frame = pd.DataFrame(
        {
            "state_name": [
                "GUJARAT",
                "GUJARAT",
                "RAJASTHAN",
                "RAJASTHAN",
            ],
            "state_id": ["24", "24", "8", "8"],
            "district_name": [
                "AHMEDABAD",
                "VADODARA",
                "JAIPUR",
                "DUDU",
            ],
            "lg_dt_code": [
                "474",
                "486",
                "102",
                "102",
            ],
            "medium": [10, 20, 100, 5],
            "micro": [100, 200, 1000, 50],
            "small": [20, 30, 200, 10],
            "total": [130, 250, 1300, 65],
        }
    )

    frame.to_csv(path, index=False)


def make_qualification(
    source: Path,
    path: Path,
) -> None:
    """Write a valid Gujarat-scope qualification."""

    value = {
        "qualification_schema_version": "1.0",
        "source_id": "OGD_UDYAM_DISTRICT",
        "source_url": "https://example.gov/source",
        "licence": "GODL-India",
        "retrieval_date": "2026-07-30",
        "source_as_of_date": None,
        "source_sha256": sha256_file(source),
        "qualification_status": ("qualified_for_gujarat_scope_only"),
        "privacy_classification": ("public_aggregate_district_data"),
    }

    path.write_text(
        json.dumps(value),
        encoding="utf-8",
    )


def test_loads_valid_qualification(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    qualification = tmp_path / "qualification.json"

    make_source(source)
    make_qualification(source, qualification)

    value = load_source_qualification(qualification)

    assert value["qualification_status"] == ("qualified_for_gujarat_scope_only")


def test_generates_complete_candidate_release(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    qualification = tmp_path / "qualification.json"
    output = tmp_path / "release"

    make_source(source)
    make_qualification(source, qualification)

    manifest = write_real_dashboard_release(
        source_path=source,
        qualification_path=qualification,
        output_directory=output,
        ranking_limit=2,
    )

    assert manifest["district_count"] == 2
    assert manifest["registration_totals"] == {
        "medium": 30,
        "micro": 300,
        "small": 50,
        "total": 380,
    }
    assert manifest["publication_allowed"] is False
    assert manifest["scope_validation"]["national_conflicting_key_group_count"] == 1
    assert manifest["scope_validation"]["gujarat_conflicting_key_group_count"] == 0

    assert (output / RELEASE_MANIFEST_FILE).exists()
    assert (output / RELEASE_SUMMARY_FILE).exists()
    assert (output / RELEASE_VALIDATION_FILE).exists()
    assert (output / DATA_PACKAGE_DIRECTORY).is_dir()
    assert (output / DASHBOARD_DIRECTORY).is_dir()

    validated = validate_written_real_dashboard_release(output)

    assert validated == manifest


def test_rejects_source_checksum_mismatch(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    qualification = tmp_path / "qualification.json"
    output = tmp_path / "release"

    make_source(source)
    make_qualification(source, qualification)

    source.write_text(
        source.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="checksum",
    ):
        write_real_dashboard_release(
            source_path=source,
            qualification_path=qualification,
            output_directory=output,
        )


def test_validator_detects_modified_release_file(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    qualification = tmp_path / "qualification.json"
    output = tmp_path / "release"

    make_source(source)
    make_qualification(source, qualification)

    write_real_dashboard_release(
        source_path=source,
        qualification_path=qualification,
        output_directory=output,
    )

    summary = output / RELEASE_SUMMARY_FILE
    summary.write_text(
        summary.read_text(encoding="utf-8") + "\nmodified",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="size mismatch|Checksum mismatch",
    ):
        validate_written_real_dashboard_release(output)
