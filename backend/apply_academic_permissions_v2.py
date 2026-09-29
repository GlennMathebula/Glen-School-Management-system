from pathlib import Path
import re


facilitator_file = Path(
    "app/facilitator_routes.py"
)

resources_file = Path(
    "app/learning_resource_routes.py"
)


# ============================================================
# HELPERS
# ============================================================

def backup_once(path: Path):

    backup_path = path.with_suffix(
        path.suffix + ".before_permissions.bak"
    )

    if not backup_path.exists():

        backup_path.write_text(
            path.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

        print(
            f"Backup created: {backup_path}"
        )


def replace_function_dependency(
    source: str,
    function_name: str,
    old_dependency: str,
    new_dependency: str,
) -> str:

    function_pattern = re.compile(
        rf"("
        rf"def\s+{re.escape(function_name)}\s*"
        rf"\("
        rf".*?"
        rf")"
        rf"(?=\n\s*(?:@router\.|def\s+|\Z))",
        re.DOTALL,
    )

    match = function_pattern.search(
        source
    )

    if not match:

        raise RuntimeError(
            f"Function not found: "
            f"{function_name}"
        )

    block = match.group(
        1
    )

    dependency_pattern = re.compile(
        rf"Depends"
        rf"\s*\("
        rf"\s*"
        rf"{re.escape(old_dependency)}"
        rf"\s*"
        rf"\)",
        re.DOTALL,
    )

    if not dependency_pattern.search(
        block
    ):

        raise RuntimeError(
            f"{old_dependency} not found "
            f"in {function_name}"
        )

    new_block = (
        dependency_pattern.sub(
            (
                "Depends(\n"
                f"        {new_dependency}\n"
                "    )"
            ),
            block,
            count=1,
        )
    )

    return (
        source[:match.start()]
        + new_block
        + source[match.end():]
    )


def ensure_permission_import(
    source: str,
) -> str:

    if (
        "from app.services.staff_permission_service "
        "import"
        in source
    ):

        return source

    import_block = (
        "\nfrom app.services."
        "staff_permission_service import (\n"
        "    require_permission,\n"
        ")\n"
    )

    marker = (
        "from app.staff_auth_dependency import"
    )

    position = source.find(
        marker
    )

    if position != -1:

        end = source.find(
            ")\n",
            position,
        )

        if end != -1:

            end += 2

            return (
                source[:end]
                + import_block
                + source[end:]
            )

    router_position = source.find(
        "router = APIRouter("
    )

    if router_position == -1:

        raise RuntimeError(
            "Could not insert permission import."
        )

    return (
        source[:router_position]
        + import_block
        + "\n"
        + source[router_position:]
    )


# ============================================================
# ACADEMIC DELIVERY ROUTES
# ============================================================

backup_once(
    facilitator_file
)

text = facilitator_file.read_text(
    encoding="utf-8"
)

text = ensure_permission_import(
    text
)


guards = """
# ============================================================
# SHARED ACADEMIC PERMISSION GUARDS
# ============================================================

require_view_staff_profile = (
    require_permission(
        "VIEW_STAFF_PROFILE"
    )
)

require_view_assigned_classes = (
    require_permission(
        "VIEW_ASSIGNED_CLASSES"
    )
)

require_view_learners = (
    require_permission(
        "VIEW_LEARNERS"
    )
)

require_manage_attendance = (
    require_permission(
        "MANAGE_ATTENDANCE"
    )
)


"""

if (
    "require_view_assigned_classes ="
    not in text
):

    router_position = text.find(
        "router = APIRouter("
    )

    if router_position == -1:

        raise RuntimeError(
            "Facilitator router not found."
        )

    text = (
        text[:router_position]
        + guards
        + text[router_position:]
    )


academic_permissions = {
    "facilitator_profile":
        "require_view_staff_profile",

    "facilitator_classes":
        "require_view_assigned_classes",

    "facilitator_timetable":
        "require_view_assigned_classes",

    "facilitator_attendance_history":
        "require_manage_attendance",

    "facilitator_class_detail":
        "require_view_assigned_classes",

    "facilitator_class_learners":
        "require_view_learners",

    "facilitator_sync_timetable_to_google_calendar":
        "require_view_assigned_classes",

    "facilitator_class_timetable":
        "require_view_assigned_classes",

    "facilitator_class_attendance_history":
        "require_manage_attendance",

    "facilitator_create_attendance_session":
        "require_manage_attendance",

    "facilitator_attendance_roster":
        "require_manage_attendance",

    "facilitator_capture_attendance":
        "require_manage_attendance",

    "facilitator_submit_attendance":
        "require_manage_attendance",

    "facilitator_notify_learners":
        "require_view_learners",
}


for function_name, dependency in (
    academic_permissions.items()
):

    text = replace_function_dependency(
        source=text,
        function_name=function_name,
        old_dependency=(
            "require_academic_delivery_staff"
        ),
        new_dependency=(
            dependency
        ),
    )


facilitator_file.write_text(
    text,
    encoding="utf-8",
)

print(
    "Academic Delivery permissions updated."
)


# ============================================================
# LEARNING RESOURCES
# ============================================================

backup_once(
    resources_file
)

text = resources_file.read_text(
    encoding="utf-8"
)

text = ensure_permission_import(
    text
)


resource_guard = """
# ============================================================
# LEARNING RESOURCE PERMISSION GUARD
# ============================================================

require_manage_learning_resources = (
    require_permission(
        "MANAGE_LEARNING_RESOURCES"
    )
)


"""

if (
    "require_manage_learning_resources ="
    not in text
):

    router_position = text.find(
        "router = APIRouter("
    )

    if router_position == -1:

        raise RuntimeError(
            "Learning resource router "
            "not found."
        )

    text = (
        text[:router_position]
        + resource_guard
        + text[router_position:]
    )


resource_functions = [
    "facilitator_create_note",
    "facilitator_create_link",
    "facilitator_upload_file",
    "facilitator_class_resources",
    "facilitator_resource_detail",
    "facilitator_publish_resource",
    "facilitator_archive_resource",
    "facilitator_generate_ai_notes",
    "facilitator_restore_resource",
]


for function_name in resource_functions:

    text = replace_function_dependency(
        source=text,
        function_name=function_name,
        old_dependency=(
            "require_facilitator"
        ),
        new_dependency=(
            "require_manage_learning_resources"
        ),
    )


resources_file.write_text(
    text,
    encoding="utf-8",
)

print(
    "Learning Resource permissions updated."
)

print()
print(
    "ACADEMIC + LEARNING RESOURCE "
    "PERMISSION PATCH COMPLETE"
)
