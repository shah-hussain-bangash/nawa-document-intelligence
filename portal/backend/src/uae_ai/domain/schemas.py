from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DemoLogin(StrictModel):
    role: Literal["analyst", "reviewer", "requester", "auditor", "admin"] = "analyst"
    tenant: Literal["operations", "research"] = "operations"


class Quote(StrictModel):
    supplier: str = Field(min_length=2, max_length=120)
    amount: Decimal = Field(gt=0, le=100_000_000, max_digits=14, decimal_places=2)
    currency: Literal["AED", "USD", "EUR"] = "AED"
    delivery_days: int = Field(ge=0, le=730)
    valid_until: date
    document_id: str = Field(min_length=1, max_length=50)
    source_version: int | None = Field(default=None, ge=1)
    review_id: str | None = Field(default=None, max_length=50)
    tax_percent: Decimal = Field(default=Decimal("5"), ge=0, le=100, decimal_places=2)


class CaseCreate(StrictModel):
    title: str = Field(min_length=4, max_length=200)
    description: str = Field(default="", max_length=4000)
    department: str = Field(min_length=2, max_length=100)
    budget: Decimal = Field(gt=0, le=100_000_000, max_digits=14, decimal_places=2)
    currency: Literal["AED", "USD", "EUR"] = "AED"
    due_date: date
    priority: Literal["Normal", "High", "Urgent"] = "Normal"
    document_ids: list[str] = Field(default_factory=list, max_length=30)
    quotes: list[Quote] = Field(default_factory=list, max_length=20)


class CaseEdit(StrictModel):
    expected_revision: int = Field(ge=1)
    document_ids: list[str] = Field(max_length=30)
    quotes: list[Quote] = Field(max_length=20)


class Decision(StrictModel):
    expected_revision: int = Field(ge=1)
    decision: Literal["approve", "reject", "request_changes"]
    reason: str = Field(min_length=5, max_length=2000)


class Question(StrictModel):
    question: str = Field(min_length=3, max_length=1500)
    domain: Literal["all", "procurement", "hr", "service"] = "all"


class TicketCreate(StrictModel):
    title: str = Field(min_length=5, max_length=200)
    category: Literal["IT support", "Access request", "Facilities", "HR enquiry"]
    priority: Literal["Normal", "High", "Urgent"] = "Normal"


class TicketUpdate(StrictModel):
    status: Literal["Open", "In progress", "Resolved"]


class Preferences(StrictModel):
    language: Literal["en", "ar"] = "en"
    digest: bool = True



class QuotationDraftRequest(StrictModel):
    expected_version: int = Field(ge=1)


class ReviewValues(StrictModel):
    supplier: str | None = Field(default=None, min_length=2, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0, le=100_000_000, decimal_places=2)
    currency: Literal['AED','USD','EUR'] | None = None
    tax_percent: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    delivery_days: int | None = Field(default=None, ge=0, le=730)
    valid_until: date | None = None


class ExtractionReviewRequest(StrictModel):
    values: ReviewValues
    reason: str = Field(min_length=5, max_length=2000)
