@echo off
setlocal
echo ========================================================
echo Starting UMCAO (Universal Multi-Language Code Analyzer)
echo ========================================================

:: Attempt standard PATH first; add common local fallback paths if needed
where python >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312" (
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    )
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\Program Files\nodejs" (
        set "PATH=C:\Program Files\nodejs;%PATH%"
    )
)

echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "UMCAO Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo Starting React Vite Frontend on http://localhost:5173 ...
start "UMCAO Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo UMCAO is running!
echo - Web UI:  http://localhost:5173/
echo - Backend: http://127.0.0.1:8000/
echo - API Docs: http://127.0.0.1:8000/docs
echo ========================================================
pause


