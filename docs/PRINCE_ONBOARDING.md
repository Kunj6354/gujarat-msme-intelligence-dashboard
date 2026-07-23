# Prince Onboarding Guide

## Project

Gujarat MSME Intelligence Dashboard

## Organisation

StackOre Technologies

## Initial Assignment

Milestone M0 — Source Validation

Prince must not begin the final Power BI dashboard before the project owner
approves the required primary sources.

## Clone the Repository

```bash
git clone https://github.com/Kunj6354/gujarat-msme-intelligence-dashboard.git
cd gujarat-msme-intelligence-dashboard
git switch feature/m0-source-validation
```

## Prepare the Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Verify the Starting Project

```bash
make check
```

Expected baseline:

- Source-registry structural validation passes.
- Automated tests pass.
- Ruff lint validation passes.
- Strict source approval validation remains blocked until Kunj approves the
  primary sources.

## M0 Work Areas

Prince should work only in these locations unless Kunj assigns otherwise:

```text
data/raw/
data/interim/source_samples/
data/reference/source_registry.csv
data/reference/source_columns.csv
docs/
```

## Required M0 Evidence

For every proposed source, record:

- Publisher.
- Exact dataset or dashboard name.
- Official URL.
- Access date.
- Exact data as-of date.
- Download or extraction format.
- Original source columns.
- Fields proposed for the MVP.
- Licence or attribution requirement.
- Known limitations.
- Any mismatch with another source.

Save original downloads unchanged under `data/raw/`.

Save representative samples under:

```text
data/interim/source_samples/
```

## Source Status

Prince may use:

- `pending_validation`
- `rejected`

Prince should not mark a primary source as approved unless Kunj explicitly
approves it during review.

## Submission Workflow

```bash
git switch feature/m0-source-validation
git status
make check
git add <specific-files>
git commit -m "data: complete initial MSME source validation"
git push
```

After pushing, open a pull request from:

```text
feature/m0-source-validation -> main
```

## Prohibited Work During M0

Do not:

- Build the final Power BI dashboard.
- Estimate missing district values.
- Allocate Gujarat totals across districts.
- Combine different reporting dates into one apparent snapshot.
- Add unofficial commercial data without approval.
- Rename source columns without recording the mapping.
- Modify original downloaded raw files.
- Present registration counts as active or successful businesses.
