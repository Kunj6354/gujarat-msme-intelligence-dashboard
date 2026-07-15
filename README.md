# Gujarat MSME Intelligence Dashboard

A source-transparent public-data analytics proof of concept by StackOre
Technologies.

The project transforms approved official MSME datasets into:

- A validated and repeatable Python/Pandas data pipeline.
- A processed analytical data model.
- An interactive Power BI dashboard.
- A screenshot-ready executive overview.
- A publishable StackOre case study.

This is not an official government dashboard, commercial market-research
report, or production SaaS application.

## Project Roles

- Project owner and reviewer: Kunj Patel
- Project contributor: Prince Gevariya
- Organisation: StackOre Technologies

## Current Project Gate

The project is currently at:

```text
M0 — Source Validation
No Power BI dashboard development or final dataset modelling should begin until
the project owner approves the primary sources.

Repository Structure
MSME/
├── data/
│   ├── raw/                    Untouched official source downloads
│   ├── interim/                Samples and intermediate transformations
│   ├── processed/              Dashboard-ready validated datasets
│   └── reference/              Source register and controlled mappings
├── docs/                       Task brief and methodology material
├── powerbi/                    Power BI Desktop file
├── reports/
│   └── screenshots/            Approved public screenshots
├── scripts/                    Executable validation and pipeline scripts
├── src/
│   └── msme_dashboard/         Reusable Python package
└── tests/                      Automated data and pipeline tests
Data Governance
Use official public data first.
Keep every raw downloaded file unchanged.
Never overwrite a raw source file with cleaned data.
Record source URL, access date, source as-of date and licence.
Never invent missing values.
Never infer district-level values from state-level totals.
Do not combine incompatible snapshots without showing separate dates.
Do not include enterprise-level personal or confidential information.
Every published derived metric must have a documented formula.
Registration counts must not be described as revenue, profitability,
active operation or business success.
Local Setup
make setup
source .venv/bin/activate
make check
Source Registry Validation

Normal structural validation:

python scripts/validate_source_registry.py

M0 approval validation:

python scripts/validate_source_registry.py --strict

Strict validation will fail until every primary source has been reviewed and
marked as approved.

Power BI Path Policy

Use relative project paths wherever possible. Do not embed paths such as:

/home/kunj/...
C:\Users\...

The final project must refresh on another StackOre computer.

Public Attribution

Gujarat MSME Intelligence Dashboard — a public-data analytics proof of concept
by StackOre Technologies, built using official Government of India open data.
Not an official government product.
