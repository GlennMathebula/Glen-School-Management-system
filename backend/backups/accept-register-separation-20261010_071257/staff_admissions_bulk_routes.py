from __future__ import annotations

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
)
from pydantic import (
    BaseModel,
    Field,
)

from app.services.staff_admissions_service import (
    accept_application,
    reject_application,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/admissions/bulk",
    tags=[
        "Staff Admissions Bulk Actions"
    ],
)


require_manage_applications = require_permission(
    "MANAGE_APPLICATIONS"
)

require_manage_registrations = require_permission(
    "MANAGE_REGISTRATIONS"
)


class BulkAcceptRequest(
    BaseModel
):
    student_numbers: list[str] = Field(
        min_length=1,
        max_length=200,
    )

    funding_type: str | None = Field(
        default=None,
        max_length=100,
    )

    cycle_code: str | None = Field(
        default=None,
        max_length=100,
    )

    program_start_date: date | None = None

    expected_completion_date: (
        date | None
    ) = None

    enforce_documents: bool = True


class BulkRejectRequest(
    BaseModel
):
    student_numbers: list[str] = Field(
        min_length=1,
        max_length=200,
    )

    reason: str | None = Field(
        default=None,
        max_length=3000,
    )


def _student_numbers(
    values: list[str],
) -> list[str]:
    result = []

    for value in values:
        student_number = str(
            value or ""
        ).strip()

        if (
            student_number
            and student_number
            not in result
        ):
            result.append(
                student_number
            )

    return result


@router.post("/accept")
def bulk_accept_applications(
    payload: BulkAcceptRequest,
    current_staff: dict = Depends(
        require_manage_applications
    ),
    registration_staff: dict = Depends(
        require_manage_registrations
    ),
):
    del registration_staff

    students = _student_numbers(
        payload.student_numbers
    )

    results = []

    for student_number in students:
        try:
            data = accept_application(
                student_number,
                funding_type=(
                    payload.funding_type
                ),
                cycle_code=(
                    payload.cycle_code
                ),
                program_start_date=(
                    payload.program_start_date
                ),
                expected_completion_date=(
                    payload.expected_completion_date
                ),
                enforce_documents=(
                    payload.enforce_documents
                ),
                actor=current_staff[
                    "staff_code"
                ],
            )

            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "success": True,
                    "message": (
                        "Accepted and "
                        "registration processed."
                    ),
                    "data": data,
                }
            )

        except Exception as error:
            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "success": False,
                    "error": str(
                        error
                    ),
                }
            )

    success_count = sum(
        1
        for item in results
        if item[
            "success"
        ]
    )

    return {
        "success": True,
        "requested_count": len(
            students
        ),
        "success_count": (
            success_count
        ),
        "failure_count": (
            len(
                students
            )
            - success_count
        ),
        "results": results,
    }


@router.post("/reject")
def bulk_reject_applications(
    payload: BulkRejectRequest,
    current_staff: dict = Depends(
        require_manage_applications
    ),
):
    students = _student_numbers(
        payload.student_numbers
    )

    results = []

    for student_number in students:
        try:
            data = reject_application(
                student_number,
                reason=(
                    payload.reason
                ),
                actor=current_staff[
                    "staff_code"
                ],
            )

            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "success": True,
                    "message": (
                        "Application rejected."
                    ),
                    "data": data,
                }
            )

        except Exception as error:
            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "success": False,
                    "error": str(
                        error
                    ),
                }
            )

    success_count = sum(
        1
        for item in results
        if item[
            "success"
        ]
    )

    return {
        "success": True,
        "requested_count": len(
            students
        ),
        "success_count": (
            success_count
        ),
        "failure_count": (
            len(
                students
            )
            - success_count
        ),
        "results": results,
    }
