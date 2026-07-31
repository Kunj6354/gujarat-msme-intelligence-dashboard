"""Tests for the complete Gujarat MSME Power BI package."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.district_metrics import (
    DERIVED_COLUMNS,
    add_district_analytical_metrics,
)
from msme_dashboard.district_pipeline import REQUIRED_COLUMNS
from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.powerbi_bundle import (
    DATA_DICTIONARY_FILE,
    DISTRICT_DATA_FILE,
    DISTRICT_METADATA_FILE,
    EXECUTIVE_SUMMARY_FILE,
    MANIFEST_FILE,
    RANKING_VIEW_FILE,
    build_data_dictionary,
    build_executive_summary,
    build_ranking_views,
    write_powerbi_bundle,
)


def make_national_frame() -> pd.DataFrame:
    """Return synthetic Gujarat and Maharashtra aggregate data."""

    rows: list[dict[str, object]] = []

    for index in range(1, 13):
        micro = index * 100
        small = index * 10
        medium = index

        rows.append(
            {
                "state_name": "GUJARAT",
                "state_id": "24",
                "district_name": f"DISTRICT {index:02d}",
                "lg_dt_code": str(400 + index),
                "medium": medium,
                "micro": micro,
                "small": small,
                "total": micro + small + medium,
            }
        )

    rows.append(
        {
            "state_name": "MAHARASHTRA",
            "state_id": "27",
            "district_name": "PUNE",
            "lg_dt_code": "521",
            "medium": 50,
            "micro": 5000,
            "small": 500,
            "total": 5550,
        }
    )

    return pd.DataFrame(rows)


def make_analytical_frame() -> pd.DataFrame:
    """Return Gujarat-only data with derived analytical fields."""

    frame = make_national_frame()
    gujarat = frame.loc[frame["state_name"].eq("GUJARAT")].copy()

    return add_district_analytical_metrics(gujarat)


def test_build_executive_summary_returns_expected_kpis() -> None:
    summary = build_executive_summary(
        make_analytical_frame(),
    )

    assert summary["geography"] == "Gujarat"
    assert summary["district_count"] == 12
    assert summary["total_registered_enterprises"] == 8658
    assert summary["micro_registered_enterprises"] == 7800
    assert summary["small_registered_enterprises"] == 780
    assert summary["medium_registered_enterprises"] == 78
    assert summary["average_registrations_per_district"] == 721.5

    assert summary["highest_registered_district"]["district_name"] == "DISTRICT 12"
    assert summary["highest_registered_district"]["total"] == 1332

    assert summary["lowest_registered_district"]["district_name"] == "DISTRICT 01"
    assert summary["lowest_registered_district"]["total"] == 111

    category_share_total = (
        summary["micro_share_pct"] + summary["small_share_pct"] + summary["medium_share_pct"]
    )

    assert category_share_total == pytest.approx(
        100,
        abs=0.01,
    )


def test_build_ranking_views_returns_top_and_bottom_groups() -> None:
    rankings = build_ranking_views(
        make_analytical_frame(),
        limit=3,
    )

    assert len(rankings) == 6

    top = rankings.loc[rankings["ranking_group"].eq("TOP")]
    bottom = rankings.loc[rankings["ranking_group"].eq("BOTTOM")]

    assert list(top["district_name"]) == [
        "DISTRICT 12",
        "DISTRICT 11",
        "DISTRICT 10",
    ]
    assert list(bottom["district_name"]) == [
        "DISTRICT 01",
        "DISTRICT 02",
        "DISTRICT 03",
    ]

    assert list(top["ranking_position"]) == [1, 2, 3]
    assert list(bottom["ranking_position"]) == [1, 2, 3]


def test_build_ranking_views_rejects_invalid_limit() -> None:
    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        build_ranking_views(
            make_analytical_frame(),
            limit=0,
        )


def test_data_dictionary_covers_all_output_fields() -> None:
    dictionary = build_data_dictionary()

    expected_fields = [
        *REQUIRED_COLUMNS,
        *DERIVED_COLUMNS,
    ]

    assert list(dictionary["field_name"]) == expected_fields
    assert len(dictionary) == 17

    derived_rows = dictionary.loc[dictionary["field_origin"].eq("derived")]

    assert set(derived_rows["field_name"]) == set(DERIVED_COLUMNS)
    assert derived_rows["calculation"].str.len().gt(0).all()


def test_write_powerbi_bundle_generates_complete_package(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "national.csv"
    output_directory = tmp_path / "powerbi"

    make_national_frame().to_csv(
        source_path,
        index=False,
    )

    returned_manifest = write_powerbi_bundle(
        source_path=source_path,
        output_directory=output_directory,
        source_id="OGD_UDYAM_DISTRICT",
        source_as_of_date="2026-07-21",
        ranking_limit=3,
    )

    expected_files = [
        DISTRICT_DATA_FILE,
        DISTRICT_METADATA_FILE,
        EXECUTIVE_SUMMARY_FILE,
        RANKING_VIEW_FILE,
        DATA_DICTIONARY_FILE,
        MANIFEST_FILE,
    ]

    for file_name in expected_files:
        assert (output_directory / file_name).exists()

    saved_manifest = json.loads((output_directory / MANIFEST_FILE).read_text(encoding="utf-8"))

    assert saved_manifest == returned_manifest
    assert saved_manifest["bundle_schema_version"] == "1.0"
    assert saved_manifest["district_row_count"] == 12
    assert saved_manifest["ranking_row_count"] == 6
    assert saved_manifest["data_dictionary_row_count"] == 17

    assert saved_manifest["source"]["source_id"] == "OGD_UDYAM_DISTRICT"
    assert saved_manifest["source"]["as_of_date"] == "2026-07-21"
    assert saved_manifest["source"]["sha256"] == sha256_file(source_path)

    for file_details in saved_manifest["files"].values():
        generated_path = output_directory / file_details["file_name"]

        assert generated_path.exists()
        assert file_details["sha256"] == sha256_file(generated_path)
        assert file_details["size_bytes"] == (generated_path.stat().st_size)

    district_data = pd.read_csv(
        output_directory / DISTRICT_DATA_FILE,
        dtype={
            "state_id": str,
            "lg_dt_code": str,
        },
    )

    assert len(district_data) == 12
    assert set(district_data["state_name"]) == {"GUJARAT"}
    assert list(district_data.columns) == [
        *REQUIRED_COLUMNS,
        *DERIVED_COLUMNS,
    ]
    assert district_data.iloc[0]["district_name"] == ("DISTRICT 12")
    assert district_data.iloc[-1]["district_name"] == ("DISTRICT 01")

    metadata = json.loads((output_directory / DISTRICT_METADATA_FILE).read_text(encoding="utf-8"))

    assert metadata["row_count"] == 12
    assert metadata["district_count"] == 12
    assert metadata["derived_columns"] == list(DERIVED_COLUMNS)
    assert metadata["registration_totals"] == {
        "medium": 78,
        "micro": 7800,
        "small": 780,
        "total": 8658,
    }

    executive_summary = json.loads(
        (output_directory / EXECUTIVE_SUMMARY_FILE).read_text(encoding="utf-8")
    )

    assert executive_summary["total_registered_enterprises"] == 8658
    assert executive_summary["highest_registered_district"]["district_name"] == "DISTRICT 12"

    ranking_data = pd.read_csv(output_directory / RANKING_VIEW_FILE)

    assert len(ranking_data) == 6
    assert set(ranking_data["ranking_group"]) == {
        "TOP",
        "BOTTOM",
    }

    dictionary = pd.read_csv(output_directory / DATA_DICTIONARY_FILE)

    assert len(dictionary) == 17
    assert list(dictionary["field_name"]) == [
        *REQUIRED_COLUMNS,
        *DERIVED_COLUMNS,
    ]


def test_bundle_contains_no_enterprise_level_fields(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "national.csv"
    output_directory = tmp_path / "powerbi"

    make_national_frame().to_csv(
        source_path,
        index=False,
    )

    write_powerbi_bundle(
        source_path=source_path,
        output_directory=output_directory,
        source_id="OGD_UDYAM_DISTRICT",
    )

    district_data = pd.read_csv(output_directory / DISTRICT_DATA_FILE)

    prohibited_fields = {
        "enterprise_name",
        "udyam_number",
        "owner_name",
        "mobile_number",
        "email",
        "address",
        "pin_code",
    }

    assert prohibited_fields.isdisjoint(district_data.columns)
