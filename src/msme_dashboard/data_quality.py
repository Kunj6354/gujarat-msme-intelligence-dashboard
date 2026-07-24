"""Reusable dataframe quality checks for MSME datasets."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


class DataQualityError(ValueError):
    """Raised when a dataset violates a required quality rule."""


def require_non_empty(frame: pd.DataFrame) -> None:
    """Require a dataframe to contain at least one row."""

    if frame.empty:
        raise DataQualityError("Dataset must contain at least one row.")


def require_columns(
    frame: pd.DataFrame,
    required_columns: Sequence[str],
) -> None:
    """Require all specified columns to exist."""

    missing_columns = [column for column in required_columns if column not in frame.columns]

    if missing_columns:
        raise DataQualityError("Missing required columns: " + ", ".join(missing_columns))


def require_no_nulls(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> None:
    """Require selected columns to contain no null values."""

    require_columns(frame, columns)

    violations = {
        column: int(frame[column].isna().sum()) for column in columns if frame[column].isna().any()
    }

    if violations:
        details = ", ".join(f"{column}={count}" for column, count in violations.items())
        raise DataQualityError(f"Null values found in required fields: {details}")


def require_unique(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> None:
    """Require the selected columns to form a unique key."""

    if not columns:
        return

    require_columns(frame, columns)

    duplicate_mask = frame.duplicated(
        subset=list(columns),
        keep=False,
    )

    if duplicate_mask.any():
        duplicate_count = int(duplicate_mask.sum())
        key_name = ", ".join(columns)

        raise DataQualityError(f"Duplicate rows found for key [{key_name}]: {duplicate_count}")


def require_nonnegative(
    frame: pd.DataFrame,
    columns: Sequence[str],
) -> None:
    """Require selected numeric columns to contain no negative values."""

    require_columns(frame, columns)

    for column in columns:
        original = frame[column]
        numeric = pd.to_numeric(original, errors="coerce")

        invalid_numeric = original.notna() & numeric.isna()

        if invalid_numeric.any():
            raise DataQualityError(
                f"Column {column!r} contains {int(invalid_numeric.sum())} non-numeric values."
            )

        negative_values = numeric < 0

        if negative_values.any():
            raise DataQualityError(
                f"Column {column!r} contains {int(negative_values.sum())} negative values."
            )


def run_basic_checks(
    frame: pd.DataFrame,
    *,
    required_columns: Sequence[str] = (),
    non_null_columns: Sequence[str] = (),
    unique_key: Sequence[str] = (),
    nonnegative_columns: Sequence[str] = (),
) -> None:
    """Run the standard reusable dataset-quality checks."""

    require_non_empty(frame)
    require_columns(frame, required_columns)
    require_no_nulls(frame, non_null_columns)
    require_unique(frame, unique_key)
    require_nonnegative(frame, nonnegative_columns)
