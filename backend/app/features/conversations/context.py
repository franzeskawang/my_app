"""Shared formatting for a stored conversation summary and its recent messages."""


def format_conversation_context(summary: str, messages: list[dict[str, str]]) -> str:
    """Render reusable context; task-specific instructions belong in each app prompt."""
    history = "\n".join(
        f"{message['role']}: {message['content']}" for message in messages
    )
    return (
        "使用者目前的狀況摘要：\n"
        f"{summary or '（尚無摘要）'}\n\n"
        "最近對話：\n"
        f"{history or '（尚無近期對話）'}"
    )
