from __future__ import annotations

from pathlib import Path


backend = Path(r"C:\Projects\Glen Moniques SMS\backend")
main_path = backend / "app" / "main.py"

source = main_path.read_text(encoding="utf-8-sig")

routers = [
    (
        "staff_admin_student_records_routes",
        "staff_admin_student_records_router",
    ),
    (
        "staff_admin_timetable_routes",
        "staff_admin_timetable_router",
    ),
    (
        "staff_admin_eisa_routes",
        "staff_admin_eisa_router",
    ),
    (
        "staff_admin_completion_routes",
        "staff_admin_completion_router",
    ),
    (
        "staff_admin_system_routes",
        "staff_admin_system_router",
    ),
]

anchor = "app = FastAPI("
position = source.find(anchor)

if position < 0:
    raise RuntimeError(
        "Could not find app = FastAPI( in app/main.py"
    )

import_blocks = []

for module_name, alias in routers:
    if f"from app.{module_name} import" not in source:
        import_blocks.append(
            f"from app.{module_name} import (\n"
            f"    router as {alias},\n"
            f")\n\n"
        )

if import_blocks:
    source = (
        source[:position]
        + "".join(import_blocks)
        + source[position:]
    )

for _, alias in routers:
    marker = f"app.include_router(\n    {alias}\n)"
    compact_marker = f"app.include_router({alias})"

    if (
        marker not in source
        and compact_marker not in source
    ):
        source = (
            source.rstrip()
            + "\n\n\n"
            + marker
            + "\n"
        )

compile(source, str(main_path), "exec")
main_path.write_text(source, encoding="utf-8")

print("Admin Completion Pack routers mounted.")

