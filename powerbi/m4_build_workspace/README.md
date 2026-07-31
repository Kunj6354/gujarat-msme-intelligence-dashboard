# M4 Power BI Desktop Build Workspace

## Purpose

This directory contains the controlled inputs for constructing the
actual StackOre Gujarat MSME Power BI report.

Do not replace these files with manually edited copies.

## Power BI input

Load:

`input/gujarat_district_msme.csv`

Rename the Power BI table:

`Gujarat MSME Districts`

## Expected PBIX

Save the report as:

`powerbi/pbix/StackOre_Gujarat_MSME_Dashboard_retrieved_2026-07-30_v1.pbix`

## Visible pages

1. Gujarat Executive Overview
2. District Comparison
3. Enterprise Category Analysis
4. Data Availability and Limitations
5. Sources and Methodology

## Hidden pages

6. District Tooltip
7. District Detail

## Required validation baseline

- Districts: 33
- Micro: 2,969,687
- Small: 54,335
- Medium: 4,245
- Total: 3,028,267
- Highest district: AHMADABAD — 603,761
- Lowest district: DANG — 2,404

## Governance

- The source is qualified for Gujarat scope only.
- Do not add national analysis.
- Do not describe registrations as active businesses.
- Do not show the retrieval date as a reporting date.
- Do not infer employment, activity type, revenue or profitability.
- Public publication remains disabled during M4.
