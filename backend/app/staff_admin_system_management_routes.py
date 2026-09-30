from fastapi import APIRouter, Depends, HTTPException

from app.models.backend_finalization import (
    RolePermissionsUpdate,
    StaffAccountCreate,
    StaffAccountStatusUpdate,
    SystemSettingUpdate,
)
from app.services.admin_system_management_service import (
    create_staff_account,
    list_roles_permissions,
    list_staff_accounts,
    list_system_settings,
    replace_role_permissions,
    set_staff_account_status,
    update_system_setting,
)
from app.services.staff_permission_service import require_permission


router = APIRouter(
    prefix="/api/staff/admin/system-management",
    tags=["Admin - System Management"],
)

require_system_settings = require_permission("MANAGE_SYSTEM_SETTINGS")
require_staff_accounts = require_permission("MANAGE_STAFF_ACCOUNTS")
require_roles_permissions = require_permission("MANAGE_ROLES_PERMISSIONS")


@router.get("/settings")
def admin_system_settings(
    current_staff: dict = Depends(require_system_settings),
):
    records = list_system_settings()
    return {"success": True, "count": len(records), "settings": records}


@router.patch("/settings/{setting_key}")
def admin_system_setting_update(
    setting_key: str,
    payload: SystemSettingUpdate,
    current_staff: dict = Depends(require_system_settings),
):
    try:
        return {
            "success": True,
            "setting": update_system_setting(
                actor_staff_code=current_staff["staff_code"],
                setting_key=setting_key,
                value=payload.value,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/staff-accounts")
def admin_staff_accounts(
    current_staff: dict = Depends(require_staff_accounts),
):
    records = list_staff_accounts()
    return {"success": True, "count": len(records), "staff_accounts": records}


@router.post("/staff-accounts")
def admin_staff_account_create(
    payload: StaffAccountCreate,
    current_staff: dict = Depends(require_staff_accounts),
):
    try:
        return {
            "success": True,
            "staff_account": create_staff_account(
                actor_staff_code=current_staff["staff_code"],
                employee_id=payload.employee_id,
                staff_code=payload.staff_code,
                role_code=payload.role_code,
                temporary_password=payload.temporary_password,
                temporary_pin=payload.temporary_pin,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/staff-accounts/{staff_code}/status")
def admin_staff_account_status(
    staff_code: str,
    payload: StaffAccountStatusUpdate,
    current_staff: dict = Depends(require_staff_accounts),
):
    try:
        return {
            "success": True,
            "staff_account": set_staff_account_status(
                actor_staff_code=current_staff["staff_code"],
                staff_code=staff_code,
                is_active=payload.is_active,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/roles")
def admin_roles(
    current_staff: dict = Depends(require_roles_permissions),
):
    records = list_roles_permissions()
    return {"success": True, "count": len(records), "roles": records}


@router.patch("/roles/{role_code}/permissions")
def admin_role_permissions_update(
    role_code: str,
    payload: RolePermissionsUpdate,
    current_staff: dict = Depends(require_roles_permissions),
):
    try:
        return {
            "success": True,
            "role": replace_role_permissions(
                actor_staff_code=current_staff["staff_code"],
                role_code=role_code,
                permission_codes=payload.permission_codes,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
