from app.critical_write_guard import redis_guarded_endpoint
from datetime import date
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import FileResponse

from app.services.daily_attendance_register_service import (
    generate_daily_attendance_pack,
)
from app.staff_admin_guard import (
    require_admin_staff,
)


router = APIRouter(
    prefix="/api/staff/admin/attendance-registers",
    tags=["Admin - Attendance Registers"],
)


@router.get("/daily-pack")
@redis_guarded_endpoint("job:attendance-pack", key_fields=('class_id', 'week_start'), ttl_seconds=600, busy_message="This attendance-register pack is already being generated.", unavailable_message="Attendance-pack generation protection is temporarily unavailable. Please try again shortly.", fail_open=False)
def admin_generate_daily_attendance_register_pack(
    class_id: str,
    week_start: date,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    try:
        pdf_path = (
            generate_daily_attendance_pack(
                class_id=class_id,
                week_start=week_start,
                generated_by=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        path = Path(
            pdf_path
        ).resolve()

        if (
            not path.exists()
            or not path.is_file()
        ):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Attendance register PDF "
                    "was generated but could "
                    "not be located."
                ),
            )

        return FileResponse(
            path=str(path),
            media_type="application/pdf",
            filename=path.name,
        )

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        print(
            "ERROR: Admin attendance register "
            f"generation failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Attendance register PDF "
                "could not be generated."
            ),
        ) from error
