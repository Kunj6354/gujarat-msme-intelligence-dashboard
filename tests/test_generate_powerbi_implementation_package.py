"""CLI tests for Power BI implementation package tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from msme_dashboard.powerbi_implementation_package import (
    PACKAGE_MANIFEST_FILE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT_ROOT / "scripts" / "generate_powerbi_implementation_package.py"
VALIDATOR = PROJECT_ROOT / "scripts" / "validate_powerbi_implementation_package.py"


def test_generator_and_validator_cli(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "implementation"

    generated = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--output-directory",
            str(output_directory),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert generated.returncode == 0
    assert "generated successfully" in generated.stdout
    assert (output_directory / PACKAGE_MANIFEST_FILE).exists()

    validated = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--package-directory",
            str(output_directory),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert validated.returncode == 0
    assert "validation passed" in validated.stdout


def test_validator_cli_rejects_missing_package(
    tmp_path: Path,
) -> None:
    missing_directory = tmp_path / "missing"

    completed = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--package-directory",
            str(missing_directory),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "validation failed" in completed.stdout
