from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from uuid import UUID

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
    get_module_mark,
    get_summative_assessment,
    moderate_module_mark,
    moderate_summative_assessment,
    return_module_mark,
    return_summative_assessment,
    submit_module_mark,
    submit_summative_assessment,
    update_module_mark,
    update_summative_assessment,
)
from app.services.staff_audit_service import (
    create_staff_audit_log,
)
from app.services.staff_permission_service import (
    require_permission,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/staff/assessment",
    tags=[
        "Staff Assessment Workflow"
    ],
)


# ============================================================
# PERMISSION GUARDS
# ============================================================

require_assessment_result = (
    require_permission(
        "ASSESS_RESULT"
    )
)

require_moderate_result = (
    require_permission(
        "MODERATE_RESULT"
    )
)


# ============================================================
# AUDIT HELPERS
# ============================================================

def _json_safe(
    value,
):
    """
    Convert service-returned database values into JSON-safe
    values before sending them to staff_audit_service.

    This is needed because assessment records may contain
    UUID, Decimal, date and datetime values.
    """

    if value is None:
        return None

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _json_safe(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            _json_safe(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        (
            datetime,
            date,
            UUID,
            Decimal,
        ),
    ):
        return str(
            value
        )

    return value


def _write_assessment_audit(
    *,
    actor_staff_code: str,
    action_code: str,
    entity_type: str,
    entity_id: str,
    description: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Write the audit event after a successful assessment action.

    Audit failure is logged as a server warning rather than
    changing a successful assessment action into a false 500
    response. Full transactional audit enforcement can be
    introduced later at the service/database layer.
    """

    try:

        create_staff_audit_log(
            actor_staff_code=(
                actor_staff_code
            ),
            action_code=(
                action_code
            ),
            module_code=(
                "ASSESSMENT"
            ),
            entity_type=(
                entity_type
            ),
            entity_id=str(
                entity_id
            ),
            description=(
                description
            ),
            before_data=(
                _json_safe(
                    before_data
                )
            ),
            after_data=(
                _json_safe(
                    after_data
                )
            ),
            metadata=(
                _json_safe(
                    metadata
                    or {}
                )
            ),
        )

    except Exception as error:

        print(
            "WARNING: Assessment action "
            "succeeded but audit logging "
            "failed: "
            f"{error}"
        )


# ============================================================
# FISA / EISA POLICY
# ============================================================

def _require_fisa_type(
    assessment_type: str | None,
) -> None:

    normalised = str(
        assessment_type
        or ""
    ).strip().upper()

    if normalised != "FISA":

        raise ValueError(
            "Assessors and Moderators may "
            "work with FISA only. "
            "EISA is an official QCTO/AQP "
            "result and must be captured or "
            "imported through the Admin "
            "workflow."
        )


def _require_fisa_record(
    record: dict | None,
) -> None:

    if not record:

        raise ValueError(
            "Summative assessment not found."
        )

    _require_fisa_type(
        record.get(
            "assessment_type"
        )
    )


# ============================================================
# ASSESSOR MODULE QUEUE
# ============================================================

@router.get(
    "/assessor/module-queue"
)
def assessor_module_queue(
    current_staff: dict = Depends(
        require_assessment_result
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
        require_assessment_result
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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "ASSESSMENT_MODULE_CAPTURED"
            ),
            entity_type=(
                "MODULE_MARK"
            ),
            entity_id=(
                record[
                    "id"
                ]
            ),
            description=(
                "Assessor captured a module "
                "assessment as Draft."
            ),
            after_data=(
                record
            ),
            metadata={
                "module_registration_id": (
                    payload.module_registration_id
                ),
                "attempt_number": (
                    payload.attempt_number
                ),
            },
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
        require_assessment_result
    ),
):

    try:

        before_record = (
            get_module_mark(
                mark_id
            )
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "ASSESSMENT_MODULE_UPDATED"
            ),
            entity_type=(
                "MODULE_MARK"
            ),
            entity_id=(
                mark_id
            ),
            description=(
                "Assessor updated a module "
                "assessment."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
        )

        return {
            "success": True,
            "message": (
                "Module assessment updated."
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
# ASSESSOR SUBMIT MODULE MARK
# ============================================================

@router.post(
    "/assessor/module-marks/{mark_id}/submit"
)
def assessor_submit_module_mark(
    mark_id: str,

    current_staff: dict = Depends(
        require_assessment_result
    ),
):

    try:

        before_record = (
            get_module_mark(
                mark_id
            )
        )

        record = submit_module_mark(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            mark_id=mark_id,
        )

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "ASSESSMENT_MODULE_SUBMITTED"
            ),
            entity_type=(
                "MODULE_MARK"
            ),
            entity_id=(
                mark_id
            ),
            description=(
                "Assessor submitted a module "
                "assessment for moderation."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
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
        require_moderate_result
    ),
):

    try:

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

    except Exception as error:

        print(
            "ERROR: Moderator module queue "
            f"failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Moderator module queue "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# MODERATOR APPROVE MODULE MARK
# ============================================================

@router.post(
    "/moderator/module-marks/{mark_id}/moderate"
)
def moderator_approve_module_mark(
    mark_id: str,

    current_staff: dict = Depends(
        require_moderate_result
    ),
):

    try:

        before_record = (
            get_module_mark(
                mark_id
            )
        )

        record = moderate_module_mark(
            moderator_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            mark_id=mark_id,
        )

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "ASSESSMENT_MODULE_MODERATED"
            ),
            entity_type=(
                "MODULE_MARK"
            ),
            entity_id=(
                mark_id
            ),
            description=(
                "Moderator approved a module "
                "assessment."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
            metadata={
                "assessor_code": (
                    record.get(
                        "assessor_code"
                    )
                ),
                "moderator_code": (
                    current_staff[
                        "staff_code"
                    ]
                ),
            },
        )

        return {
            "success": True,
            "message": (
                "Module assessment moderated "
                "successfully."
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
# MODERATOR RETURN MODULE MARK
# ============================================================

@router.post(
    "/moderator/module-marks/{mark_id}/return"
)
def moderator_return_module_mark(
    mark_id: str,
    payload: ModerationReturnRequest,

    current_staff: dict = Depends(
        require_moderate_result
    ),
):

    try:

        before_record = (
            get_module_mark(
                mark_id
            )
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "ASSESSMENT_MODULE_RETURNED"
            ),
            entity_type=(
                "MODULE_MARK"
            ),
            entity_id=(
                mark_id
            ),
            description=(
                "Moderator returned a module "
                "assessment to the assessor."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
            metadata={
                "return_reason": (
                    payload.return_reason
                ),
            },
        )

        return {
            "success": True,
            "message": (
                "Module assessment returned "
                "to the assessor."
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
# ASSESSOR SUMMATIVE QUEUE
# ============================================================

@router.get(
    "/assessor/summative-queue"
)
def assessor_summative_queue(
    current_staff: dict = Depends(
        require_assessment_result
    ),
):

    try:

        records = [
            record
            for record in (
                get_assessor_summative_queue(
                    staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    )
                )
            )
            if str(
                record.get(
                    "assessment_type"
                )
                or ""
            ).strip().upper()
            == "FISA"
        ]

        return {
            "success": True,
            "count": len(
                records
            ),
            "data": records,
        }

    except Exception as error:

        print(
            "ERROR: Assessor summative queue "
            f"failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Assessor summative queue "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# ASSESSOR CAPTURE SUMMATIVE
# ============================================================

@router.post(
    "/assessor/summative"
)
def assessor_capture_summative(
    payload: SummativeAssessmentCaptureRequest,

    current_staff: dict = Depends(
        require_assessment_result
    ),
):

    try:

        _require_fisa_type(
            payload.assessment_type
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "SUMMATIVE_CAPTURED"
            ),
            entity_type=(
                "SUMMATIVE_ASSESSMENT"
            ),
            entity_id=(
                record[
                    "id"
                ]
            ),
            description=(
                "Assessor captured a summative "
                "assessment as Draft."
            ),
            after_data=(
                record
            ),
            metadata={
                "assessment_type": (
                    payload.assessment_type
                ),
                "registration_id": (
                    payload.registration_id
                ),
                "attempt_number": (
                    payload.attempt_number
                ),
            },
        )

        return {
            "success": True,
            "message": (
                "Summative assessment saved "
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
# ASSESSOR UPDATE SUMMATIVE
# ============================================================

@router.put(
    "/assessor/summative/{assessment_id}"
)
def assessor_update_summative(
    assessment_id: str,
    payload: SummativeAssessmentUpdateRequest,

    current_staff: dict = Depends(
        require_assessment_result
    ),
):

    try:

        before_record = (
            get_summative_assessment(
                assessment_id
            )
        )

        _require_fisa_record(
            before_record
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "SUMMATIVE_UPDATED"
            ),
            entity_type=(
                "SUMMATIVE_ASSESSMENT"
            ),
            entity_id=(
                assessment_id
            ),
            description=(
                "Assessor updated a summative "
                "assessment."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
        )

        return {
            "success": True,
            "message": (
                "Summative assessment updated."
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
# ASSESSOR SUBMIT SUMMATIVE
# ============================================================

@router.post(
    "/assessor/summative/{assessment_id}/submit"
)
def assessor_submit_summative(
    assessment_id: str,

    current_staff: dict = Depends(
        require_assessment_result
    ),
):

    try:

        before_record = (
            get_summative_assessment(
                assessment_id
            )
        )

        _require_fisa_record(
            before_record
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "SUMMATIVE_SUBMITTED"
            ),
            entity_type=(
                "SUMMATIVE_ASSESSMENT"
            ),
            entity_id=(
                assessment_id
            ),
            description=(
                "Assessor submitted a summative "
                "assessment for moderation."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
        )

        return {
            "success": True,
            "message": (
                "Summative assessment submitted "
                "for moderation."
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
# MODERATOR SUMMATIVE QUEUE
# ============================================================

@router.get(
    "/moderator/summative-queue"
)
def moderator_summative_queue(
    current_staff: dict = Depends(
        require_moderate_result
    ),
):

    try:

        records = [
            record
            for record in (
                get_moderator_summative_queue(
                    staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    )
                )
            )
            if str(
                record.get(
                    "assessment_type"
                )
                or ""
            ).strip().upper()
            == "FISA"
        ]

        return {
            "success": True,
            "count": len(
                records
            ),
            "data": records,
        }

    except Exception as error:

        print(
            "ERROR: Moderator summative queue "
            f"failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Moderator summative queue "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# MODERATOR APPROVE SUMMATIVE
# ============================================================

@router.post(
    "/moderator/summative/{assessment_id}/moderate"
)
def moderator_approve_summative(
    assessment_id: str,

    current_staff: dict = Depends(
        require_moderate_result
    ),
):

    try:

        before_record = (
            get_summative_assessment(
                assessment_id
            )
        )

        _require_fisa_record(
            before_record
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "SUMMATIVE_MODERATED"
            ),
            entity_type=(
                "SUMMATIVE_ASSESSMENT"
            ),
            entity_id=(
                assessment_id
            ),
            description=(
                "Moderator approved a summative "
                "assessment."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
            metadata={
                "assessor_code": (
                    record.get(
                        "assessor_code"
                    )
                ),
                "moderator_code": (
                    current_staff[
                        "staff_code"
                    ]
                ),
            },
        )

        return {
            "success": True,
            "message": (
                "Summative assessment moderated "
                "successfully."
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
# MODERATOR RETURN SUMMATIVE
# ============================================================

@router.post(
    "/moderator/summative/{assessment_id}/return"
)
def moderator_return_summative(
    assessment_id: str,
    payload: ModerationReturnRequest,

    current_staff: dict = Depends(
        require_moderate_result
    ),
):

    try:

        before_record = (
            get_summative_assessment(
                assessment_id
            )
        )

        _require_fisa_record(
            before_record
        )

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

        _write_assessment_audit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            action_code=(
                "SUMMATIVE_RETURNED"
            ),
            entity_type=(
                "SUMMATIVE_ASSESSMENT"
            ),
            entity_id=(
                assessment_id
            ),
            description=(
                "Moderator returned a summative "
                "assessment to the assessor."
            ),
            before_data=(
                before_record
            ),
            after_data=(
                record
            ),
            metadata={
                "return_reason": (
                    payload.return_reason
                ),
            },
        )

        return {
            "success": True,
            "message": (
                "Summative assessment returned "
                "to the assessor."
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
