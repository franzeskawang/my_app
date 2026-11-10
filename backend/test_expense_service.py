"""Unit tests for expense submission, dashboard, deletion, and AI fallback workflows."""
import unittest
from datetime import date

from app.features.expenses.service import ExpensePersistenceError, ExpenseService, FALLBACK_ADVICE
from app.features.expenses.schemas import (
    ClassifiedExpense, ExpenseAnalysis, ExpenseCategory, ExpenseInput, Submission,
)


class FakeExpenseRepository:
    def __init__(self):
        self.saved = None
        self.deleted_id = None
        self.dashboard = {
            "today": 12.0, "this_month": 34.0, "big_boss": 20.0, "daily": 14.0,
            "expenses": [],
        }

    def get_dashboard(self, today):
        return self.dashboard

    def get_totals(self, today):
        return 10.0, 25.0

    def create_expenses(self, expenses, categories, comment):
        self.saved = (expenses, categories, comment)
        return [101]

    def delete_expense(self, expense_id):
        self.deleted_id = expense_id
        return expense_id == 101


class FakeMemoryManager:
    def __init__(self):
        self.saved_turn = None

    def prepare_context(self, latest_message):
        return {"summary": "existing summary", "messages": [{"role": "user", "content": "prior"}]}

    def save_turn(self, user_message, assistant_message):
        self.saved_turn = (user_message, assistant_message)


class ExpenseServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = FakeExpenseRepository()
        self.memory = FakeMemoryManager()
        self.submission = Submission(
            expenses=[ExpenseInput(item="Lunch", amount=100, spent_on=date.today())],
            comment="A quick lunch",
        )

    def test_successful_submission_uses_context_and_persists_analysis(self):
        captured = {}

        def analyzer(expenses, comment, today_total, month_total, **context):
            captured.update({"today_total": today_total, "month_total": month_total, **context})
            return ExpenseAnalysis(
                classifications=[ClassifiedExpense(index=0, category=ExpenseCategory.DAILY)],
                advice="Keep tracking lunch costs.",
            )

        service = ExpenseService(self.repository, self.memory, analyzer)
        result = service.create_expenses(self.submission)
        self.assertEqual(result["ids"], [101])
        self.assertTrue(result["ai_available"])
        self.assertEqual(result["saved"], 1)
        self.assertEqual(captured["today_total"], 110.0)
        self.assertEqual(captured["month_total"], 125.0)
        self.assertEqual(captured["memory_summary"], "existing summary")
        self.assertEqual(self.repository.saved[1], {0: ExpenseCategory.DAILY.value})
        self.assertEqual(self.memory.saved_turn[1], "Keep tracking lunch costs.")

    def test_ai_failure_falls_back_and_still_saves_expenses(self):
        def failing_analyzer(*args, **kwargs):
            raise RuntimeError("temporary Gemini failure")

        service = ExpenseService(self.repository, self.memory, failing_analyzer)
        result = service.create_expenses(self.submission)
        self.assertFalse(result["ai_available"])
        self.assertEqual(result["advice"], FALLBACK_ADVICE)
        self.assertEqual(self.repository.saved[1], {0: ExpenseCategory.DAILY.value})
        self.assertIn("ai_error", result)
        self.assertEqual(self.memory.saved_turn[1], FALLBACK_ADVICE)

    def test_dashboard_returns_existing_contract(self):
        result = ExpenseService(self.repository, self.memory).get_dashboard()
        self.assertEqual(result.model_dump()["this_month"], 34.0)
        self.assertEqual(result.model_dump()["expenses"], [])

    def test_delete_returns_not_found_state_to_route(self):
        service = ExpenseService(self.repository, self.memory)
        self.assertFalse(service.delete_expense(999))
        self.assertEqual(self.repository.deleted_id, 999)

    def test_expense_persistence_error_is_a_service_boundary(self):
        def failing_create(*args, **kwargs):
            raise OSError("database unavailable")

        self.repository.create_expenses = failing_create
        service = ExpenseService(
            self.repository,
            self.memory,
            lambda *args, **kwargs: ExpenseAnalysis(
                classifications=[ClassifiedExpense(index=0, category=ExpenseCategory.DAILY)],
                advice="Advice",
            ),
        )
        with self.assertRaises(ExpensePersistenceError):
            service.create_expenses(self.submission)


if __name__ == "__main__":
    unittest.main()
