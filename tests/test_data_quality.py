import pandas as pd
import pytest

from msme_dashboard.data_quality import (
    DataQualityError,
    run_basic_checks,
)


def test_basic_quality_checks_accept_valid_dataset() -> None:
    frame = pd.DataFrame(
        {
            "district": ["Ahmedabad", "Vadodara"],
            "registrations": [100, 75],
        }
    )

    run_basic_checks(
        frame,
        required_columns=("district", "registrations"),
        non_null_columns=("district",),
        unique_key=("district",),
        nonnegative_columns=("registrations",),
    )


def test_basic_quality_checks_reject_duplicate_key() -> None:
    frame = pd.DataFrame(
        {
            "district": ["Ahmedabad", "Ahmedabad"],
            "registrations": [100, 75],
        }
    )

    with pytest.raises(
        DataQualityError,
        match="Duplicate rows",
    ):
        run_basic_checks(
            frame,
            unique_key=("district",),
        )


def test_basic_quality_checks_reject_negative_value() -> None:
    frame = pd.DataFrame(
        {
            "district": ["Ahmedabad"],
            "registrations": [-1],
        }
    )

    with pytest.raises(
        DataQualityError,
        match="negative values",
    ):
        run_basic_checks(
            frame,
            nonnegative_columns=("registrations",),
        )


def test_basic_quality_checks_reject_missing_column() -> None:
    frame = pd.DataFrame(
        {
            "district": ["Ahmedabad"],
        }
    )

    with pytest.raises(
        DataQualityError,
        match="Missing required columns",
    ):
        run_basic_checks(
            frame,
            required_columns=("registrations",),
        )
