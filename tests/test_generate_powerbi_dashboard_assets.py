"""CLI tests for Power BI dashboard asset generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from msme_dashboard.powerbi_dashboard_assets import (
    MANIFEST_FILE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate_powerbi_dashboard_assets.py"


def test_cli_generates_dashboard_assets(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "dashboard_assets"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output-directory",
            str(output_directory),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "dashboard assets generated successfully" in completed.stdout

    manifest_path = output_directory / MANIFEST_FILE

    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["page_count"] == 5
    assert manifest["visual_count"] >= 25
    assert manifest["measure_count"] >= 10
