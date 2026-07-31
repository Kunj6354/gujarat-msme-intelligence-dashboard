# M2 — Power BI Dashboard Implementation Guide

## Purpose

This guide converts the generated M1 Gujarat district data package
into the five-page Gujarat MSME Intelligence Dashboard.

The dashboard is a StackOre Technologies proof of concept based on
public aggregate data. It is not an official government product.

## Required inputs

Load these files from the generated M1 package:

- `gujarat_district_msme.csv`
- `gujarat_district_msme.metadata.json`
- `gujarat_powerbi_bundle_manifest.json`
- `gujarat_msme_data_dictionary.csv`

Use these M2 implementation assets:

- `stackore_gujarat_msme_theme.json`
- `gujarat_msme_measures.dax`
- `gujarat_msme_dashboard_spec.json`
- `gujarat_msme_visual_inventory.csv`
- `gujarat_msme_acceptance_criteria.csv`
- `gujarat_msme_model_spec.json`
- `gujarat_msme_page_layouts.csv`
- `gujarat_msme_interaction_rules.csv`
- `gujarat_msme_tooltip_drillthrough.json`

## Semantic model

Rename the main fact table to `Gujarat MSME Districts`.

Keep `state_id` and `lg_dt_code` as Text. Registration counts and
district ranks use Whole Number. Percentage fields use Decimal Number
with two displayed decimal places.

Create a dedicated `_Measures` table and place all DAX measures there.

Metadata and manifest tables are disconnected reference tables. No
relationship is required because the current model has one analytical
fact table and no separate dimensions.

## Build sequence

1. Load the validated M1 data package.
2. Apply the supplied Power BI theme.
3. Rename tables according to the model specification.
4. Assign data types and hidden-column settings.
5. Create the `_Measures` table.
6. copy the supplied DAX measures.
7. Create the five visible pages in specification order.
8. Apply the pixel layouts from the layout CSV.
9. Configure visual interactions from the interaction-rules CSV.
10. Create the hidden tooltip and drill-through pages.
11. Apply page-level and visual-level filters.
12. Validate values against the M1 JSON and CSV outputs.
13. Run the acceptance checklist.
14. Save the PBIX using a source-date-aware file name.

## Visible pages

### 1. Gujarat Executive Overview

Use cards for Gujarat totals, category totals, district count and the
highest-registration district. Use a Top-10 bar chart and category
share donut chart.

Do not describe total registrations as active enterprises.

### 2. District Comparison

Provide district selection, district ranking, Gujarat contribution,
average registrations and a sortable district table.

The selected district contribution measure must remove only district
filters when calculating the Gujarat denominator.

### 3. Enterprise Category Analysis

Compare Micro, Small and Medium registrations and shares across
districts. Include the dominant-category slicer and Medium-share
ranking.

Category shares should total approximately 100 percent for nonzero
districts.

### 4. Data Availability and Limitations

Display source ID, source reporting date, generated timestamp and
source checksum.

Clearly state that district-level activity type and employment data
are unavailable and are not inferred.

### 5. Sources and Methodology

Display source provenance, bundle details, transformation methodology,
field dictionary and governance warnings.

The primary reporting date must match the approved source snapshot.

## Tooltip page

Create a hidden report-tooltip page named `District Tooltip`.

The tooltip displays district name, LGD code, district rank, dominant
category, category totals and contribution to the Gujarat total.

Assign it to the supported analytical charts listed in the tooltip
specification.

## Drill-through page

Create a hidden page named `District Detail`.

Use `district_name` and `lg_dt_code` as drill-through fields and enable
Keep all filters.

Include a Back button, total card, category chart and percentage table.

## Visual interactions

Slicers filter all same-page analytical visuals.

Charts, tables and matrices cross-highlight compatible same-page
visuals. Reference text, methodology blocks and limitation notices do
not participate in cross-filtering.

## Theme

The supplied theme is a StackOre prototype theme. It uses clean
light-background cards, dark typography, blue as the primary accent,
and distinct category colours.

Before client delivery, compare it with the final StackOre brand kit
and update colours, fonts and logo treatment when necessary.

## Data governance

- Only aggregate district data is permitted.
- Enterprise names, registration numbers, owner details and contact
  details must never be loaded.
- Missing values must not be inferred from state totals.
- Different reporting snapshots must not be silently combined.
- Registration counts are not revenue, profitability or employment.
- The source reporting date and checksum must remain visible.
- Final publication requires an approved M0 source.

## Validation

Run the generated acceptance-criteria checklist and verify:

- KPI values against the executive summary JSON
- District order against the analytical CSV
- Category shares against derived columns
- Source information against metadata
- File integrity against the package manifest
- Absence of identifiable enterprise-level fields
- Page rendering with Power BI Performance Analyzer

## Delivery naming

Use a PBIX file name such as:

`StackOre_Gujarat_MSME_Dashboard_<SOURCE_DATE>_v1.pbix`

Do not place an unconfirmed date in the PBIX file name.
