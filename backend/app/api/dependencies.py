"""FastAPI dependency providers for application services."""
from ..application.container import conversation_service, expense_service


def get_expense_service():
    return expense_service


def get_conversation_service():
    return conversation_service
