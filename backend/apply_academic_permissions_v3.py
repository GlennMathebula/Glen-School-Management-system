from pathlib import Path
import ast
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

def backup_once(
    path: Path,
):

    backup_path = path.with_suffix(
        path.suffix
        + ".before_permissions.bak"
    )

    if not backup_path.exists():

        backup_path.write_text(
            path.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

        print(
            f"Backup created: "
            f"{backup_path}"
        )


def ensure_permission_import(
    source: str,
) -> str:

    if (
        "from app.services."
        "staff_permission_service import"
        in source
    ):

        return source

    import_block = (
        "\n"
        "from app.services."
        "staff_permission_service import (\n"
        "    require_permission,\n"
        ")\n"
    )

    router_position = source.find(
        "router = APIRouter("
    )

    if router_position == -1:

        raise RuntimeError(
            "Router declaration not found."
        )

    return (
        source[:router_position]
        + import_block
        + "\n"
        + source[router_position:]
    )


def get_function_range(
    source: str,
    function_name: str,
):

    tree = ast.parse(
        source
    )

    for node in ast.walk(
        tree
    ):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):

            if (
                node.name
                == function_name
            ):

                lines = source.splitlines(
                    keepends=True
                )

                start = sum(
                    len(
                        lines[index]
                    )
                    for index
                    in range(
                        node.lineno - 1
                    )
                )

                end = sum(
                    len(
                        lines[index]
                    )
                    for index
                    in range(
                        node.end_lineno
                    )
                )

                return (
                    start,
                    end,
                )

    raise RuntimeError(
        f"Function not found: "
        f"{function_name}"
    )


def replace_dependency(
    source: str,
    function_name: str,
    old_dependency: str,
    new_dependency: str,
) -> str:

    start, end = (
        get_function_range(
            source,
            function_name,
        )
    )

    block = source[
        start:end
    ]

    pattern = re.compile(
        r"Depends\s*\(\s*"
        + re.escape(
            old_dependency
        )
        + r"\s*\)",
        re.DOTALL,
    )

    if not pattern.search(
        block
    ):

        raise RuntimeError(
            f"{old_dependency} not found "
            f"in {function_name}"
        )

    replacement = (
        "Depends(\n"
        f"        {new_dependency}\n"
        "    )"
    )

    block = pattern.sub(
        replacement,
        block,
        count=1,
    )

    return (
        source[:start]
        + block
        + source[end:]
    )


def remove_old_import_name(
    source: str,
    dependency_name: str,
) -> str:

    source = re.sub(
        rf"\n\s*{re.escape(dependency_name)},",
        "",
        source,
    )

    return source


# ============================================================
# ACADEMIC DELIVERY
# ============================================================

backup_once(
    facilitator_file
)

facilitator_text = (
    facilitator_file.read_text(
        encoding="utf-8"
    )
)

facilitator_text = (
    ensure_permission_import(
        facilitator_text
    )
)


academic_guards = """
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
    not in facilitator_text
):

    router_position = (
        facilitator_text.find(
            "router = APIRouter("
        )
    )

    if router_position == -1:

        raise RuntimeError(
            "Facilitator router "
            "not found."
        )

    facilitator_text = (
        facilitator_text[
            :router_position
        ]
        + academic_guards
        + facilitator_text[
            router_position:
        ]
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


for (
    function_name,
    permission_dependency,
) in academic_permissions.items():

    facilitator_text = (
        replace_dependency(
            source=(
                facilitator_text
            ),

            function_name=(
                function_name
            ),

            old_dependency=(
                "require_academic_delivery_staff"
            ),

            new_dependency=(
                permission_dependency
            ),
        )
    )


facilitator_text = (
    remove_old_import_name(
        facilitator_text,
        "require_academic_delivery_staff",
    )
)


# Validate before writing.
ast.parse(
    facilitator_text
)


# ============================================================
# LEARNING RESOURCES
# ============================================================

backup_once(
    resources_file
)

resources_text = (
    resources_file.read_text(
        encoding="utf-8"
    )
)

resources_text = (
    ensure_permission_import(
        resources_text
    )
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
    not in resources_text
):

    router_position = (
        resources_text.find(
            "router = APIRouter("
        )
    )

    if router_position == -1:

        raise RuntimeError(
            "Learning resource router "
            "not found."
        )

    resources_text = (
        resources_text[
            :router_position
        ]
        + resource_guard
        + resources_text[
            router_position:
        ]
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


for function_name in (
    resource_functions
):

    resources_text = (
        replace_dependency(
            source=(
                resources_text
            ),

            function_name=(
                function_name
            ),

            old_dependency=(
                "require_facilitator"
            ),

            new_dependency=(
                "require_manage_learning_resources"
            ),
        )
    )


resources_text = (
    remove_old_import_name(
        resources_text,
        "require_facilitator",
    )
)


# Validate before writing.
ast.parse(
    resources_text
)


# ============================================================
# SAVE ONLY AFTER EVERYTHING PASSES
# ============================================================

facilitator_file.write_text(
    facilitator_text,
    encoding="utf-8",
)

resources_file.write_text(
    resources_text,
    encoding="utf-8",
)


print()
print(
    "Academic Delivery permissions updated."
)

print(
    "Learning Resource permissions updated."
)

print()
print(
    "ACADEMIC + LEARNING RESOURCE "
    "PERMISSION PATCH COMPLETE"
)
