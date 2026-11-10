"""Tests for conversation windowing, summary thresholds, and memory retention."""
import os
import unittest
from unittest.mock import patch
from app.features.expenses.memory_manager import MemoryManager


class FakeMemoryRepository:
    def __init__(self):
        self.summary = ""
        self.messages = []
        self.next_id = 1

    def ensure_conversation(self, conversation_id, owner_id, source_app_id):
        return None

    def load_context(self, conversation_id="bookkeeping-default", owner_id="local-user"):
        return self.summary, [dict(message) for message in self.messages]

    def update_summary(self, summary, message_ids, conversation_id="bookkeeping-default", owner_id="local-user"):
        self.summary = summary
        removed = set(message_ids)
        self.messages = [message for message in self.messages if message["id"] not in removed]

    def save_turn(self, user_message, assistant_message, conversation_id="bookkeeping-default", source_app_id="bookkeeping", owner_id="local-user"):
        for role, content in (("user", user_message), ("assistant", assistant_message)):
            self.messages.append({"id": self.next_id, "role": role, "content": content})
            self.next_id += 1


class MemoryManagerTests(unittest.TestCase):
    def setUp(self):
        self.repository = FakeMemoryRepository()

    def add_turns(self, count):
        for index in range(count):
            self.repository.save_turn(f"user {index}", f"assistant {index}")

    def manager(self, summarize, **config):
        settings = {
            "MEMORY_MAX_TURNS": "5",
            "MEMORY_SUMMARY_MAX_MESSAGES": "20",
            "MEMORY_SUMMARY_MAX_TOKENS": "8000",
            **config,
        }
        with patch.dict(os.environ, settings):
            return MemoryManager(summarize, self.repository)

    def test_summarizes_older_messages_and_keeps_two_recent_turns(self):
        self.add_turns(10)
        captured = []
        manager = self.manager(lambda summary, messages: captured.append(messages) or "financial summary")
        context = manager.prepare_context("latest user message")
        self.assertEqual([message["content"] for message in captured[0]], [
            content for index in range(8) for content in (f"user {index}", f"assistant {index}")
        ])
        self.assertEqual(context["summary"], "financial summary")
        self.assertEqual([message["content"] for message in context["messages"]], [
            "user 8", "assistant 8", "user 9", "assistant 9",
        ])

    def test_token_threshold_triggers_summary(self):
        self.add_turns(3)
        manager = self.manager(
            lambda summary, messages: "summary",
            MEMORY_SUMMARY_MAX_MESSAGES="100",
            MEMORY_SUMMARY_MAX_TOKENS="1",
        )
        context = manager.prepare_context("new")
        self.assertEqual(context["summary"], "summary")
        self.assertEqual(len(context["messages"]), 4)

    def test_summary_failure_does_not_delete_old_messages(self):
        self.add_turns(10)

        def fail_summary(summary, messages):
            raise RuntimeError("provider unavailable")

        manager = self.manager(fail_summary)
        with self.assertRaises(RuntimeError):
            manager.prepare_context("latest")
        self.assertEqual(len(self.repository.messages), 20)

    def test_database_retains_unsummarized_turns_but_context_uses_five_turn_window(self):
        manager = self.manager(lambda summary, messages: "summary")
        for index in range(6):
            manager.save_turn(f"user {index}", f"assistant {index}")
        self.assertEqual(len(self.repository.messages), 12)
        context = manager.prepare_context("latest")
        self.assertEqual(len(context["messages"]), 10)
        self.assertEqual(context["messages"][0]["content"], "user 1")
        self.assertEqual(context["messages"][-1]["content"], "assistant 5")


if __name__ == "__main__":
    unittest.main()
