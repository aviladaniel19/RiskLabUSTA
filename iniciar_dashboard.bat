@echo off
title RiskLabUSTA Dashboard
echo ============================================
echo   RiskLabUSTA - Tablero de Riesgo Financiero
echo ============================================
echo.

cd /d "%~dp0"

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Iniciando Servidor Web FastAPI...
echo.
echo  El tablero se abrira en: http://localhost:8000
echo  Presiona Ctrl+C para detener el servidor.
echo.
start http://localhost:8000
cd backend
uvicorn app.main:app --port 8000 --workers 4
pause
