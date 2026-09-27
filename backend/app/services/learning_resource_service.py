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
# CONFIGURATION
# ============================================================

LEARNING_RESOURCE_BUCKET = (
    "learning-resources"
)

MAX_RESOURCE_SIZE_BYTES = (
    25 * 1024 * 1024
)

SIGNED_URL_EXPIRY_SECONDS = (
    60 * 60
)


ALLOWED_MIME_TYPES = {
    "application/pdf",

    (
        "application/vnd.openxmlformats-"
        "officedocument.wordprocessingml."
        "document"
    ),

    (
        "application/vnd.openxmlformats-"
        "officedocument.presentationml."
        "presentation"
    ),

    "image/jpeg",
    "image/png",
}


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
}


# ============================================================
# STORAGE CLIENT
# ============================================================

def get_storage_client():

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


# ============================================================
# UUID VALIDATION
# ============================================================

def validate_uuid(
    value: str,
    field_name: str,
) -> str:

    try:

        return str(
            UUID(
                str(
                    value
                )
            )
        )

    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as error:

        raise ValueError(
            f"Invalid {field_name}."
        ) from error


# ============================================================
# OPTIONAL UUID VALIDATION
# ============================================================

def validate_optional_uuid(
    value: str | None,
    field_name: str,
) -> str | None:

    if not value:
        return None

    return validate_uuid(
        value,
        field_name,
    )


# ============================================================
# SAFE FILENAME
# ============================================================

def sanitise_filename(
    filename: str,
) -> str:

    filename = (
        Path(
            filename
            or "resource"
        )
        .name
        .strip()
    )

    if not filename:

        filename = (
            "resource"
        )

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

    return filename[:200]


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_required_text(
    value: str,
    field_name: str,
) -> str:

    cleaned = (
        str(
            value
            or ""
        )
        .strip()
    )

    if not cleaned:

        raise ValueError(
            f"{field_name} is required."
        )

    return cleaned


# ============================================================
# CLEAN OPTIONAL TEXT
# ============================================================

def clean_optional_text(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    cleaned = (
        str(
            value
        )
        .strip()
    )

    return (
        cleaned
        if cleaned
        else None
    )


# ============================================================
# VALIDATE FILE
# ============================================================

def validate_resource_file(
    *,
    filename: str,
    mime_type: str | None,
    file_bytes: bytes,
) -> None:

    if not file_bytes:

        raise ValueError(
            "The selected resource file "
            "is empty."
        )

    if (
        len(
            file_bytes
        )
        > MAX_RESOURCE_SIZE_BYTES
    ):

        raise ValueError(
            "The learning resource exceeds "
            "the 25 MB upload limit."
        )

    extension = (
        Path(
            filename
        )
        .suffix
        .lower()
    )

    if (
        extension
        not in ALLOWED_EXTENSIONS
    ):

        raise ValueError(
            "Only PDF, DOCX, PPTX, JPG, "
            "JPEG and PNG files are allowed."
        )

    if (
        mime_type
        not in ALLOWED_MIME_TYPES
    ):

        raise ValueError(
            "The selected file type is "
            "not supported."
        )


# ============================================================
# GET FACILITATOR CLASS
# ============================================================

def get_facilitator_class(
    *,
    staff_code: str,
    class_id: str,
) -> dict | None:

    class_id = validate_uuid(
        class_id,
        "class ID",
    )

    query = text(
        """
        SELECT
            id,
            class_code,
            class_name,
            course_code,
            cycle_code,
            class_group,
            facilitator_code,
            status

        FROM public.classes

        WHERE
            id = CAST(
                :class_id
                AS uuid
            )

            AND facilitator_code
                = :staff_code

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "class_id": (
                        class_id
                    ),

                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return None

    return dict(
        row
    )


# ============================================================
# VALIDATE RELATED MODULE / SESSION
# ============================================================

def validate_related_scope(
    *,
    connection,
    class_record: dict,
    module_id: str | None,
    timetable_session_id: str | None,
) -> tuple[
    str | None,
    str | None,
]:

    module_id = (
        validate_optional_uuid(
            module_id,
            "module ID",
        )
    )

    timetable_session_id = (
        validate_optional_uuid(
            timetable_session_id,
            "timetable session ID",
        )
    )

    # --------------------------------------------------------
    # MODULE
    # --------------------------------------------------------

    if module_id:

        module_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        course_code,
                        module_code,
                        module_name,
                        status

                    FROM public.modules

                    WHERE
                        id = CAST(
                            :module_id
                            AS uuid
                        )

                        AND course_code
                            = :course_code

                    LIMIT 1
                    """
                ),
                {
                    "module_id": (
                        module_id
                    ),

                    "course_code": (
                        class_record[
                            "course_code"
                        ]
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not module_row:

            raise ValueError(
                "The selected module does "
                "not belong to this class "
                "programme."
            )

    # --------------------------------------------------------
    # TIMETABLE SESSION
    # --------------------------------------------------------

    if timetable_session_id:

        session_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        class_id,
                        module_id,
                        session_title

                    FROM
                        public.timetable_sessions

                    WHERE
                        id = CAST(
                            :session_id
                            AS uuid
                        )

                        AND class_id = CAST(
                            :class_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "session_id": (
                        timetable_session_id
                    ),

                    "class_id": str(
                        class_record[
                            "id"
                        ]
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not session_row:

            raise ValueError(
                "The selected timetable "
                "session does not belong "
                "to this class."
            )

        session_module_id = (
            str(
                session_row[
                    "module_id"
                ]
            )
            if session_row[
                "module_id"
            ]
            else None
        )

        if (
            module_id
            and session_module_id
            and module_id
            != session_module_id
        ):

            raise ValueError(
                "The selected module does "
                "not match the timetable "
                "session module."
            )

        if (
            not module_id
            and session_module_id
        ):

            module_id = (
                session_module_id
            )

    return (
        module_id,
        timetable_session_id,
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
            LEARNING_RESOURCE_BUCKET
        ).remove(
            [
                storage_path
            ]
        )

    except Exception as error:

        print(
            "WARNING: Learning resource "
            "storage cleanup failed: "
            f"{error}"
        )


# ============================================================
# CREATE SIGNED DOWNLOAD URL
# ============================================================

def create_signed_download_url(
    *,
    storage_bucket: str | None,
    storage_path: str | None,
) -> str | None:

    if (
        not storage_bucket
        or not storage_path
    ):

        return None

    try:

        storage = (
            get_storage_client()
        )

        response = (
            storage.storage
            .from_(
                storage_bucket
            )
            .create_signed_url(
                storage_path,
                SIGNED_URL_EXPIRY_SECONDS,
            )
        )

        if isinstance(
            response,
            dict,
        ):

            return (
                response.get(
                    "signedURL"
                )
                or response.get(
                    "signedUrl"
                )
                or response.get(
                    "signed_url"
                )
            )

        return None

    except Exception as error:

        print(
            "WARNING: Signed resource URL "
            "could not be created: "
            f"{error}"
        )

        return None


# ============================================================
# FORMAT RESOURCE
# ============================================================

def format_resource(
    row: dict,
) -> dict:

    resource = dict(
        row
    )

    resource_type = (
        resource.get(
            "resource_type"
        )
    )

    download_url = None

    if (
        resource_type
        == "FILE"
    ):

        download_url = (
            create_signed_download_url(
                storage_bucket=(
                    resource.get(
                        "storage_bucket"
                    )
                ),
                storage_path=(
                    resource.get(
                        "storage_path"
                    )
                ),
            )
        )

    return {
        "resource_id": str(
            resource[
                "id"
            ]
        ),

        "class": {
            "class_id": str(
                resource[
                    "class_id"
                ]
            ),

            "class_code": (
                resource[
                    "class_code"
                ]
            ),

            "class_name": (
                resource[
                    "class_name"
                ]
            ),

            "course_code": (
                resource[
                    "course_code"
                ]
            ),

            "class_group": (
                resource[
                    "class_group"
                ]
            ),
        },

        "module": (
            {
                "module_id": str(
                    resource[
                        "module_id"
                    ]
                ),

                "module_code": (
                    resource[
                        "module_code"
                    ]
                ),

                "module_name": (
                    resource[
                        "module_name"
                    ]
                ),

                "module_type": (
                    resource[
                        "module_type"
                    ]
                ),
            }
            if resource.get(
                "module_id"
            )
            else None
        ),

        "timetable_session": (
            {
                "timetable_session_id": (
                    str(
                        resource[
                            "timetable_session_id"
                        ]
                    )
                ),

                "session_title": (
                    resource[
                        "session_title"
                    ]
                ),

                "session_date": (
                    resource[
                        "session_date"
                    ]
                ),

                "start_time": (
                    resource[
                        "start_time"
                    ]
                ),

                "end_time": (
                    resource[
                        "end_time"
                    ]
                ),
            }
            if resource.get(
                "timetable_session_id"
            )
            else None
        ),

        "title": (
            resource[
                "title"
            ]
        ),

        "description": (
            resource.get(
                "description"
            )
        ),

        "resource_type": (
            resource_type
        ),

        "content_text": (
            resource.get(
                "content_text"
            )
        ),

        "external_url": (
            resource.get(
                "external_url"
            )
        ),

        "file": (
            {
                "filename": (
                    resource.get(
                        "original_filename"
                    )
                ),

                "mime_type": (
                    resource.get(
                        "mime_type"
                    )
                ),

                "file_size_bytes": (
                    resource.get(
                        "file_size_bytes"
                    )
                ),

                "download_url": (
                    download_url
                ),

                "download_url_expires_in": (
                    SIGNED_URL_EXPIRY_SECONDS
                ),
            }
            if resource_type
            == "FILE"
            else None
        ),

        "status": (
            resource[
                "status"
            ]
        ),

        "visibility": (
            resource[
                "visibility"
            ]
        ),

        "ai_generated": bool(
            resource[
                "ai_generated"
            ]
        ),

        "ai_provider": (
            resource.get(
                "ai_provider"
            )
        ),

        "ai_model": (
            resource.get(
                "ai_model"
            )
        ),

        "source_resource_id": (
            str(
                resource[
                    "source_resource_id"
                ]
            )
            if resource.get(
                "source_resource_id"
            )
            else None
        ),

        "created_by_staff_code": (
            resource[
                "created_by_staff_code"
            ]
        ),

        "created_by_role": (
            resource.get(
                "created_by_role"
            )
        ),

        "published_by_staff_code": (
            resource.get(
                "published_by_staff_code"
            )
        ),

        "published_at": (
            resource.get(
                "published_at"
            )
        ),

        "created_at": (
            resource[
                "created_at"
            ]
        ),

        "updated_at": (
            resource[
                "updated_at"
            ]
        ),
    }


# ============================================================
# COMMON RESOURCE SELECT
# ============================================================

RESOURCE_SELECT = """
    SELECT
        lr.id,
        lr.class_id,
        lr.module_id,
        lr.timetable_session_id,
        lr.source_resource_id,

        lr.title,
        lr.description,
        lr.resource_type,

        lr.content_text,
        lr.external_url,

        lr.original_filename,
        lr.storage_bucket,
        lr.storage_path,
        lr.mime_type,
        lr.file_size_bytes,

        lr.status,
        lr.visibility,

        lr.ai_generated,
        lr.ai_provider,
        lr.ai_model,

        lr.created_by_staff_code,
        lr.created_by_role,

        lr.published_by_staff_code,
        lr.published_at,

        lr.created_at,
        lr.updated_at,

        c.class_code,
        c.class_name,
        c.course_code,
        c.class_group,

        m.module_code,
        m.module_name,
        m.module_type,

        ts.session_title,
        ts.session_date,
        ts.start_time,
        ts.end_time

    FROM public.learning_resources lr

    JOIN public.classes c
        ON c.id = lr.class_id

    LEFT JOIN public.modules m
        ON m.id = lr.module_id

    LEFT JOIN public.timetable_sessions ts
        ON ts.id =
            lr.timetable_session_id
"""


# ============================================================
# CREATE NOTE RESOURCE
# ============================================================

def create_note_resource(
    *,
    staff_code: str,
    role_code: str,
    class_id: str,
    module_id: str | None,
    timetable_session_id: str | None,
    title: str,
    description: str | None,
    content_text: str,
) -> dict:

    class_record = (
        get_facilitator_class(
            staff_code=(
                staff_code
            ),
            class_id=(
                class_id
            ),
        )
    )

    if not class_record:

        raise ValueError(
            "Class not found or not assigned "
            "to this facilitator."
        )

    title = (
        clean_required_text(
            title,
            "Resource title",
        )
    )

    description = (
        clean_optional_text(
            description
        )
    )

    content_text = (
        clean_required_text(
            content_text,
            "Resource content",
        )
    )

    with engine.begin() as connection:

        (
            module_id,
            timetable_session_id,
        ) = validate_related_scope(
            connection=(
                connection
            ),
            class_record=(
                class_record
            ),
            module_id=(
                module_id
            ),
            timetable_session_id=(
                timetable_session_id
            ),
        )

        resource_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.learning_resources
                    (
                        class_id,
                        module_id,
                        timetable_session_id,

                        title,
                        description,

                        resource_type,
                        content_text,

                        status,
                        visibility,

                        ai_generated,

                        created_by_staff_code,
                        created_by_role
                    )

                    VALUES
                    (
                        CAST(
                            :class_id
                            AS uuid
                        ),

                        CAST(
                            :module_id
                            AS uuid
                        ),

                        CAST(
                            :timetable_session_id
                            AS uuid
                        ),

                        :title,
                        :description,

                        'NOTE',
                        :content_text,

                        'Draft',
                        'Class',

                        false,

                        :staff_code,
                        :role_code
                    )

                    RETURNING id
                    """
                ),
                {
                    "class_id": str(
                        class_record[
                            "id"
                        ]
                    ),

                    "module_id": (
                        module_id
                    ),

                    "timetable_session_id": (
                        timetable_session_id
                    ),

                    "title": (
                        title
                    ),

                    "description": (
                        description
                    ),

                    "content_text": (
                        content_text
                    ),

                    "staff_code": (
                        staff_code
                    ),

                    "role_code": (
                        role_code
                    ),
                },
            )
            .scalar_one()
        )

    resource = (
        get_facilitator_resource(
            staff_code=(
                staff_code
            ),
            resource_id=str(
                resource_id
            ),
        )
    )

    if not resource:

        raise RuntimeError(
            "Learning resource was created "
            "but could not be reloaded."
        )

    return resource


# ============================================================
# CREATE LINK RESOURCE
# ============================================================

def create_link_resource(
    *,
    staff_code: str,
    role_code: str,
    class_id: str,
    module_id: str | None,
    timetable_session_id: str | None,
    title: str,
    description: str | None,
    external_url: str,
) -> dict:

    class_record = (
        get_facilitator_class(
            staff_code=(
                staff_code
            ),
            class_id=(
                class_id
            ),
        )
    )

    if not class_record:

        raise ValueError(
            "Class not found or not assigned "
            "to this facilitator."
        )

    title = (
        clean_required_text(
            title,
            "Resource title",
        )
    )

    description = (
        clean_optional_text(
            description
        )
    )

    external_url = (
        clean_required_text(
            external_url,
            "External URL",
        )
    )

    if not (
        external_url.startswith(
            "https://"
        )
        or external_url.startswith(
            "http://"
        )
    ):

        raise ValueError(
            "External resource URL must "
            "use HTTP or HTTPS."
        )

    with engine.begin() as connection:

        (
            module_id,
            timetable_session_id,
        ) = validate_related_scope(
            connection=(
                connection
            ),
            class_record=(
                class_record
            ),
            module_id=(
                module_id
            ),
            timetable_session_id=(
                timetable_session_id
            ),
        )

        resource_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.learning_resources
                    (
                        class_id,
                        module_id,
                        timetable_session_id,

                        title,
                        description,

                        resource_type,
                        external_url,

                        status,
                        visibility,

                        ai_generated,

                        created_by_staff_code,
                        created_by_role
                    )

                    VALUES
                    (
                        CAST(
                            :class_id
                            AS uuid
                        ),

                        CAST(
                            :module_id
                            AS uuid
                        ),

                        CAST(
                            :timetable_session_id
                            AS uuid
                        ),

                        :title,
                        :description,

                        'LINK',
                        :external_url,

                        'Draft',
                        'Class',

                        false,

                        :staff_code,
                        :role_code
                    )

                    RETURNING id
                    """
                ),
                {
                    "class_id": str(
                        class_record[
                            "id"
                        ]
                    ),

                    "module_id": (
                        module_id
                    ),

                    "timetable_session_id": (
                        timetable_session_id
                    ),

                    "title": (
                        title
                    ),

                    "description": (
                        description
                    ),

                    "external_url": (
                        external_url
                    ),

                    "staff_code": (
                        staff_code
                    ),

                    "role_code": (
                        role_code
                    ),
                },
            )
            .scalar_one()
        )

    resource = (
        get_facilitator_resource(
            staff_code=(
                staff_code
            ),
            resource_id=str(
                resource_id
            ),
        )
    )

    if not resource:

        raise RuntimeError(
            "Learning resource was created "
            "but could not be reloaded."
        )

    return resource


# ============================================================
# UPLOAD FILE RESOURCE
# ============================================================

def upload_file_resource(
    *,
    staff_code: str,
    role_code: str,
    class_id: str,
    module_id: str | None,
    timetable_session_id: str | None,
    title: str,
    description: str | None,
    filename: str,
    mime_type: str | None,
    file_bytes: bytes,
) -> dict:

    class_record = (
        get_facilitator_class(
            staff_code=(
                staff_code
            ),
            class_id=(
                class_id
            ),
        )
    )

    if not class_record:

        raise ValueError(
            "Class not found or not assigned "
            "to this facilitator."
        )

    title = (
        clean_required_text(
            title,
            "Resource title",
        )
    )

    description = (
        clean_optional_text(
            description
        )
    )

    safe_filename = (
        sanitise_filename(
            filename
        )
    )

    validate_resource_file(
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

    with engine.connect() as connection:

        (
            module_id,
            timetable_session_id,
        ) = validate_related_scope(
            connection=(
                connection
            ),
            class_record=(
                class_record
            ),
            module_id=(
                module_id
            ),
            timetable_session_id=(
                timetable_session_id
            ),
        )

    storage_path = (
        f"{class_record['class_code']}/"
        f"{uuid4()}_"
        f"{safe_filename}"
    )

    storage = (
        get_storage_client()
    )

    try:

        storage.storage.from_(
            LEARNING_RESOURCE_BUCKET
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

                "upsert": (
                    "false"
                ),
            },
        )

    except Exception as error:

        print(
            "ERROR: Learning resource "
            "storage upload failed: "
            f"{error}"
        )

        raise RuntimeError(
            "The learning resource file "
            "could not be stored."
        ) from error

    try:

        with engine.begin() as connection:

            resource_id = (
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            public.learning_resources
                        (
                            class_id,
                            module_id,
                            timetable_session_id,

                            title,
                            description,

                            resource_type,

                            original_filename,
                            storage_bucket,
                            storage_path,
                            mime_type,
                            file_size_bytes,

                            status,
                            visibility,

                            ai_generated,

                            created_by_staff_code,
                            created_by_role
                        )

                        VALUES
                        (
                            CAST(
                                :class_id
                                AS uuid
                            ),

                            CAST(
                                :module_id
                                AS uuid
                            ),

                            CAST(
                                :timetable_session_id
                                AS uuid
                            ),

                            :title,
                            :description,

                            'FILE',

                            :original_filename,
                            :storage_bucket,
                            :storage_path,
                            :mime_type,
                            :file_size_bytes,

                            'Draft',
                            'Class',

                            false,

                            :staff_code,
                            :role_code
                        )

                        RETURNING id
                        """
                    ),
                    {
                        "class_id": str(
                            class_record[
                                "id"
                            ]
                        ),

                        "module_id": (
                            module_id
                        ),

                        "timetable_session_id": (
                            timetable_session_id
                        ),

                        "title": (
                            title
                        ),

                        "description": (
                            description
                        ),

                        "original_filename": (
                            safe_filename
                        ),

                        "storage_bucket": (
                            LEARNING_RESOURCE_BUCKET
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

                        "staff_code": (
                            staff_code
                        ),

                        "role_code": (
                            role_code
                        ),
                    },
                )
                .scalar_one()
            )

    except Exception as error:

        delete_storage_file(
            storage_path
        )

        print(
            "ERROR: Learning resource "
            "database save failed: "
            f"{error}"
        )

        raise RuntimeError(
            "The learning resource upload "
            "could not be completed."
        ) from error

    resource = (
        get_facilitator_resource(
            staff_code=(
                staff_code
            ),
            resource_id=str(
                resource_id
            ),
        )
    )

    if not resource:

        raise RuntimeError(
            "Learning resource was uploaded "
            "but could not be reloaded."
        )

    return resource


# ============================================================
# GET ONE FACILITATOR RESOURCE
# ============================================================

def get_facilitator_resource(
    *,
    staff_code: str,
    resource_id: str,
) -> dict | None:

    resource_id = validate_uuid(
        resource_id,
        "resource ID",
    )

    query = text(
        RESOURCE_SELECT
        + """
        WHERE
            lr.id = CAST(
                :resource_id
                AS uuid
            )

            AND c.facilitator_code
                = :staff_code

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "resource_id": (
                        resource_id
                    ),

                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return None

    return format_resource(
        dict(
            row
        )
    )


# ============================================================
# GET FACILITATOR CLASS RESOURCES
# ============================================================

def get_facilitator_class_resources(
    *,
    staff_code: str,
    class_code: str,
) -> list[dict] | None:

    class_query = text(
        """
        SELECT
            id

        FROM public.classes

        WHERE
            class_code = :class_code

            AND facilitator_code
                = :staff_code

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        class_row = (
            connection.execute(
                class_query,
                {
                    "class_code": (
                        class_code
                    ),

                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not class_row:

            return None

        query = text(
            RESOURCE_SELECT
            + """
            WHERE
                lr.class_id = CAST(
                    :class_id
                    AS uuid
                )

            ORDER BY
                lr.created_at DESC,
                lr.title
            """
        )

        rows = (
            connection.execute(
                query,
                {
                    "class_id": str(
                        class_row[
                            "id"
                        ]
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        format_resource(
            dict(
                row
            )
        )
        for row in rows
    ]


# ============================================================
# PUBLISH RESOURCE
# ============================================================

def publish_learning_resource(
    *,
    staff_code: str,
    resource_id: str,
) -> dict:

    resource_id = validate_uuid(
        resource_id,
        "resource ID",
    )

    with engine.begin() as connection:

        existing = (
            connection.execute(
                text(
                    """
                    SELECT
                        lr.id,
                        lr.status

                    FROM
                        public.learning_resources lr

                    JOIN public.classes c
                        ON c.id = lr.class_id

                    WHERE
                        lr.id = CAST(
                            :resource_id
                            AS uuid
                        )

                        AND c.facilitator_code
                            = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "resource_id": (
                        resource_id
                    ),

                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not existing:

            raise ValueError(
                "Learning resource not found "
                "or not assigned to this "
                "facilitator."
            )

        if (
            existing[
                "status"
            ]
            == "Archived"
        ):

            raise ValueError(
                "An archived learning resource "
                "cannot be published."
            )

        connection.execute(
            text(
                """
                UPDATE
                    public.learning_resources

                SET
                    status = 'Published',

                    published_by_staff_code
                        = :staff_code,

                    published_at = COALESCE(
                        published_at,
                        now()
                    ),

                    updated_at = now()

                WHERE
                    id = CAST(
                        :resource_id
                        AS uuid
                    )
                """
            ),
            {
                "resource_id": (
                    resource_id
                ),

                "staff_code": (
                    staff_code
                ),
            },
        )

    resource = (
        get_facilitator_resource(
            staff_code=(
                staff_code
            ),
            resource_id=(
                resource_id
            ),
        )
    )

    if not resource:

        raise RuntimeError(
            "Published resource could not "
            "be reloaded."
        )

    return resource


# ============================================================
# ARCHIVE RESOURCE
# ============================================================

def archive_learning_resource(
    *,
    staff_code: str,
    resource_id: str,
) -> dict:

    resource_id = validate_uuid(
        resource_id,
        "resource ID",
    )

    with engine.begin() as connection:

        result = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.learning_resources lr

                    SET
                        status = 'Archived',
                        updated_at = now()

                    FROM public.classes c

                    WHERE
                        lr.id = CAST(
                            :resource_id
                            AS uuid
                        )

                        AND c.id = lr.class_id

                        AND c.facilitator_code
                            = :staff_code

                    RETURNING lr.id
                    """
                ),
                {
                    "resource_id": (
                        resource_id
                    ),

                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .scalar_one_or_none()
        )

        if not result:

            raise ValueError(
                "Learning resource not found "
                "or not assigned to this "
                "facilitator."
            )

    resource = (
        get_facilitator_resource(
            staff_code=(
                staff_code
            ),
            resource_id=(
                resource_id
            ),
        )
    )

    if not resource:

        raise RuntimeError(
            "Archived resource could not "
            "be reloaded."
        )

    return resource


# ============================================================
# GET STUDENT RESOURCES
# ============================================================

def get_student_learning_resources(
    student_number: str,
) -> list[dict]:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    query = text(
        RESOURCE_SELECT
        + """
        WHERE
            lr.status = 'Published'

            AND c.status = 'Active'

            AND EXISTS
            (
                SELECT 1

                FROM public.class_enrolments ce

                JOIN public.registrations r
                    ON r.id =
                        ce.registration_id

                WHERE
                    ce.class_id =
                        lr.class_id

                    AND r.student_number
                        = :student_number

                    AND ce.status
                        = 'Active'
            )

        ORDER BY
            lr.published_at DESC NULLS LAST,
            lr.created_at DESC,
            lr.title
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        format_resource(
            dict(
                row
            )
        )
        for row in rows
    ]


# ============================================================
# GET ONE STUDENT RESOURCE
# ============================================================

def get_student_learning_resource(
    *,
    student_number: str,
    resource_id: str,
) -> dict | None:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    resource_id = validate_uuid(
        resource_id,
        "resource ID",
    )

    query = text(
        RESOURCE_SELECT
        + """
        WHERE
            lr.id = CAST(
                :resource_id
                AS uuid
            )

            AND lr.status = 'Published'

            AND c.status = 'Active'

            AND EXISTS
            (
                SELECT 1

                FROM public.class_enrolments ce

                JOIN public.registrations r
                    ON r.id =
                        ce.registration_id

                WHERE
                    ce.class_id =
                        lr.class_id

                    AND r.student_number
                        = :student_number

                    AND ce.status
                        = 'Active'
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "resource_id": (
                        resource_id
                    ),

                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return None

    return format_resource(
        dict(
            row
        )
    )