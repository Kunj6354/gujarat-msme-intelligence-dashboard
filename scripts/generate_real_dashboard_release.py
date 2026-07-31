#!/usr/bin/env python3
"""Generate the real Gujarat MSME dashboard candidate release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from msme_dashboard.data_quality import DataQualityError
from msme_dashboard.real_dashboard_release import (
    write_real_dashboard_release,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate the qualified Gujarat real-data package, "
            "Power BI implementation assets and release manifest."
        ),
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Qualified national aggregate source CSV.",
    )
    parser.add_argument(
        "--qualification",
        type=Path,
        required=True,
        help="Gujarat-scope qualification JSON.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        required=True,
        help="Destination directory for the candidate release.",
    )
    parser.add_argument(
        "--ranking-limit",
        type=int,
        default=10,
        help="Top and Bottom district ranking size.",
    )

    return parser.parse_args()


def main() -> int:
    """Generate the candidate release."""

    arguments = parse_arguments()

    try:
        manifest = write_real_dashboard_release(
            source_path=arguments.source,
            qualification_path=arguments.qualification,
            output_directory=arguments.output_directory,
            ranking_limit=arguments.ranking_limit,
        )
    except (
        DataQualityError,
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Real dashboard release generation failed: {error}")
        return 1

    print("Real Gujarat dashboard candidate release generated successfully.")
    print(f"Output directory: {arguments.output_directory}")
    print()
    print(
        json.dumps(
            {
                "release_status": manifest["release_status"],
                "district_count": manifest["district_count"],
                "registration_totals": manifest["registration_totals"],
                "visible_page_count": manifest["dashboard_implementation"]["visible_page_count"],
                "visual_count": manifest["dashboard_implementation"]["visual_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
