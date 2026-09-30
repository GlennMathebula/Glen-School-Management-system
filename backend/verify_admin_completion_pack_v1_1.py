from app.main import app


EXPECTED = {
    "/api/staff/admin/students": {"GET"},
    "/api/staff/admin/students/{student_number}": {"GET"},
    "/api/staff/admin/students/{student_number}/documents": {"GET"},
    "/api/staff/admin/timetable": {"GET"},
    "/api/staff/admin/timetable/sessions/{timetable_session_id}/status": {"PATCH"},
    "/api/staff/admin/eisa/learners": {"GET"},
    "/api/staff/admin/eisa/learners/{student_number}/eligibility": {"PATCH"},
    "/api/staff/admin/completion": {"GET"},
    "/api/staff/admin/completion/{student_number}": {"GET"},
    "/api/staff/admin/system/summary": {"GET"},
}


schema = app.openapi()
paths = schema.get("paths", {})

print("FASTAPI APP IMPORT: OK")
print("TOTAL OPENAPI PATHS:", len(paths))
print("")
print("ADMIN COMPLETION PACK ROUTE AUDIT")
print("")

missing = []
method_errors = []
found = []

for path, expected_methods in EXPECTED.items():
    item = paths.get(path)

    if item is None:
        missing.append(path)
        print("MISSING", path)
        continue

    actual_methods = {
        method.upper()
        for method in item
        if method.lower()
        in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "options",
            "head",
        }
    }

    missing_methods = (
        expected_methods
        - actual_methods
    )

    if missing_methods:
        method_errors.append(
            (
                path,
                sorted(missing_methods),
                sorted(actual_methods),
            )
        )
        print(
            "METHOD ERROR",
            path,
            "expected=",
            sorted(expected_methods),
            "actual=",
            sorted(actual_methods),
        )
        continue

    found.append(path)
    print(
        "OK",
        ",".join(sorted(expected_methods)),
        path,
    )

print("")
print("EXPECTED ADMIN PATHS:", len(EXPECTED))
print("CONFIRMED ADMIN PATHS:", len(found))
print("MISSING ADMIN PATHS:", len(missing))
print("METHOD ERRORS:", len(method_errors))

operation_ids = {}

for path, item in paths.items():
    for method, operation in item.items():
        if not isinstance(operation, dict):
            continue

        operation_id = operation.get("operationId")
        if not operation_id:
            continue

        operation_ids.setdefault(
            operation_id,
            [],
        ).append(
            f"{method.upper()} {path}"
        )

duplicates = {
    key: value
    for key, value in operation_ids.items()
    if len(value) > 1
}

print("")
print("DUPLICATE OPERATION IDS:", len(duplicates))

for operation_id, locations in sorted(
    duplicates.items()
):
    print(
        "DUPLICATE",
        operation_id,
        "=>",
        " | ".join(locations),
    )

if missing:
    raise SystemExit(
        "FAILED: One or more Admin Completion "
        "Pack paths are missing from OpenAPI."
    )

if method_errors:
    raise SystemExit(
        "FAILED: One or more Admin Completion "
        "Pack paths have incorrect HTTP methods."
    )

if duplicates:
    raise SystemExit(
        "FAILED: Duplicate OpenAPI operation IDs found."
    )

print("")
print(
    "ADMIN COMPLETION PACK V1.1 ROUTE AUDIT: PASSED"
)
