from datetime import date

from pydantic import BaseModel, Field

# ============================================================
# CREATE REGISTRATION
# ============================================================

class RegistrationCreate(BaseModel):

    student_number: str = Field(
        min_length=1,
        max_length=30,
    )

    funding_type: str | None = None

    cycle: str | None = None

    # Set by Admin / IT.
    # This is the intended programme commencement date,
    # NOT necessarily the date the learner is registered.
    program_start_date: date

    expected_completion_date: date | None = None


# ============================================================
# UPDATE REGISTRATION STATUS
# ============================================================

class RegistrationStatusUpdate(BaseModel):

    status: str = Field(
        min_length=1,
        max_length=30,
    )