@echo off
title RiskLabUSTA Dashboard
echo ============================================
echo   RiskLabUSTA - Tablero de Riesgo Financiero
echo ============================================
echo.

cd /d "%~dp0"

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Iniciando Streamlit...
echo.
echo  El tablero se abrira en: http://localhost:8501
echo  Presiona Ctrl+C para detener el servidor.
echo.
streamlit run dashboard\app.py
pause
