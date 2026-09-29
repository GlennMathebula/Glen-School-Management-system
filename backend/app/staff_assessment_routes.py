from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.staff_assessment import (
    ModerationReturnRequest,
    ModuleMarkCaptureRequest,
    ModuleMarkUpdateRequest,
    SummativeAssessmentCaptureRequest,
    SummativeAssessmentUpdateRequest,
)
from app.services.staff_assessment_service import (
    capture_module_mark,
    capture_summative_assessment,
    get_assessor_module_queue,
    get_assessor_summative_queue,
    get_moderator_module_queue,
    get_moderator_summative_queue,
    moderate_module_mark,
    moderate_summative_assessment,
    return_module_mark,
    return_summative_assessment,
    submit_module_mark,
    submit_summative_assessment,
    update_module_mark,
    update_summative_assessment,
)
from app.staff_auth_dependency import (
    require_assessor,
    require_moderator,
)


router = APIRouter(
    prefix="/api/staff/assessment",
    tags=[
        "Staff Assessment Workflow"
    ],
)


# ============================================================
# ASSESSOR MODULE QUEUE
# ============================================================

@router.get(
    "/assessor/module-queue"
)
def assessor_module_queue(
    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        records = (
            get_assessor_module_queue(
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
            "data": records,
        }

    except Exception as error:

        print(
            "ERROR: Assessor module queue "
            f"failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Assessor module queue "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# ASSESSOR CAPTURE MODULE MARK
# ============================================================

@router.post(
    "/assessor/module-marks"
)
def assessor_capture_module_mark(
    payload: ModuleMarkCaptureRequest,

    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        record = capture_module_mark(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            module_registration_id=(
                payload.module_registration_id
            ),
            attempt_number=(
                payload.attempt_number
            ),
            mark=payload.mark,
            grade=payload.grade,
            semester=payload.semester,
            academic_year=(
                payload.academic_year
            ),
            result=payload.result,
        )

        return {
            "success": True,
            "message": (
                "Module assessment saved "
                "as Draft."
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


# ============================================================
# ASSESSOR UPDATE MODULE MARK
# ============================================================

@router.put(
    "/assessor/module-marks/{mark_id}"
)
def assessor_update_module_mark(
    mark_id: str,
    payload: ModuleMarkUpdateRequest,

    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        record = update_module_mark(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            mark_id=mark_id,
            mark=payload.mark,
            grade=payload.grade,
            semester=payload.semester,
            academic_year=(
                payload.academic_year
            ),
            result=payload.result,
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# ASSESSOR SUBMIT MODULE MARK
# ============================================================

@router.post(
    "/assessor/module-marks/{mark_id}/submit"
)
def assessor_submit_module_mark(
    mark_id: str,

    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        record = submit_module_mark(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            mark_id=mark_id,
        )

        return {
            "success": True,
            "message": (
                "Submitted for moderation."
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


# ============================================================
# MODERATOR MODULE QUEUE
# ============================================================

@router.get(
    "/moderator/module-queue"
)
def moderator_module_queue(
    current_staff: dict = Depends(
        require_moderator
    ),
):

    records = (
        get_moderator_module_queue(
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
        "data": records,
    }


# ============================================================
# MODERATOR APPROVE MODULE MARK
# ============================================================

@router.post(
    "/moderator/module-marks/{mark_id}/moderate"
)
def moderator_approve_module_mark(
    mark_id: str,

    current_staff: dict = Depends(
        require_moderator
    ),
):

    try:

        record = moderate_module_mark(
            moderator_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            mark_id=mark_id,
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# MODERATOR RETURN MODULE MARK
# ============================================================

@router.post(
    "/moderator/module-marks/{mark_id}/return"
)
def moderator_return_module_mark(
    mark_id: str,
    payload: ModerationReturnRequest,

    current_staff: dict = Depends(
        require_moderator
    ),
):

    try:

        record = return_module_mark(
            moderator_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            mark_id=mark_id,
            return_reason=(
                payload.return_reason
            ),
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# ASSESSOR SUMMATIVE QUEUE
# ============================================================

@router.get(
    "/assessor/summative-queue"
)
def assessor_summative_queue(
    current_staff: dict = Depends(
        require_assessor
    ),
):

    records = (
        get_assessor_summative_queue(
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
        "data": records,
    }


# ============================================================
# ASSESSOR CAPTURE SUMMATIVE
# ============================================================

@router.post(
    "/assessor/summative"
)
def assessor_capture_summative(
    payload: SummativeAssessmentCaptureRequest,

    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        record = (
            capture_summative_assessment(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                registration_id=(
                    payload.registration_id
                ),
                assessment_type=(
                    payload.assessment_type
                ),
                attempt_number=(
                    payload.attempt_number
                ),
                mark=payload.mark,
                assessment_date=(
                    payload.assessment_date
                ),
                result=payload.result,
            )
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# ASSESSOR UPDATE SUMMATIVE
# ============================================================

@router.put(
    "/assessor/summative/{assessment_id}"
)
def assessor_update_summative(
    assessment_id: str,
    payload: SummativeAssessmentUpdateRequest,

    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        record = (
            update_summative_assessment(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                assessment_id=(
                    assessment_id
                ),
                mark=payload.mark,
                assessment_date=(
                    payload.assessment_date
                ),
                result=payload.result,
            )
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# ASSESSOR SUBMIT SUMMATIVE
# ============================================================

@router.post(
    "/assessor/summative/{assessment_id}/submit"
)
def assessor_submit_summative(
    assessment_id: str,

    current_staff: dict = Depends(
        require_assessor
    ),
):

    try:

        record = (
            submit_summative_assessment(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                assessment_id=(
                    assessment_id
                ),
            )
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# MODERATOR SUMMATIVE QUEUE
# ============================================================

@router.get(
    "/moderator/summative-queue"
)
def moderator_summative_queue(
    current_staff: dict = Depends(
        require_moderator
    ),
):

    records = (
        get_moderator_summative_queue(
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
        "data": records,
    }


# ============================================================
# MODERATOR APPROVE SUMMATIVE
# ============================================================

@router.post(
    "/moderator/summative/{assessment_id}/moderate"
)
def moderator_approve_summative(
    assessment_id: str,

    current_staff: dict = Depends(
        require_moderator
    ),
):

    try:

        record = (
            moderate_summative_assessment(
                moderator_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                assessment_id=(
                    assessment_id
                ),
            )
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# MODERATOR RETURN SUMMATIVE
# ============================================================

@router.post(
    "/moderator/summative/{assessment_id}/return"
)
def moderator_return_summative(
    assessment_id: str,
    payload: ModerationReturnRequest,

    current_staff: dict = Depends(
        require_moderator
    ),
):

    try:

        record = (
            return_summative_assessment(
                moderator_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                assessment_id=(
                    assessment_id
                ),
                return_reason=(
                    payload.return_reason
                ),
            )
        )

        return {
            "success": True,
            "data": record,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error