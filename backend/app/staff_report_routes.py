from datetime import date
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse

from app.services.staff_permission_service import (
    require_permission,
)
from app.services.staff_report_service import (
    build_report,
    generate_report_pdf,
    get_report_catalog,
)


router = APIRouter(
    prefix="/api/staff/reports",
    tags=["Staff QA & Compliance Reports"],
)

require_view_reports = require_permission(
    "VIEW_REPORTS"
)


@router.get("/catalog")
def staff_report_catalog(
    current_staff: dict = Depends(
        require_view_reports
    ),
):
    reports = get_report_catalog()
    return {
        "success": True,
        "count": len(reports),
        "reports": reports,
    }


@router.get("/{report_code}")
def staff_report_preview(
    report_code: str,
    cycle_code: str | None = Query(default=None),
    course_code: str | None = Query(default=None),
    class_code: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_staff: dict = Depends(
        require_view_reports
    ),
):
    try:
        report = build_report(
            report_code,
            cycle_code=cycle_code,
            course_code=course_code,
            class_code=class_code,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "success": True,
            "report": report,
        }
    except NotImplementedError as error:
        raise HTTPException(
            status_code=501,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(
            "ERROR: Staff report preview failed: "
            f"{error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Report could not be generated.",
        ) from error


@router.get("/{report_code}/pdf")
def staff_report_pdf(
    report_code: str,
    cycle_code: str | None = Query(default=None),
    course_code: str | None = Query(default=None),
    class_code: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_staff: dict = Depends(
        require_view_reports
    ),
):
    try:
        pdf_path, report = generate_report_pdf(
            report_code,
            generated_by=current_staff["staff_code"],
            cycle_code=cycle_code,
            course_code=course_code,
            class_code=class_code,
            date_from=date_from,
            date_to=date_to,
        )

        path = Path(pdf_path)

        if not path.exists():
            raise HTTPException(
                status_code=500,
                detail=(
                    "Report PDF was generated but "
                    "the file could not be located."
                ),
            )

        filename = (
            report_code.replace(".", "_")
            + ".pdf"
        )

        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=filename,
        )
    except HTTPException:
        raise
    except NotImplementedError as error:
        raise HTTPException(
            status_code=501,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(
            "ERROR: Report PDF generation failed: "
            f"{error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Report PDF could not be generated.",
        ) from error
