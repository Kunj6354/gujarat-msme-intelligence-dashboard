#!/usr/bin/env python3
"""Validate the Gujarat MSME source registry."""

from __future__ import annotations

import argparse

from msme_dashboard.paths import SOURCE_REGISTRY_PATH
from msme_dashboard.source_registry import (
    load_source_registry,
    validate_source_registry,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Validate source_registry.csv.",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require every primary source to be approved.",
    )

    return parser.parse_args()


def main() -> int:
    """Run source-registry validation."""

    arguments = parse_arguments()

    frame = load_source_registry(SOURCE_REGISTRY_PATH)

    errors = validate_source_registry(
        frame,
        strict=arguments.strict,
    )

    print(f"Source registry: {SOURCE_REGISTRY_PATH}")
    print(f"Registered sources: {len(frame)}")
    print(
        "Status counts:",
        frame["status"].value_counts(dropna=False).to_dict(),
    )

    if errors:
        print("\nVALIDATION FAILED")

        for error in errors:
            print(f"- {error}")

        return 1

    print("\nVALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
