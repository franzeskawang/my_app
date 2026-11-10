"""Trusted backend-to-backend endpoints for structured conversation context."""
import os
from fastapi import APIRouter, Depends, Header, HTTPException

from ...api.auth import require_conversation_api_key
from ...api.dependencies import get_conversation_service
from ...api.schemas import ApiErrorResponse
from .schemas import ConversationContextResponse, ConversationTurn
from .service import ConversationService

router = APIRouter(
    prefix="/api/conversations/{conversation_id}",
    dependencies=[Depends(require_conversation_api_key)],
)


def _max_turns() -> int:
    try:
        return max(1, int(os.getenv("MEMORY_MAX_TURNS", "5")))
    except ValueError:
        return 5


@router.get(
    "/context",
    response_model=ConversationContextResponse,
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}, 503: {"model": ApiErrorResponse}},
)
def get_conversation_context(
    conversation_id: str,
    source_app_id: str = Header(alias="X-Source-App", min_length=1, max_length=64),
    service: ConversationService = Depends(get_conversation_service),
) -> dict:
    try:
        return service.get_context(
            conversation_id=conversation_id,
            source_app_id=source_app_id,
            max_turns=_max_turns(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc


@router.post(
    "/turns",
    status_code=204,
    responses={401: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}, 503: {"model": ApiErrorResponse}},
)
def append_conversation_turn(
    conversation_id: str,
    turn: ConversationTurn,
    source_app_id: str = Header(alias="X-Source-App", min_length=1, max_length=64),
    service: ConversationService = Depends(get_conversation_service),
) -> None:
    try:
        service.append_turn(
            turn.user_message,
            turn.assistant_message,
            conversation_id=conversation_id,
            source_app_id=source_app_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found") from exc
