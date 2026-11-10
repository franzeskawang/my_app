"""Schemas shared by the application-wide API endpoints."""
from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool


class ApiErrorResponse(BaseModel):
    # FastAPI uses a string for application errors and a list for validation errors.
    detail: str | list[dict[str, Any]]
