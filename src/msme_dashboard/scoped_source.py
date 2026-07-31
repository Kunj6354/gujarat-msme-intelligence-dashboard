"""Qualify aggregate sources for controlled Gujarat-only processing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from msme_dashboard.data_quality import DataQualityError
from msme_dashboard.district_pipeline import (
    REQUIRED_COLUMNS,
    validate_district_dataset,
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

SUPPORTED_ENCODINGS = (
    "utf-8-sig",
    "utf-8",
    "cp1252",
    "latin-1",
)


def read_aggregate_source(
    path: Path,
) -> tuple[pd.DataFrame, str]:
    """Read an aggregate CSV using controlled encoding fallback."""

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Aggregate source does not exist: {path}")

    last_error: UnicodeDecodeError | None = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            frame = pd.read_csv(
                path,
                encoding=encoding,
                dtype={
                    "state_id": str,
                    "lg_dt_code": str,
                },
            )
            return frame, encoding
        except UnicodeDecodeError as error:
            last_error = error

    raise DataQualityError(
        "Aggregate source could not be decoded using the "
        f"supported encodings: {SUPPORTED_ENCODINGS}"
    ) from last_error


def normalise_aggregate_source(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Validate schema and row-level rules without key uniqueness."""

    result = frame.copy()
    result.columns = [str(column).strip() for column in result.columns]

    missing = [column for column in REQUIRED_COLUMNS if column not in result.columns]

    if missing:
        raise DataQualityError("Missing required columns: " + ", ".join(missing))

    result = result.loc[:, REQUIRED_COLUMNS].copy()

    if result.empty:
        raise DataQualityError("Aggregate source must not be empty.")

    for column in TEXT_COLUMNS:
        if result[column].isna().any():
            raise DataQualityError(f"Column {column!r} contains null values.")

        result[column] = result[column].astype(str).str.strip()

        if result[column].eq("").any():
            raise DataQualityError(f"Column {column!r} contains blank values.")

    for column in COUNT_COLUMNS:
        numeric = pd.to_numeric(
            result[column],
            errors="coerce",
        )

        if numeric.isna().any():
            raise DataQualityError(f"Column {column!r} contains nonnumeric values.")

        if numeric.lt(0).any():
            raise DataQualityError(f"Column {column!r} contains negative values.")

        if numeric.mod(1).ne(0).any():
            raise DataQualityError(f"Column {column!r} must contain whole numbers.")

        result[column] = numeric.astype("int64")

    expected_total = result["micro"] + result["small"] + result["medium"]

    invalid_total = result["total"].ne(expected_total)

    if invalid_total.any():
        raise DataQualityError("Column 'total' must equal micro plus small plus medium.")

    return result


def classify_national_key_conflicts(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Classify conflicting national state/district-code keys."""

    normalised = normalise_aggregate_source(frame)

    duplicate_rows = normalised.loc[
        normalised.duplicated(
            subset=[
                "state_id",
                "lg_dt_code",
            ],
            keep=False,
        )
    ].copy()

    rows: list[dict[str, Any]] = []

    for key, group in duplicate_rows.groupby(
        [
            "state_id",
            "lg_dt_code",
        ],
        sort=True,
        dropna=False,
    ):
        state_id, lg_dt_code = key

        rows.append(
            {
                "state_id": str(state_id),
                "lg_dt_code": str(lg_dt_code),
                "row_count": len(group),
                "state_names": sorted(set(group["state_name"])),
                "district_names": sorted(set(group["district_name"])),
                "conflicting": (len(group.drop_duplicates(subset=list(REQUIRED_COLUMNS))) > 1),
                "contains_gujarat": (group["state_name"].str.casefold().eq("gujarat").any()),
            }
        )

    return pd.DataFrame(rows)


def build_gujarat_scoped_dataset(
    source_path: Path,
) -> pd.DataFrame:
    """Filter Gujarat before enforcing strict district uniqueness."""

    national, _ = read_aggregate_source(source_path)
    national = normalise_aggregate_source(national)

    gujarat = national.loc[national["state_name"].str.casefold().eq("gujarat")].copy()

    if gujarat.empty:
        raise DataQualityError("The source contains no Gujarat district records.")

    validate_district_dataset(gujarat)

    return gujarat.sort_values(
        by=[
            "district_name",
            "lg_dt_code",
        ],
        kind="stable",
    ).reset_index(drop=True)


def build_scope_qualification_summary(
    source_path: Path,
) -> dict[str, Any]:
    """Return national conflict and Gujarat qualification evidence."""

    national, encoding = read_aggregate_source(source_path)
    national = normalise_aggregate_source(national)

    conflicts = classify_national_key_conflicts(national)

    gujarat = build_gujarat_scoped_dataset(source_path)

    gujarat_conflicts = (
        conflicts.loc[conflicts["contains_gujarat"]] if not conflicts.empty else conflicts
    )

    return {
        "encoding": encoding,
        "national_row_count": len(national),
        "national_conflicting_key_group_count": (
            int(conflicts["conflicting"].sum()) if not conflicts.empty else 0
        ),
        "national_conflicting_key_row_count": (
            int(
                conflicts.loc[
                    conflicts["conflicting"],
                    "row_count",
                ].sum()
            )
            if not conflicts.empty
            else 0
        ),
        "gujarat_row_count": len(gujarat),
        "gujarat_district_count": int(gujarat["lg_dt_code"].nunique()),
        "gujarat_conflicting_key_group_count": (
            int(gujarat_conflicts["conflicting"].sum()) if not gujarat_conflicts.empty else 0
        ),
        "gujarat_total": int(gujarat["total"].sum()),
        "qualified_for_gujarat_scope": (
            gujarat_conflicts.empty or not gujarat_conflicts["conflicting"].any()
        ),
    }
