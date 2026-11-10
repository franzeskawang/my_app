"""SQLite repository tests using an isolated temporary database."""
import tempfile
import sqlite3
from contextlib import closing
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app.infrastructure.sqlite import database
from app.features.expenses.repository import ExpenseRepository
from app.features.conversations.repository import ConversationRepository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(database, "DB_PATH", Path(self.temp_dir.name) / "test.db")
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.temp_dir.cleanup)
        database.initialize()
        self.expenses = ExpenseRepository()
        self.memory = ConversationRepository()

    def test_expense_repository_writes_calculates_and_deletes(self):
        today = date.today()
        records = [
            {"item": "Rent", "amount": 500, "spent_on": today.isoformat()},
            {"item": "Lunch", "amount": 100, "spent_on": today.isoformat()},
        ]
        ids = self.expenses.create_expenses(
            records,
            {0: "大魔王支出", 1: "日常支出"},
            "Monthly expenses",
        )
        self.assertEqual(len(ids), 2)
        self.assertEqual(self.expenses.get_totals(today), (600.0, 600.0))
        dashboard = self.expenses.get_dashboard(today)
        self.assertEqual(dashboard["today"], 600.0)
        self.assertEqual(dashboard["big_boss"], 500.0)
        self.assertEqual(dashboard["daily"], 100.0)
        self.assertTrue(self.expenses.delete_expense(ids[1]))
        self.assertFalse(self.expenses.delete_expense(ids[1]))
        self.assertEqual(self.expenses.get_totals(today), (500.0, 500.0))

    def test_memory_repository_round_trip_and_summary_compaction(self):
        self.memory.save_turn("user one", "assistant one")
        self.memory.save_turn("user two", "assistant two")
        summary, messages = self.memory.load_context()
        self.assertEqual(summary, "")
        self.assertEqual(len(messages), 4)
        self.memory.update_summary("financial summary", [messages[0]["id"], messages[1]["id"]])
        summary, messages = self.memory.load_context()
        self.assertEqual(summary, "financial summary")
        self.assertEqual([message["content"] for message in messages], ["user two", "assistant two"])

    def test_reinitialization_preserves_existing_expense_data(self):
        today = date.today()
        self.expenses.create_expenses(
            [{"item": "Coffee", "amount": 80, "spent_on": today.isoformat()}],
            {0: "日常支出"},
            "Existing entry",
        )
        database.initialize()
        self.assertEqual(self.expenses.get_totals(today), (80.0, 80.0))

    def test_conversation_repository_isolates_threads_and_records_source_app(self):
        conversations = ConversationRepository()
        conversations.save_turn("finance question", "finance answer", "finance", "finance-app")
        conversations.save_turn("bookkeeping question", "bookkeeping answer", "bookkeeping-app", "bookkeeping-app")

        finance_summary, finance_messages = conversations.load_context("finance")
        bookkeeping_summary, bookkeeping_messages = conversations.load_context("bookkeeping-app")
        self.assertEqual(finance_summary, "")
        self.assertEqual([message["content"] for message in finance_messages], [
            "finance question", "finance answer",
        ])
        self.assertEqual({message["source_app_id"] for message in finance_messages}, {"finance-app"})
        self.assertEqual(bookkeeping_summary, "")
        self.assertEqual([message["content"] for message in bookkeeping_messages], [
            "bookkeeping question", "bookkeeping answer",
        ])

    def test_conversation_repository_rejects_a_different_owner(self):
        conversations = ConversationRepository()
        conversations.save_turn("private question", "private answer", "private-thread", owner_id="user-1")
        with self.assertRaises(PermissionError):
            conversations.load_context("private-thread", owner_id="user-2")

    def test_initialize_migrates_legacy_global_conversation_without_losing_messages(self):
        legacy_path = Path(self.temp_dir.name) / "legacy.db"
        with patch.object(database, "DB_PATH", legacy_path):
            with closing(sqlite3.connect(legacy_path)) as db, db:
                db.execute("CREATE TABLE conversation_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')))")
                db.execute("CREATE TABLE conversation_memory (id INTEGER PRIMARY KEY CHECK(id = 1), summary TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT (datetime('now')))")
                db.execute("INSERT INTO conversation_messages(role, content) VALUES ('user', 'legacy user')")
                db.execute("INSERT INTO conversation_messages(role, content) VALUES ('assistant', 'legacy answer')")
                db.execute("INSERT INTO conversation_memory(id, summary) VALUES (1, 'legacy summary')")
            database.initialize()
            summary, messages = ConversationRepository().load_context()
        self.assertEqual(summary, "legacy summary")
        self.assertEqual([message["content"] for message in messages], ["legacy user", "legacy answer"])
        self.assertTrue(all(message["conversation_id"] == "bookkeeping-default" for message in messages))


if __name__ == "__main__":
    unittest.main()
