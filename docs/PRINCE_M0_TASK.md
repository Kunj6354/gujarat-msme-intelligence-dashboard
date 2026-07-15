Prince Task — M0 Source Validation
Objective

Validate the official public sources before any dashboard modelling or Power BI
development begins.

Required Work

For every proposed source:

Open the official source page.
Confirm that it is publicly accessible.
Record the access date.
Record the exact data as-of date.
Confirm the available download format.
Record the exact source columns.
Record the licence or attribution requirement.
Download the source file without modifying it.
Save it inside data/raw/.
Save five representative rows inside
data/interim/source_samples/.
Update data/reference/source_registry.csv.
Update data/reference/source_columns.csv.
Source Status Rules

Use one of:

pending_validation
approved
rejected
superseded

Prince may recommend approval, but final source approval belongs to the project
owner.

M0 Submission

Prince must submit:

Completed source registry.
Source-column inventory.
Untouched raw files.
Five sample rows from every proposed primary source.
Notes about missing, conflicting or unclear fields.
A simple five-page dashboard wireframe.
The output of:
python scripts/validate_source_registry.py
pytest -q
Restrictions

Do not:

Build the final Power BI dashboard yet.
Estimate unavailable values.
Combine sources with different as-of dates.
Treat registrations as active businesses or successful businesses.
Add unofficial commercial datasets.
Include enterprise-level personal information.
