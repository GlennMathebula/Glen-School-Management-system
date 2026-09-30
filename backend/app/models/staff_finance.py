from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class FinanceChargeCreate(BaseModel):
    charge_type: str = Field(
        min_length=2,
        max_length=30,
    )
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
    )
    description: str = Field(
        min_length=2,
        max_length=500,
    )
    due_date: date | None = None


class FinancePaymentCreate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
    )
    method: str = Field(
        min_length=2,
        max_length=50,
    )
    reference: str | None = Field(
        default=None,
        max_length=150,
    )
    invoice_number: str | None = Field(
        default=None,
        max_length=80,
    )


class FinancePaymentReverse(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class FinanceCreditCreate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
    )
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class FinancePaymentPlanCreate(BaseModel):
    plan_months: int = Field(
        ge=1,
        le=36,
    )
    deposit: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
    )
    interest_rate: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        decimal_places=2,
    )
    start_date: date | None = None


class FinanceSponsorCreate(BaseModel):
    sponsor_name: str = Field(
        min_length=2,
        max_length=200,
    )
    sponsor_type: str = Field(
        min_length=2,
        max_length=50,
    )
    approval_number: str | None = Field(
        default=None,
        max_length=150,
    )
    approved_amount: Decimal = Field(
        gt=0,
        decimal_places=2,
    )


class FinanceSponsorAssign(BaseModel):
    sponsor_id: str = Field(
        min_length=3,
        max_length=80,
    )
    amount_covered: Decimal = Field(
        gt=0,
        decimal_places=2,
    )
    reference: str | None = Field(
        default=None,
        max_length=150,
    )
