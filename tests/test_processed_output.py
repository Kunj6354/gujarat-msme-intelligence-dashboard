import json
from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.processed_output import (
    create_output_metadata,
    summarise_gujarat_dataset,
    write_processed_district_outputs,
)


def make_national_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state_name": [
                "GUJARAT",
                "GUJARAT",
                "MAHARASHTRA",
            ],
            "state_id": ["24", "24", "27"],
            "district_name": [
                "VADODARA",
                "AHMEDABAD",
                "PUNE",
            ],
            "lg_dt_code": ["486", "474", "521"],
            "medium": [2, 1, 3],
            "micro": [200, 100, 300],
            "small": [20, 10, 30],
            "total": [222, 111, 333],
        }
    )


def make_gujarat_frame() -> pd.DataFrame:
    return make_national_frame().iloc[:2].copy()


def test_summarise_gujarat_dataset_returns_expected_totals() -> None:
    summary = summarise_gujarat_dataset(
        make_gujarat_frame(),
    )

    assert summary == {
        "row_count": 2,
        "district_count": 2,
        "registration_totals": {
            "micro": 300,
            "small": 30,
            "medium": 3,
            "total": 333,
        },
    }


def test_summarise_gujarat_dataset_rejects_other_states() -> None:
    with pytest.raises(
        ValueError,
        match="only Gujarat",
    ):
        summarise_gujarat_dataset(
            make_national_frame(),
        )


def test_create_output_metadata_records_provenance(
    tmp_path: Path,
) -> None:
    source = tmp_path / "national.csv"
    output = tmp_path / "gujarat.csv"

    make_national_frame().to_csv(
        source,
        index=False,
    )

    metadata = create_output_metadata(
        frame=make_gujarat_frame(),
        source_path=source,
        output_path=output,
        source_as_of_date="2026-07-21",
    )

    assert metadata["schema_version"] == "1.0"
    assert metadata["source_id"] == "OGD_UDYAM_DISTRICT"
    assert metadata["source_file_name"] == "national.csv"
    assert metadata["output_file_name"] == "gujarat.csv"
    assert metadata["source_sha256"] == sha256_file(source)
    assert metadata["source_as_of_date"] == "2026-07-21"
    assert metadata["row_count"] == 2
    assert metadata["district_count"] == 2
    assert metadata["registration_totals"]["total"] == 333
    assert metadata["generated_at_utc"].endswith("+00:00")


def test_write_processed_outputs_creates_csv_and_json(
    tmp_path: Path,
) -> None:
    source = tmp_path / "national.csv"
    output_csv = tmp_path / "processed" / "gujarat.csv"
    metadata_json = tmp_path / "processed" / "gujarat.metadata.json"

    make_national_frame().to_csv(
        source,
        index=False,
    )

    returned_metadata = write_processed_district_outputs(
        source_path=source,
        output_csv_path=output_csv,
        metadata_json_path=metadata_json,
        source_as_of_date="2026-07-21",
    )

    assert output_csv.exists()
    assert metadata_json.exists()

    processed = pd.read_csv(
        output_csv,
        dtype={"state_id": str, "lg_dt_code": str},
    )

    assert list(processed["district_name"]) == [
        "AHMEDABAD",
        "VADODARA",
    ]
    assert set(processed["state_name"]) == {"GUJARAT"}
    assert len(processed) == 2

    saved_metadata = json.loads(metadata_json.read_text(encoding="utf-8"))

    assert saved_metadata == returned_metadata
    assert saved_metadata["row_count"] == 2
    assert saved_metadata["district_count"] == 2
    assert saved_metadata["registration_totals"]["total"] == 333


def test_processed_csv_has_expected_column_order(
    tmp_path: Path,
) -> None:
    source = tmp_path / "national.csv"
    output_csv = tmp_path / "gujarat.csv"
    metadata_json = tmp_path / "gujarat.metadata.json"

    make_national_frame().to_csv(
        source,
        index=False,
    )

    write_processed_district_outputs(
        source_path=source,
        output_csv_path=output_csv,
        metadata_json_path=metadata_json,
    )

    processed = pd.read_csv(output_csv)

    assert list(processed.columns) == [
        "state_name",
        "state_id",
        "district_name",
        "lg_dt_code",
        "medium",
        "micro",
        "small",
        "total",
    ]
