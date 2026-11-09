import os
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .database import connect, initialize
from .llm_service import analyze_expenses
from .schemas import Dashboard, ExpenseCategory, ExpenseRecord, Submission

load_dotenv()

app = FastAPI(title="記帳小幫手 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    initialize()


def _totals(today: str, month_prefix: str) -> tuple[float, float]:
    with connect() as db:
        today_total = db.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE spent_on = ?", (today,)).fetchone()[0]
        month_total = db.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE spent_on LIKE ?", (f"{month_prefix}%",)).fetchone()[0]
    return float(today_total), float(month_total)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/dashboard", response_model=Dashboard)
def dashboard() -> Dashboard:
    today = date.today()
    with connect() as db:
        row = db.execute("""
            SELECT
              COALESCE(SUM(CASE WHEN spent_on = ? THEN amount ELSE 0 END), 0) AS today,
              COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? THEN amount ELSE 0 END), 0) AS month,
              COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? AND category = ? THEN amount ELSE 0 END), 0) AS big_boss,
              COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? AND category = ? THEN amount ELSE 0 END), 0) AS daily
            FROM expenses
        """, (today.isoformat(), today.strftime("%Y-%m"), today.strftime("%Y-%m"), ExpenseCategory.BIG_BOSS.value,
              today.strftime("%Y-%m"), ExpenseCategory.DAILY.value)).fetchone()
        records = db.execute("SELECT * FROM expenses ORDER BY spent_on DESC, id DESC LIMIT 100").fetchall()
    return Dashboard(
        today=float(row["today"]), this_month=float(row["month"]), big_boss=float(row["big_boss"]), daily=float(row["daily"]),
        expenses=[ExpenseRecord(**dict(record)) for record in records],
    )


@app.post("/api/expenses", response_model=dict)
def create_expenses(submission: Submission) -> dict:
    expense_data = [expense.model_dump(mode="json") for expense in submission.expenses]
    # Prompt includes running totals after adding the submitted records.
    today = date.today()
    prior_today, prior_month = _totals(today.isoformat(), today.strftime("%Y-%m"))
    today_total = prior_today + sum(e.amount for e in submission.expenses if e.spent_on == today)
    month_total = prior_month + sum(e.amount for e in submission.expenses if e.spent_on.strftime("%Y-%m") == today.strftime("%Y-%m"))
    try:
        analysis = analyze_expenses(expense_data, submission.comment, today_total, month_total)
        categories = {item.index: item.category.value for item in analysis.classifications}
        advice = analysis.advice
        ai_available = True
    except Exception as exc:
        # Preserve the user's entries even if the optional AI service is unavailable.
        categories = {i: ExpenseCategory.DAILY.value for i in range(len(expense_data))}
        advice = "本次 AI 分析暫時無法使用，記帳已保存。請檢查後端 API 金鑰與網路連線後重試分析。"
        ai_available = False
        error = f"{type(exc).__name__}: {exc}"
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            error = error.replace(api_key, "[金鑰已隱藏]")
        error = error[:500]

    try:
        with connect() as db:
            ids = []
            for i, expense in enumerate(expense_data):
                cursor = db.execute(
                    "INSERT INTO expenses(item, amount, spent_on, category, comment) VALUES (?, ?, ?, ?, ?)",
                    (expense["item"], expense["amount"], expense["spent_on"], categories[i], submission.comment),
                )
                ids.append(cursor.lastrowid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"記帳儲存失敗：{exc}") from exc

    return {"saved": len(expense_data), "ids": ids, "advice": advice, "ai_available": ai_available,
            **({"ai_error": error} if not ai_available else {})}


@app.delete("/api/expenses/{expense_id}", response_model=dict)
def delete_expense(expense_id: int) -> dict:
    """Remove an expense so it no longer contributes to dashboard totals."""
    with connect() as db:
        cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
    return {"deleted": expense_id}
