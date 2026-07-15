"""Repository-relative project paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REFERENCE_DATA_DIR = DATA_DIR / "reference"

SOURCE_REGISTRY_PATH = REFERENCE_DATA_DIR / "source_registry.csv"
SOURCE_COLUMNS_PATH = REFERENCE_DATA_DIR / "source_columns.csv"
DISTRICT_MAPPING_PATH = REFERENCE_DATA_DIR / "district_mapping.csv"
