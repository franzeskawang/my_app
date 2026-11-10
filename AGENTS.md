# 專案代理人指引

- 與使用者溝通及編寫說明時使用繁體中文；說明保持清楚、實用，適度使用 emoji 和顏文字。🙂
- 專案由 `frontend/`（React、Vite、Tailwind CSS）及 `backend/`（FastAPI、SQLite）組成。
- FastAPI 組合入口位於 `backend/app/main.py`；後端功能按 `backend/app/features/<feature>/` 集中 routes、schemas、services、repositories 與功能專屬流程；共用 API、SQLite 連線與 Gemini 整合分別位於 `api/`、`infrastructure/sqlite/` 與 `integrations/gemini/`；服務組裝位於 `application/container.py`。
- 前端功能模組位於 `frontend/src/features/`；瀏覽器專屬程式位於 `frontend/src/platform/web/`；不要在 feature/UI/hook 直接操作瀏覽器全域物件或自行呼叫 `fetch`。
- 後端 OpenAPI 契約由 `backend/export_openapi.py` 產生到 `backend/openapi.json`；在 `frontend/` 執行 `npm run api:types` 產生型別，API client 使用該產物。
- 前端呼叫後端的設定是 `VITE_API_BASE_URL`；後端 CORS 設定是 `FRONTEND_ORIGIN`。範例設定放在 `.env.example`，不要提交任何實際 `.env` 或 API 金鑰。
- SQLite 資料庫預設建立於 `backend/data/expenses.db`。除非使用者要求，不要刪除或覆寫資料庫。
- 後端依賴清單是 `backend/requirements.txt`；前端以 `frontend/package-lock.json` 搭配 `npm ci` 安裝。
- 維持現有路由及資料格式的相容性。變更前確認相關呼叫端與 schema；不要將金鑰寫入程式碼、文件、日誌或版本控制。
- 專案啟動及 GitHub 搬移步驟以根目錄 `README.md` 為準。
