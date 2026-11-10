"""Application workflows for expense submissions, dashboards, and deletion."""
import json
import logging
import os
from collections.abc import Callable
from datetime import date
from typing import Protocol

from .schemas import Dashboard, ExpenseCategory, Submission

logger = logging.getLogger(__name__)
FALLBACK_ADVICE = "本次 AI 分析暫時無法使用，記帳已保存。請檢查後端 API 金鑰與網路連線後重試分析。"


class ExpensePersistenceError(RuntimeError):
    """Raised when an expense submission cannot be stored."""


class ExpenseStore(Protocol):
    def get_dashboard(self, today: date) -> dict: ...
    def get_totals(self, today: date) -> tuple[float, float]: ...
    def create_expenses(self, expenses: list[dict], categories: dict[int, str], comment: str) -> list[int]: ...
    def delete_expense(self, expense_id: int) -> bool: ...


class BookkeepingMemory(Protocol):
    def prepare_context(self, latest_message: str) -> dict: ...
    def save_turn(self, user_message: str, assistant_message: str) -> None: ...


def _missing_analyzer(*args, **kwargs):
    raise RuntimeError("Expense analyzer is not configured")


class ExpenseService:
    def __init__(
        self,
        expenses: ExpenseStore,
        memory: BookkeepingMemory,
        analyzer: Callable | None = None,
    ):
        self.expenses = expenses
        self.memory = memory
        self.analyzer = analyzer or _missing_analyzer

    def get_dashboard(self) -> Dashboard:
        return Dashboard(**self.expenses.get_dashboard(date.today()))

    def create_expenses(self, submission: Submission) -> dict:
        expense_data = [expense.model_dump(mode="json") for expense in submission.expenses]
        logger.info("Starting expense submission with %d entries", len(expense_data))
        today = date.today()
        prior_today, prior_month = self.expenses.get_totals(today)
        today_total = prior_today + sum(
            expense.amount for expense in submission.expenses if expense.spent_on == today
        )
        month_total = prior_month + sum(
            expense.amount for expense in submission.expenses
            if expense.spent_on.strftime("%Y-%m") == today.strftime("%Y-%m")
        )
        memory_user_message = json.dumps(
            {"comment": submission.comment, "expenses": expense_data},
            ensure_ascii=False,
        )

        try:
            context = self.memory.prepare_context(memory_user_message)
        except Exception as exc:
            logger.warning(
                "Could not prepare conversation memory (%s); continuing without history",
                type(exc).__name__,
            )
            context = {"summary": "", "messages": []}

        try:
            logger.info("Starting Gemini expense analysis")
            analysis = self.analyzer(
                expense_data,
                submission.comment,
                today_total,
                month_total,
                memory_summary=context["summary"],
                history=context["messages"],
            )
            categories = {
                item.index: item.category.value for item in analysis.classifications
            }
            advice = analysis.advice
            ai_available = True
            logger.info("Gemini expense analysis completed")
        except Exception as exc:
            categories = {
                index: ExpenseCategory.DAILY.value for index in range(len(expense_data))
            }
            advice = FALLBACK_ADVICE
            ai_available = False
            error = f"{type(exc).__name__}: {exc}"
            api_key = os.getenv("GEMINI_API_KEY", "")
            if api_key:
                error = error.replace(api_key, "[金鑰已隱藏]")
            error = error[:500]

        try:
            ids = self.expenses.create_expenses(expense_data, categories, submission.comment)
        except Exception as exc:
            raise ExpensePersistenceError(f"記帳儲存失敗：{exc}") from exc

        try:
            self.memory.save_turn(memory_user_message, advice)
        except Exception as exc:
            logger.warning("Could not save conversation memory (%s)", type(exc).__name__)

        return {
            "saved": len(expense_data),
            "ids": ids,
            "advice": advice,
            "ai_available": ai_available,
            **({"ai_error": error} if not ai_available else {}),
        }

    def delete_expense(self, expense_id: int) -> bool:
        return self.expenses.delete_expense(expense_id)
