from fastapi import Depends, HTTPException

from app.staff_auth_dependency import get_current_staff


def require_admin_staff(
    current_staff: dict = Depends(get_current_staff),
) -> dict:
    role_code = str(
        current_staff.get("role_code") or ""
    ).strip().upper()

    if role_code != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Administrator access is required.",
        )

    return current_staff

