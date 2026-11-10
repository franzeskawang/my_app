"""Authentication dependency for trusted backend-to-backend conversation calls."""
import hmac
import os
from fastapi import Header, HTTPException


def require_conversation_api_key(
    api_key: str | None = Header(default=None, alias="X-Conversation-API-Key"),
) -> None:
    expected_key = os.getenv("CONVERSATION_API_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=503, detail="Conversation API is not configured")
    if not api_key or not hmac.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid conversation API key")
