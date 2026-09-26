from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
)


class PayFastStartRequest(
    BaseModel
):

    amount: Decimal | None = Field(
        default=None,
        ge=Decimal("5.00"),
    )


class PayFastStartResponse(
    BaseModel
):

    payment_url: str

    fields: dict[str, str]

    merchant_payment_id: str

    amount: Decimal