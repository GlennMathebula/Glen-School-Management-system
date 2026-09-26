from uuid import UUID

from sqlalchemy import text

from app.database import engine

# ============================================================
# REVIEW ACTIONS
# ============================================================

REVIEW_ACTIONS = {
    "Approved",
    "Rejected",
    "Resubmission Required",
}


# ============================================================
# VALIDATE DOCUMENT ID
# ============================================================

def validate_document_id(
    document_id: str,
) -> str:

    try:

        return str(
            UUID(
                document_id
            )
        )

    except ValueError as error:

        raise ValueError(
            "Invalid document ID."
        ) from error


# ============================================================
# GET DOCUMENT FOR REVIEW
# ============================================================

def get_document_for_review(
    document_id: str,
) -> dict | None:

    document_id = (
        validate_document_id(
            document_id
        )
    )

    query = text(
        """
        SELECT
            d.id,
            d.request_id,
            d.student_number,

            d.document_type,
            d.document_label,

            d.original_filename,

            d.version_number,
            d.is_current,

            d.review_status,

            d.uploaded_at,

            dr.status AS request_status,
            dr.reason,
            dr.instructions,
            dr.due_date

        FROM public.student_documents d

        LEFT JOIN public.student_document_requests dr
            ON dr.id = d.request_id

        WHERE d.id = CAST(
            :document_id
            AS uuid
        )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "document_id": (
                    document_id
                ),
            },
        ).mappings().first()

    if not row:
        return None

    return dict(
        row
    )


# ============================================================
# REVIEW STUDENT DOCUMENT
# ============================================================

def review_student_document(
    document_id: str,
    action: str,
    reviewed_by: str,
    review_notes: str | None = None,
) -> dict:

    document_id = (
        validate_document_id(
            document_id
        )
    )

    action = (
        action
        .strip()
    )

    reviewed_by = (
        reviewed_by
        .strip()
    )

    review_notes = (
        review_notes.strip()
        if review_notes
        else None
    )

    # --------------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------------

    if action not in REVIEW_ACTIONS:

        raise ValueError(
            "Invalid document review action."
        )

    if not reviewed_by:

        raise ValueError(
            "Reviewer is required."
        )

    if (
        action
        in {
            "Rejected",
            "Resubmission Required",
        }
        and not review_notes
    ):

        raise ValueError(
            "Review notes are required "
            "when rejecting a document "
            "or requesting resubmission."
        )

    # --------------------------------------------------------
    # GET CURRENT DOCUMENT
    # --------------------------------------------------------

    document = (
        get_document_for_review(
            document_id
        )
    )

    if not document:

        raise ValueError(
            "Document not found."
        )

    if not document.get(
        "is_current"
    ):

        raise ValueError(
            "Only the current document "
            "version can be reviewed."
        )

    if (
        document.get(
            "review_status"
        )
        == "Approved"
    ):

        raise ValueError(
            "This document has already "
            "been approved."
        )

    request_id = (
        document.get(
            "request_id"
        )
    )

    if not request_id:

        raise ValueError(
            "This document is not linked "
            "to a document request."
        )

    student_number = (
        document[
            "student_number"
        ]
    )

    # --------------------------------------------------------
    # MAP DOCUMENT + REQUEST STATUSES
    # --------------------------------------------------------

    if action == "Approved":

        document_review_status = (
            "Approved"
        )

        request_status = (
            "Approved"
        )

    elif action == "Rejected":

        document_review_status = (
            "Rejected"
        )

        request_status = (
            "Rejected"
        )

    else:

        document_review_status = (
            "Rejected"
        )

        request_status = (
            "Resubmission Required"
        )

    # --------------------------------------------------------
    # TRANSACTION
    # --------------------------------------------------------

    with engine.begin() as connection:

        # ----------------------------------------------------
        # UPDATE DOCUMENT
        # ----------------------------------------------------

        connection.execute(
            text(
                """
                UPDATE
                    public.student_documents

                SET
                    review_status
                        = :review_status,

                    reviewed_by
                        = :reviewed_by,

                    reviewed_at
                        = now(),

                    review_notes
                        = :review_notes,

                    updated_at
                        = now()

                WHERE
                    id = CAST(
                        :document_id
                        AS uuid
                    )
                """
            ),
            {
                "review_status": (
                    document_review_status
                ),

                "reviewed_by": (
                    reviewed_by
                ),

                "review_notes": (
                    review_notes
                ),

                "document_id": (
                    document_id
                ),
            },
        )

        # ----------------------------------------------------
        # UPDATE REQUEST
        # ----------------------------------------------------

        connection.execute(
            text(
                """
                UPDATE
                    public.student_document_requests

                SET
                    status
                        = :request_status,

                    reviewed_by
                        = :reviewed_by,

                    reviewed_at
                        = now(),

                    review_notes
                        = :review_notes,

                    updated_at
                        = now()

                WHERE
                    id = :request_id
                """
            ),
            {
                "request_status": (
                    request_status
                ),

                "reviewed_by": (
                    reviewed_by
                ),

                "review_notes": (
                    review_notes
                ),

                "request_id": (
                    request_id
                ),
            },
        )

        # ----------------------------------------------------
        # SAVE REVIEW HISTORY
        # ----------------------------------------------------

        review_row = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.student_document_reviews
                    (
                        document_id,
                        request_id,
                        student_number,

                        action,
                        review_notes,

                        reviewed_by
                    )

                    VALUES
                    (
                        CAST(
                            :document_id
                            AS uuid
                        ),

                        :request_id,
                        :student_number,

                        :action,
                        :review_notes,

                        :reviewed_by
                    )

                    RETURNING
                        id,
                        action,
                        review_notes,
                        reviewed_by,
                        reviewed_at
                    """
                ),
                {
                    "document_id": (
                        document_id
                    ),

                    "request_id": (
                        request_id
                    ),

                    "student_number": (
                        student_number
                    ),

                    "action": (
                        action
                    ),

                    "review_notes": (
                        review_notes
                    ),

                    "reviewed_by": (
                        reviewed_by
                    ),
                },
            )
            .mappings()
            .one()
        )

    return {
        "document_id": (
            document_id
        ),

        "request_id": str(
            request_id
        ),

        "student_number": (
            student_number
        ),

        "document_type": (
            document.get(
                "document_type"
            )
        ),

        "document_label": (
            document.get(
                "document_label"
            )
        ),

        "version_number": (
            document.get(
                "version_number"
            )
        ),

        "document_review_status": (
            document_review_status
        ),

        "request_status": (
            request_status
        ),

        "review": dict(
            review_row
        ),
    }