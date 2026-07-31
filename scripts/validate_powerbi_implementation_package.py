#!/usr/bin/env python3
"""Validate a generated Power BI implementation package."""

from __future__ import annotations

import argparse
from pathlib import Path

from msme_dashboard.powerbi_implementation_package import (
    validate_written_implementation_package,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate implementation files, checksums, layouts and dashboard design consistency."
        ),
    )

    parser.add_argument(
        "--package-directory",
        type=Path,
        required=True,
        help="Generated Power BI implementation package directory.",
    )

    return parser.parse_args()


def main() -> int:
    """Validate the package."""

    arguments = parse_arguments()

    try:
        manifest = validate_written_implementation_package(
            arguments.package_directory,
        )
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Power BI package validation failed: {error}")
        return 1

    print("Power BI implementation package validation passed.")
    print(f"Validated files: {len(manifest['files'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
