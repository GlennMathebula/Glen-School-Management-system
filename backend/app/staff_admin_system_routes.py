from fastapi import APIRouter, Depends

from app.services.admin_system_service import (
    get_admin_system_summary,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/system",
    tags=["Admin - System Administration & Configuration"],
)


@router.get("/summary")
def admin_system_summary(
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    return {
        "success": True,
        **get_admin_system_summary(),
    }

