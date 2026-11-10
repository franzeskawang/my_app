"""Composition root that wires application ports to concrete adapters."""
from ..features.conversations.service import ConversationService
from ..features.expenses.service import ExpenseService
from ..features.expenses.memory_manager import MemoryManager
from ..features.conversations.repository import ConversationRepository
from ..features.expenses.repository import ExpenseRepository
from ..integrations.gemini.llm_service import analyze_expenses, summarize_conversation

conversation_repository = ConversationRepository()
expense_repository = ExpenseRepository()

conversation_service = ConversationService(conversation_repository)
bookkeeping_memory = MemoryManager(summarize_conversation, conversation_repository)
expense_service = ExpenseService(expense_repository, bookkeeping_memory, analyze_expenses)
