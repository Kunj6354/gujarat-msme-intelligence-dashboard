#!/usr/bin/env python3
"""Generate the complete Power BI implementation package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from msme_dashboard.powerbi_implementation_package import (
    write_powerbi_implementation_package,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate dashboard assets, model specifications, "
            "layouts, interactions and implementation guidance."
        ),
    )

    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("powerbi/implementation_package"),
        help="Destination for generated implementation assets.",
    )

    return parser.parse_args()


def main() -> int:
    """Generate the package and print its summary."""

    arguments = parse_arguments()

    manifest = write_powerbi_implementation_package(
        arguments.output_directory,
    )

    print("Power BI implementation package generated successfully.")
    print(f"Output directory: {arguments.output_directory}")
    print()
    print(
        json.dumps(
            {
                "visible_page_count": manifest["visible_page_count"],
                "technical_page_count": manifest["technical_page_count"],
                "visual_count": manifest["visual_count"],
                "interaction_rule_count": manifest["interaction_rule_count"],
                "file_count": len(manifest["files"]),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
