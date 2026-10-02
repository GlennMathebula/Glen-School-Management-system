from __future__ import annotations

from sqlalchemy import text

from app.database import engine
from app.services.student_document_service import (
    get_storage_client,
)


def get_admission_document_metadata(
    document_id: str,
) -> dict:
    document_id = str(
        document_id or ""
    ).strip()

    if not document_id:
        raise ValueError(
            "Document ID is required."
        )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                '''
                SELECT
                    id,
                    student_number,
                    document_type,
                    document_label,
                    original_filename,
                    storage_bucket,
                    storage_path,
                    mime_type,
                    file_size_bytes,
                    version_number,
                    is_current,
                    review_status,
                    uploaded_at
                FROM public.student_documents
                WHERE
                    id = CAST(
                        :document_id
                        AS uuid
                    )
                LIMIT 1
                '''
            ),
            {
                "document_id": (
                    document_id
                ),
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "Uploaded document was not found."
        )

    return dict(
        row
    )


def load_admission_document_preview(
    document_id: str,
) -> dict:
    document = (
        get_admission_document_metadata(
            document_id
        )
    )

    bucket = str(
        document.get(
            "storage_bucket"
        )
        or "student-documents"
    ).strip()

    storage_path = str(
        document.get(
            "storage_path"
        )
        or ""
    ).strip()

    if not storage_path:
        raise ValueError(
            "The uploaded document does not "
            "have a storage path."
        )

    storage = get_storage_client()

    try:
        file_bytes = (
            storage.storage
            .from_(
                bucket
            )
            .download(
                storage_path
            )
        )
    except Exception as error:
        print(
            "ERROR: Admission document "
            f"preview download failed: {error}"
        )

        raise RuntimeError(
            "The uploaded document could "
            "not be loaded for preview."
        ) from error

    if isinstance(
        file_bytes,
        bytearray,
    ):
        file_bytes = bytes(
            file_bytes
        )

    if not isinstance(
        file_bytes,
        bytes,
    ):
        try:
            file_bytes = bytes(
                file_bytes
            )
        except Exception as error:
            raise RuntimeError(
                "The uploaded document could "
                "not be read for preview."
            ) from error

    return {
        "document": document,
        "content": file_bytes,
    }
