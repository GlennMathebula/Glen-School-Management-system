from datetime import date, datetime
from pydantic import BaseModel, Field

class CareerApplicantRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    cell_number: str = Field(min_length=5, max_length=40)
    national_id: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=255)

class CareerApplicantLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=255)

class CareerPasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)

class CareerApplicationDraftCreate(BaseModel):
    cover_letter: str | None = Field(default=None, max_length=10000)

class HRVacancyCreate(BaseModel):
    job_title: str = Field(min_length=2, max_length=200)
    department: str | None = Field(default=None, max_length=150)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str = Field(min_length=2, max_length=80)
    positions_available: int = Field(default=1, ge=1, le=500)
    description: str = Field(min_length=10, max_length=20000)
    responsibilities: str | None = Field(default=None, max_length=20000)
    minimum_requirements: str = Field(min_length=5, max_length=20000)
    preferred_requirements: str | None = Field(default=None, max_length=20000)
    required_documents: list[str] = Field(default_factory=list, max_length=30)
    opening_date: date | None = None
    closing_date: date

class HRVacancyUpdate(BaseModel):
    job_title: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=150)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=80)
    positions_available: int | None = Field(default=None, ge=1, le=500)
    description: str | None = Field(default=None, max_length=20000)
    responsibilities: str | None = Field(default=None, max_length=20000)
    minimum_requirements: str | None = Field(default=None, max_length=20000)
    preferred_requirements: str | None = Field(default=None, max_length=20000)
    required_documents: list[str] | None = Field(default=None, max_length=30)
    opening_date: date | None = None
    closing_date: date | None = None

class HRApplicationStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=80)
    reason: str | None = Field(default=None, max_length=3000)

class HRDocumentReview(BaseModel):
    review_status: str = Field(min_length=2, max_length=30)
    review_notes: str | None = Field(default=None, max_length=3000)

class HRInterviewCreate(BaseModel):
    scheduled_at: datetime
    mode: str = Field(min_length=2, max_length=80)
    venue: str | None = Field(default=None, max_length=300)
    panel: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=5000)

class HRInterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    mode: str | None = Field(default=None, max_length=80)
    venue: str | None = Field(default=None, max_length=300)
    panel: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=5000)
    outcome: str | None = Field(default=None, max_length=80)

class HROfferCreate(BaseModel):
    start_date: date | None = None
    employment_type: str | None = Field(default=None, max_length=80)
    offer_summary: str = Field(min_length=5, max_length=10000)

class HROfferUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=30)
    response_notes: str | None = Field(default=None, max_length=5000)

class HRHireRequest(BaseModel):
    start_date: date
    employment_type: str | None = Field(default=None, max_length=80)


class HREmploymentUpdate(BaseModel):
    job_title: str | None = Field(
        default=None,
        max_length=200,
    )
    department: str | None = Field(
        default=None,
        max_length=150,
    )
    employment_type: str | None = Field(
        default=None,
        max_length=80,
    )
    employment_status: str | None = Field(
        default=None,
        max_length=80,
    )

