"""FastAPI composition root: middleware, startup, and HTTP router registration."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .features.conversations.routes import router as conversation_router
from .features.expenses.routes import router as expense_router
from .api.schemas import HealthResponse
from .infrastructure.sqlite.database import initialize

app = FastAPI(title="記帳小幫手 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    initialize()


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)


app.include_router(expense_router)
app.include_router(conversation_router)
