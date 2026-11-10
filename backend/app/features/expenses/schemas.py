"""Request, response, and domain schemas for bookkeeping."""
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ExpenseCategory(str, Enum):
    BIG_BOSS = "大魔王支出"
    DAILY = "日常支出"


class ExpenseInput(BaseModel):
    item: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0, le=100_000_000)
    spent_on: date


class Submission(BaseModel):
    expenses: list[ExpenseInput] = Field(min_length=1, max_length=50)
    comment: str = Field(min_length=1, max_length=2000)

    @field_validator("comment")
    @classmethod
    def comment_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("請填寫一則留言")
        return value


class ExpenseSubmissionResponse(BaseModel):
    saved: int
    ids: list[int]
    advice: str
    ai_available: bool
    ai_error: str | None = None


class DeleteExpenseResponse(BaseModel):
    deleted: int


class ClassifiedExpense(BaseModel):
    index: int = Field(ge=0)
    category: ExpenseCategory


class ExpenseAnalysis(BaseModel):
    classifications: list[ClassifiedExpense]
    advice: str = Field(min_length=1, max_length=1500)


class ExpenseRecord(ExpenseInput):
    id: int
    category: ExpenseCategory
    comment: str
    created_at: str


class Dashboard(BaseModel):
    today: float
    this_month: float
    big_boss: float
    daily: float
    expenses: list[ExpenseRecord]
