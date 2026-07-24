from pathlib import Path

from msme_dashboard.file_inventory import (
    inventory_files,
    sha256_file,
    write_inventory_csv,
)


def test_sha256_file_is_deterministic(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.csv"
    source.write_text(
        "district,total\nAhmedabad,10\n",
        encoding="utf-8",
    )

    first = sha256_file(source)
    second = sha256_file(source)

    assert first == second
    assert len(first) == 64


def test_inventory_files_uses_relative_paths(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "raw"
    source_dir.mkdir()

    (source_dir / "source.csv").write_text(
        "district,total\nVadodara,5\n",
        encoding="utf-8",
    )

    records = inventory_files(source_dir)

    assert len(records) == 1
    assert records[0].relative_path == "source.csv"
    assert records[0].size_bytes > 0


def test_inventory_ignores_hidden_files_by_default(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "raw"
    source_dir.mkdir()

    (source_dir / ".gitkeep").write_text(
        "",
        encoding="utf-8",
    )
    (source_dir / "source.csv").write_text(
        "district,total\nSurat,8\n",
        encoding="utf-8",
    )

    records = inventory_files(source_dir)

    assert [record.relative_path for record in records] == [
        "source.csv",
    ]


def test_write_inventory_csv(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "raw"
    source_dir.mkdir()

    (source_dir / "source.csv").write_text(
        "district,total\nRajkot,6\n",
        encoding="utf-8",
    )

    destination = tmp_path / "inventory.csv"

    write_inventory_csv(
        inventory_files(source_dir),
        destination,
    )

    content = destination.read_text(encoding="utf-8")

    assert "relative_path,size_bytes,sha256" in content
    assert "source.csv" in content
