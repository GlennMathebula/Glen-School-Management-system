from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.services.admin_bulk_documents_service import (
    cleanup_bulk_archive,
    generate_bulk_documents_zip,
    resolve_bulk_document_scope,
)
from app.staff_admin_guard import require_admin_staff

router = APIRouter(
    prefix="/api/staff/admin/bulk-documents",
    tags=["Admin - Bulk Documents"],
)


@router.get("/scope")
def admin_bulk_document_scope(
    scope_type: str = Query(...),
    scope_value: str = Query(...),
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        records = resolve_bulk_document_scope(
            scope_type=scope_type,
            scope_value=scope_value,
        )
        return {"success": True, "count": len(records), "learners": records}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/zip")
def admin_bulk_documents_zip(
    document_type: str = Query(...),
    scope_type: str = Query(...),
    scope_value: str = Query(...),
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        result = generate_bulk_documents_zip(
            document_type=document_type,
            scope_type=scope_type,
            scope_value=scope_value,
        )
        archive_path = Path(result["archive_path"]).resolve()
        return FileResponse(
            path=str(archive_path),
            filename=result["filename"],
            media_type="application/zip",
            headers={
                "X-Bulk-Learner-Count": str(result["learner_count"]),
                "X-Bulk-Generated-Count": str(result["generated_count"]),
                "X-Bulk-Skipped-Count": str(result["skipped_count"]),
            },
            background=BackgroundTask(cleanup_bulk_archive, str(archive_path)),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        print(f"ERROR: Bulk document ZIP generation failed: {error}")
        raise HTTPException(
            status_code=500,
            detail="Bulk document ZIP could not be generated.",
        ) from error
