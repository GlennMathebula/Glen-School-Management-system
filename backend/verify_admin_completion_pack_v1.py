from app.main import app

from app.services.admin_completion_service import (
    list_completion_status,
)
from app.services.admin_eisa_service import (
    list_eisa_learners,
)
from app.services.admin_student_records_service import (
    list_students,
)
from app.services.admin_system_service import (
    get_admin_system_summary,
)
from app.services.admin_timetable_service import (
    list_admin_timetable,
)


prefixes = (
    "/api/staff/admin/students",
    "/api/staff/admin/timetable",
    "/api/staff/admin/eisa",
    "/api/staff/admin/completion",
    "/api/staff/admin/system",
)

routes = [
    (
        getattr(route, "path", ""),
        getattr(route, "methods", set()) or set(),
    )
    for route in app.routes
    if getattr(route, "path", "").startswith(prefixes)
]

print("FASTAPI APP IMPORT: OK")
print("TOTAL OPENAPI PATHS:", len(app.openapi()["paths"]))
print("ADMIN COMPLETION PACK ROUTES:", len(routes))

for path, methods in sorted(routes):
    print(
        ",".join(sorted(methods)),
        path,
    )

print("")
print("LIVE DATABASE READ-ONLY VALIDATION")

students = list_students(limit=1)
print("STUDENT RECORDS QUERY: OK")
print("STUDENT TOTAL:", students["total"])

timetable = list_admin_timetable(limit=1)
print("TIMETABLE QUERY: OK")
print("TIMETABLE TOTAL:", timetable["total"])

eisa = list_eisa_learners(limit=1)
print("EISA QUERY: OK")
print("EISA TOTAL:", eisa["total"])

completion = list_completion_status(limit=1)
print("COMPLETION QUERY: OK")
print("COMPLETION SAMPLE COUNT:", completion["count"])

system = get_admin_system_summary()
print("SYSTEM SUMMARY QUERY: OK")
print(
    "CORE TABLES PRESENT:",
    sum(
        1
        for value
        in system["core_table_status"].values()
        if value
    ),
    "/",
    len(system["core_table_status"]),
)

print("")
print("ADMIN COMPLETION PACK V1 VALIDATION: PASSED")

