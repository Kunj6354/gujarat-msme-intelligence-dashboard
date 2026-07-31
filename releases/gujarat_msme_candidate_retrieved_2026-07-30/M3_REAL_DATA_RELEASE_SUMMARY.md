# M3 — Gujarat MSME Real Data Candidate Release

## Release status

**Candidate for internal Power BI implementation and validation.**

This release is not approved for public dashboard publication until
the final human review and acceptance checklist are completed.

## Source qualification

- Source ID: `OGD_UDYAM_DISTRICT`
- Source file: `ogd_udyam_district_retrieved_2026-07-30.csv`
- Source SHA-256: `9236f99a4540c6215858c210970491a10462fb2027986232c64238cab76a0aca`
- Retrieval date: `2026-07-30`
- Fixed source reporting date: **Not provided**
- Qualification: `qualified_for_gujarat_scope_only`

The source contains conflicting national state/district-code keys.
No conflicting keys occur within the Gujarat subset.

The complete national file is preserved without automatic deletion,
merging or reconciliation of conflicting records.

## Gujarat release totals

- Districts: **33**
- Micro registrations: **2,969,687**
- Small registrations: **54,335**
- Medium registrations: **4,245**
- Total registrations: **3,028,267**

## Highest and lowest districts

- Highest: **AHMADABAD**
  (603,761)
- Lowest: **DANG**
  (2,404)

## Release contents

### Data package

- Main analytical district CSV
- Dataset metadata JSON
- Gujarat executive summary JSON
- Top and Bottom district ranking CSV
- Power BI data dictionary
- Data-package manifest and checksums

### Dashboard implementation package

- Five visible dashboard page specifications
- Two hidden technical pages
- DAX measure library
- Prototype StackOre theme
- Pixel-level page layouts
- Visual interaction rules
- Tooltip and drill-through specification
- Acceptance criteria
- Implementation guide
- Implementation manifest and checksums

## Restrictions

- Do not use this source for national district ranking.
- Do not describe registrations as active businesses.
- Do not infer employment, activity type, revenue or profitability.
- Do not represent the retrieval date as a reporting date.
- Do not introduce enterprise-level identifiable records.
- Do not publish until the M3 acceptance checklist is complete.
