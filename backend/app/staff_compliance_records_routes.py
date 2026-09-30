from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.compliance_records import (
    AppealCreate,
    AppealUpdate,
    CorrectiveActionCreate,
    CorrectiveActionUpdate,
    EisaCandidateCreate,
    EisaCandidateUpdate,
    EisaSittingCreate,
    EisaSittingUpdate,
    PlacementCreate,
    PlacementUpdate,
    SupervisorReportCreate,
    SupervisorReportUpdate,
    WeeklySubmissionCreate,
    WeeklySubmissionUpdate,
    WorkplaceAttendanceCreate,
)
from app.services.staff_compliance_records_service import (
    add_eisa_candidate,
    create_appeal,
    create_corrective_action,
    create_eisa_sitting,
    create_placement,
    create_supervisor_report,
    create_weekly_submission,
    list_appeals,
    list_corrective_actions,
    list_eisa_candidates,
    list_eisa_sittings,
    list_placements,
    list_supervisor_reports,
    list_weekly_submissions,
    list_workplace_attendance,
    update_appeal,
    update_corrective_action,
    update_eisa_candidate,
    update_eisa_sitting,
    update_placement,
    update_supervisor_report,
    update_weekly_submission,
    upsert_workplace_attendance,
)
from app.services.staff_permission_service import require_permission


router = APIRouter(
    prefix="/api/staff/compliance-records",
    tags=["Staff QA & Compliance Records"],
)

require_appeals = require_permission(
    "MANAGE_ASSESSMENT_APPEALS"
)
require_workplace = require_permission(
    "MANAGE_WORK_EXPERIENCE"
)
require_eisa_sittings = require_permission(
    "MANAGE_EISA_SITTINGS"
)
require_qa_actions = require_permission(
    "MANAGE_QA_ACTIONS"
)


def _handle(callable_):
    try:
        return callable_()
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(
            "ERROR: QA/Compliance records request failed: "
            f"{error}"
        )
        raise HTTPException(
            status_code=500,
            detail="The requested QA/Compliance action failed.",
        ) from error


@router.get("/appeals")
def appeals_list(
    cycle_code: str | None = Query(default=None),
    course_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_staff: dict = Depends(require_appeals),
):
    return {
        "success": True,
        "appeals": _handle(
            lambda: list_appeals(
                cycle_code=cycle_code,
                course_code=course_code,
                status=status,
            )
        ),
    }


@router.post("/appeals")
def appeals_create(
    payload: AppealCreate,
    current_staff: dict = Depends(require_appeals),
):
    return {
        "success": True,
        "appeal": _handle(
            lambda: create_appeal(
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/appeals/{appeal_id}")
def appeals_update(
    appeal_id: str,
    payload: AppealUpdate,
    current_staff: dict = Depends(require_appeals),
):
    return {
        "success": True,
        "appeal": _handle(
            lambda: update_appeal(
                appeal_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/workplace/placements")
def placements_list(
    cycle_code: str | None = Query(default=None),
    course_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "placements": _handle(
            lambda: list_placements(
                cycle_code=cycle_code,
                course_code=course_code,
                status=status,
            )
        ),
    }


@router.post("/workplace/placements")
def placements_create(
    payload: PlacementCreate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "placement": _handle(
            lambda: create_placement(
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/workplace/placements/{placement_id}")
def placements_update(
    placement_id: str,
    payload: PlacementUpdate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "placement": _handle(
            lambda: update_placement(
                placement_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/workplace/placements/{placement_id}/attendance")
def workplace_attendance_list(
    placement_id: str,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "attendance": _handle(
            lambda: list_workplace_attendance(
                placement_id
            )
        ),
    }


@router.post("/workplace/placements/{placement_id}/attendance")
def workplace_attendance_capture(
    placement_id: str,
    payload: WorkplaceAttendanceCreate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "attendance": _handle(
            lambda: upsert_workplace_attendance(
                placement_id,
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/workplace/placements/{placement_id}/weekly-submissions")
def weekly_submissions_list(
    placement_id: str,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "submissions": _handle(
            lambda: list_weekly_submissions(
                placement_id
            )
        ),
    }


@router.post("/workplace/placements/{placement_id}/weekly-submissions")
def weekly_submissions_create(
    placement_id: str,
    payload: WeeklySubmissionCreate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "submission": _handle(
            lambda: create_weekly_submission(
                placement_id,
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/workplace/weekly-submissions/{submission_id}")
def weekly_submissions_update(
    submission_id: str,
    payload: WeeklySubmissionUpdate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "submission": _handle(
            lambda: update_weekly_submission(
                submission_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/workplace/placements/{placement_id}/supervisor-reports")
def supervisor_reports_list(
    placement_id: str,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "reports": _handle(
            lambda: list_supervisor_reports(
                placement_id
            )
        ),
    }


@router.post("/workplace/placements/{placement_id}/supervisor-reports")
def supervisor_reports_create(
    placement_id: str,
    payload: SupervisorReportCreate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "report": _handle(
            lambda: create_supervisor_report(
                placement_id,
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/workplace/supervisor-reports/{report_id}")
def supervisor_reports_update(
    report_id: str,
    payload: SupervisorReportUpdate,
    current_staff: dict = Depends(require_workplace),
):
    return {
        "success": True,
        "report": _handle(
            lambda: update_supervisor_report(
                report_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/eisa/sittings")
def eisa_sittings_list(
    cycle_code: str | None = Query(default=None),
    course_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_staff: dict = Depends(require_eisa_sittings),
):
    return {
        "success": True,
        "sittings": _handle(
            lambda: list_eisa_sittings(
                cycle_code=cycle_code,
                course_code=course_code,
                status=status,
            )
        ),
    }


@router.post("/eisa/sittings")
def eisa_sittings_create(
    payload: EisaSittingCreate,
    current_staff: dict = Depends(require_eisa_sittings),
):
    return {
        "success": True,
        "sitting": _handle(
            lambda: create_eisa_sitting(
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/eisa/sittings/{sitting_id}")
def eisa_sittings_update(
    sitting_id: str,
    payload: EisaSittingUpdate,
    current_staff: dict = Depends(require_eisa_sittings),
):
    return {
        "success": True,
        "sitting": _handle(
            lambda: update_eisa_sitting(
                sitting_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/eisa/sittings/{sitting_id}/candidates")
def eisa_candidates_list(
    sitting_id: str,
    current_staff: dict = Depends(require_eisa_sittings),
):
    return {
        "success": True,
        "candidates": _handle(
            lambda: list_eisa_candidates(
                sitting_id
            )
        ),
    }


@router.post("/eisa/sittings/{sitting_id}/candidates")
def eisa_candidates_create(
    sitting_id: str,
    payload: EisaCandidateCreate,
    current_staff: dict = Depends(require_eisa_sittings),
):
    return {
        "success": True,
        "candidate": _handle(
            lambda: add_eisa_candidate(
                sitting_id,
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/eisa/candidates/{candidate_id}")
def eisa_candidates_update(
    candidate_id: str,
    payload: EisaCandidateUpdate,
    current_staff: dict = Depends(require_eisa_sittings),
):
    return {
        "success": True,
        "candidate": _handle(
            lambda: update_eisa_candidate(
                candidate_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.get("/qa/corrective-actions")
def corrective_actions_list(
    cycle_code: str | None = Query(default=None),
    course_code: str | None = Query(default=None),
    class_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_staff: dict = Depends(require_qa_actions),
):
    return {
        "success": True,
        "actions": _handle(
            lambda: list_corrective_actions(
                cycle_code=cycle_code,
                course_code=course_code,
                class_code=class_code,
                status=status,
            )
        ),
    }


@router.post("/qa/corrective-actions")
def corrective_actions_create(
    payload: CorrectiveActionCreate,
    current_staff: dict = Depends(require_qa_actions),
):
    return {
        "success": True,
        "action": _handle(
            lambda: create_corrective_action(
                payload.model_dump(),
                actor=current_staff["staff_code"],
            )
        ),
    }


@router.patch("/qa/corrective-actions/{action_id}")
def corrective_actions_update(
    action_id: str,
    payload: CorrectiveActionUpdate,
    current_staff: dict = Depends(require_qa_actions),
):
    return {
        "success": True,
        "action": _handle(
            lambda: update_corrective_action(
                action_id,
                payload.model_dump(
                    exclude_unset=True
                ),
                actor=current_staff["staff_code"],
            )
        ),
    }
