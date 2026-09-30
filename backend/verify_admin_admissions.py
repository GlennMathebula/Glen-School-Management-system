from __future__ import annotations

import inspect
import sys
from pathlib import Path


BACKEND = Path(r"C:\Projects\Glen Moniques SMS\backend")

if str(BACKEND) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND),
    )

from app.main import app
from app.services.registration_service import (
    register_student,
)
from app.services.staff_admissions_service import (
    list_applications,
)


schema = app.openapi()
paths = schema.get(
    "paths",
    {},
)

admission_paths = {
    path
    for path in paths
    if path.startswith(
        "/api/staff/admissions"
    )
}

expected = {
    "/api/staff/admissions/applications",
    "/api/staff/admissions/applications/{student_number}",
    "/api/staff/admissions/applications/{student_number}/document-checklist",
    "/api/staff/admissions/documents/{document_id}/review",
    "/api/staff/admissions/applications/{student_number}/outstanding-documents",
    "/api/staff/admissions/applications/{student_number}/accept",
    "/api/staff/admissions/applications/{student_number}/reject",
    "/api/staff/admissions/applications/{student_number}/registration/retry",
    "/api/staff/admissions/registrations/{student_number}",
}

print(
    "FASTAPI APP IMPORT: OK"
)
print(
    "TOTAL OPENAPI PATHS:",
    len(paths),
)
print(
    "ADMIN ADMISSIONS PATHS:",
    len(admission_paths),
)

for path in sorted(
    admission_paths
):
    methods = paths[
        path
    ].keys()

    print(
        ",".join(
            method.upper()
            for method in methods
        ),
        path,
    )

missing = expected - admission_paths

if missing:
    print()
    print(
        "MISSING ADMIN ADMISSIONS PATHS:"
    )

    for path in sorted(
        missing
    ):
        print(
            " ",
            path,
        )

    raise SystemExit(
        "ADMIN ADMISSIONS OPENAPI VALIDATION FAILED"
    )

signature = inspect.signature(
    register_student
)

if "program_start_date" not in signature.parameters:
    raise SystemExit(
        "registration_service.register_student "
        "does not support program_start_date."
    )

result = list_applications(
    limit=1,
    offset=0,
)

print()
print(
    "ADMISSIONS DB QUERY: OK"
)
print(
    "APPLICATION TOTAL:",
    result[
        "total"
    ],
)
print(
    "ADMIN ADMISSIONS VALIDATION: PASSED"
)
