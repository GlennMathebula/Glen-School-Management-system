from pydantic import BaseModel, Field

# ============================================================
# PIN SETUP
# ============================================================

class StudentPinSetup(BaseModel):

    student_number: str = Field(
        min_length=1,
        max_length=30,
    )

    password: str = Field(
        min_length=1,
        max_length=200,
    )

    pin: str = Field(
        min_length=5,
        max_length=5,
    )


# ============================================================
# PIN LOGIN
# ============================================================

class StudentPinLogin(BaseModel):

    student_number: str = Field(
        min_length=1,
        max_length=30,
    )

    pin: str = Field(
        min_length=5,
        max_length=5,
    )


# ============================================================
# PASSWORD LOGIN
# ============================================================

class StudentPasswordLogin(BaseModel):

    student_number: str = Field(
        min_length=1,
        max_length=30,
    )

    password: str = Field(
        min_length=1,
        max_length=200,
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

class StudentPasswordChange(BaseModel):

    student_number: str = Field(
        min_length=1,
        max_length=30,
    )

    current_password: str = Field(
        min_length=1,
        max_length=200,
    )

    new_password: str = Field(
        min_length=8,
        max_length=200,
    )