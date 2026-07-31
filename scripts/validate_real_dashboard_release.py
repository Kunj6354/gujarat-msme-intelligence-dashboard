#!/usr/bin/env python3
"""Validate the real Gujarat MSME dashboard candidate release."""

from __future__ import annotations

import argparse
from pathlib import Path

from msme_dashboard.real_dashboard_release import (
    validate_written_real_dashboard_release,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate real-data release files, checksums, district totals and Power BI assets."
        ),
    )

    parser.add_argument(
        "--release-directory",
        type=Path,
        required=True,
        help="Generated real dashboard release directory.",
    )

    return parser.parse_args()


def main() -> int:
    """Validate the release."""

    arguments = parse_arguments()

    try:
        manifest = validate_written_real_dashboard_release(arguments.release_directory)
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Real dashboard release validation failed: {error}")
        return 1

    print("Real dashboard release validation passed.")
    print(f"Districts: {manifest['district_count']}")
    print(f"Total registrations: {manifest['registration_totals']['total']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
