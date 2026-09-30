from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.models.principal_portal import (
    PrincipalStaffContactUpdate,
    PrincipalStaffCredentialReset,
    PrincipalStaffSupportCreate,
    PrincipalSupportTicketUpdate,
)
from app.services.principal_portal_service import (
    create_staff_support_ticket,
    get_principal_overview,
    list_my_staff_support_tickets,
    list_principal_staff,
    list_staff_support_tickets,
    reset_staff_credentials,
    update_staff_contact,
    update_staff_support_ticket,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/principal",
    tags=[
        "Principal Portal"
    ],
)


require_system_oversight = (
    require_permission(
        "SYSTEM_OVERSIGHT"
    )
)

require_edit_staff_contact = (
    require_permission(
        "EDIT_STAFF_CONTACT"
    )
)

require_change_staff_credentials = (
    require_permission(
        "CHANGE_STAFF_CREDENTIALS"
    )
)

require_staff_support = (
    require_permission(
        "USE_STAFF_SUPPORT"
    )
)

require_manage_support = (
    require_permission(
        "MANAGE_SUPPORT"
    )
)


@router.get(
    "/overview"
)
def principal_overview(
    current_staff: dict = Depends(
        require_system_oversight
    ),
):
    try:
        return {
            "success": True,
            "data": (
                get_principal_overview()
            ),
        }
    except Exception as error:
        print(
            "ERROR: Principal overview "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Principal overview could "
                "not be loaded."
            ),
        ) from error


@router.get(
    "/staff"
)
def principal_staff(
    current_staff: dict = Depends(
        require_system_oversight
    ),
):
    try:
        records = (
            list_principal_staff()
        )

        return {
            "success": True,
            "count": len(
                records
            ),
            "staff": records,
        }
    except Exception as error:
        print(
            "ERROR: Principal staff list "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Staff list could not "
                "be loaded."
            ),
        ) from error


@router.patch(
    "/staff/{staff_code}/contact"
)
def principal_staff_contact_update(
    staff_code: str,
    payload: (
        PrincipalStaffContactUpdate
    ),
    current_staff: dict = Depends(
        require_edit_staff_contact
    ),
):
    try:
        record = update_staff_contact(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            staff_code=staff_code,
            email=payload.email,
            cell_number=(
                payload.cell_number
            ),
            phone_number=(
                payload.phone_number
            ),
        )

        return {
            "success": True,
            "message": (
                "Staff contact details "
                "updated."
            ),
            "data": record,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/staff/{staff_code}/temporary-credentials"
)
def principal_staff_credentials_reset(
    staff_code: str,
    payload: (
        PrincipalStaffCredentialReset
    ),
    current_staff: dict = Depends(
        require_change_staff_credentials
    ),
):
    try:
        record = (
            reset_staff_credentials(
                actor_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                staff_code=staff_code,
                temporary_password=(
                    payload.temporary_password
                ),
                temporary_pin=(
                    payload.temporary_pin
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Temporary staff "
                "credentials issued."
            ),
            "data": record,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/support/mine"
)
def principal_my_support(
    current_staff: dict = Depends(
        require_staff_support
    ),
):
    records = (
        list_my_staff_support_tickets(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            )
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "tickets": records,
    }


@router.post(
    "/support/mine"
)
def principal_support_create(
    payload: PrincipalStaffSupportCreate,
    current_staff: dict = Depends(
        require_staff_support
    ),
):
    try:
        ticket = (
            create_staff_support_ticket(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                subject=payload.subject,
                category=(
                    payload.category
                ),
                description=(
                    payload.description
                ),
                priority=(
                    payload.priority
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Support ticket created."
            ),
            "ticket": ticket,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/support/tickets"
)
def principal_support_tickets(
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    current_staff: dict = Depends(
        require_manage_support
    ),
):
    records = (
        list_staff_support_tickets(
            status=status,
            priority=priority,
            search=search,
            limit=limit,
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "tickets": records,
    }


@router.patch(
    "/support/tickets/{ticket_id}"
)
def principal_support_ticket_update(
    ticket_id: str,
    payload: (
        PrincipalSupportTicketUpdate
    ),
    current_staff: dict = Depends(
        require_manage_support
    ),
):
    try:
        ticket = (
            update_staff_support_ticket(
                actor_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                ticket_id=ticket_id,
                status=payload.status,
                priority=payload.priority,
                assigned_to_staff_code=(
                    payload.assigned_to_staff_code
                ),
                resolution=(
                    payload.resolution
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Support ticket updated."
            ),
            "ticket": ticket,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error
