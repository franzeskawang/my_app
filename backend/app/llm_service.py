"""Gemini adapter. Replace this module to switch providers without changing routes."""
import os
from google import genai
from google.genai import types
from .schemas import ExpenseAnalysis


def analyze_expenses(expenses: list[dict], comment: str, today_total: float, month_total: float) -> ExpenseAnalysis:
    """Classify every expense and return concise Traditional Chinese advice."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("尚未設定 GEMINI_API_KEY")

    # Bound the provider request so a stalled Gemini call cannot hold the form forever.
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60_000))
    prompt = f"""你是繁體中文記帳助手。請分類每一筆支出。大魔王支出是房租、貸款、保險、電信、固定訂閱等週期性固定或大額支出；其他一般消費歸類為日常支出。
依照輸入順序，每筆回傳一個從 0 開始的 index 與分類；不得漏筆或增加筆數。根據留言與消費內容給出友善、實際、簡短的繁體中文理財建議，不要假設未提供的資訊。

記帳內容：{expenses}
使用者留言：{comment}
送出後今日總花費：{today_total}
送出後本月總花費：{month_total}
"""
    interaction = client.interactions.create(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ExpenseAnalysis.model_json_schema(),
        },
    )
    if not interaction.output_text:
        raise RuntimeError("AI 沒有回傳可解析的分類結果")
    result = ExpenseAnalysis.model_validate_json(interaction.output_text)
    expected = set(range(len(expenses)))
    actual = {item.index for item in result.classifications}
    if actual != expected or len(result.classifications) != len(expenses):
        raise RuntimeError("AI 回傳的分類筆數與記帳筆數不符")
    return result
