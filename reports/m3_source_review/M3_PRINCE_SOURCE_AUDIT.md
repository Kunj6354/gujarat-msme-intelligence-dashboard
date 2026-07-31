# M3 Prince M0 Source Audit

## Encoding and integrity

- Detected encoding: **utf-8-sig**
- Original SHA-256: `9236f99a4540c6215858c210970491a10462fb2027986232c64238cab76a0aca`
- Normalized review SHA-256: `9236f99a4540c6215858c210970491a10462fb2027986232c64238cab76a0aca`
- Original checksum recorded in registry: **False**

The normalized UTF-8 file is an audit copy only. The original source checksum remains authoritative.

## Schema and privacy

- Source columns: `['state_name', 'state_id', 'district_name', 'lg_dt_code', 'medium', 'micro', 'small', 'total']`
- Exact authoritative column order: **True**
- Prohibited enterprise-level columns: `[]`
- Null counts: `{}`
- Duplicate state/district-key rows: **20**

## Pipeline result

- Validation failed: `Duplicate rows found for key [state_id, lg_dt_code]: 20`

## Structural approval blockers

- Pipeline validation failed: Duplicate rows found for key [state_id, lg_dt_code]: 20
- Duplicate state/district-code key rows are present.
- The original source checksum is not recorded in Prince's source registry.

## Manual validation still required

- Confirm the exact source reporting date.
- Confirm the primary data.gov.in resource URL.
- Confirm that GODL-India applies to this resource.
- Reconcile the source checksum with the registry.
- Confirm the district coverage expected for Gujarat.
