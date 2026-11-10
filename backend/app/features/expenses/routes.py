"""Expense HTTP endpoints; request and response shapes are defined by API schemas."""
from fastapi import APIRouter, Depends, HTTPException

from ...api.dependencies import get_expense_service
from ...api.schemas import ApiErrorResponse
from .schemas import (
    Dashboard,
    DeleteExpenseResponse,
    ExpenseSubmissionResponse,
    Submission,
)
from .service import ExpensePersistenceError, ExpenseService

router = APIRouter(prefix="/api")


@router.get("/dashboard", response_model=Dashboard)
def dashboard(service: ExpenseService = Depends(get_expense_service)) -> Dashboard:
    return service.get_dashboard()


@router.post(
    "/expenses",
    response_model=ExpenseSubmissionResponse,
    response_model_exclude_none=True,
    responses={500: {"model": ApiErrorResponse}},
)
def create_expenses(
    submission: Submission,
    service: ExpenseService = Depends(get_expense_service),
) -> dict:
    try:
        return service.create_expenses(submission)
    except ExpensePersistenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete(
    "/expenses/{expense_id}",
    response_model=DeleteExpenseResponse,
    responses={404: {"model": ApiErrorResponse}},
)
def delete_expense(
    expense_id: int,
    service: ExpenseService = Depends(get_expense_service),
) -> DeleteExpenseResponse:
    if not service.delete_expense(expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")
    return DeleteExpenseResponse(deleted=expense_id)
