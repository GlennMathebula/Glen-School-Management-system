from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.models.learning_resources import (
    LearningResourceLinkCreate,
    LearningResourceNoteCreate,
)

from app.services.learning_resource_service import (
    MAX_RESOURCE_SIZE_BYTES,
    archive_learning_resource,
    create_link_resource,
    create_note_resource,
    get_facilitator_class_resources,
    get_facilitator_resource,
    get_student_learning_resource,
    get_student_learning_resources,
    publish_learning_resource,
    upload_file_resource,
)

from app.staff_auth_dependency import (
    require_facilitator,
)

from app.student_auth_dependency import (
    require_full_student_access,
)

from app.services.learning_resource_ai_service import (
    generate_ai_notes_from_resource,
    restore_learning_resource,
)

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=[
        "Learning Resources"
    ],
)


# ============================================================
# FACILITATOR - CREATE NOTE
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/note"
)
def facilitator_create_note(
    payload: LearningResourceNoteCreate,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resource = (
            create_note_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                class_id=(
                    payload.class_id
                ),

                module_id=(
                    payload.module_id
                ),

                timetable_session_id=(
                    payload.timetable_session_id
                ),

                title=(
                    payload.title
                ),

                description=(
                    payload.description
                ),

                content_text=(
                    payload.content_text
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Learning note created "
                "successfully as a draft."
            ),

            "data": (
                resource
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Learning note creation "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning note could not "
                "be created."
            ),
        ) from error


# ============================================================
# FACILITATOR - CREATE LINK
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/link"
)
def facilitator_create_link(
    payload: LearningResourceLinkCreate,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resource = (
            create_link_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                class_id=(
                    payload.class_id
                ),

                module_id=(
                    payload.module_id
                ),

                timetable_session_id=(
                    payload.timetable_session_id
                ),

                title=(
                    payload.title
                ),

                description=(
                    payload.description
                ),

                external_url=str(
                    payload.external_url
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Learning link created "
                "successfully as a draft."
            ),

            "data": (
                resource
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Learning link creation "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning link could not "
                "be created."
            ),
        ) from error


# ============================================================
# FACILITATOR - UPLOAD FILE
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/file"
)
async def facilitator_upload_file(
    class_id: str = Form(...),

    title: str = Form(...),

    description: str | None = Form(
        None
    ),

    module_id: str | None = Form(
        None
    ),

    timetable_session_id: str | None = Form(
        None
    ),

    file: UploadFile = File(...),

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        file_bytes = await file.read(
            MAX_RESOURCE_SIZE_BYTES
            + 1
        )

        resource = (
            upload_file_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                class_id=(
                    class_id
                ),

                module_id=(
                    module_id
                ),

                timetable_session_id=(
                    timetable_session_id
                ),

                title=(
                    title
                ),

                description=(
                    description
                ),

                filename=(
                    file.filename
                    or "resource"
                ),

                mime_type=(
                    file.content_type
                ),

                file_bytes=(
                    file_bytes
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Learning resource uploaded "
                "successfully as a draft."
            ),

            "data": (
                resource
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except RuntimeError as error:

        print(
            "ERROR: Learning resource "
            "upload failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be uploaded."
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Unexpected learning "
            "resource upload failure: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be uploaded."
            ),
        ) from error

    finally:

        await file.close()


# ============================================================
# FACILITATOR - CLASS RESOURCES
# ============================================================

@router.get(
    "/api/staff/facilitator/"
    "classes/{class_code}/"
    "learning-resources"
)
def facilitator_class_resources(
    class_code: str,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resources = (
            get_facilitator_class_resources(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                class_code=(
                    class_code
                ),
            )
        )

        if resources is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Class not found or not "
                    "assigned to this facilitator."
                ),
            )

        return {
            "success": True,

            "class_code": (
                class_code
            ),

            "count": len(
                resources
            ),

            "resources": (
                resources
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Facilitator learning "
            "resources could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resources could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR - ONE RESOURCE
# ============================================================

@router.get(
    "/api/staff/facilitator/"
    "learning-resources/{resource_id}"
)
def facilitator_resource_detail(
    resource_id: str,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resource = (
            get_facilitator_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                resource_id=(
                    resource_id
                ),
            )
        )

        if not resource:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Learning resource not found."
                ),
            )

        return {
            "success": True,

            "data": (
                resource
            ),
        }

    except HTTPException:

        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Learning resource "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR - PUBLISH RESOURCE
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/"
    "{resource_id}/publish"
)
def facilitator_publish_resource(
    resource_id: str,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resource = (
            publish_learning_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                resource_id=(
                    resource_id
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Learning resource published "
                "successfully."
            ),

            "data": (
                resource
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Learning resource "
            "publication failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be published."
            ),
        ) from error


# ============================================================
# FACILITATOR - ARCHIVE RESOURCE
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/"
    "{resource_id}/archive"
)
def facilitator_archive_resource(
    resource_id: str,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resource = (
            archive_learning_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                resource_id=(
                    resource_id
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Learning resource archived "
                "successfully."
            ),

            "data": (
                resource
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Learning resource "
            "archive failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be archived."
            ),
        ) from error

# ============================================================
# FACILITATOR - GENERATE AI STUDY NOTES
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/"
    "{resource_id}/generate-ai-notes"
)
def facilitator_generate_ai_notes(
    resource_id: str,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        result = (
            generate_ai_notes_from_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                source_resource_id=(
                    resource_id
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "AI study notes generated "
                "successfully as a draft. "
                "Review them before publishing."
            ),

            "data": (
                result
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except RuntimeError as error:

        print(
            "ERROR: AI learning note "
            "generation failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Unexpected AI learning "
            "note generation failure: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "AI study notes could "
                "not be generated."
            ),
        ) from error

# ============================================================
# STUDENT - ALL PUBLISHED RESOURCES
# ============================================================

@router.get(
    "/api/student/learning-resources"
)
def student_learning_resources(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        resources = (
            get_student_learning_resources(
                student_number
            )
        )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "count": len(
                resources
            ),

            "resources": (
                resources
            ),
        }

    except Exception as error:

        print(
            "ERROR: Student learning "
            "resources could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resources could "
                "not be loaded."
            ),
        ) from error

# ============================================================
# FACILITATOR - RESTORE RESOURCE
# ============================================================

@router.post(
    "/api/staff/facilitator/"
    "learning-resources/"
    "{resource_id}/restore"
)
def facilitator_restore_resource(
    resource_id: str,

    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        resource = (
            restore_learning_resource(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                resource_id=(
                    resource_id
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Learning resource restored "
                "successfully as a draft."
            ),

            "data": (
                resource
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Learning resource "
            "restore failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be restored."
            ),
        ) from error

# ============================================================
# STUDENT - ONE PUBLISHED RESOURCE
# ============================================================

@router.get(
    "/api/student/"
    "learning-resources/{resource_id}"
)
def student_learning_resource_detail(
    resource_id: str,

    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        resource = (
            get_student_learning_resource(
                student_number=(
                    student_number
                ),

                resource_id=(
                    resource_id
                ),
            )
        )

        if not resource:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Learning resource not found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                resource
            ),
        }

    except HTTPException:

        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Student learning resource "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learning resource could "
                "not be loaded."
            ),
        ) from error