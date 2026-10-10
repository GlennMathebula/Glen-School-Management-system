from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.models.academic_management import (
    ClassCreateRequest,
    ClassEnrolmentRequest,
    ClassStaffAssignmentRequest,
    ClassUpdateRequest,
    CycleCourseStatusRequest,
    CycleCreateRequest,
    CycleStatusRequest,
    CycleUpdateRequest,
)
from app.services.academic_management_service import (
    assign_class_staff,
    create_class,
    create_cycle,
    enrol_registration_in_class,
    get_academic_staff_options,
    get_class_learners,
    get_classes,
    get_courses,
    get_cycle_courses,
    get_cycles,
    get_eligible_class_learners,
    remove_registration_from_class,
    set_cycle_course_status,
    set_cycle_status,
    update_class,
    update_cycle,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/academic-management",
    tags=[
        "Staff Academic Management"
    ],
)


require_manage_academic_structure = (
    require_permission(
        "MANAGE_ACADEMIC_STRUCTURE"
    )
)

require_manage_class_enrolments = (
    require_permission(
        "MANAGE_CLASS_ENROLMENTS"
    )
)


# ============================================================
# CYCLES
# ============================================================

@router.get(
    "/cycles"
)
def academic_cycles(
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        records = get_cycles()

        return {
            "success": True,
            "count": len(
                records
            ),
            "cycles": records,
        }

    except Exception as error:
        print(
            "ERROR: Academic cycles "
            f"could not load: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Academic cycles could "
                "not be loaded."
            ),
        ) from error


@router.post(
    "/cycles"
)
def academic_cycle_create(
    payload: CycleCreateRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = create_cycle(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            cycle_code=(
                payload.cycle_code
            ),
            cycle_name=(
                payload.cycle_name
            ),
            application_start_date=(
                payload.application_start_date
            ),
            application_end_date=(
                payload.application_end_date
            ),
            registration_start_date=(
                payload.registration_start_date
            ),
            registration_end_date=(
                payload.registration_end_date
            ),
            program_start_date=(
                payload.program_start_date
            ),
            expected_completion_date=(
                payload.expected_completion_date
            ),
            cipc_required=(
                payload.cipc_required
            ),
            status=payload.status,
        )

        return {
            "success": True,
            "message": (
                "Academic cycle created."
            ),
            "cycle": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.put(
    "/cycles/{cycle_code}"
)
def academic_cycle_update(
    cycle_code: str,
    payload: CycleUpdateRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = update_cycle(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            cycle_code=cycle_code,
            cycle_name=(
                payload.cycle_name
            ),
            application_start_date=(
                payload.application_start_date
            ),
            application_end_date=(
                payload.application_end_date
            ),
            registration_start_date=(
                payload.registration_start_date
            ),
            registration_end_date=(
                payload.registration_end_date
            ),
            program_start_date=(
                payload.program_start_date
            ),
            expected_completion_date=(
                payload.expected_completion_date
            ),
            cipc_required=(
                payload.cipc_required
            ),
        )

        return {
            "success": True,
            "message": (
                "Academic cycle updated."
            ),
            "cycle": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.patch(
    "/cycles/{cycle_code}/status"
)
def academic_cycle_status(
    cycle_code: str,
    payload: CycleStatusRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = set_cycle_status(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            cycle_code=cycle_code,
            status=payload.status,
        )

        return {
            "success": True,
            "message": (
                "Cycle status updated."
            ),
            "cycle": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# COURSES + CYCLE OFFERINGS
# ============================================================

@router.get(
    "/courses"
)
def academic_courses(
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        records = get_courses()

        return {
            "success": True,
            "count": len(
                records
            ),
            "courses": records,
        }

    except Exception as error:
        print(
            "ERROR: Courses could not "
            f"load: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Courses could not "
                "be loaded."
            ),
        ) from error


@router.get(
    "/cycles/{cycle_code}/courses"
)
def academic_cycle_courses(
    cycle_code: str,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        records = get_cycle_courses(
            cycle_code=cycle_code
        )

        return {
            "success": True,
            "cycle_code": (
                cycle_code
            ),
            "count": len(
                records
            ),
            "courses": records,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.put(
    "/cycles/{cycle_code}/courses/{course_code}"
)
def academic_cycle_course_status(
    cycle_code: str,
    course_code: str,
    payload: CycleCourseStatusRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = (
            set_cycle_course_status(
                actor_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                cycle_code=cycle_code,
                course_code=course_code,
                is_active=(
                    payload.is_active
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Cycle course offering "
                "updated."
            ),
            "cycle_course": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# CLASSES
# ============================================================

@router.get(
    "/classes"
)
def academic_classes(
    cycle_code: str | None = Query(
        default=None
    ),
    course_code: str | None = Query(
        default=None
    ),
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        records = get_classes(
            cycle_code=cycle_code,
            course_code=course_code,
        )

        return {
            "success": True,
            "count": len(
                records
            ),
            "classes": records,
        }

    except Exception as error:
        print(
            "ERROR: Classes could not "
            f"load: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Classes could not "
                "be loaded."
            ),
        ) from error


@router.post(
    "/classes"
)
def academic_class_create(
    payload: ClassCreateRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = create_class(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            class_code=(
                payload.class_code
            ),
            class_name=(
                payload.class_name
            ),
            course_code=(
                payload.course_code
            ),
            cycle_code=(
                payload.cycle_code
            ),
            class_group=(
                payload.class_group
            ),
            facilitator_code=(
                payload.facilitator_code
            ),
            assessor_code=(
                payload.assessor_code
            ),
            status=payload.status,
        )

        return {
            "success": True,
            "message": (
                "Class created."
            ),
            "class": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.put(
    "/classes/{class_code}"
)
def academic_class_update(
    class_code: str,
    payload: ClassUpdateRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = update_class(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            class_code=class_code,
            class_name=(
                payload.class_name
            ),
            course_code=(
                payload.course_code
            ),
            cycle_code=(
                payload.cycle_code
            ),
            class_group=(
                payload.class_group
            ),
            status=payload.status,
        )

        return {
            "success": True,
            "message": (
                "Class updated."
            ),
            "class": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/staff-options"
)
def academic_staff_options(
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        records = (
            get_academic_staff_options()
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
            "ERROR: Academic staff "
            f"options failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Academic staff options "
                "could not be loaded."
            ),
        ) from error


@router.put(
    "/classes/{class_code}/staff"
)
def academic_class_staff_assignment(
    class_code: str,
    payload: ClassStaffAssignmentRequest,
    current_staff: dict = Depends(
        require_manage_academic_structure
    ),
):
    try:
        record = assign_class_staff(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            class_code=class_code,
            facilitator_code=(
                payload.facilitator_code
            ),
            assessor_code=(
                payload.assessor_code
            ),
        )

        return {
            "success": True,
            "message": (
                "Class staff assignment "
                "updated."
            ),
            "class": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# CLASS ENROLMENTS
# ============================================================

@router.get(
    "/classes/{class_code}/learners"
)
def academic_class_learners(
    class_code: str,
    current_staff: dict = Depends(
        require_manage_class_enrolments
    ),
):
    try:
        records = get_class_learners(
            class_code=class_code
        )

        return {
            "success": True,
            "class_code": (
                class_code
            ),
            "count": len(
                records
            ),
            "learners": records,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/classes/{class_code}/eligible-learners"
)
def academic_eligible_class_learners(
    class_code: str,
    current_staff: dict = Depends(
        require_manage_class_enrolments
    ),
):
    try:
        records = (
            get_eligible_class_learners(
                class_code=class_code
            )
        )

        return {
            "success": True,
            "class_code": (
                class_code
            ),
            "count": len(
                records
            ),
            "learners": records,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/classes/{class_code}/enrolments"
)
def academic_class_enrolment_create(
    class_code: str,
    payload: ClassEnrolmentRequest,
    current_staff: dict = Depends(
        require_manage_class_enrolments
    ),
):
    try:
        record = (
            enrol_registration_in_class(
                actor_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                class_code=class_code,
                registration_id=(
                    payload.registration_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Learner enrolled in class."
            ),
            "enrolment": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.patch(
    "/classes/{class_code}/enrolments/"
    "{registration_id}/remove"
)
def academic_class_enrolment_remove(
    class_code: str,
    registration_id: str,
    current_staff: dict = Depends(
        require_manage_class_enrolments
    ),
):
    try:
        record = (
            remove_registration_from_class(
                actor_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                class_code=class_code,
                registration_id=(
                    registration_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Learner removed from class."
            ),
            "enrolment": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

