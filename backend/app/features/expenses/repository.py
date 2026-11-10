"""SQLite data access for expense records and dashboard totals."""
from contextlib import closing
from datetime import date

from ...infrastructure.sqlite.database import connect


class ExpenseRepository:
    def get_dashboard(self, today: date) -> dict:
        month = today.strftime("%Y-%m")
        with closing(connect()) as db, db:
            totals = db.execute("""
                SELECT
                  COALESCE(SUM(CASE WHEN spent_on = ? THEN amount ELSE 0 END), 0) AS today,
                  COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? THEN amount ELSE 0 END), 0) AS this_month,
                  COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? AND category = '大魔王支出' THEN amount ELSE 0 END), 0) AS big_boss,
                  COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? AND category = '日常支出' THEN amount ELSE 0 END), 0) AS daily
                FROM expenses
            """, (today.isoformat(), month, month, month)).fetchone()
            records = db.execute(
                "SELECT * FROM expenses ORDER BY spent_on DESC, id DESC LIMIT 100"
            ).fetchall()
        return {
            "today": float(totals["today"]),
            "this_month": float(totals["this_month"]),
            "big_boss": float(totals["big_boss"]),
            "daily": float(totals["daily"]),
            "expenses": [dict(record) for record in records],
        }

    def get_totals(self, today: date) -> tuple[float, float]:
        month = today.strftime("%Y-%m")
        with closing(connect()) as db, db:
            row = db.execute("""
                SELECT
                  COALESCE(SUM(CASE WHEN spent_on = ? THEN amount ELSE 0 END), 0) AS today,
                  COALESCE(SUM(CASE WHEN substr(spent_on, 1, 7) = ? THEN amount ELSE 0 END), 0) AS this_month
                FROM expenses
            """, (today.isoformat(), month)).fetchone()
        return float(row["today"]), float(row["this_month"])

    def create_expenses(self, expenses: list[dict], categories: dict[int, str], comment: str) -> list[int]:
        with closing(connect()) as db, db:
            ids = []
            for index, expense in enumerate(expenses):
                cursor = db.execute(
                    "INSERT INTO expenses(item, amount, spent_on, category, comment) VALUES (?, ?, ?, ?, ?)",
                    (expense["item"], expense["amount"], expense["spent_on"], categories[index], comment),
                )
                ids.append(cursor.lastrowid)
        return ids

    def delete_expense(self, expense_id: int) -> bool:
        with closing(connect()) as db, db:
            cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0
