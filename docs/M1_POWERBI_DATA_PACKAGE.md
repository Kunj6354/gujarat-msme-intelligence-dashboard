# M1 — Gujarat MSME Analytics and Power BI Data Package

## Purpose

M1 converts an approved national district-level UDYAM aggregate
dataset into a reproducible Gujarat-focused analytical package for
Power BI.

M1 provides processing infrastructure. It does not approve a source.
Source approval remains part of M0 source validation.

## Input schema

The source CSV must contain:

| Field | Description |
|---|---|
| `state_name` | State name |
| `state_id` | Source state identifier |
| `district_name` | District name |
| `lg_dt_code` | Local Government Directory district code |
| `medium` | Registered Medium enterprises |
| `micro` | Registered Micro enterprises |
| `small` | Registered Small enterprises |
| `total` | Total registered enterprises |

The authoritative output order is:

`state_name, state_id, district_name, lg_dt_code, medium, micro, small, total`

## Validation rules

The pipeline verifies:

- Required columns are present.
- The dataset is not empty.
- State and district identifiers are not blank.
- Registration counts are whole numbers.
- Registration counts are nonnegative.
- State and district-code combinations are unique.
- `total = micro + small + medium`.
- Processed output contains only Gujarat districts.

## Derived analytical fields

| Field | Calculation |
|---|---|
| `district_rank_total` | Descending rank by district total |
| `district_rank_total_ascending` | Ascending rank by district total |
| `micro_share_pct` | Micro divided by district total × 100 |
| `small_share_pct` | Small divided by district total × 100 |
| `medium_share_pct` | Medium divided by district total × 100 |
| `gujarat_total_share_pct` | District total divided by Gujarat total × 100 |
| `dominant_category` | Largest district registration category |
| `top_10_flag` | Descending rank is 10 or below |
| `bottom_10_flag` | Ascending rank is 10 or below |

A zero-registration district receives zero category shares and
`NO_REGISTRATIONS` as its dominant category.

A district with equal maximum values across categories receives `TIE`.

## Generated Power BI package

| File | Purpose |
|---|---|
| `gujarat_district_msme.csv` | Main district analytical table |
| `gujarat_district_msme.metadata.json` | Provenance and transformation metadata |
| `gujarat_executive_summary.json` | Gujarat-level KPI summary |
| `gujarat_district_rankings.csv` | Top-N and Bottom-N ranking view |
| `gujarat_msme_data_dictionary.csv` | Field definitions and formulas |
| `gujarat_powerbi_bundle_manifest.json` | Checksums, sizes and package inventory |

## Executive KPIs

The package calculates:

- Number of Gujarat districts
- Total registered enterprises
- Micro registrations
- Small registrations
- Medium registrations
- Category percentage shares
- Average registrations per district
- Highest-registration district
- Lowest-registration district

These values describe registrations in the source snapshot. They do
not represent active businesses, revenue, profitability or current
employment.

## Power BI data types

| Field group | Type |
|---|---|
| State, district and category fields | Text |
| State ID and LGD district code | Text |
| Registration totals | Whole Number |
| District ranks | Whole Number |
| Percentage shares | Decimal Number |
| Top and Bottom flags | True/False |

Identifiers must remain text values. They must not be treated as
measures.

The main table grain is one row per Gujarat district for one approved
source snapshot.

## Suggested report pages

### Page 1 — Gujarat Executive Overview

- Total registration cards
- Micro, Small and Medium totals
- Category shares
- District count
- Highest and lowest districts
- Top-10 district chart

### Page 2 — District Comparison

- District ranking table
- Top-N and Bottom-N view
- District contribution percentage
- District search and selection

### Page 3 — Category Analysis

- Micro, Small and Medium stacked chart
- Category-share comparison
- Dominant category
- Medium-share ranking

### Page 4 — Data Quality

- Source ID
- Reporting date
- Source checksum
- Generated timestamp
- Validation rules
- Known limitations

### Page 5 — Sources and Methodology

- Source name and URL
- Licence
- Access date
- Field dictionary
- Transformation summary
- Interpretation warnings

## Generation command

Run only after the M0 source is approved:

```bash
python scripts/generate_powerbi_bundle.py \
  --source "path/to/approved-district-file.csv" \
  --output-directory data/processed/powerbi \
  --source-id OGD_UDYAM_DISTRICT \
  --source-as-of-date YYYY-MM-DD \
  --ranking-limit 10
The source reporting date must be copied from the validated source.
It must never be guessed.

Governance
Only aggregate public data is permitted.
Enterprise-level identifiable records are prohibited.
Missing district values must not be inferred from state totals.
Incompatible source snapshots must not be combined.
Source checksum changes require regeneration and review.
Metadata and manifest files must remain with generated outputs.
No final dashboard output may be published from a source that is
still marked pending_validation.
Current status

The repository source registry currently marks the available sources
as pending_validation.

M1 is therefore production-ready processing infrastructure, but it
does not declare the current raw source approved for publication.
