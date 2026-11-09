# 專案代理人指引

- 與使用者溝通及編寫說明時使用繁體中文；說明保持清楚、實用，適度使用 emoji 和顏文字。🙂
- 專案由 `frontend/`（React、Vite、Tailwind CSS）及 `backend/`（FastAPI、SQLite）組成。
- 後端 API 路由位於 `backend/app/main.py`；Gemini 整合位於 `backend/app/llm_service.py`；資料庫程式位於 `backend/app/database.py`。
- 前端呼叫後端的設定是 `VITE_API_BASE_URL`；後端 CORS 設定是 `FRONTEND_ORIGIN`。範例設定放在 `.env.example`，不要提交任何實際 `.env` 或 API 金鑰。
- SQLite 資料庫預設建立於 `backend/data/expenses.db`。除非使用者要求，不要刪除或覆寫資料庫。
- 後端依賴清單是 `backend/requirements.txt`；前端以 `frontend/package-lock.json` 搭配 `npm ci` 安裝。
- 維持現有路由及資料格式的相容性。變更前確認相關呼叫端與 schema；不要將金鑰寫入程式碼、文件、日誌或版本控制。
- 專案啟動及 GitHub 搬移步驟以根目錄 `README.md` 為準。
