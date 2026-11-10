"""Request and response schemas for conversation context APIs."""
from typing import Literal
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """A completed turn submitted by a trusted app backend."""
    user_message: str = Field(min_length=1, max_length=8000)
    assistant_message: str = Field(min_length=1, max_length=8000)


class ConversationMessage(BaseModel):
    id: int
    conversation_id: str
    source_app_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class ConversationContextResponse(BaseModel):
    summary: str
    messages: list[ConversationMessage]
