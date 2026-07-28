from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.data_quality import DataQualityError
from msme_dashboard.district_pipeline import (
    build_gujarat_district_dataset,
    filter_gujarat_districts,
    load_district_dataset,
    validate_district_dataset,
)


def make_valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state_name": ["GUJARAT", "GUJARAT", "MAHARASHTRA"],
            "state_id": ["24", "24", "27"],
            "district_name": ["VADODARA", "AHMEDABAD", "PUNE"],
            "lg_dt_code": ["486", "474", "521"],
            "medium": [20, 30, 25],
            "micro": [1000, 2000, 1500],
            "small": [100, 200, 150],
            "total": [1120, 2230, 1675],
        }
    )


def test_validate_district_dataset_accepts_valid_data() -> None:
    frame = make_valid_frame()

    validate_district_dataset(frame)


def test_filter_gujarat_districts_returns_only_gujarat() -> None:
    frame = make_valid_frame()

    result = filter_gujarat_districts(frame)

    assert list(result["district_name"]) == [
        "AHMEDABAD",
        "VADODARA",
    ]
    assert set(result["state_name"]) == {"GUJARAT"}
    assert len(result) == 2


def test_validate_district_dataset_rejects_wrong_total() -> None:
    frame = make_valid_frame()
    frame.loc[0, "total"] = 999

    with pytest.raises(
        DataQualityError,
        match="micro \\+ small \\+ medium",
    ):
        validate_district_dataset(frame)


def test_validate_district_dataset_rejects_duplicate_key() -> None:
    frame = make_valid_frame()

    duplicate = frame.iloc[[0]].copy()
    frame = pd.concat([frame, duplicate], ignore_index=True)

    with pytest.raises(
        DataQualityError,
        match="Duplicate rows",
    ):
        validate_district_dataset(frame)


def test_load_district_dataset_converts_counts_to_integers(
    tmp_path: Path,
) -> None:
    source = tmp_path / "districts.csv"

    make_valid_frame().astype(str).to_csv(
        source,
        index=False,
    )

    result = load_district_dataset(source)

    assert result["micro"].dtype == "int64"
    assert result["small"].dtype == "int64"
    assert result["medium"].dtype == "int64"
    assert result["total"].dtype == "int64"


def test_build_gujarat_district_dataset_from_csv(
    tmp_path: Path,
) -> None:
    source = tmp_path / "districts.csv"

    make_valid_frame().to_csv(
        source,
        index=False,
    )

    result = build_gujarat_district_dataset(source)

    assert len(result) == 2
    assert list(result["district_name"]) == [
        "AHMEDABAD",
        "VADODARA",
    ]


def test_filter_gujarat_districts_rejects_missing_gujarat() -> None:
    frame = make_valid_frame()
    frame = frame[frame["state_name"].eq("MAHARASHTRA")]

    with pytest.raises(
        DataQualityError,
        match="No Gujarat district records",
    ):
        filter_gujarat_districts(frame)
