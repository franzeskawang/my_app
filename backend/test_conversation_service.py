"""Tests for the reusable conversation service and prompt-context formatter."""
import unittest

from app.features.conversations.context import format_conversation_context
from app.features.conversations.service import ConversationService


class FakeConversationStore:
    def __init__(self):
        self.summary = "shared summary"
        self.messages = [
            {"id": index, "role": "user" if index % 2 else "assistant", "content": f"message {index}"}
            for index in range(1, 9)
        ]
        self.saved = None
        self.conversation = None

    def ensure_conversation(self, conversation_id, owner_id, source_app_id):
        self.conversation = (conversation_id, owner_id, source_app_id)

    def load_context(self, conversation_id, owner_id):
        return self.summary, self.messages

    def save_turn(self, user_message, assistant_message, conversation_id, source_app_id, owner_id):
        self.saved = (user_message, assistant_message, conversation_id, source_app_id, owner_id)

    def update_summary(self, summary, message_ids, conversation_id, owner_id):
        raise NotImplementedError


class ConversationServiceTests(unittest.TestCase):
    def test_context_is_structured_and_limited_to_requested_recent_turns(self):
        store = FakeConversationStore()
        service = ConversationService(store)

        context = service.get_context("shared-thread", "user-1", "travel-app", max_turns=2)

        self.assertEqual(context["summary"], "shared summary")
        self.assertEqual([message["content"] for message in context["messages"]], [
            "message 5", "message 6", "message 7", "message 8",
        ])
        self.assertEqual(store.conversation, ("shared-thread", "user-1", "travel-app"))

    def test_turn_is_saved_with_conversation_and_source_app(self):
        store = FakeConversationStore()
        ConversationService(store).append_turn(
            "question", "answer", "shared-thread", "user-1", "travel-app"
        )
        self.assertEqual(store.saved, (
            "question", "answer", "shared-thread", "travel-app", "user-1",
        ))

    def test_prompt_context_format_can_be_reused_by_each_app(self):
        rendered = format_conversation_context(
            "prefers concise answers",
            [{"role": "user", "content": "recent question"}],
        )
        self.assertIn("prefers concise answers", rendered)
        self.assertIn("user: recent question", rendered)
        self.assertIn("使用者目前的狀況摘要", rendered)


if __name__ == "__main__":
    unittest.main()
