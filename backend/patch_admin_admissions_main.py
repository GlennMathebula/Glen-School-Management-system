from __future__ import annotations

import ast
import shutil
from datetime import datetime
from pathlib import Path


BACKEND = Path(r"C:\Projects\Glen Moniques SMS\backend")
MAIN = BACKEND / "app" / "main.py"
MODULE_NAME = "app.staff_admissions_routes"
ROUTER_NAME = "staff_admissions_router"


def _is_fastapi_assignment(node: ast.AST) -> bool:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False

    value = getattr(node, "value", None)

    if not isinstance(value, ast.Call):
        return False

    func = value.func

    if isinstance(func, ast.Name):
        return func.id == "FastAPI"

    if isinstance(func, ast.Attribute):
        return func.attr == "FastAPI"

    return False


def _targets_app(node: ast.AST) -> bool:
    if isinstance(node, ast.Assign):
        return any(
            isinstance(target, ast.Name)
            and target.id == "app"
            for target in node.targets
        )

    if isinstance(node, ast.AnnAssign):
        return (
            isinstance(node.target, ast.Name)
            and node.target.id == "app"
        )

    return False


def _strip_existing(source: str) -> str:
    tree = ast.parse(source)
    ranges = []

    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == MODULE_NAME
        ):
            ranges.append(
                (
                    node.lineno,
                    node.end_lineno or node.lineno,
                )
            )

        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
        ):
            call = node.value

            if (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "app"
                and call.func.attr == "include_router"
                and call.args
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id == ROUTER_NAME
            ):
                ranges.append(
                    (
                        node.lineno,
                        node.end_lineno or node.lineno,
                    )
                )

    lines = source.splitlines(
        keepends=True
    )

    for start, end in sorted(
        ranges,
        reverse=True,
    ):
        del lines[start - 1:end]

    return "".join(lines)


def main() -> None:
    if not MAIN.exists():
        raise FileNotFoundError(
            f"main.py not found: {MAIN}"
        )

    source = MAIN.read_text(
        encoding="utf-8-sig"
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = MAIN.with_name(
        f"main.py.admin-admissions-backup-{stamp}"
    )

    shutil.copy2(
        MAIN,
        backup,
    )

    source = _strip_existing(
        source
    )

    tree = ast.parse(
        source
    )

    apps = [
        node
        for node in tree.body
        if _targets_app(node)
        and _is_fastapi_assignment(node)
    ]

    if not apps:
        raise RuntimeError(
            "No module-level app = FastAPI(...) "
            "assignment was found."
        )

    target = apps[-1]

    block = """
from app.staff_admissions_routes import (
    router as staff_admissions_router,
)

app.include_router(
    staff_admissions_router
)

"""

    lines = source.splitlines(
        keepends=True
    )

    lines.insert(
        target.end_lineno,
        block,
    )

    patched = "".join(
        lines
    )

    ast.parse(
        patched
    )

    MAIN.write_text(
        patched,
        encoding="utf-8",
    )

    print(
        "Admin Admissions router mounted."
    )
    print(
        "Backup:",
        backup,
    )


if __name__ == "__main__":
    main()
