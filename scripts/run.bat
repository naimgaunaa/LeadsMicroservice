@echo off
chcp 65001 >nul
setlocal

REM Levanta el microservicio de leads con Uvicorn usando el entorno virtual

cd /d "%~dp0.."

if not exist ".venv\Scripts\activate.bat" (
    echo No se encontro el entorno virtual en .venv
    echo Por favor ejecute scripts/setup.bat e intente nuevamente
    exit /b 1
)

call .venv\Scripts\activate.bat

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

endlocal