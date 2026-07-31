"""Derived analytical metrics for Gujarat district MSME data."""

from __future__ import annotations

import pandas as pd

from msme_dashboard.data_quality import (
    DataQualityError,
    require_columns,
    require_nonnegative,
)
from msme_dashboard.district_pipeline import (
    REQUIRED_COLUMNS,
    validate_district_dataset,
)

DERIVED_COLUMNS = (
    "district_rank_total",
    "district_rank_total_ascending",
    "micro_share_pct",
    "small_share_pct",
    "medium_share_pct",
    "gujarat_total_share_pct",
    "dominant_category",
    "top_10_flag",
    "bottom_10_flag",
)

PERCENTAGE_COLUMNS = (
    "micro_share_pct",
    "small_share_pct",
    "medium_share_pct",
    "gujarat_total_share_pct",
)

ALLOWED_DOMINANT_CATEGORIES = {
    "MICRO",
    "SMALL",
    "MEDIUM",
    "TIE",
    "NO_REGISTRATIONS",
}


def _require_gujarat_only(frame: pd.DataFrame) -> None:
    """Require every row to belong to Gujarat."""

    states = {str(value).strip().casefold() for value in frame["state_name"]}

    if states != {"gujarat"}:
        raise DataQualityError("Analytical metrics require Gujarat-only district data.")


def _safe_percentage(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """Calculate percentages while safely handling zero totals."""

    result = pd.Series(
        0.0,
        index=numerator.index,
        dtype="float64",
    )

    valid_denominator = denominator.ne(0)

    result.loc[valid_denominator] = (
        numerator.loc[valid_denominator] / denominator.loc[valid_denominator] * 100
    )

    return result.round(4)


def _dominant_category(frame: pd.DataFrame) -> pd.Series:
    """Return the dominant enterprise category for every district."""

    category_columns = ["micro", "small", "medium"]
    category_values = frame.loc[:, category_columns]

    maximum = category_values.max(axis=1)
    tie_count = category_values.eq(maximum, axis=0).sum(axis=1)

    dominant = category_values.idxmax(axis=1).str.upper()

    dominant = dominant.mask(
        maximum.eq(0),
        "NO_REGISTRATIONS",
    )

    dominant = dominant.mask(
        maximum.ne(0) & tie_count.gt(1),
        "TIE",
    )

    return dominant


def add_district_analytical_metrics(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Add Power BI-ready analytical fields to Gujarat district data."""

    validate_district_dataset(frame)
    _require_gujarat_only(frame)

    result = frame.loc[:, REQUIRED_COLUMNS].copy()

    result = result.sort_values(
        by=["total", "district_name", "lg_dt_code"],
        ascending=[False, True, True],
        kind="stable",
    ).reset_index(drop=True)

    row_count = len(result)

    result["district_rank_total"] = range(
        1,
        row_count + 1,
    )

    ascending_order = result.sort_values(
        by=["total", "district_name", "lg_dt_code"],
        ascending=[True, True, True],
        kind="stable",
    ).index

    ascending_ranks = pd.Series(
        range(1, row_count + 1),
        index=ascending_order,
        dtype="int64",
    )

    result["district_rank_total_ascending"] = ascending_ranks

    result["micro_share_pct"] = _safe_percentage(
        result["micro"],
        result["total"],
    )
    result["small_share_pct"] = _safe_percentage(
        result["small"],
        result["total"],
    )
    result["medium_share_pct"] = _safe_percentage(
        result["medium"],
        result["total"],
    )

    gujarat_total = int(result["total"].sum())

    result["gujarat_total_share_pct"] = _safe_percentage(
        result["total"],
        pd.Series(
            gujarat_total,
            index=result.index,
            dtype="int64",
        ),
    )

    result["dominant_category"] = _dominant_category(result)

    rank_cutoff = min(10, row_count)

    result["top_10_flag"] = result["district_rank_total"] <= rank_cutoff
    result["bottom_10_flag"] = result["district_rank_total_ascending"] <= rank_cutoff

    validate_analytical_metrics(result)

    return result


def validate_analytical_metrics(
    frame: pd.DataFrame,
) -> None:
    """Validate all derived district analytical fields."""

    validate_district_dataset(frame)
    _require_gujarat_only(frame)
    require_columns(frame, DERIVED_COLUMNS)
    require_nonnegative(frame, PERCENTAGE_COLUMNS)

    row_count = len(frame)
    expected_ranks = set(range(1, row_count + 1))

    if set(frame["district_rank_total"]) != expected_ranks:
        raise DataQualityError("Descending district ranks are incomplete or duplicated.")

    if set(frame["district_rank_total_ascending"]) != expected_ranks:
        raise DataQualityError("Ascending district ranks are incomplete or duplicated.")

    for column in PERCENTAGE_COLUMNS:
        above_limit = frame[column].gt(100)

        if above_limit.any():
            raise DataQualityError(f"Column {column!r} contains percentages above 100.")

    category_share_total = (
        frame["micro_share_pct"] + frame["small_share_pct"] + frame["medium_share_pct"]
    )

    nonzero_rows = frame["total"].gt(0)
    zero_rows = frame["total"].eq(0)

    invalid_nonzero = category_share_total.loc[nonzero_rows].sub(100).abs().gt(0.01)

    if invalid_nonzero.any():
        raise DataQualityError("Category percentages do not total 100 for all districts.")

    invalid_zero = category_share_total.loc[zero_rows].abs().gt(0.01)

    if invalid_zero.any():
        raise DataQualityError("Zero-registration districts must have zero category shares.")

    gujarat_total = int(frame["total"].sum())
    contribution_total = float(frame["gujarat_total_share_pct"].sum())

    if gujarat_total == 0:
        if abs(contribution_total) > 0.01:
            raise DataQualityError("Zero Gujarat total must produce zero contribution shares.")
    elif abs(contribution_total - 100) > 0.05:
        raise DataQualityError("District contribution percentages do not total 100.")

    invalid_categories = set(frame["dominant_category"]) - ALLOWED_DOMINANT_CATEGORIES

    if invalid_categories:
        raise DataQualityError(
            "Invalid dominant categories: " + ", ".join(sorted(invalid_categories))
        )

    rank_cutoff = min(10, row_count)

    expected_top = frame["district_rank_total"].le(rank_cutoff)
    expected_bottom = frame["district_rank_total_ascending"].le(rank_cutoff)

    if not frame["top_10_flag"].eq(expected_top).all():
        raise DataQualityError("Top-10 flags do not match district ranks.")

    if not frame["bottom_10_flag"].eq(expected_bottom).all():
        raise DataQualityError("Bottom-10 flags do not match district ranks.")
