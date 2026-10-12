@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Levanta el microservicio de leads con Uvicorn usando el entorno virtual local.

cd /d "%~dp0.."

set "VENV=.venv\Scripts\activate.bat"
set "HOST=0.0.0.0"
set "PORT=8000"

if not exist "%VENV%" (
    echo [ERROR] No se encontro el entorno virtual en .venv
    echo [INFO] Ejecute scripts/setup.bat primero e intente nuevamente.
    exit /b 1
)

call "%VENV%" || (
    echo [ERROR] No se pudo activar el entorno virtual.
    exit /b 1
)

python -c "import uvicorn" 2>nul || (
    echo [ERROR] Uvicorn no esta instalado en el entorno virtual.
    echo [INFO] Instale las dependencias con: pip install -r requirements.txt
    exit /b 1
)

echo [INFO] Iniciando LeadsMicroservice en http://%HOST%:%PORT%
python -m uvicorn app.main:app --host %HOST% --port %PORT% --reload

endlocal
