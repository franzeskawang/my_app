"""Bookkeeping-specific summary policy layered on the reusable conversation service."""
import logging
import math
import os
import re
from collections.abc import Callable

from ..conversations.service import ConversationService, ConversationStore
from ...constants import DEFAULT_CONVERSATION_ID, DEFAULT_OWNER_ID, DEFAULT_SOURCE_APP_ID

logger = logging.getLogger(__name__)


def _positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def estimate_tokens(text: str) -> int:
    """Conservative local estimate: CJK characters count individually, Latin words by 4 chars."""
    cjk = sum(1 for char in text if "\u3400" <= char <= "\u9fff")
    remainder = re.sub(r"[\u3400-\u9fff]", " ", text)
    return cjk + math.ceil(len(remainder) / 4)


class MemoryManager:
    """Apply bookkeeping summary/window rules without owning conversation storage."""

    def __init__(
        self,
        summarizer: Callable[[str, list[dict[str, str]]], str],
        repository: ConversationStore,
        conversation_id: str = DEFAULT_CONVERSATION_ID,
        owner_id: str = DEFAULT_OWNER_ID,
        source_app_id: str = DEFAULT_SOURCE_APP_ID,
    ):
        self.max_turns = _positive_int("MEMORY_MAX_TURNS", 5)
        self.summary_max_messages = _positive_int("MEMORY_SUMMARY_MAX_MESSAGES", 20)
        self.summary_max_tokens = _positive_int("MEMORY_SUMMARY_MAX_TOKENS", 8000)
        self.keep_turns = 2
        self.summarizer = summarizer
        self.repository = repository
        self.conversations = ConversationService(self.repository)
        self.conversation_id = conversation_id
        self.owner_id = owner_id
        self.source_app_id = source_app_id

    def prepare_context(self, latest_message: str) -> dict:
        """Summarize old bookkeeping messages while retaining the latest two old turns."""
        # Read all persisted messages for thresholding and compaction; the public reusable
        # ConversationService returns a bounded context window to downstream consumers.
        self.repository.ensure_conversation(
            self.conversation_id, self.owner_id, self.source_app_id
        )
        summary, rows = self.repository.load_context(self.conversation_id, self.owner_id)
        total_tokens = estimate_tokens(
            summary + latest_message + "".join(message["content"] for message in rows)
        )
        should_summarize = (
            len(rows) + 1 > self.summary_max_messages
            or total_tokens > self.summary_max_tokens
        )
        summarize_count = max(0, len(rows) - self.keep_turns * 2)
        summarize_count -= summarize_count % 2
        if should_summarize and summarize_count:
            old_messages = rows[:summarize_count]
            logger.info("Starting conversation summary for %d older messages", summarize_count)
            new_summary = self.summarizer(summary, old_messages).strip()
            if not new_summary:
                raise RuntimeError("AI 沒有產生有效的對話摘要")
            self.repository.update_summary(
                new_summary,
                [message["id"] for message in old_messages],
                self.conversation_id,
                self.owner_id,
            )
            summary = new_summary
            rows = rows[summarize_count:]
            logger.info("Conversation summary completed")

        return {"summary": summary, "messages": rows[-self.max_turns * 2:]}

    def save_turn(self, user_message: str, assistant_message: str) -> None:
        """Persist this bookkeeping turn through the common conversation service."""
        self.conversations.append_turn(
            user_message,
            assistant_message,
            conversation_id=self.conversation_id,
            owner_id=self.owner_id,
            source_app_id=self.source_app_id,
        )
