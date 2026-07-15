from msme_dashboard.paths import (
    DATA_DIR,
    DISTRICT_MAPPING_PATH,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REFERENCE_DATA_DIR,
    SOURCE_COLUMNS_PATH,
    SOURCE_REGISTRY_PATH,
)


def test_required_project_paths_exist() -> None:
    required_paths = (
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        REFERENCE_DATA_DIR,
        SOURCE_REGISTRY_PATH,
        SOURCE_COLUMNS_PATH,
        DISTRICT_MAPPING_PATH,
    )

    for path in required_paths:
        assert path.exists(), f"Missing required path: {path}"
