from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(r"C:\Projects\Glen Moniques SMS\backend")

if str(BACKEND) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND),
    )

from app.main import app
from app.services.staff_report_service import (
    get_report_catalog,
)


schema = app.openapi()
paths = schema.get(
    "paths",
    {},
)

report_paths = [
    path
    for path in paths
    if path.startswith(
        "/api/staff/reports"
    )
]

record_paths = [
    path
    for path in paths
    if path.startswith(
        "/api/staff/compliance-records"
    )
]

catalog = get_report_catalog()

unavailable = [
    item
    for item in catalog
    if not item.get(
        "available"
    )
]

print(
    "FASTAPI APP IMPORT: OK"
)
print(
    "TOTAL OPENAPI PATHS:",
    len(
        paths
    ),
)
print(
    "REPORT API PATHS:",
    len(
        report_paths
    ),
)
print(
    "QA/COMPLIANCE RECORD API PATHS:",
    len(
        record_paths
    ),
)
print(
    "REPORT CATALOG COUNT:",
    len(
        catalog
    ),
)
print(
    "UNAVAILABLE REPORTS:",
    len(
        unavailable
    ),
)

if len(catalog) != 44:
    raise SystemExit(
        "Expected 44 report definitions."
    )

if unavailable:
    for item in unavailable:
        print(
            "UNAVAILABLE:",
            item["code"],
        )
    raise SystemExit(
        "Some reports are still unavailable."
    )

expected_reports = {
    "/api/staff/reports/catalog",
    "/api/staff/reports/{report_code}",
    "/api/staff/reports/{report_code}/pdf",
}

if not expected_reports.issubset(
    set(
        report_paths
    )
):
    raise SystemExit(
        "Report API validation failed."
    )

if not record_paths:
    raise SystemExit(
        "QA/Compliance records API "
        "was not mounted."
    )

print()
print(
    "ALL 44 REPORTS: AVAILABLE"
)
print(
    "QA REPORTS V4 VALIDATION: PASSED"
)
