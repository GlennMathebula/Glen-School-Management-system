from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from app.database import (
    test_database_connection,
)
from app.database_inspector import (
    get_database_tables,
)
from app.facilitator_routes import (
    router as facilitator_router,
)
from app.google_calendar_routes import (
    router as google_calendar_router,
)
from app.payfast_routes import (
    router as payfast_router,
)
from app.payfast_test_routes import (
    router as payfast_test_router,
)
from app.public_routes import (
    router as public_router,
)
from app.routes import (
    router as core_router,
)
from app.staff_auth_routes import (
    router as staff_auth_router,
)
from app.student_card_routes import (
    router as student_card_router,
)
from app.student_communications_routes import (
    router as student_communications_router,
)
from app.student_completion_documents_routes import (
    router as student_completion_documents_router,
)
from app.student_finance_document_routes import (
    router as student_finance_document_router,
)
from app.student_portal_routes import (
    router as student_portal_router,
)
from app.student_settings_routes import (
    router as student_settings_router,
)
from app.learning_resource_routes import (
    router as learning_resource_router,
)
from app.student_support_routes import (
    router as student_support_router,
)
from app.utils.sa_id import (
    validate_sa_id,
)
from app.staff_profile_routes import (
    router as staff_profile_router,
)
from app.staff_permission_routes import (
    router as staff_permission_router,
)
from app.staff_audit_routes import (
    router as staff_audit_router,
)

from app.staff_assessment_routes import (
    router as staff_assessment_router,
)
from app.staff_dashboard_routes import (
    router as staff_dashboard_router,
)
# ============================================================
# FASTAPI APP
# ============================================================

from app.staff_notification_routes import (
    router as staff_notification_router,
)
from app.staff_communications_routes import (
    router as staff_communications_router,
)
from app.staff_academic_management_routes import (
    router as staff_academic_management_router,
)



from app.staff_admin_student_records_routes import (
    router as staff_admin_student_records_router,
)

from app.staff_admin_timetable_routes import (
    router as staff_admin_timetable_router,
)

from app.staff_admin_eisa_routes import (
    router as staff_admin_eisa_router,
)

from app.staff_admin_completion_routes import (
    router as staff_admin_completion_router,
)

from app.staff_admin_system_routes import (
    router as staff_admin_system_router,
)


from app.staff_principal_routes import (
    router as staff_principal_router,
)



from app.staff_finance_routes import (
    router as staff_finance_router,
)


from app.career_routes import (
    router as career_router,
)
from app.staff_hr_routes import (
    router as staff_hr_router,
)



from app.staff_hr_employment_routes import (
    router as staff_hr_employment_router,
)



from app.staff_admin_completion_management_routes import (
    router as staff_admin_completion_management_router,
)
from app.staff_admin_system_management_routes import (
    router as staff_admin_system_management_router,
)
from app.staff_student_support_routes import (
    router as staff_student_support_router,
)



from app.staff_admin_enrolment_form_routes import (
    router as staff_admin_enrolment_form_router,
)


app = FastAPI(
    title=(
        "Glen Moniques School Management System"
    ),
    description=(
        "Backend API for Glen Moniques"
    ),
    version="1.0.0",
)

from app.staff_admissions_routes import (
    router as staff_admissions_router,
)

app.include_router(
    staff_admissions_router
)


from app.staff_compliance_records_routes import (
    router as staff_compliance_records_router,
)

app.include_router(
    staff_compliance_records_router
)


from app.staff_report_routes import (
    router as staff_report_router,
)

app.include_router(
    staff_report_router
)



# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    core_router
)

app.include_router(
    public_router
)

app.include_router(
    student_portal_router
)

app.include_router(
    student_finance_document_router
)

app.include_router(
    payfast_router
)

app.include_router(
    payfast_test_router
)

app.include_router(
    student_card_router
)

app.include_router(
    student_communications_router
)

app.include_router(
    student_support_router
)

app.include_router(
    student_settings_router
)

app.include_router(
    student_completion_documents_router
)

app.include_router(
    staff_auth_router
)

app.include_router(
    facilitator_router
)

app.include_router(
    google_calendar_router
)

app.include_router(
    learning_resource_router
)

app.include_router(
    staff_profile_router
)
app.include_router(
    staff_permission_router
)
app.include_router(
    staff_audit_router
)
app.include_router(
    staff_assessment_router
)
app.include_router(
    staff_dashboard_router
)
# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": (
            "Welcome to Glen Moniques SMS API"
        ),
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health"
)
def health_check():

    return {
        "status": "healthy",
    }


# ============================================================
# DATABASE HEALTH
# ============================================================

@app.get(
    "/health/database"
)
def database_health_check():

    try:

        result = (
            test_database_connection()
        )

        return {
            "status": "connected",

            "database": (
                "Supabase PostgreSQL"
            ),

            "test_result": (
                result
            ),
        }

    except SQLAlchemyError as error:

        return {
            "status": "error",

            "message": (
                str(
                    error
                )
            ),
        }


# ============================================================
# DATABASE TABLES
# ============================================================

@app.get(
    "/health/database/tables"
)
def database_tables():

    tables = (
        get_database_tables()
    )

    return {
        "status": "connected",

        "table_count": (
            len(
                tables
            )
        ),

        "tables": (
            tables
        ),
    }


# ============================================================
# SA ID TEST
# ============================================================

@app.get(
    "/test/sa-id"
)
def test_sa_id(
    id_number: str,
):

    return (
        validate_sa_id(
            id_number
        )
    )

# ============================================================
# NORMALIZED STAFF ROUTERS
# ============================================================

app.include_router(
    staff_notification_router
)

app.include_router(
    staff_communications_router
)

app.include_router(
    staff_academic_management_router
)


app.include_router(
    staff_admin_student_records_router
)


app.include_router(
    staff_admin_timetable_router
)


app.include_router(
    staff_admin_eisa_router
)


app.include_router(
    staff_admin_completion_router
)


app.include_router(
    staff_admin_system_router
)



app.include_router(
    staff_principal_router
)



app.include_router(
    staff_finance_router
)


app.include_router(
    career_router
)


app.include_router(
    staff_hr_router
)


app.include_router(
    staff_hr_employment_router
)

app.include_router(
    staff_admin_completion_management_router
)

app.include_router(
    staff_admin_system_management_router
)

app.include_router(
    staff_student_support_router
)

app.include_router(
    staff_admin_enrolment_form_router
)

# ============================================================
# PUBLIC APPLICATION SUPPORT
# ============================================================
from app.application_public_support_routes import (
    router as application_public_support_router,
)

app.include_router(
    application_public_support_router
)
# ============================================================
# PUBLIC REGISTRATION PREVIEW / VERIFICATION
# ============================================================
from app.public_registration_preview_routes import (
    router as public_registration_preview_router,
)

app.include_router(
    public_registration_preview_router
)

from app.student_finance_portal_routes import router as student_finance_portal_router
app.include_router(student_finance_portal_router)


from app.staff_admin_document_center_routes import (
    router as staff_admin_document_center_router,
)

app.include_router(
    staff_admin_document_center_router
)


from app.staff_admin_attendance_register_routes import (
    router as staff_admin_attendance_register_router,
)

app.include_router(
    staff_admin_attendance_register_router
)


from app.staff_admin_attendance_review_routes import (
    router as staff_admin_attendance_review_router,
)

app.include_router(
    staff_admin_attendance_review_router
)



from app.staff_admission_document_preview_routes import (
    router as staff_admission_document_preview_router,
)

app.include_router(
    staff_admission_document_preview_router
)



from app.staff_admissions_bulk_routes import (
    router as staff_admissions_bulk_router,
)

app.include_router(
    staff_admissions_bulk_router
)


from app.staff_admin_bulk_documents_routes import (
    router as staff_admin_bulk_documents_router,
)

app.include_router(
    staff_admin_bulk_documents_router
)


from app.staff_desktop_v5_routes import (
    router as staff_desktop_v5_router,
)

app.include_router(
    staff_desktop_v5_router
)
