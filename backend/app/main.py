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

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title=(
        "Glen Moniques School Management System"
    ),
    description=(
        "Backend API for Glen Moniques"
    ),
    version="1.0.0",
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