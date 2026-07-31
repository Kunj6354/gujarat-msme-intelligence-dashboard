#!/usr/bin/env python3
"""Generate Gujarat MSME Power BI dashboard implementation assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from msme_dashboard.powerbi_dashboard_assets import (
    write_dashboard_assets,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate the Power BI theme, DAX measures, dashboard "
            "specification, visual inventory and acceptance criteria."
        ),
    )

    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("powerbi/dashboard_assets"),
        help="Destination directory for generated dashboard assets.",
    )

    return parser.parse_args()


def main() -> int:
    """Generate dashboard implementation assets."""

    arguments = parse_arguments()

    manifest = write_dashboard_assets(
        arguments.output_directory,
    )

    print("Power BI dashboard assets generated successfully.")
    print(f"Output directory: {arguments.output_directory}")
    print()
    print(
        json.dumps(
            {
                "page_count": manifest["page_count"],
                "visual_count": manifest["visual_count"],
                "measure_count": manifest["measure_count"],
                "acceptance_criteria_count": manifest["acceptance_criteria_count"],
                "files": manifest["files"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
