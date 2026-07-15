from msme_dashboard.paths import SOURCE_REGISTRY_PATH
from msme_dashboard.source_registry import (
    REQUIRED_COLUMNS,
    load_source_registry,
    validate_source_registry,
)


def test_source_registry_has_expected_structure() -> None:
    frame = load_source_registry(SOURCE_REGISTRY_PATH)

    assert tuple(frame.columns) == REQUIRED_COLUMNS
    assert len(frame) >= 3


def test_source_registry_passes_non_strict_validation() -> None:
    frame = load_source_registry(SOURCE_REGISTRY_PATH)

    assert validate_source_registry(frame, strict=False) == []


def test_primary_sources_begin_pending_validation() -> None:
    frame = load_source_registry(SOURCE_REGISTRY_PATH)
    primary_sources = frame[frame["priority"].eq("primary")]

    assert not primary_sources.empty
    assert set(primary_sources["status"]) == {
        "pending_validation",
    }
