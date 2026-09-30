from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


ApplicationOutcome = Literal[
    "Accepted",
    "Rejected",
    "Outstanding Documents",
]

DocumentReviewAction = Literal[
    "Approved",
    "Rejected",
    "Resubmission Required",
]


class DocumentReviewRequest(BaseModel):
    action: DocumentReviewAction
    review_notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class OutstandingDocumentItem(BaseModel):
    document_type: str = Field(
        min_length=1,
        max_length=100,
    )
    document_label: str = Field(
        min_length=1,
        max_length=200,
    )
    reason: str | None = Field(
        default=None,
        max_length=2000,
    )
    instructions: str | None = Field(
        default=None,
        max_length=3000,
    )
    due_date: date | None = None
    is_required: bool = True


class OutstandingDocumentsRequest(BaseModel):
    documents: list[OutstandingDocumentItem] = Field(
        min_length=1,
    )


class AcceptApplicationRequest(BaseModel):
    funding_type: str | None = Field(
        default=None,
        max_length=100,
    )
    cycle_code: str | None = Field(
        default=None,
        max_length=100,
    )
    program_start_date: date | None = None
    expected_completion_date: date | None = None
    enforce_documents: bool = True


class RejectApplicationRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=3000,
    )


class RegistrationRetryRequest(BaseModel):
    funding_type: str | None = Field(
        default=None,
        max_length=100,
    )
    cycle_code: str | None = Field(
        default=None,
        max_length=100,
    )
    program_start_date: date | None = None
    expected_completion_date: date | None = None
