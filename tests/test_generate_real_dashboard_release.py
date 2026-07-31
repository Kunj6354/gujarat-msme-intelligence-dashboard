"""CLI tests for the real dashboard release tools."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from msme_dashboard.file_inventory import sha256_file
from msme_dashboard.real_dashboard_release import (
    RELEASE_MANIFEST_FILE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GENERATOR = PROJECT_ROOT / "scripts" / "generate_real_dashboard_release.py"

VALIDATOR = PROJECT_ROOT / "scripts" / "validate_real_dashboard_release.py"


def write_fixture(
    source: Path,
    qualification: Path,
) -> None:
    """Write a qualified synthetic fixture."""

    frame = pd.DataFrame(
        {
            "state_name": [
                "GUJARAT",
                "RAJASTHAN",
                "RAJASTHAN",
            ],
            "state_id": ["24", "8", "8"],
            "district_name": [
                "VADODARA",
                "JAIPUR",
                "DUDU",
            ],
            "lg_dt_code": ["486", "102", "102"],
            "medium": [20, 100, 5],
            "micro": [200, 1000, 50],
            "small": [30, 200, 10],
            "total": [250, 1300, 65],
        }
    )

    frame.to_csv(source, index=False)

    qualification.write_text(
        json.dumps(
            {
                "source_id": "OGD_UDYAM_DISTRICT",
                "source_url": "https://example.gov/source",
                "licence": "GODL-India",
                "retrieval_date": "2026-07-30",
                "source_as_of_date": None,
                "source_sha256": sha256_file(source),
                "qualification_status": ("qualified_for_gujarat_scope_only"),
                "privacy_classification": ("public_aggregate_district_data"),
            }
        ),
        encoding="utf-8",
    )


def test_generator_and_validator_cli(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.csv"
    qualification = tmp_path / "qualification.json"
    output = tmp_path / "release"

    write_fixture(source, qualification)

    generated = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--source",
            str(source),
            "--qualification",
            str(qualification),
            "--output-directory",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert generated.returncode == 0
    assert "generated successfully" in generated.stdout
    assert (output / RELEASE_MANIFEST_FILE).exists()

    validated = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--release-directory",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert validated.returncode == 0
    assert "validation passed" in validated.stdout
