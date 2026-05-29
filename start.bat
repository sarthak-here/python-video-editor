@echo off
cd /d "%~dp0"
start "Video Editor Server" cmd /k "uvicorn backend.main:app --reload"
timeout /t 3 /nobreak >nul
start "" http://localhost:8000
