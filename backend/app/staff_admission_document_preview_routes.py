from __future__ import annotations

from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import Response

from app.services.staff_admission_document_preview_service import (
    load_admission_document_preview,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/admissions",
    tags=[
        "Staff Admissions Document Preview"
    ],
)


require_view_applications = require_permission(
    "VIEW_APPLICATIONS"
)


@router.get(
    "/documents/{document_id}/preview"
)
def preview_admission_document(
    document_id: str,
    current_staff: dict = Depends(
        require_view_applications
    ),
):
    del current_staff

    try:
        result = (
            load_admission_document_preview(
                document_id
            )
        )

        document = result[
            "document"
        ]

        filename = str(
            document.get(
                "original_filename"
            )
            or "document"
        ).replace(
            '"',
            "",
        )

        mime_type = (
            document.get(
                "mime_type"
            )
            or "application/octet-stream"
        )

        return Response(
            content=result[
                "content"
            ],
            media_type=mime_type,
            headers={
                "Content-Disposition": (
                    "inline; "
                    f"filename*=UTF-8''"
                    f"{quote(filename)}"
                ),
                "Cache-Control": (
                    "private, no-store"
                ),
                "X-Content-Type-Options": (
                    "nosniff"
                ),
            },
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:
        print(
            "ERROR: Staff admission "
            f"document preview failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The uploaded document "
                "could not be previewed."
            ),
        ) from error
