"""CLI integration tests for Power BI package generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from msme_dashboard.powerbi_bundle import (
    MANIFEST_FILE,
    RANKING_VIEW_FILE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate_powerbi_bundle.py"


def make_source_file(path: Path) -> None:
    """Write a valid national aggregate source fixture."""

    frame = pd.DataFrame(
        {
            "state_name": [
                "GUJARAT",
                "GUJARAT",
                "GUJARAT",
                "MAHARASHTRA",
            ],
            "state_id": ["24", "24", "24", "27"],
            "district_name": [
                "AHMEDABAD",
                "SURAT",
                "VADODARA",
                "PUNE",
            ],
            "lg_dt_code": ["474", "492", "486", "521"],
            "medium": [10, 20, 15, 30],
            "micro": [100, 300, 200, 400],
            "small": [20, 30, 25, 40],
            "total": [130, 350, 240, 470],
        }
    )

    frame.to_csv(
        path,
        index=False,
    )


def test_cli_generates_complete_powerbi_package(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "national.csv"
    output_directory = tmp_path / "powerbi"

    make_source_file(source_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--source",
            str(source_path),
            "--output-directory",
            str(output_directory),
            "--source-as-of-date",
            "2026-07-21",
            "--ranking-limit",
            "2",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Power BI bundle generated successfully" in completed.stdout

    manifest_path = output_directory / MANIFEST_FILE
    ranking_path = output_directory / RANKING_VIEW_FILE

    assert manifest_path.exists()
    assert ranking_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["district_row_count"] == 3
    assert manifest["ranking_row_count"] == 4
    assert manifest["source"]["as_of_date"] == ("2026-07-21")

    rankings = pd.read_csv(ranking_path)

    assert len(rankings) == 4
    assert list(
        rankings.loc[
            rankings["ranking_group"].eq("TOP"),
            "district_name",
        ]
    ) == [
        "SURAT",
        "VADODARA",
    ]


def test_cli_returns_error_for_missing_source(
    tmp_path: Path,
) -> None:
    missing_source = tmp_path / "missing.csv"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--source",
            str(missing_source),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "Power BI bundle generation failed" in completed.stdout


def test_cli_returns_error_for_invalid_ranking_limit(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "national.csv"
    output_directory = tmp_path / "powerbi"

    make_source_file(source_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--source",
            str(source_path),
            "--output-directory",
            str(output_directory),
            "--ranking-limit",
            "0",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "at least 1" in completed.stdout
    assert not output_directory.exists()
