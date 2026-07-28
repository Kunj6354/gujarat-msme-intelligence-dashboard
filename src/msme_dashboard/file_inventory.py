"""File inventory and integrity helpers for raw source data."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileRecord:
    """Integrity metadata for one project file."""

    relative_path: str
    size_bytes: int
    sha256: str


def sha256_file(path: Path) -> str:
    """Calculate the SHA-256 digest for a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def inventory_files(
    root: Path,
    *,
    include_hidden: bool = False,
) -> list[FileRecord]:
    """Create a deterministic inventory of files below a directory."""

    if not root.exists():
        raise FileNotFoundError(f"Inventory root does not exist: {root}")

    records: list[FileRecord] = []

    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative_path = path.relative_to(root)

        if not include_hidden and any(part.startswith(".") for part in relative_path.parts):
            continue

        records.append(
            FileRecord(
                relative_path=relative_path.as_posix(),
                size_bytes=path.stat().st_size,
                sha256=sha256_file(path),
            )
        )

    return records


def write_inventory_csv(
    records: list[FileRecord],
    destination: Path,
) -> None:
    """Write file-integrity records to a CSV file."""

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=(
                "relative_path",
                "size_bytes",
                "sha256",
            ),
        )
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
