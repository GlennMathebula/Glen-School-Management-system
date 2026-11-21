from app.abuse_rate_limit import enforce_resend_cooldown
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
    # REDIS_ABUSE_RATE_LIMIT: staff-temporary-credentials-reset
    enforce_resend_cooldown(
        scope="staff-temporary-credentials-reset",
        identity=staff_code,
        cooldown_seconds=60,
        hourly_limit=5,
    )
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

# ============================================================
# PRINCIPAL EXECUTIVE REPORTING - PRINCIPAL ROLE ONLY
# No generic reporting permission grants access to these routes.
# ============================================================
from fastapi.responses import Response as _PrincipalReportResponse
from app.staff_auth_dependency import require_principal as _require_principal
from app.services.principal_analytics_service import get_principal_statistics as _get_principal_statistics
from app.services.principal_report_documents import create_pdf as _principal_create_pdf, create_docx as _principal_create_docx
import re as _principal_re


@router.get("/statistics")
def principal_statistics(
    response: _PrincipalReportResponse,
    cycle_code: str | None = Query(default=None, max_length=100),
    staff: dict = Depends(_require_principal),
):
    try:
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return {"success": True, "data": _get_principal_statistics(cycle_code)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"ERROR: Principal statistics failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Principal statistics could not be generated.") from exc


@router.get("/statistics/{report_format}")
def principal_statistics_document(
    report_format: str,
    cycle_code: str | None = Query(default=None, max_length=100),
    staff: dict = Depends(_require_principal),
):
    if report_format not in ("pdf", "docx"):
        raise HTTPException(status_code=404, detail="Unsupported report format.")
    try:
        snapshot = _get_principal_statistics(cycle_code)
        output = _principal_create_pdf(snapshot, staff["staff_code"]) if report_format == "pdf" else _principal_create_docx(snapshot, staff["staff_code"])
        media_type = "application/pdf" if report_format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        slug = _principal_re.sub(r"[^A-Za-z0-9-]", "_", cycle_code or "Overall")[:90]
        return _PrincipalReportResponse(
            content=output,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="Glen_Moniques_Principal_{slug}_Report.{report_format}"',
                "Cache-Control": "private, no-store, max-age=0",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"ERROR: Principal document generation failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Principal report could not be generated.") from exc
