from pathlib import Path

# ============================================================
# FILES
# ============================================================

facilitator_file = Path("app/facilitator_routes.py")
resources_file = Path("app/learning_resource_routes.py")


# ============================================================
# HELPERS
# ============================================================

def backup(path: Path):
    backup_path = path.with_suffix(
        path.suffix + ".bak"
    )

    backup_path.write_text(
        path.read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    print(
        f"Backup created: {backup_path}"
    )


def replace_dependency_in_function(
    text: str,
    function_name: str,
    old_dependency: str,
    new_dependency: str,
) -> str:

    marker = (
        f"def {function_name}("
    )

    start = text.find(
        marker
    )

    if start == -1:

        raise RuntimeError(
            f"Function not found: "
            f"{function_name}"
        )

    next_function = text.find(
        "\ndef ",
        start + len(
            marker
        ),
    )

    if next_function == -1:

        next_function = len(
            text
        )

    block = text[
        start:next_function
    ]

    old = (
        f"Depends(\n"
        f"        {old_dependency}\n"
        f"    )"
    )

    new = (
        f"Depends(\n"
        f"        {new_dependency}\n"
        f"    )"
    )

    if old not in block:

        raise RuntimeError(
            f"{old_dependency} not found "
            f"in {function_name}"
        )

    block = block.replace(
        old,
        new,
        1,
    )

    return (
        text[:start]
        + block
        + text[next_function:]
    )


# ============================================================
# FACILITATOR / ASSESSOR SHARED ACADEMIC ROUTES
# ============================================================

backup(
    facilitator_file
)

text = facilitator_file.read_text(
    encoding="utf-8"
)

permission_import = """
from app.services.staff_permission_service import (
    require_permission,
)
"""

if (
    "from app.services.staff_permission_service import"
    not in text
):

    anchor = """
from app.staff_auth_dependency import (

    require_academic_delivery_staff,

)
"""

    if anchor not in text:

        raise RuntimeError(
            "Could not locate academic "
            "dependency import."
        )

    text = text.replace(
        anchor,
        permission_import,
        1,
    )


guard_code = """

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

router_marker = """
router = APIRouter(
"""

if (
    "require_view_assigned_classes"
    not in text
):

    position = text.find(
        router_marker
    )

    if position == -1:

        raise RuntimeError(
            "Could not locate facilitator "
            "router."
        )

    text = (
        text[:position]
        + guard_code
        + text[position:]
    )


facilitator_permissions = {
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
    facilitator_permissions.items()
):

    text = replace_dependency_in_function(
        text=text,
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
# LEARNING RESOURCE ROUTES
# ============================================================

backup(
    resources_file
)

text = resources_file.read_text(
    encoding="utf-8"
)


permission_import = """
from app.services.staff_permission_service import (
    require_permission,
)
"""

if (
    "from app.services.staff_permission_service import"
    not in text
):

    anchor = """
from app.staff_auth_dependency import (
    require_facilitator,
)
"""

    if anchor not in text:

        raise RuntimeError(
            "Could not locate learning "
            "resource staff dependency."
        )

    text = text.replace(
        anchor,
        permission_import,
        1,
    )


guard_code = """

# ============================================================
# LEARNING RESOURCE PERMISSION GUARD
# ============================================================

require_manage_learning_resources = (
    require_permission(
        "MANAGE_LEARNING_RESOURCES"
    )
)

"""

router_marker = """
router = APIRouter(
"""

if (
    "require_manage_learning_resources ="
    not in text
):

    position = text.find(
        router_marker
    )

    if position == -1:

        raise RuntimeError(
            "Could not locate learning "
            "resource router."
        )

    text = (
        text[:position]
        + guard_code
        + text[position:]
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

    text = replace_dependency_in_function(
        text=text,
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
    "PERMISSION PATCH COMPLETED SUCCESSFULLY"
)
