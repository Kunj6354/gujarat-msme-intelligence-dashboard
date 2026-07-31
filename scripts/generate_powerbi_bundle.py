#!/usr/bin/env python3
"""Generate the complete Gujarat MSME Power BI data package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from msme_dashboard.data_quality import DataQualityError
from msme_dashboard.powerbi_bundle import write_powerbi_bundle
from msme_dashboard.processed_output import DEFAULT_SOURCE_ID


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate Gujarat district data, analytical metrics, "
            "Power BI support files and an audit manifest."
        ),
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Official national district aggregate CSV.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("data/processed/powerbi"),
        help="Destination directory for the Power BI package.",
    )
    parser.add_argument(
        "--source-id",
        default=DEFAULT_SOURCE_ID,
        help="Source registry identifier.",
    )
    parser.add_argument(
        "--source-as-of-date",
        default=None,
        help="Official source date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--ranking-limit",
        type=int,
        default=10,
        help="Number of districts in Top and Bottom ranking views.",
    )

    return parser.parse_args()


def main() -> int:
    """Generate the Power BI package."""

    arguments = parse_arguments()

    try:
        manifest = write_powerbi_bundle(
            source_path=arguments.source,
            output_directory=arguments.output_directory,
            source_id=arguments.source_id,
            source_as_of_date=arguments.source_as_of_date,
            ranking_limit=arguments.ranking_limit,
        )
    except (
        DataQualityError,
        FileNotFoundError,
        ValueError,
    ) as error:
        print(f"Power BI bundle generation failed: {error}")
        return 1

    print("Power BI bundle generated successfully.")
    print(f"Output directory: {arguments.output_directory}")
    print()
    print(
        json.dumps(
            {
                "district_row_count": manifest["district_row_count"],
                "ranking_row_count": manifest["ranking_row_count"],
                "source": manifest["source"],
                "files": manifest["files"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
