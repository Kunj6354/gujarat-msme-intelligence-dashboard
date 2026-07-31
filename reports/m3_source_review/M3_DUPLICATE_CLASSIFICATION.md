# M3 Duplicate-Key Classification

## Summary

- Source rows: **788**
- Duplicate key rows: **20**
- Duplicate key groups: **9**
- Exact duplicate groups: **0**
- Conflicting duplicate groups: **9**
- Gujarat duplicate rows: **0**
- Gujarat duplicate groups: **0**

## Exact-row deduplication test

- Rows after removing exact repeated records: **788**
- Remaining duplicate key rows: **20**
- Exact deduplication resolves every key conflict: **False**

## Registry-date check

- Access date: `30/07/2026`
- Source as-of date: `30/07/2026`
- Dates are identical: **True**

## Decision rule

- **Reject the source in its current form.**
- Conflicting records cannot be removed automatically.
- Obtain a corrected source/API response or document the authoritative row for each conflict.

The source remains `pending_validation` until the reporting date, checksum and duplicate-resolution decision are approved.
