# Contributing to the Gujarat MSME Intelligence Dashboard

## Repository Roles

- Project owner and reviewer: Kunj Patel
- Project contributor: Prince Gevariya
- Organisation: StackOre Technologies

## Protected Development Principle

The `main` branch represents reviewed project work. Contributors should not
develop directly on `main`.

Prince's initial working branch is:

```text
feature/m0-source-validation
```

## Standard Workflow

```bash
git switch feature/m0-source-validation
git pull --ff-only origin feature/m0-source-validation
```

Make focused changes and run:

```bash
make check
```

Then commit and push:

```bash
git add <specific-files>
git commit -m "data: validate <source-name>"
git push
```

Open a pull request into `main`. Kunj reviews the evidence, source metadata,
validation output and data-governance compliance before merging.

## Commit Categories

Use one of these prefixes:

- `data:` source files, source metadata or mappings
- `pipeline:` ingestion, cleaning and transformation logic
- `test:` automated validation
- `dashboard:` Power BI work
- `docs:` methodology or handover documents
- `fix:` correction of an existing implementation
- `chore:` repository maintenance

## Source Rules

- Raw downloaded files must remain unchanged.
- Every source must be entered in `source_registry.csv`.
- Every source column used must be entered in `source_columns.csv`.
- Access date and source as-of date are different fields.
- Missing values must not be invented.
- State totals must not be allocated to districts without official evidence.
- Different reporting snapshots must remain visibly separated.
- Registration counts must not be described as active businesses, revenue,
  profitability or business success.
- Personal or enterprise-level confidential data must not be introduced.
- The project owner provides final source approval.

## Pull Request Requirements

Every pull request must state:

- What changed.
- Which source or milestone it belongs to.
- Which files were added or modified.
- What validation was performed.
- Which assumptions or unresolved questions remain.
