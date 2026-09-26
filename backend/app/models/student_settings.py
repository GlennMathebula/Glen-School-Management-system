from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class StudentContactUpdate(BaseModel):

    email: EmailStr | None = None

    phone_number: str | None = Field(
        default=None,
        max_length=50,
    )

    cell_number: str | None = Field(
        default=None,
        max_length=50,
    )

    home_addr_1: str | None = Field(
        default=None,
        max_length=255,
    )

    home_addr_2: str | None = Field(
        default=None,
        max_length=255,
    )

    home_addr_3: str | None = Field(
        default=None,
        max_length=255,
    )

    home_postal_code: str | None = Field(
        default=None,
        max_length=20,
    )

    postal_addr_1: str | None = Field(
        default=None,
        max_length=255,
    )

    postal_addr_2: str | None = Field(
        default=None,
        max_length=255,
    )

    postal_addr_3: str | None = Field(
        default=None,
        max_length=255,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )


class StudentPreferenceUpdate(BaseModel):

    preferred_notification_channel: Literal[
        "Portal",
        "Email",
    ]

    preferred_language: str | None = Field(
        default=None,
        max_length=50,
    )