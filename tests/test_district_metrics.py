"""Tests for Gujarat district analytical metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from msme_dashboard.data_quality import DataQualityError
from msme_dashboard.district_metrics import (
    add_district_analytical_metrics,
    validate_analytical_metrics,
)


def make_gujarat_frame() -> pd.DataFrame:
    """Return representative Gujarat district aggregate data."""

    return pd.DataFrame(
        {
            "state_name": [
                "GUJARAT",
                "GUJARAT",
                "GUJARAT",
                "GUJARAT",
            ],
            "state_id": ["24", "24", "24", "24"],
            "district_name": [
                "VADODARA",
                "AHMEDABAD",
                "SURAT",
                "ZERO DISTRICT",
            ],
            "lg_dt_code": ["486", "474", "492", "999"],
            "medium": [20, 10, 25, 0],
            "micro": [200, 100, 150, 0],
            "small": [30, 10, 25, 0],
            "total": [250, 120, 200, 0],
        }
    )


def test_add_metrics_ranks_districts_by_total() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    assert list(result["district_name"]) == [
        "VADODARA",
        "SURAT",
        "AHMEDABAD",
        "ZERO DISTRICT",
    ]

    assert list(result["district_rank_total"]) == [
        1,
        2,
        3,
        4,
    ]

    assert list(result["district_rank_total_ascending"]) == [
        4,
        3,
        2,
        1,
    ]


def test_add_metrics_calculates_category_shares() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    vadodara = result.loc[result["district_name"].eq("VADODARA")].iloc[0]

    assert vadodara["micro_share_pct"] == 80.0
    assert vadodara["small_share_pct"] == 12.0
    assert vadodara["medium_share_pct"] == 8.0


def test_add_metrics_calculates_gujarat_contribution() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    gujarat_total = 570

    vadodara = result.loc[result["district_name"].eq("VADODARA")].iloc[0]

    assert vadodara["gujarat_total_share_pct"] == pytest.approx(
        250 / gujarat_total * 100,
        abs=0.0001,
    )

    assert result["gujarat_total_share_pct"].sum() == pytest.approx(
        100,
        abs=0.01,
    )


def test_add_metrics_identifies_dominant_categories() -> None:
    frame = make_gujarat_frame()

    result = add_district_analytical_metrics(frame)

    dominant = dict(
        zip(
            result["district_name"],
            result["dominant_category"],
            strict=True,
        )
    )

    assert dominant["VADODARA"] == "MICRO"
    assert dominant["SURAT"] == "MICRO"
    assert dominant["ZERO DISTRICT"] == "NO_REGISTRATIONS"


def test_add_metrics_identifies_tied_category() -> None:
    frame = pd.DataFrame(
        {
            "state_name": ["GUJARAT"],
            "state_id": ["24"],
            "district_name": ["TIE DISTRICT"],
            "lg_dt_code": ["998"],
            "medium": [10],
            "micro": [10],
            "small": [5],
            "total": [25],
        }
    )

    result = add_district_analytical_metrics(frame)

    assert result.loc[0, "dominant_category"] == "TIE"


def test_zero_registration_district_has_zero_shares() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    zero_district = result.loc[result["district_name"].eq("ZERO DISTRICT")].iloc[0]

    assert zero_district["micro_share_pct"] == 0
    assert zero_district["small_share_pct"] == 0
    assert zero_district["medium_share_pct"] == 0
    assert zero_district["gujarat_total_share_pct"] == 0


def test_small_dataset_marks_all_rows_top_and_bottom() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    assert result["top_10_flag"].all()
    assert result["bottom_10_flag"].all()


def test_metrics_reject_non_gujarat_rows() -> None:
    frame = make_gujarat_frame()
    frame.loc[0, "state_name"] = "MAHARASHTRA"

    with pytest.raises(
        DataQualityError,
        match="Gujarat-only",
    ):
        add_district_analytical_metrics(frame)


def test_validation_rejects_invalid_percentage() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    result.loc[0, "micro_share_pct"] = 120

    with pytest.raises(
        DataQualityError,
        match="above 100",
    ):
        validate_analytical_metrics(result)


def test_validation_rejects_invalid_top_flag() -> None:
    result = add_district_analytical_metrics(
        make_gujarat_frame(),
    )

    result.loc[0, "top_10_flag"] = False

    with pytest.raises(
        DataQualityError,
        match="Top-10 flags",
    ):
        validate_analytical_metrics(result)
