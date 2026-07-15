"""Source registry loading and validation."""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = (
    "source_id",
    "publisher",
    "dataset_name",
    "source_url",
    "priority",
    "expected_use",
    "access_date",
    "source_as_of_date",
    "licence",
    "fields_used",
    "transformation",
    "status",
    "notes",
)

ALLOWED_PRIORITIES = {"primary", "secondary", "optional"}

ALLOWED_STATUSES = {
    "pending_validation",
    "approved",
    "rejected",
    "superseded",
}

APPROVAL_REQUIRED_FIELDS = (
    "publisher",
    "dataset_name",
    "source_url",
    "access_date",
    "source_as_of_date",
    "licence",
    "fields_used",
)


def load_source_registry(path: Path) -> pd.DataFrame:
    """Load the source registry while preserving blank cells."""

    if not path.exists():
        raise FileNotFoundError(f"Source registry does not exist: {path}")

    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )


def validate_source_registry(
    frame: pd.DataFrame,
    *,
    strict: bool = False,
) -> list[str]:
    """Return validation errors found in the source registry."""

    errors: list[str] = []

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]

    if missing_columns:
        errors.append("Missing required source-registry columns: " + ", ".join(missing_columns))
        return errors

    if frame.empty:
        errors.append("Source registry must contain at least one source.")
        return errors

    blank_ids = frame["source_id"].str.strip().eq("")

    if blank_ids.any():
        rows = [str(index + 2) for index in frame.index[blank_ids]]
        errors.append("Blank source_id found on CSV rows: " + ", ".join(rows))

    duplicate_ids = frame.loc[
        frame["source_id"].duplicated(keep=False),
        "source_id",
    ].tolist()

    if duplicate_ids:
        errors.append("Duplicate source_id values: " + ", ".join(sorted(set(duplicate_ids))))

    invalid_priorities = sorted(set(frame["priority"].str.strip()) - ALLOWED_PRIORITIES)

    if invalid_priorities:
        errors.append("Invalid priority values: " + ", ".join(invalid_priorities))

    invalid_statuses = sorted(set(frame["status"].str.strip()) - ALLOWED_STATUSES)

    if invalid_statuses:
        errors.append("Invalid status values: " + ", ".join(invalid_statuses))

    approved_rows = frame[frame["status"].eq("approved")]

    for index, row in approved_rows.iterrows():
        missing_values = [field for field in APPROVAL_REQUIRED_FIELDS if not row[field].strip()]

        if missing_values:
            errors.append(
                f"Approved source {row['source_id']!r} on CSV row "
                f"{index + 2} is missing: " + ", ".join(missing_values)
            )

    if strict:
        unapproved_primary = frame[
            frame["priority"].eq("primary") & ~frame["status"].eq("approved")
        ]

        for _, row in unapproved_primary.iterrows():
            errors.append(
                f"Primary source {row['source_id']!r} is not approved "
                f"(current status: {row['status']!r})."
            )

    return errors
