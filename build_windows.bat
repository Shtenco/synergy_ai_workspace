@echo off
cd /d "%~dp0desktop"
call npm install || exit /b 1
call npm run tauri build || exit /b 1
