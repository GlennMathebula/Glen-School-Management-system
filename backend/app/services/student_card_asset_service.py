from io import BytesIO
from pathlib import Path
from uuid import UUID

import barcode
import qrcode
from barcode.writer import ImageWriter
from PIL import (
    Image,
    ImageOps,
)
from sqlalchemy import text

from app.database import engine

# ============================================================
# PATHS
# ============================================================

APP_DIRECTORY = (
    Path(__file__)
    .resolve()
    .parents[1]
)

AVATAR_DIRECTORY = (
    APP_DIRECTORY
    / "generated_assets"
    / "student_cards"
    / "avatars"
)

AVATAR_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# AVATAR SETTINGS
# ============================================================

ALLOWED_AVATAR_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_AVATAR_SIZE_BYTES = (
    5
    * 1024
    * 1024
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def validate_card_id(
    card_id: str,
) -> str:

    try:

        return str(
            UUID(
                str(
                    card_id
                )
            )
        )

    except (
        ValueError,
        TypeError,
    ) as error:

        raise ValueError(
            "Invalid student card ID."
        ) from error


def validate_avatar(
    content: bytes,
    mime_type: str,
) -> None:

    if not content:

        raise ValueError(
            "Avatar file is empty."
        )

    if len(
        content
    ) > MAX_AVATAR_SIZE_BYTES:

        raise ValueError(
            "Avatar must not exceed 5 MB."
        )

    if mime_type not in ALLOWED_AVATAR_MIME_TYPES:

        raise ValueError(
            
                "Avatar must be JPEG, PNG "
                "or WebP."
            
        )


def prepare_avatar_image(
    content: bytes,
) -> Image.Image:

    try:

        source = Image.open(
            BytesIO(
                content
            )
        )

        source = (
            ImageOps.exif_transpose(
                source
            )
        )

        source = source.convert(
            "RGB"
        )

    except Exception as error:

        raise ValueError(
            
                "The uploaded avatar is "
                "not a valid image."
            
        ) from error

    # Passport / ID portrait style.
    processed = ImageOps.fit(
        source,
        (
            600,
            800,
        ),
        method=(
            Image.Resampling.LANCZOS
        ),
        centering=(
            0.5,
            0.45,
        ),
    )

    return processed


def get_student_card_avatar_state(
    card_id: str,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        student_number,

                        avatar_bucket,
                        avatar_path,
                        avatar_mime_type,
                        avatar_updated_at,
                        avatar_status,
                        avatar_upload_locked,
                        avatar_upload_count,

                        avatar_replacement_requested,
                        avatar_replacement_reason,
                        avatar_replacement_requested_at,

                        avatar_replacement_authorized,
                        avatar_replacement_authorized_by,
                        avatar_replacement_authorized_at,

                        pending_avatar_bucket,
                        pending_avatar_path,
                        pending_avatar_mime_type,
                        pending_avatar_uploaded_at,
                        pending_avatar_status,
                        pending_avatar_reviewed_by,
                        pending_avatar_reviewed_at,
                        pending_avatar_rejection_reason

                    FROM
                        public.student_cards

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Student card not found."
        )

    return dict(
        row
    )


# ============================================================
# FILE HELPERS
# ============================================================

def get_avatar_file_path(
    avatar_path: str | None,
) -> Path | None:

    if not avatar_path:

        return None

    path = (
        APP_DIRECTORY
        / avatar_path
    )

    if not path.exists():

        return None

    if not path.is_file():

        return None

    return path


def save_processed_avatar(
    image: Image.Image,
    filename: str,
) -> tuple[Path, str]:

    output_path = (
        AVATAR_DIRECTORY
        / filename
    )

    image.save(
        output_path,
        format="JPEG",
        quality=92,
        optimize=True,
    )

    relative_path = str(
        output_path.relative_to(
            APP_DIRECTORY
        )
    ).replace(
        "\\",
        "/",
    )

    return (
        output_path,
        relative_path,
    )


def safely_delete_avatar_file(
    avatar_path: str | None,
) -> None:

    path = get_avatar_file_path(
        avatar_path
    )

    if not path:

        return

    try:

        path.unlink(
            missing_ok=True
        )

    except Exception:

        # File cleanup must never
        # break the database workflow.
        pass


# ============================================================
# STUDENT UPLOAD
# ============================================================

def save_student_card_avatar(
    card_id: str,
    student_number: str,
    content: bytes,
    mime_type: str,
) -> dict:

    """
    Avatar rules:

    1. First-ever upload:
       - becomes official immediately
       - upload is locked
       - no admin review required

    2. Existing official avatar:
       - student cannot overwrite it directly

    3. Replacement:
       - student must first request replacement
       - admin must authorize replacement
       - authorized replacement becomes PENDING
       - current official avatar remains unchanged
       - admin compares old/new
       - admin approves or rejects pending avatar
    """

    card_id = validate_card_id(
        card_id
    )

    validate_avatar(
        content,
        mime_type,
    )

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    if (
        str(
            state[
                "student_number"
            ]
        )
        != str(
            student_number
        )
    ):

        raise ValueError(
            
                "Student card does not belong "
                "to this student."
            
        )

    processed = (
        prepare_avatar_image(
            content
        )
    )

    # ========================================================
    # FIRST EVER AVATAR
    # ========================================================

    if not state.get(
        "avatar_path"
    ):

        filename = (
            f"{student_number}_avatar.jpg"
        )

        (
            _,
            relative_path,
        ) = save_processed_avatar(
            processed,
            filename,
        )

        with engine.begin() as connection:

            row = (
                connection.execute(
                    text(
                        """
                        UPDATE
                            public.student_cards

                        SET
                            avatar_bucket = 'local',
                            avatar_path = :avatar_path,
                            avatar_mime_type = 'image/jpeg',
                            avatar_updated_at = now(),

                            avatar_status = 'Approved',
                            avatar_upload_locked = true,
                            avatar_upload_count =
                                avatar_upload_count + 1,

                            avatar_replacement_requested = false,
                            avatar_replacement_reason = null,
                            avatar_replacement_requested_at = null,

                            avatar_replacement_authorized = false,
                            avatar_replacement_authorized_by = null,
                            avatar_replacement_authorized_at = null,

                            pending_avatar_bucket = null,
                            pending_avatar_path = null,
                            pending_avatar_mime_type = null,
                            pending_avatar_uploaded_at = null,
                            pending_avatar_status = null,
                            pending_avatar_reviewed_by = null,
                            pending_avatar_reviewed_at = null,
                            pending_avatar_rejection_reason = null,

                            updated_at = now()

                        WHERE
                            id = CAST(
                                :card_id
                                AS uuid
                            )

                        RETURNING
                            id,
                            student_number,
                            avatar_path,
                            avatar_status,
                            avatar_upload_locked,
                            avatar_upload_count,
                            avatar_updated_at
                        """
                    ),
                    {
                        "card_id": (
                            card_id
                        ),

                        "avatar_path": (
                            relative_path
                        ),
                    },
                )
                .mappings()
                .first()
            )

        return {
            "card_id": (
                str(
                    row[
                        "id"
                    ]
                )
            ),

            "student_number": (
                row[
                    "student_number"
                ]
            ),

            "upload_type": (
                "FirstUpload"
            ),

            "official": True,

            "avatar_status": (
                row[
                    "avatar_status"
                ]
            ),

            "avatar_upload_locked": (
                row[
                    "avatar_upload_locked"
                ]
            ),

            "avatar_upload_count": (
                row[
                    "avatar_upload_count"
                ]
            ),

            "avatar_path": (
                row[
                    "avatar_path"
                ]
            ),

            "avatar_updated_at": (
                row[
                    "avatar_updated_at"
                ]
            ),

            # Backward compatibility
            # for existing route code.
            "avatar_bucket": "local",
            "avatar_mime_type": (
                "image/jpeg"
            ),
        }

    # ========================================================
    # EXISTING OFFICIAL AVATAR
    # ========================================================

    if state.get(
        "pending_avatar_path"
    ):

        raise ValueError(
            
                "A replacement photo is already "
                "awaiting administrator review."
            
        )

    if not state.get(
        "avatar_replacement_authorized"
    ):

        raise ValueError(
            
                "Your student card photo has already "
                "been submitted. Request a replacement "
                "and wait for administrator authorization "
                "before uploading another photo."
            
        )

    # ========================================================
    # AUTHORIZED REPLACEMENT UPLOAD
    # ========================================================

    pending_filename = (
        f"{student_number}_avatar_pending.jpg"
    )

    (
        _,
        pending_relative_path,
    ) = save_processed_avatar(
        processed,
        pending_filename,
    )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        pending_avatar_bucket = 'local',
                        pending_avatar_path =
                            :pending_avatar_path,
                        pending_avatar_mime_type =
                            'image/jpeg',
                        pending_avatar_uploaded_at =
                            now(),
                        pending_avatar_status =
                            'PendingComparison',

                        pending_avatar_reviewed_by =
                            null,
                        pending_avatar_reviewed_at =
                            null,
                        pending_avatar_rejection_reason =
                            null,

                        avatar_replacement_authorized =
                            false,

                        avatar_upload_locked = true,

                        avatar_upload_count =
                            avatar_upload_count + 1,

                        updated_at = now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_upload_count,
                        pending_avatar_path,
                        pending_avatar_status,
                        pending_avatar_uploaded_at
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),

                    "pending_avatar_path": (
                        pending_relative_path
                    ),
                },
            )
            .mappings()
            .first()
        )

    return {
        "card_id": (
            str(
                row[
                    "id"
                ]
            )
        ),

        "student_number": (
            row[
                "student_number"
            ]
        ),

        "upload_type": (
            "Replacement"
        ),

        "official": False,

        "pending_review": True,

        "pending_avatar_status": (
            row[
                "pending_avatar_status"
            ]
        ),

        "pending_avatar_path": (
            row[
                "pending_avatar_path"
            ]
        ),

        "pending_avatar_uploaded_at": (
            row[
                "pending_avatar_uploaded_at"
            ]
        ),

        "avatar_upload_count": (
            row[
                "avatar_upload_count"
            ]
        ),

        "avatar_upload_locked": True,

        # Existing route compatibility.
        "avatar_updated_at": (
            row[
                "pending_avatar_uploaded_at"
            ]
        ),

        "avatar_bucket": (
            "local"
        ),

        "avatar_path": (
            row[
                "pending_avatar_path"
            ]
        ),

        "avatar_mime_type": (
            "image/jpeg"
        ),
    }


# ============================================================
# STUDENT REQUESTS REPLACEMENT
# ============================================================

def request_avatar_replacement(
    card_id: str,
    student_number: str,
    reason: str,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    reason = str(
        reason or ""
    ).strip()

    if len(
        reason
    ) < 5:

        raise ValueError(
            
                "Please provide a reason for "
                "requesting a new photo."
            
        )

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    if (
        str(
            state[
                "student_number"
            ]
        )
        != str(
            student_number
        )
    ):

        raise ValueError(
            
                "Student card does not belong "
                "to this student."
            
        )

    if not state.get(
        "avatar_path"
    ):

        raise ValueError(
            
                "No existing student card photo "
                "needs replacement."
            
        )

    if state.get(
        "pending_avatar_path"
    ):

        raise ValueError(
            
                "A replacement photo is already "
                "awaiting administrator review."
            
        )

    if state.get(
        "avatar_replacement_authorized"
    ):

        raise ValueError(
            
                "A replacement upload has already "
                "been authorized. Please upload "
                "the new photo."
            
        )

    if state.get(
        "avatar_replacement_requested"
    ):

        raise ValueError(
            
                "A replacement request is already "
                "waiting for administrator action."
            
        )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        avatar_replacement_requested =
                            true,

                        avatar_replacement_reason =
                            :reason,

                        avatar_replacement_requested_at =
                            now(),

                        avatar_replacement_authorized =
                            false,

                        updated_at =
                            now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_replacement_requested,
                        avatar_replacement_reason,
                        avatar_replacement_requested_at
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),

                    "reason": (
                        reason
                    ),
                },
            )
            .mappings()
            .first()
        )

    return dict(
        row
    )


# ============================================================
# ADMIN AUTHORIZES ONE REPLACEMENT UPLOAD
# ============================================================

def authorize_avatar_replacement(
    card_id: str,
    authorized_by: str,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    authorized_by = str(
        authorized_by or ""
    ).strip()

    if not authorized_by:

        raise ValueError(
            
                "Administrator identity "
                "is required."
            
        )

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    if not state.get(
        "avatar_path"
    ):

        raise ValueError(
            
                "The student has no existing "
                "photo to replace."
            
        )

    if not state.get(
        "avatar_replacement_requested"
    ):

        raise ValueError(
            
                "The student has not requested "
                "a replacement photo."
            
        )

    if state.get(
        "pending_avatar_path"
    ):

        raise ValueError(
            
                "A replacement photo has already "
                "been uploaded."
            
        )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        avatar_replacement_authorized =
                            true,

                        avatar_replacement_authorized_by =
                            :authorized_by,

                        avatar_replacement_authorized_at =
                            now(),

                        updated_at =
                            now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_replacement_requested,
                        avatar_replacement_reason,
                        avatar_replacement_authorized,
                        avatar_replacement_authorized_by,
                        avatar_replacement_authorized_at
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),

                    "authorized_by": (
                        authorized_by
                    ),
                },
            )
            .mappings()
            .first()
        )

    return dict(
        row
    )


# ============================================================
# ADMIN DECLINES REPLACEMENT REQUEST
# ============================================================

def decline_avatar_replacement_request(
    card_id: str,
    reviewed_by: str,
    reason: str | None = None,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    reviewed_by = str(
        reviewed_by or ""
    ).strip()

    if not reviewed_by:

        raise ValueError(
            
                "Administrator identity "
                "is required."
            
        )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        avatar_replacement_requested =
                            false,

                        avatar_replacement_reason =
                            null,

                        avatar_replacement_requested_at =
                            null,

                        avatar_replacement_authorized =
                            false,

                        avatar_replacement_authorized_by =
                            null,

                        avatar_replacement_authorized_at =
                            null,

                        updated_at =
                            now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_replacement_requested,
                        avatar_replacement_authorized
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Student card not found."
        )

    result = dict(
        row
    )

    result[
        "reviewed_by"
    ] = reviewed_by

    result[
        "reason"
    ] = reason

    return result


# ============================================================
# ADMIN GETS BOTH PHOTOS FOR COMPARISON
# ============================================================

def get_avatar_comparison(
    card_id: str,
) -> dict:

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    return {
        "card_id": (
            str(
                state[
                    "id"
                ]
            )
        ),

        "student_number": (
            state[
                "student_number"
            ]
        ),

        "current_avatar": {
            "available": bool(
                state.get(
                    "avatar_path"
                )
            ),

            "path": (
                state.get(
                    "avatar_path"
                )
            ),

            "mime_type": (
                state.get(
                    "avatar_mime_type"
                )
            ),

            "updated_at": (
                state.get(
                    "avatar_updated_at"
                )
            ),
        },

        "replacement_request": {
            "requested": (
                state.get(
                    "avatar_replacement_requested"
                )
            ),

            "reason": (
                state.get(
                    "avatar_replacement_reason"
                )
            ),

            "requested_at": (
                state.get(
                    "avatar_replacement_requested_at"
                )
            ),
        },

        "pending_avatar": {
            "available": bool(
                state.get(
                    "pending_avatar_path"
                )
            ),

            "path": (
                state.get(
                    "pending_avatar_path"
                )
            ),

            "mime_type": (
                state.get(
                    "pending_avatar_mime_type"
                )
            ),

            "uploaded_at": (
                state.get(
                    "pending_avatar_uploaded_at"
                )
            ),

            "status": (
                state.get(
                    "pending_avatar_status"
                )
            ),
        },
    }


# ============================================================
# ADMIN APPROVES PENDING REPLACEMENT
# ============================================================

def approve_pending_avatar(
    card_id: str,
    reviewed_by: str,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    reviewed_by = str(
        reviewed_by or ""
    ).strip()

    if not reviewed_by:

        raise ValueError(
            
                "Administrator identity "
                "is required."
            
        )

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    pending_path = (
        state.get(
            "pending_avatar_path"
        )
    )

    if not pending_path:

        raise ValueError(
            
                "There is no pending replacement "
                "photo to approve."
            
        )

    pending_file = (
        get_avatar_file_path(
            pending_path
        )
    )

    if not pending_file:

        raise ValueError(
            
                "Pending replacement photo file "
                "could not be found."
            
        )

    official_filename = (
        f"{state['student_number']}_avatar.jpg"
    )

    official_path = (
        AVATAR_DIRECTORY
        / official_filename
    )

    # Keep the current official file until
    # the pending replacement has been safely read.
    pending_image = (
        Image.open(
            pending_file
        )
        .convert(
            "RGB"
        )
    )

    pending_image.save(
        official_path,
        format="JPEG",
        quality=92,
        optimize=True,
    )

    official_relative_path = str(
        official_path.relative_to(
            APP_DIRECTORY
        )
    ).replace(
        "\\",
        "/",
    )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        avatar_bucket =
                            'local',

                        avatar_path =
                            :official_path,

                        avatar_mime_type =
                            'image/jpeg',

                        avatar_updated_at =
                            now(),

                        avatar_status =
                            'Approved',

                        avatar_upload_locked =
                            true,

                        avatar_reviewed_by =
                            :reviewed_by,

                        avatar_reviewed_at =
                            now(),

                        avatar_rejection_reason =
                            null,

                        avatar_replacement_requested =
                            false,

                        avatar_replacement_reason =
                            null,

                        avatar_replacement_requested_at =
                            null,

                        avatar_replacement_authorized =
                            false,

                        avatar_replacement_authorized_by =
                            null,

                        avatar_replacement_authorized_at =
                            null,

                        pending_avatar_bucket =
                            null,

                        pending_avatar_path =
                            null,

                        pending_avatar_mime_type =
                            null,

                        pending_avatar_uploaded_at =
                            null,

                        pending_avatar_status =
                            null,

                        pending_avatar_reviewed_by =
                            :reviewed_by,

                        pending_avatar_reviewed_at =
                            now(),

                        pending_avatar_rejection_reason =
                            null,

                        updated_at =
                            now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_path,
                        avatar_status,
                        avatar_updated_at,
                        avatar_upload_count
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),

                    "official_path": (
                        official_relative_path
                    ),

                    "reviewed_by": (
                        reviewed_by
                    ),
                },
            )
            .mappings()
            .first()
        )

    # Pending file no longer needed after
    # successful database update.
    if (
        pending_file.resolve()
        != official_path.resolve()
    ):

        safely_delete_avatar_file(
            pending_path
        )

    return {
        **dict(
            row
        ),

        "replacement_approved": (
            True
        ),
    }


# ============================================================
# ADMIN REJECTS PENDING REPLACEMENT
# ============================================================

def reject_pending_avatar(
    card_id: str,
    reviewed_by: str,
    reason: str,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    reviewed_by = str(
        reviewed_by or ""
    ).strip()

    reason = str(
        reason or ""
    ).strip()

    if not reviewed_by:

        raise ValueError(
            
                "Administrator identity "
                "is required."
            
        )

    if len(
        reason
    ) < 3:

        raise ValueError(
            
                "A rejection reason is "
                "required."
            
        )

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    pending_path = (
        state.get(
            "pending_avatar_path"
        )
    )

    if not pending_path:

        raise ValueError(
            
                "There is no pending replacement "
                "photo to reject."
            
        )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        pending_avatar_status =
                            'Rejected',

                        pending_avatar_reviewed_by =
                            :reviewed_by,

                        pending_avatar_reviewed_at =
                            now(),

                        pending_avatar_rejection_reason =
                            :reason,

                        avatar_replacement_requested =
                            false,

                        avatar_replacement_reason =
                            null,

                        avatar_replacement_requested_at =
                            null,

                        avatar_replacement_authorized =
                            false,

                        avatar_replacement_authorized_by =
                            null,

                        avatar_replacement_authorized_at =
                            null,

                        avatar_upload_locked =
                            true,

                        updated_at =
                            now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_path,
                        pending_avatar_path,
                        pending_avatar_status,
                        pending_avatar_rejection_reason
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),

                    "reviewed_by": (
                        reviewed_by
                    ),

                    "reason": (
                        reason
                    ),
                },
            )
            .mappings()
            .first()
        )

    return {
        **dict(
            row
        ),

        "replacement_approved": (
            False
        ),

        "official_avatar_unchanged": (
            True
        ),
    }


# ============================================================
# ADMIN CLEARS REJECTED PENDING PHOTO
# ============================================================

def clear_rejected_pending_avatar(
    card_id: str,
) -> dict:

    card_id = validate_card_id(
        card_id
    )

    state = (
        get_student_card_avatar_state(
            card_id
        )
    )

    if (
        state.get(
            "pending_avatar_status"
        )
        != "Rejected"
    ):

        raise ValueError(
            
                "There is no rejected pending "
                "photo to clear."
            
        )

    pending_path = (
        state.get(
            "pending_avatar_path"
        )
    )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.student_cards

                    SET
                        pending_avatar_bucket =
                            null,

                        pending_avatar_path =
                            null,

                        pending_avatar_mime_type =
                            null,

                        pending_avatar_uploaded_at =
                            null,

                        pending_avatar_status =
                            null,

                        pending_avatar_reviewed_by =
                            null,

                        pending_avatar_reviewed_at =
                            null,

                        pending_avatar_rejection_reason =
                            null,

                        updated_at =
                            now()

                    WHERE
                        id = CAST(
                            :card_id
                            AS uuid
                        )

                    RETURNING
                        id,
                        student_number,
                        avatar_path,
                        avatar_status
                    """
                ),
                {
                    "card_id": (
                        card_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    safely_delete_avatar_file(
        pending_path
    )

    return dict(
        row
    )


# ============================================================
# QR CODE
# ============================================================

def generate_student_card_qr(
    verification_url: str,
) -> BytesIO:

    qr = qrcode.QRCode(
        version=None,

        error_correction=(
            qrcode.constants.ERROR_CORRECT_M
        ),

        box_size=10,

        border=2,
    )

    qr.add_data(
        verification_url
    )

    qr.make(
        fit=True
    )

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    buffer.seek(
        0
    )

    return buffer


# ============================================================
# CODE128 BARCODE
# ============================================================

def generate_identity_barcode(
    identity_value: str,
) -> BytesIO:

    identity_value = str(
        identity_value
    ).strip()

    if not identity_value:

        raise ValueError(
            
                "Student has no ID or "
                "passport value."
            
        )

    code128 = barcode.get(
        "code128",
        identity_value,
        writer=ImageWriter(),
    )

    buffer = BytesIO()

    code128.write(
        buffer,
        options={
            "module_width": 0.28,
            "module_height": 10.0,
            "quiet_zone": 1.0,
            "font_size": 0,
            "text_distance": 0,
            "write_text": False,
            "dpi": 300,
        },
    )

    buffer.seek(
        0
    )

    return buffer