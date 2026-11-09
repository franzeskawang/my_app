# 記帳小幫手

React + Vite 前端、FastAPI 後端、SQLite 資料庫的記帳專案。AI 分類與建議使用 Google Gemini；未設定 API 金鑰時，仍可儲存記錄，但會使用預設分類且沒有 AI 建議。

## 需求

- Windows 10/11、PowerShell
- Python 3.10 或更新版本
- Node.js 20 或更新版本（含 npm）
- Gemini API 金鑰（只在需要 AI 分類/建議時使用）

## 從 GitHub 下載後啟動

先安裝以上工具，開啟 PowerShell，將 `<GitHub-repo-url>` 換成你的儲存庫網址：

```powershell
git clone <GitHub-repo-url>
cd <repo-folder>
```

### 設定及啟動後端

在專案根目錄執行：

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

編輯 `backend/.env`，填入自己的 `GEMINI_API_KEY`。金鑰可從 Google AI Studio 取得；不要把 `.env` 上傳或貼到公開儲存庫。若 PowerShell 阻止啟用虛擬環境，可在目前視窗執行 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`，再執行啟用指令。

啟動 API：

```powershell
python -m uvicorn app.main:app --reload
```

保持這個視窗開啟。API 文件位於 <http://localhost:8000/docs>。首次啟動會在 `backend/data/expenses.db` 建立 SQLite 資料庫。

### 設定及啟動前端

另開一個 PowerShell 視窗，從專案根目錄執行：

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

開啟終端機顯示的網址（預設 <http://localhost:5173>）。要停止服務，在各自終端機按 `Ctrl+C`。

### 後續再次開啟

每次使用都要分別啟動後端與前端。後端：

```powershell
cd <repo-folder>\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

前端（另一視窗）：

```powershell
cd <repo-folder>\frontend
npm run dev
```

## 環境設定與資料

- `backend/.env.example` 是後端設定範本；複製成未追蹤的 `backend/.env`，填入自己的 Gemini 金鑰。
- `frontend/.env.example` 是前端設定範本。預設 API 位址為 `http://localhost:8000`。
- 若改用其他連接埠，請同步設定前端的 `VITE_API_BASE_URL` 和後端的 `FRONTEND_ORIGIN`。
- 記帳資料存於 `backend/data/expenses.db`，不會因為從 GitHub 重新下載而自動帶過去。要搬移舊資料，先停止後端，再安全地複製這個資料庫檔案到新電腦的 `backend/data/`。
- `backend/.env`、`frontend/.env` 和資料庫都不應提交至 GitHub。範例檔可提交，但只能放佔位值。

## 上傳至 GitHub

1. 在 GitHub 建立一個空白儲存庫；不要勾選新增 README、`.gitignore` 或 License（本專案已有檔案）。
2. 在專案根目錄的 PowerShell 確認 `git status --short` 不會列出 `.env`、`backend/data/`、`.venv/` 或 `node_modules/`。若這些機密或本機資料曾經提交，即使後來刪除，也應視為已外洩：撤銷並重設 Gemini 金鑰，再清理 Git 歷史。
3. 若尚未初始化 Git，執行以下命令；若已初始化，略過第一行：

   ```powershell
   git init
   git add .
   git status
   git commit -m "Initial project setup"
   git branch -M main
   git remote add origin <GitHub-repo-url>
   git push -u origin main
   ```

   若 `origin` 已存在，改用 `git remote set-url origin <GitHub-repo-url>`。推送後可在 GitHub 儲存庫頁面確認檔案清單，確定沒有 `.env` 或資料庫。

在其他電腦安裝 Git 後，使用本文件「從 GitHub 下載後啟動」的步驟即可。GitHub 是程式碼備份，不會自動備份 `.env` 或個人記帳資料；請用安全方式另行保管金鑰，並自行備份資料庫。
