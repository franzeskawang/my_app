"""Tests for public API route paths, delegation, and response behavior."""
import unittest
import os
from unittest.mock import patch

from fastapi import HTTPException

from app import main
from app.api import auth
from app.features.expenses import routes as expense_routes
from app.features.expenses.schemas import Dashboard, Submission


class FakeExpenseService:
    def __init__(self):
        self.submission = None
        self.deleted_id = None

    def get_dashboard(self):
        return Dashboard(today=1, this_month=2, big_boss=0, daily=2, expenses=[])

    def create_expenses(self, submission):
        self.submission = submission
        return {"saved": 1, "ids": [12], "advice": "Advice", "ai_available": True}

    def delete_expense(self, expense_id):
        self.deleted_id = expense_id
        return expense_id == 12


class ApiRouteTests(unittest.TestCase):
    def test_existing_paths_and_methods_remain_available(self):
        paths = main.app.openapi()["paths"]
        self.assertIn("get", paths["/api/dashboard"])
        self.assertIn("post", paths["/api/expenses"])
        self.assertIn("delete", paths["/api/expenses/{expense_id}"])
        self.assertIn("get", paths["/api/conversations/{conversation_id}/context"])
        self.assertIn("post", paths["/api/conversations/{conversation_id}/turns"])
        dashboard_schema = paths["/api/dashboard"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(dashboard_schema["$ref"], "#/components/schemas/Dashboard")

    def test_conversation_api_requires_a_configured_service_key(self):
        with patch.dict(os.environ, {"CONVERSATION_API_KEY": "trusted-secret"}):
            with self.assertRaises(HTTPException) as error:
                auth.require_conversation_api_key("wrong-secret")
            self.assertEqual(error.exception.status_code, 401)
            self.assertIsNone(auth.require_conversation_api_key("trusted-secret"))
        with patch.dict(os.environ, {"CONVERSATION_API_KEY": ""}):
            with self.assertRaises(HTTPException) as error:
                auth.require_conversation_api_key("anything")
            self.assertEqual(error.exception.status_code, 503)

    def test_routes_delegate_and_keep_response_shapes(self):
        service = FakeExpenseService()
        submission = Submission(
            expenses=[{"item": "Coffee", "amount": 50, "spent_on": "2026-11-10"}],
            comment="Morning coffee",
        )
        dashboard = expense_routes.dashboard(service)
        created = expense_routes.create_expenses(submission, service)
        deleted = expense_routes.delete_expense(12, service)
        self.assertEqual(dashboard.model_dump()["this_month"], 2)
        self.assertEqual(created["ids"], [12])
        self.assertIs(service.submission, submission)
        self.assertEqual(deleted.model_dump(), {"deleted": 12})
        self.assertEqual(service.deleted_id, 12)

    def test_delete_missing_record_still_returns_404(self):
        with self.assertRaises(HTTPException) as error:
            expense_routes.delete_expense(999, FakeExpenseService())
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
