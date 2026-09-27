from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)


class StaffNotificationCreate(
    BaseModel
):
    recipient_staff_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    notification_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    priority: str = Field(
        default="Normal",
        pattern=(
            "^(Normal|Important|Urgent)$"
        ),
    )

    action_url: str | None = None

    metadata: dict = Field(
        default_factory=dict
    )

    show_desktop_popup: bool = True

    expires_at: datetime | None = None


class StaffNotificationReadUpdate(
    BaseModel
):
    is_read: bool = True


class StaffNotificationPopupDelivered(
    BaseModel
):
    delivered: bool = True