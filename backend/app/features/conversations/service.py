"""Provider-neutral conversation operations used by app workflows and API routes."""
from typing import Protocol

from ...constants import DEFAULT_CONVERSATION_ID, DEFAULT_OWNER_ID, DEFAULT_SOURCE_APP_ID


class ConversationStore(Protocol):
    """Storage contract; services do not need to know which database implements it."""

    def ensure_conversation(
        self, conversation_id: str, owner_id: str, source_app_id: str
    ) -> None: ...

    def load_context(
        self, conversation_id: str, owner_id: str
    ) -> tuple[str, list[dict]]: ...

    def save_turn(
        self,
        user_message: str,
        assistant_message: str,
        conversation_id: str,
        source_app_id: str,
        owner_id: str,
    ) -> None: ...

    def update_summary(
        self,
        summary: str,
        message_ids: list[int],
        conversation_id: str,
        owner_id: str,
    ) -> None: ...


class ConversationService:
    """Expose a small, reusable conversation interface independent of HTTP and LLMs."""

    def __init__(self, store: ConversationStore):
        self.store = store

    def get_context(
        self,
        conversation_id: str = DEFAULT_CONVERSATION_ID,
        owner_id: str = DEFAULT_OWNER_ID,
        source_app_id: str = DEFAULT_SOURCE_APP_ID,
        max_turns: int = 5,
    ) -> dict:
        self.store.ensure_conversation(conversation_id, owner_id, source_app_id)
        summary, messages = self.store.load_context(conversation_id, owner_id)
        return {"summary": summary, "messages": messages[-max(1, max_turns) * 2:]}

    def append_turn(
        self,
        user_message: str,
        assistant_message: str,
        conversation_id: str = DEFAULT_CONVERSATION_ID,
        owner_id: str = DEFAULT_OWNER_ID,
        source_app_id: str = DEFAULT_SOURCE_APP_ID,
    ) -> None:
        self.store.save_turn(
            user_message,
            assistant_message,
            conversation_id,
            source_app_id,
            owner_id,
        )
