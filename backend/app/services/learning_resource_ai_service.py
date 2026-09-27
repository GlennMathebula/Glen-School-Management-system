import time

from google import genai
from sqlalchemy import text
from supabase import create_client

from app.config import settings
from app.database import engine

from app.services.learning_resource_service import (
    get_facilitator_resource,
    validate_uuid,
)

from app.services.learning_resource_text_service import (
    extract_learning_resource_text,
)


# ============================================================
# AI CONFIGURATION
# ============================================================

AI_PROVIDER_NAME = "Google Gemini"

FALLBACK_GEMINI_MODEL = (
    "gemini-3.5-flash-lite"
)

RETRY_DELAYS_SECONDS = [
    2,
    4,
    8,
]


# ============================================================
# STORAGE CLIENT
# ============================================================

def get_storage_client():

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


# ============================================================
# GET AI SOURCE RESOURCE
# ============================================================

def get_ai_source_resource(
    *,
    staff_code: str,
    resource_id: str,
) -> dict | None:

    resource_id = validate_uuid(
        resource_id,
        "resource ID",
    )

    query = text(
        """
        SELECT
            lr.id,
            lr.class_id,
            lr.module_id,
            lr.timetable_session_id,

            lr.title,
            lr.description,
            lr.resource_type,

            lr.original_filename,
            lr.storage_bucket,
            lr.storage_path,
            lr.mime_type,
            lr.file_size_bytes,

            lr.status,

            c.class_code,
            c.class_name,
            c.course_code,
            c.facilitator_code,

            m.module_code,
            m.module_name,
            m.module_type,

            ts.session_title

        FROM public.learning_resources lr

        JOIN public.classes c
            ON c.id = lr.class_id

        LEFT JOIN public.modules m
            ON m.id = lr.module_id

        LEFT JOIN public.timetable_sessions ts
            ON ts.id =
                lr.timetable_session_id

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

    return dict(
        row
    )


# ============================================================
# DOWNLOAD SOURCE RESOURCE
# ============================================================

def download_source_resource(
    source_resource: dict,
) -> bytes:

    storage_bucket = (
        source_resource.get(
            "storage_bucket"
        )
    )

    storage_path = (
        source_resource.get(
            "storage_path"
        )
    )

    if (
        not storage_bucket
        or not storage_path
    ):

        raise ValueError(
            "The selected learning resource "
            "does not contain a stored file."
        )

    try:

        storage = (
            get_storage_client()
        )

        file_bytes = (
            storage.storage
            .from_(
                storage_bucket
            )
            .download(
                storage_path
            )
        )

    except Exception as error:

        print(
            "ERROR: AI source resource "
            "download failed: "
            f"{error}"
        )

        raise RuntimeError(
            "The source learning resource "
            "could not be downloaded."
        ) from error

    if not file_bytes:

        raise RuntimeError(
            "The source learning resource "
            "file is empty."
        )

    return file_bytes


# ============================================================
# BUILD GEMINI PROMPT
# ============================================================

def build_learning_notes_prompt(
    *,
    source_resource: dict,
    extracted_text: str,
) -> str:

    module_code = (
        source_resource.get(
            "module_code"
        )
        or "Not specified"
    )

    module_name = (
        source_resource.get(
            "module_name"
        )
        or "Not specified"
    )

    class_name = (
        source_resource.get(
            "class_name"
        )
        or "Not specified"
    )

    source_title = (
        source_resource.get(
            "title"
        )
        or "Learning Resource"
    )

    return f"""
You are assisting a South African training provider to prepare
learner-friendly study notes.

SOURCE INFORMATION
------------------
Class: {class_name}
Module code: {module_code}
Module name: {module_name}
Source resource title: {source_title}

INSTRUCTIONS
------------
Create clear, structured study notes using ONLY the source text
provided below.

Important rules:

1. Do not introduce facts that are not supported by the source.
2. Do not invent legislation, definitions, examples, statistics,
   assessment requirements, qualification rules, or references.
3. Preserve the terminology and meaning used in the source.
4. Simplify difficult wording where appropriate without changing
   its meaning.
5. Organise the notes with useful headings and subheadings.
6. Use bullet points where they improve readability.
7. Explain important concepts in learner-friendly language.
8. Include key points learners should remember.
9. If the source contains steps or procedures, preserve their
   correct sequence.
10. If the source contains examples, retain or summarise them.
11. Do not state that something is compulsory unless the source
    says so.
12. Do not include information merely because it is generally
    known about the subject.
13. Do not mention these instructions in the final notes.
14. Do not produce an answer key or assessment result.
15. Output the notes in clean Markdown.

Use the following structure where supported by the source:

# [Appropriate Study Notes Title]

## Introduction

## Main Learning Topics

### Relevant subheadings

## Key Concepts

## Important Points to Remember

## Summary

If a section is not supported by the source, omit it rather than
inventing content.

SOURCE TEXT
-----------
{extracted_text}
""".strip()


# ============================================================
# TEMPORARY GEMINI ERROR CHECK
# ============================================================

def is_temporary_gemini_error(
    error: Exception,
) -> bool:

    error_text = (
        str(
            error
        )
        .lower()
    )

    temporary_markers = (
        "503",
        "unavailable",
        "high demand",
        "resource_exhausted",
        "429",
        "too many requests",
        "temporarily unavailable",
    )

    return any(
        marker in error_text
        for marker in temporary_markers
    )


# ============================================================
# GENERATE NOTES WITH GEMINI
# ============================================================

def generate_notes_with_gemini(
    *,
    prompt: str,
) -> tuple[
    str,
    str,
]:

    api_key = (
        settings.gemini_api_key
        or ""
    ).strip()

    if not api_key:

        raise RuntimeError(
            "Gemini API key is not configured."
        )

    primary_model = (
        settings.gemini_model
        or ""
    ).strip()

    if not primary_model:

        raise RuntimeError(
            "Gemini model is not configured."
        )

    models_to_try = [
        primary_model,
    ]

    if (
        FALLBACK_GEMINI_MODEL
        != primary_model
    ):

        models_to_try.append(
            FALLBACK_GEMINI_MODEL
        )

    try:

        client = genai.Client(
            api_key=(
                api_key
            )
        )

    except Exception as error:

        raise RuntimeError(
            "Gemini client could not "
            "be initialised."
        ) from error

    last_error = None

    # --------------------------------------------------------
    # TRY PRIMARY THEN FALLBACK
    # --------------------------------------------------------

    for model_name in (
        models_to_try
    ):

        total_attempts = len(
            RETRY_DELAYS_SECONDS
        )

        for attempt_number in range(
            1,
            total_attempts + 1,
        ):

            try:

                print(
                    "INFO: Gemini AI note "
                    "generation attempt "
                    f"{attempt_number}/"
                    f"{total_attempts} "
                    f"using {model_name}"
                )

                response = (
                    client.models.generate_content(
                        model=(
                            model_name
                        ),

                        contents=(
                            prompt
                        ),
                    )
                )

                generated_text = (
                    response.text
                    or ""
                ).strip()

                if not generated_text:

                    raise RuntimeError(
                        "Gemini returned an "
                        "empty learning note."
                    )

                print(
                    "INFO: Gemini AI note "
                    "generation successful "
                    f"using {model_name}"
                )

                return (
                    generated_text,
                    model_name,
                )

            except Exception as error:

                last_error = (
                    error
                )

                temporary_error = (
                    is_temporary_gemini_error(
                        error
                    )
                )

                print(
                    "WARNING: Gemini request "
                    "failed using "
                    f"{model_name} on attempt "
                    f"{attempt_number}: "
                    f"{error}"
                )

                # -------------------------------------------
                # DO NOT RETRY PERMANENT ERRORS
                # -------------------------------------------

                if not temporary_error:

                    raise RuntimeError(
                        "AI notes could not "
                        "be generated because "
                        "the Gemini request "
                        "was rejected."
                    ) from error

                # -------------------------------------------
                # RETRY CURRENT MODEL
                # -------------------------------------------

                if (
                    attempt_number
                    < total_attempts
                ):

                    delay_seconds = (
                        RETRY_DELAYS_SECONDS[
                            attempt_number - 1
                        ]
                    )

                    print(
                        "INFO: Retrying Gemini "
                        f"in {delay_seconds} "
                        "seconds."
                    )

                    time.sleep(
                        delay_seconds
                    )

        print(
            "WARNING: Gemini model "
            f"{model_name} remained "
            "unavailable."
        )

        if (
            model_name
            != models_to_try[-1]
        ):

            print(
                "INFO: Switching to Gemini "
                "fallback model."
            )

    print(
        "ERROR: All Gemini models failed: "
        f"{last_error}"
    )

    raise RuntimeError(
        "Gemini is temporarily unavailable. "
        "Please try generating the notes "
        "again later."
    )


# ============================================================
# BUILD AI NOTE TITLE
# ============================================================

def build_ai_note_title(
    source_title: str,
) -> str:

    source_title = (
        source_title
        or "Learning Resource"
    ).strip()

    title = (
        f"Study Notes - {source_title}"
    )

    return title[:200]


# ============================================================
# SAVE AI NOTE
# ============================================================

def save_ai_note(
    *,
    staff_code: str,
    role_code: str,
    source_resource: dict,
    generated_notes: str,
    model_used: str,
) -> str:

    generated_notes = (
        generated_notes
        or ""
    ).strip()

    model_used = (
        model_used
        or ""
    ).strip()

    if not generated_notes:

        raise RuntimeError(
            "Generated AI notes are empty."
        )

    if not model_used:

        raise RuntimeError(
            "AI model information is missing."
        )

    title = (
        build_ai_note_title(
            source_resource.get(
                "title"
            )
            or "Learning Resource"
        )
    )

    source_title = (
        source_resource.get(
            "title"
        )
        or "Learning Resource"
    )

    description = (
        "AI-generated study notes created "
        "from the learning resource "
        f"'{source_title}'. "
        "Review before publishing."
    )

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
                        source_resource_id,

                        title,
                        description,

                        resource_type,
                        content_text,

                        status,
                        visibility,

                        ai_generated,
                        ai_provider,
                        ai_model,

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

                        CAST(
                            :source_resource_id
                            AS uuid
                        ),

                        :title,
                        :description,

                        'AI_NOTE',
                        :content_text,

                        'Draft',
                        'Class',

                        true,
                        :ai_provider,
                        :ai_model,

                        :staff_code,
                        :role_code
                    )

                    RETURNING id
                    """
                ),
                {
                    "class_id": str(
                        source_resource[
                            "class_id"
                        ]
                    ),

                    "module_id": (
                        str(
                            source_resource[
                                "module_id"
                            ]
                        )
                        if source_resource.get(
                            "module_id"
                        )
                        else None
                    ),

                    "timetable_session_id": (
                        str(
                            source_resource[
                                "timetable_session_id"
                            ]
                        )
                        if source_resource.get(
                            "timetable_session_id"
                        )
                        else None
                    ),

                    "source_resource_id": str(
                        source_resource[
                            "id"
                        ]
                    ),

                    "title": (
                        title
                    ),

                    "description": (
                        description
                    ),

                    "content_text": (
                        generated_notes
                    ),

                    "ai_provider": (
                        AI_PROVIDER_NAME
                    ),

                    "ai_model": (
                        model_used
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

    return str(
        resource_id
    )


# ============================================================
# GENERATE AI NOTES FROM RESOURCE
# ============================================================

def generate_ai_notes_from_resource(
    *,
    staff_code: str,
    role_code: str,
    source_resource_id: str,
) -> dict:

    # --------------------------------------------------------
    # LOAD SOURCE RESOURCE
    # --------------------------------------------------------

    source_resource = (
        get_ai_source_resource(
            staff_code=(
                staff_code
            ),

            resource_id=(
                source_resource_id
            ),
        )
    )

    if not source_resource:

        raise ValueError(
            "Learning resource not found "
            "or not assigned to this "
            "facilitator."
        )

    # --------------------------------------------------------
    # SOURCE MUST BE FILE
    # --------------------------------------------------------

    if (
        source_resource[
            "resource_type"
        ]
        != "FILE"
    ):

        raise ValueError(
            "AI notes can currently be "
            "generated only from uploaded "
            "file resources."
        )

    # --------------------------------------------------------
    # SOURCE CANNOT BE ARCHIVED
    # --------------------------------------------------------

    if (
        source_resource[
            "status"
        ]
        == "Archived"
    ):

        raise ValueError(
            "AI notes cannot be generated "
            "from an archived resource."
        )

    filename = (
        source_resource.get(
            "original_filename"
        )
        or ""
    )

    mime_type = (
        source_resource.get(
            "mime_type"
        )
    )

    # --------------------------------------------------------
    # DOWNLOAD FILE
    # --------------------------------------------------------

    file_bytes = (
        download_source_resource(
            source_resource
        )
    )

    # --------------------------------------------------------
    # EXTRACT TEXT
    # --------------------------------------------------------

    extracted_text = (
        extract_learning_resource_text(
            filename=(
                filename
            ),

            mime_type=(
                mime_type
            ),

            file_bytes=(
                file_bytes
            ),
        )
    )

    if not extracted_text.strip():

        raise ValueError(
            "No readable text could be "
            "extracted from the source file."
        )

    print(
        "INFO: Extracted "
        f"{len(extracted_text)} characters "
        "from learning resource."
    )

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    prompt = (
        build_learning_notes_prompt(
            source_resource=(
                source_resource
            ),

            extracted_text=(
                extracted_text
            ),
        )
    )

    # --------------------------------------------------------
    # GENERATE NOTES
    # --------------------------------------------------------

    (
        generated_notes,
        model_used,
    ) = (
        generate_notes_with_gemini(
            prompt=(
                prompt
            )
        )
    )

    # --------------------------------------------------------
    # SAVE AS DRAFT
    # --------------------------------------------------------

    ai_resource_id = (
        save_ai_note(
            staff_code=(
                staff_code
            ),

            role_code=(
                role_code
            ),

            source_resource=(
                source_resource
            ),

            generated_notes=(
                generated_notes
            ),

            model_used=(
                model_used
            ),
        )
    )

    # --------------------------------------------------------
    # RELOAD CREATED AI NOTE
    # --------------------------------------------------------

    ai_resource = (
        get_facilitator_resource(
            staff_code=(
                staff_code
            ),

            resource_id=(
                ai_resource_id
            ),
        )
    )

    if not ai_resource:

        raise RuntimeError(
            "AI notes were generated but "
            "could not be reloaded."
        )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if (
        ai_resource.get(
            "resource_type"
        )
        != "AI_NOTE"
    ):

        raise RuntimeError(
            "Generated learning resource "
            "was saved with an invalid type."
        )

    if (
        ai_resource.get(
            "status"
        )
        != "Draft"
    ):

        raise RuntimeError(
            "Generated AI notes were not "
            "saved as a draft."
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "source_resource": {
            "resource_id": str(
                source_resource[
                    "id"
                ]
            ),

            "title": (
                source_resource[
                    "title"
                ]
            ),

            "filename": (
                filename
            ),

            "mime_type": (
                mime_type
            ),

            "extracted_characters": len(
                extracted_text
            ),
        },

        "generation": {
            "provider": (
                AI_PROVIDER_NAME
            ),

            "model_used": (
                model_used
            ),
        },

        "ai_note": (
            ai_resource
        ),
    }


# ============================================================
# RESTORE ARCHIVED RESOURCE
# ============================================================

def restore_learning_resource(
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

                    FROM public.learning_resources lr

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
            != "Archived"
        ):

            raise ValueError(
                "Only archived learning "
                "resources can be restored."
            )

        connection.execute(
            text(
                """
                UPDATE
                    public.learning_resources

                SET
                    status = 'Draft',

                    published_by_staff_code
                        = NULL,

                    published_at = NULL,

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
            "Restored resource could not "
            "be reloaded."
        )

    return resource