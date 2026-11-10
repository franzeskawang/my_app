"""SQLite implementation of scoped conversation persistence."""
from contextlib import closing

from ...constants import (
    DEFAULT_CONVERSATION_ID,
    DEFAULT_OWNER_ID,
    DEFAULT_SOURCE_APP_ID,
)
from ...infrastructure.sqlite.database import connect


class ConversationRepository:
    """Persist conversation threads, summaries, and messages in SQLite."""

    def ensure_conversation(
        self,
        conversation_id: str,
        owner_id: str = DEFAULT_OWNER_ID,
        source_app_id: str = DEFAULT_SOURCE_APP_ID,
    ) -> None:
        with closing(connect()) as db, db:
            db.execute(
                "INSERT OR IGNORE INTO conversations(id, owner_id, created_by_app_id) VALUES (?, ?, ?)",
                (conversation_id, owner_id, source_app_id),
            )
            row = db.execute(
                "SELECT owner_id FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row is None or row["owner_id"] != owner_id:
                raise PermissionError("Conversation is not available to this owner")
            db.execute(
                "INSERT OR IGNORE INTO conversation_summaries(conversation_id, summary) VALUES (?, '')",
                (conversation_id,),
            )

    def load_context(
        self,
        conversation_id: str = DEFAULT_CONVERSATION_ID,
        owner_id: str = DEFAULT_OWNER_ID,
    ) -> tuple[str, list[dict]]:
        self.ensure_conversation(conversation_id, owner_id)
        with closing(connect()) as db, db:
            summary_row = db.execute(
                "SELECT summary FROM conversation_summaries WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            messages = [dict(row) for row in db.execute(
                "SELECT id, conversation_id, source_app_id, role, content, created_at "
                "FROM conversation_messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            ).fetchall()]
        return summary_row["summary"] if summary_row else "", messages

    def update_summary(
        self,
        summary: str,
        message_ids: list[int],
        conversation_id: str = DEFAULT_CONVERSATION_ID,
        owner_id: str = DEFAULT_OWNER_ID,
    ) -> None:
        self.ensure_conversation(conversation_id, owner_id)
        with closing(connect()) as db, db:
            db.execute(
                "UPDATE conversation_summaries SET summary = ?, updated_at = datetime('now') "
                "WHERE conversation_id = ?",
                (summary, conversation_id),
            )
            db.executemany(
                "DELETE FROM conversation_messages WHERE conversation_id = ? AND id = ?",
                [(conversation_id, message_id) for message_id in message_ids],
            )

    def save_turn(
        self,
        user_message: str,
        assistant_message: str,
        conversation_id: str = DEFAULT_CONVERSATION_ID,
        source_app_id: str = DEFAULT_SOURCE_APP_ID,
        owner_id: str = DEFAULT_OWNER_ID,
    ) -> None:
        self.ensure_conversation(conversation_id, owner_id, source_app_id)
        with closing(connect()) as db, db:
            db.executemany(
                "INSERT INTO conversation_messages(conversation_id, source_app_id, role, content) "
                "VALUES (?, ?, ?, ?)",
                [
                    (conversation_id, source_app_id, "user", user_message),
                    (conversation_id, source_app_id, "assistant", assistant_message),
                ],
            )
