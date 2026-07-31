from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate_processed_districts.py"


def make_source_file(path: Path) -> None:
    frame = pd.DataFrame(
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

    frame.to_csv(path, index=False)


def test_cli_generates_processed_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "national.csv"
    output_csv = tmp_path / "gujarat.csv"
    metadata_json = tmp_path / "gujarat.metadata.json"

    make_source_file(source)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--source",
            str(source),
            "--output-csv",
            str(output_csv),
            "--metadata-json",
            str(metadata_json),
            "--source-as-of-date",
            "2026-07-21",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "generated successfully" in completed.stdout
    assert output_csv.exists()
    assert metadata_json.exists()

    metadata = json.loads(metadata_json.read_text(encoding="utf-8"))

    assert metadata["source_as_of_date"] == "2026-07-21"
    assert metadata["row_count"] == 2
    assert metadata["district_count"] == 2
    assert metadata["registration_totals"] == {
        "medium": 3,
        "micro": 300,
        "small": 30,
        "total": 333,
    }


def test_cli_output_contains_only_gujarat(
    tmp_path: Path,
) -> None:
    source = tmp_path / "national.csv"
    output_csv = tmp_path / "gujarat.csv"
    metadata_json = tmp_path / "gujarat.metadata.json"

    make_source_file(source)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--source",
            str(source),
            "--output-csv",
            str(output_csv),
            "--metadata-json",
            str(metadata_json),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0

    processed = pd.read_csv(output_csv)

    assert set(processed["state_name"]) == {"GUJARAT"}
    assert list(processed["district_name"]) == [
        "AHMEDABAD",
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
    assert "Generation failed" in completed.stdout
    assert "does not exist" in completed.stdout
