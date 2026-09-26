import re
from pathlib import Path
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import text
from supabase import create_client

from app.config import settings
from app.database import engine

# ============================================================
# DOCUMENT STORAGE CONFIGURATION
# ============================================================

STUDENT_DOCUMENT_BUCKET = (
    "student-documents"
)

MAX_DOCUMENT_SIZE_BYTES = (
    10 * 1024 * 1024
)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


# ============================================================
# SUPABASE STORAGE CLIENT
# ============================================================

def get_storage_client():

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


# ============================================================
# SAFE FILENAME
# ============================================================

def sanitise_filename(
    filename: str,
) -> str:

    filename = (
        Path(
            filename or "document"
        )
        .name
        .strip()
    )

    if not filename:
        filename = "document"

    filename = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        filename,
    )

    filename = re.sub(
        r"_+",
        "_",
        filename,
    )

    return filename[:180]


# ============================================================
# VALIDATE REQUEST ID
# ============================================================

def validate_request_id(
    request_id: str,
) -> str:

    try:

        return str(
            UUID(
                request_id
            )
        )

    except ValueError as error:

        raise ValueError(
            "Invalid document request."
        ) from error


# ============================================================
# VALIDATE DOCUMENT FILE
# ============================================================

def validate_document_file(
    filename: str,
    mime_type: str | None,
    file_bytes: bytes,
) -> None:

    if not file_bytes:

        raise ValueError(
            "The selected file is empty."
        )

    if (
        len(file_bytes)
        > MAX_DOCUMENT_SIZE_BYTES
    ):

        raise ValueError(
            "The document exceeds the "
            "10 MB upload limit."
        )

    if (
        mime_type
        not in ALLOWED_MIME_TYPES
    ):

        raise ValueError(
            "Only PDF, JPG, JPEG and PNG "
            "documents are allowed."
        )

    extension = (
        Path(
            filename
        )
        .suffix
        .lower()
    )

    allowed_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
    }

    if (
        extension
        not in allowed_extensions
    ):

        raise ValueError(
            "Only PDF, JPG, JPEG and PNG "
            "documents are allowed."
        )


# ============================================================
# GET DOCUMENT REQUEST
# ============================================================

def get_student_document_request(
    student_number: str,
    request_id: str,
) -> dict | None:

    query = text(
        """
        SELECT
            id,
            student_number,
            course_code,

            document_type,
            document_label,

            reason,
            instructions,

            request_source,
            is_required,
            due_date,

            status,

            requested_by,
            requested_at

        FROM public.student_document_requests

        WHERE
            id = CAST(
                :request_id
                AS uuid
            )

            AND student_number
                = :student_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "request_id": (
                    request_id
                ),
                "student_number": (
                    student_number
                ),
            },
        ).mappings().first()

    if not row:
        return None

    return dict(
        row
    )


# ============================================================
# CHECK REQUEST CAN ACCEPT UPLOAD
# ============================================================

def validate_request_for_upload(
    request: dict,
) -> None:

    status = (
        request.get(
            "status"
        )
        or ""
    )

    if status == "Approved":

        raise ValueError(
            "This document request has "
            "already been approved."
        )

    if status == "Cancelled":

        raise ValueError(
            "This document request "
            "has been cancelled."
        )

    if status == "Submitted":

        raise ValueError(
            "This document has already "
            "been submitted and is "
            "awaiting review."
        )

    allowed_statuses = {
        "Requested",
        "Rejected",
        "Resubmission Required",
    }

    if (
        status
        not in allowed_statuses
    ):

        raise ValueError(
            "This document request is not "
            "currently accepting uploads."
        )


# ============================================================
# GET NEXT DOCUMENT VERSION
# ============================================================

def get_next_document_version(
    connection,
    request_id: str,
) -> int:

    current_version = (
        connection.execute(
            text(
                """
                SELECT
                    COALESCE(
                        MAX(version_number),
                        0
                    )

                FROM public.student_documents

                WHERE request_id = CAST(
                    :request_id
                    AS uuid
                )
                """
            ),
            {
                "request_id": (
                    request_id
                ),
            },
        ).scalar_one()
    )

    return (
        int(
            current_version
        )
        + 1
    )


# ============================================================
# DELETE STORAGE FILE
# ============================================================

def delete_storage_file(
    storage_path: str,
) -> None:

    try:

        storage = (
            get_storage_client()
        )

        storage.storage.from_(
            STUDENT_DOCUMENT_BUCKET
        ).remove(
            [
                storage_path
            ]
        )

    except Exception as error:

        print(
            "WARNING: Failed to remove "
            "storage file after rollback: "
            f"{error}"
        )


# ============================================================
# UPLOAD STUDENT DOCUMENT
# ============================================================

def upload_student_document(
    student_number: str,
    request_id: str,
    filename: str,
    mime_type: str | None,
    file_bytes: bytes,
) -> dict:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    request_id = (
        validate_request_id(
            request_id
        )
    )

    safe_filename = (
        sanitise_filename(
            filename
        )
    )

    # --------------------------------------------------------
    # VALIDATE FILE
    # --------------------------------------------------------

    validate_document_file(
        filename=(
            safe_filename
        ),
        mime_type=(
            mime_type
        ),
        file_bytes=(
            file_bytes
        ),
    )

    # --------------------------------------------------------
    # GET REQUEST
    # --------------------------------------------------------

    document_request = (
        get_student_document_request(
            student_number=(
                student_number
            ),
            request_id=(
                request_id
            ),
        )
    )

    if not document_request:

        raise ValueError(
            "Document request not found."
        )

    # --------------------------------------------------------
    # VERIFY REQUEST STATUS
    # --------------------------------------------------------

    validate_request_for_upload(
        document_request
    )

    # --------------------------------------------------------
    # BUILD PRIVATE STORAGE PATH
    # --------------------------------------------------------

    storage_path = (
        f"{student_number}/"
        f"{request_id}/"
        f"{uuid4()}_"
        f"{safe_filename}"
    )

    # --------------------------------------------------------
    # UPLOAD TO SUPABASE STORAGE
    # --------------------------------------------------------

    storage = (
        get_storage_client()
    )

    try:

        storage.storage.from_(
            STUDENT_DOCUMENT_BUCKET
        ).upload(
            path=(
                storage_path
            ),
            file=(
                file_bytes
            ),
            file_options={
                "content-type": (
                    mime_type
                ),
                "upsert": "false",
            },
        )

    except Exception as error:

        print(
            "ERROR: Supabase document "
            "upload failed: "
            f"{error}"
        )

        raise RuntimeError(
            "The document could not "
            "be stored."
        ) from error

    # --------------------------------------------------------
    # SAVE DATABASE RECORD
    # --------------------------------------------------------

    try:

        with engine.begin() as connection:

            version_number = (
                get_next_document_version(
                    connection=(
                        connection
                    ),
                    request_id=(
                        request_id
                    ),
                )
            )

            # -----------------------------------------------
            # OLD VERSIONS ARE RETAINED
            # -----------------------------------------------

            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_documents

                    SET
                        is_current = false,
                        updated_at = now()

                    WHERE
                        request_id = CAST(
                            :request_id
                            AS uuid
                        )

                        AND student_number
                            = :student_number

                        AND is_current = true
                    """
                ),
                {
                    "request_id": (
                        request_id
                    ),
                    "student_number": (
                        student_number
                    ),
                },
            )

            # -----------------------------------------------
            # INSERT DOCUMENT
            # -----------------------------------------------

            document_row = (
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            public.student_documents
                        (
                            request_id,
                            student_number,

                            document_type,
                            document_label,

                            original_filename,

                            storage_bucket,
                            storage_path,

                            mime_type,
                            file_size_bytes,

                            uploaded_by_type,
                            uploaded_by_identifier,

                            version_number,
                            is_current,

                            review_status
                        )

                        VALUES
                        (
                            CAST(
                                :request_id
                                AS uuid
                            ),

                            :student_number,

                            :document_type,
                            :document_label,

                            :original_filename,

                            :storage_bucket,
                            :storage_path,

                            :mime_type,
                            :file_size_bytes,

                            'Student',
                            :student_number,

                            :version_number,
                            true,

                            'Pending'
                        )

                        RETURNING
                            id,
                            document_type,
                            document_label,
                            original_filename,
                            version_number,
                            review_status,
                            uploaded_at
                        """
                    ),
                    {
                        "request_id": (
                            request_id
                        ),

                        "student_number": (
                            student_number
                        ),

                        "document_type": (
                            document_request[
                                "document_type"
                            ]
                        ),

                        "document_label": (
                            document_request[
                                "document_label"
                            ]
                        ),

                        "original_filename": (
                            safe_filename
                        ),

                        "storage_bucket": (
                            STUDENT_DOCUMENT_BUCKET
                        ),

                        "storage_path": (
                            storage_path
                        ),

                        "mime_type": (
                            mime_type
                        ),

                        "file_size_bytes": (
                            len(
                                file_bytes
                            )
                        ),

                        "version_number": (
                            version_number
                        ),
                    },
                )
                .mappings()
                .one()
            )

            # -----------------------------------------------
            # REQUEST BECOMES SUBMITTED
            # -----------------------------------------------

            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_document_requests

                    SET
                        status = 'Submitted',

                        reviewed_by = NULL,
                        reviewed_at = NULL,
                        review_notes = NULL,

                        updated_at = now()

                    WHERE
                        id = CAST(
                            :request_id
                            AS uuid
                        )

                        AND student_number
                            = :student_number
                    """
                ),
                {
                    "request_id": (
                        request_id
                    ),
                    "student_number": (
                        student_number
                    ),
                },
            )

    except Exception as error:

        # Storage upload succeeded but DB failed.
        # Remove the orphaned file.

        delete_storage_file(
            storage_path
        )

        print(
            "ERROR: Student document "
            "database save failed: "
            f"{error}"
        )

        raise RuntimeError(
            "The document upload could "
            "not be completed."
        ) from error

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    document = dict(
        document_row
    )

    return {
        "request_id": (
            request_id
        ),

        "document_id": str(
            document[
                "id"
            ]
        ),

        "document_type": (
            document[
                "document_type"
            ]
        ),

        "document_label": (
            document[
                "document_label"
            ]
        ),

        "filename": (
            document[
                "original_filename"
            ]
        ),

        "version_number": (
            document[
                "version_number"
            ]
        ),

        "review_status": (
            document[
                "review_status"
            ]
        ),

        "request_status": (
            "Submitted"
        ),

        "uploaded_at": (
            document[
                "uploaded_at"
            ]
        ),
    }