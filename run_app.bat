@echo off
echo ==============================================
echo   STARTING STUDYSYNC FULLSTACK APPLICATION
echo   Frontend: Vue 3 (Vite) on http://localhost:5173
echo   Backend:  FastAPI on http://127.0.0.1:8000
echo   Database: SQLite (study_group.db)
echo ==============================================

start "StudySync Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "StudySync Frontend (Vue 3)" cmd /k "cd frontend && npm run dev"

echo Both services launched! Opening browser at http://localhost:5173...
start http://localhost:5173
