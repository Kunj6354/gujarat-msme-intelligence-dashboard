#!/usr/bin/env python3
"""Run all repository quality checks consistently on Windows and Linux."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    (
        "Source registry validation",
        (
            sys.executable,
            "scripts/validate_source_registry.py",
        ),
    ),
    (
        "Automated tests",
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ),
    ),
    (
        "Ruff lint",
        (
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src",
            "scripts",
            "tests",
        ),
    ),
    (
        "Ruff formatting",
        (
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "src",
            "scripts",
            "tests",
        ),
    ),
)


def main() -> int:
    """Run each quality check and stop at the first failure."""

    for name, command in CHECKS:
        print(f"\n===== {name.upper()} =====", flush=True)

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        )

        if completed.returncode != 0:
            print(
                f"\n{name} failed with exit code {completed.returncode}.",
                flush=True,
            )
            return completed.returncode

    print("\n===== ALL QUALITY CHECKS PASSED =====")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
