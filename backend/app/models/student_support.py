from typing import Literal

from pydantic import BaseModel, Field

SupportCategory = Literal[
    "Login",
    "PasswordPIN",
    "Portal",
    "Documents",
    "StudentCard",
    "MobileApp",
    "DesktopApp",
    "TechnicalError",
    "Other",
]


SupportPriority = Literal[
    "Normal",
    "High",
    "Urgent",
]


class StudentSupportTicketCreate(BaseModel):

    category: SupportCategory

    subject: str = Field(
        ...,
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        ...,
        min_length=5,
        max_length=5000,
    )

    priority: SupportPriority = "Normal"


class StudentSupportReply(BaseModel):

    message: str = Field(
        ...,
        min_length=2,
        max_length=5000,
    )