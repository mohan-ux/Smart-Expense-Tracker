from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=12)
    category: str = Field(min_length=1)
    date: date

    @field_validator("title", "category")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class Expense(ExpenseCreate):
    id: int


class CategoryTotal(BaseModel):
    category: str
    total: Decimal


class TotalsResponse(BaseModel):
    overall_total: Decimal
    by_category: list[CategoryTotal]
