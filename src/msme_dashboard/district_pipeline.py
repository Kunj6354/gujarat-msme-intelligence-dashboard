"""Pipeline for the official district-level aggregate Udyam dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from msme_dashboard.data_quality import (
    DataQualityError,
    require_columns,
    require_non_empty,
    require_nonnegative,
    require_unique,
)

REQUIRED_COLUMNS = (
    "state_name",
    "state_id",
    "district_name",
    "lg_dt_code",
    "medium",
    "micro",
    "small",
    "total",
)

TEXT_COLUMNS = (
    "state_name",
    "state_id",
    "district_name",
    "lg_dt_code",
)

COUNT_COLUMNS = (
    "medium",
    "micro",
    "small",
    "total",
)


def _require_nonblank_text(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
) -> None:
    """Reject blank values in required text fields."""

    require_columns(frame, columns)

    for column in columns:
        blank_count = int(frame[column].astype("string").str.strip().fillna("").eq("").sum())

        if blank_count:
            raise DataQualityError(f"Column {column!r} contains {blank_count} blank values.")


def _convert_count_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert aggregate count columns to integers."""

    converted = frame.copy()

    for column in COUNT_COLUMNS:
        try:
            numeric = pd.to_numeric(
                converted[column],
                errors="raise",
            )
        except (TypeError, ValueError) as exc:
            raise DataQualityError(f"Column {column!r} contains non-numeric values.") from exc

        fractional = numeric.notna() & numeric.mod(1).ne(0)

        if fractional.any():
            raise DataQualityError(
                f"Column {column!r} contains {int(fractional.sum())} non-integer values."
            )

        converted[column] = numeric.astype("int64")

    return converted


def validate_district_dataset(frame: pd.DataFrame) -> None:
    """Validate the district aggregate dataset."""

    require_non_empty(frame)
    require_columns(frame, REQUIRED_COLUMNS)
    _require_nonblank_text(frame, TEXT_COLUMNS)
    require_nonnegative(frame, COUNT_COLUMNS)
    require_unique(
        frame,
        ("state_id", "lg_dt_code"),
    )

    expected_total = frame["micro"] + frame["small"] + frame["medium"]

    total_mismatches = frame["total"].ne(expected_total)

    if total_mismatches.any():
        raise DataQualityError(
            "The total column does not equal "
            "micro + small + medium for "
            f"{int(total_mismatches.sum())} rows."
        )


def load_district_dataset(path: Path) -> pd.DataFrame:
    """Load and validate an official district aggregate CSV."""

    if not path.exists():
        raise FileNotFoundError(f"District dataset does not exist: {path}")

    frame = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    frame.columns = [str(column).strip() for column in frame.columns]

    require_columns(frame, REQUIRED_COLUMNS)

    frame = frame.loc[:, REQUIRED_COLUMNS].copy()

    for column in TEXT_COLUMNS:
        frame[column] = frame[column].astype("string").str.strip()

    frame = _convert_count_columns(frame)
    validate_district_dataset(frame)

    return frame


def filter_gujarat_districts(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return validated Gujarat district records only."""

    validate_district_dataset(frame)

    gujarat = frame[
        frame["state_name"].astype("string").str.strip().str.casefold().eq("gujarat")
    ].copy()

    if gujarat.empty:
        raise DataQualityError("No Gujarat district records were found.")

    gujarat["state_name"] = "GUJARAT"

    gujarat = gujarat.sort_values(
        by=["district_name", "lg_dt_code"],
        kind="stable",
    ).reset_index(drop=True)

    validate_district_dataset(gujarat)

    return gujarat


def build_gujarat_district_dataset(
    source_path: Path,
) -> pd.DataFrame:
    """Load the national source and return Gujarat records."""

    national = load_district_dataset(source_path)
    return filter_gujarat_districts(national)
