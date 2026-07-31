#!/usr/bin/env python3
"""Generate validated Gujarat district MSME output files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from msme_dashboard.processed_output import (
    DEFAULT_SOURCE_ID,
    write_processed_district_outputs,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=("Generate a Gujarat-only district MSME CSV and its provenance metadata."),
    )

    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to the official national district aggregate CSV.",
    )

    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path(
            "data/processed/gujarat_district_msme.csv",
        ),
        help="Destination for the processed Gujarat CSV.",
    )

    parser.add_argument(
        "--metadata-json",
        type=Path,
        default=Path(
            "data/processed/gujarat_district_msme.metadata.json",
        ),
        help="Destination for the generated metadata JSON.",
    )

    parser.add_argument(
        "--source-id",
        default=DEFAULT_SOURCE_ID,
        help="Source registry ID associated with the input file.",
    )

    parser.add_argument(
        "--source-as-of-date",
        default=None,
        help="Official source reporting date in YYYY-MM-DD format.",
    )

    return parser.parse_args()


def main() -> int:
    """Generate the processed dataset and display its summary."""

    arguments = parse_arguments()

    try:
        metadata = write_processed_district_outputs(
            source_path=arguments.source,
            output_csv_path=arguments.output_csv,
            metadata_json_path=arguments.metadata_json,
            source_id=arguments.source_id,
            source_as_of_date=arguments.source_as_of_date,
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Generation failed: {error}")
        return 1

    print("Processed district dataset generated successfully.")
    print(f"Source:        {arguments.source}")
    print(f"Output CSV:    {arguments.output_csv}")
    print(f"Metadata JSON: {arguments.metadata_json}")
    print()
    print(
        json.dumps(
            {
                "row_count": metadata["row_count"],
                "district_count": metadata["district_count"],
                "registration_totals": metadata["registration_totals"],
                "source_sha256": metadata["source_sha256"],
                "source_as_of_date": metadata["source_as_of_date"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
