"""Tests for controlled Gujarat-only source qualification."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from msme_dashboard.data_quality import DataQualityError
from msme_dashboard.scoped_source import (
    build_gujarat_scoped_dataset,
    build_scope_qualification_summary,
    classify_national_key_conflicts,
    normalise_aggregate_source,
    read_aggregate_source,
)


def make_source_frame() -> pd.DataFrame:
    """Return Gujarat rows plus an out-of-scope conflict."""

    return pd.DataFrame(
        {
            "state_name": [
                "GUJARAT",
                "GUJARAT",
                "RAJASTHAN",
                "RAJASTHAN",
            ],
            "state_id": [
                "24",
                "24",
                "8",
                "8",
            ],
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


def test_normalise_validates_row_level_rules() -> None:
    result = normalise_aggregate_source(make_source_frame())

    assert list(result.columns) == [
        "state_name",
        "state_id",
        "district_name",
        "lg_dt_code",
        "medium",
        "micro",
        "small",
        "total",
    ]
    assert result["total"].dtype == "int64"


def test_classifies_out_of_scope_conflict() -> None:
    conflicts = classify_national_key_conflicts(make_source_frame())

    assert len(conflicts) == 1
    assert conflicts.loc[0, "conflicting"]
    assert not conflicts.loc[0, "contains_gujarat"]
    assert conflicts.loc[0, "row_count"] == 2


def test_gujarat_scope_ignores_out_of_scope_key_conflict(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    make_source_frame().to_csv(
        source,
        index=False,
    )

    gujarat = build_gujarat_scoped_dataset(source)

    assert len(gujarat) == 2
    assert set(gujarat["state_name"]) == {"GUJARAT"}
    assert list(gujarat["district_name"]) == [
        "AHMEDABAD",
        "VADODARA",
    ]


def test_gujarat_scope_rejects_internal_conflict(
    tmp_path: Path,
) -> None:
    frame = make_source_frame()
    duplicate = frame.iloc[[0]].copy()
    duplicate["district_name"] = "OTHER DISTRICT"
    duplicate["total"] = duplicate[["micro", "small", "medium"]].sum(axis=1)

    frame = pd.concat(
        [frame, duplicate],
        ignore_index=True,
    )

    source = tmp_path / "source.csv"
    frame.to_csv(source, index=False)

    with pytest.raises(
        DataQualityError,
        match="Duplicate rows",
    ):
        build_gujarat_scoped_dataset(source)


def test_scope_summary_qualifies_gujarat_only(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    make_source_frame().to_csv(
        source,
        index=False,
    )

    summary = build_scope_qualification_summary(source)

    assert summary["national_conflicting_key_group_count"] == 1
    assert summary["national_conflicting_key_row_count"] == 2
    assert summary["gujarat_conflicting_key_group_count"] == 0
    assert summary["gujarat_district_count"] == 2
    assert summary["qualified_for_gujarat_scope"]


def test_reader_supports_cp1252(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"

    content = (
        "state_name,state_id,district_name,lg_dt_code,"
        "medium,micro,small,total\n"
        "GUJARAT,24,VADODARA–URBAN,486,1,10,2,13\n"
    )

    source.write_bytes(content.encode("cp1252"))

    frame, encoding = read_aggregate_source(source)

    assert encoding == "cp1252"
    assert frame.loc[0, "district_name"] == ("VADODARA–URBAN")


def test_normalise_rejects_invalid_total() -> None:
    frame = make_source_frame()
    frame.loc[0, "total"] = 999

    with pytest.raises(
        DataQualityError,
        match="must equal",
    ):
        normalise_aggregate_source(frame)
