@echo off
setlocal EnableDelayedExpansion

REM ====================================================================
REM Setup script - LeadsMicroservice
REM Crea el entorno virtual (.venv) e instala las dependencias
REM ====================================================================

set "PROJECT_ROOT=%~dp0.."
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS=%PROJECT_ROOT%\requirements.txt"

echo.
echo ============================================================
echo   LeadsMicroservice - Setup
echo ============================================================
echo   Project root : %PROJECT_ROOT%
echo   Virtual env  : %VENV_DIR%
echo ============================================================
echo.

REM ----------------------------------------------------------------------
REM 1. Verificar que Python este disponible
REM ----------------------------------------------------------------------
echo [1/4] Verificando instalacion de Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo         Descarga Python desde https://www.python.org/downloads/
    echo         y asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    exit /b 1
)

for /f "delims=" %%v in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo       OK - !PYTHON_VERSION! encontrado.

REM ----------------------------------------------------------------------
REM 2. Verificar requirements.txt
REM ----------------------------------------------------------------------
echo [2/4] Verificando requirements.txt...
if not exist "%REQUIREMENTS%" (
    echo.
    echo [ERROR] No se encontro requirements.txt en "%REQUIREMENTS%".
    echo.
    exit /b 1
)
echo       OK - requirements.txt encontrado.

REM ----------------------------------------------------------------------
REM 3. Crear el entorno virtual
REM ----------------------------------------------------------------------
echo [3/4] Creando entorno virtual...
if exist "%VENV_DIR%" (
    echo       El entorno virtual ya existe en "%VENV_DIR%".
    set /p "RECREATE=Deseas recrearlo? [s/N]: "
    if /i "!RECREATE!"=="s" (
        echo       Eliminando entorno virtual existente...
        rmdir /s /q "%VENV_DIR%"
        python -m venv "%VENV_DIR%"
        if errorlevel 1 goto :error_venv
        echo       OK - Entorno virtual recreado.
    ) else (
        echo       Se reutilizara el entorno virtual existente.
    )
) else (
    python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error_venv
    echo       OK - Entorno virtual creado.
)

REM ----------------------------------------------------------------------
REM 4. Instalar dependencias
REM ----------------------------------------------------------------------
echo [4/4] Instalando dependencias...
echo       Actualizando pip, setuptools y wheel...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel >nul
if errorlevel 1 (
    echo       [ADVERTENCIA] No se pudo actualizar pip. Continuando...
)

echo       Instalando paquetes desde requirements.txt...
"%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS%"
if errorlevel 1 goto :error_install
echo       OK - Dependencias instaladas correctamente.

REM ----------------------------------------------------------------------
REM Finalizado
REM ----------------------------------------------------------------------
echo.
echo ============================================================
echo   Setup completado exitosamente
echo ============================================================
echo.
echo   Para activar el entorno virtual ejecuta:
echo     %VENV_DIR%\Scripts\activate.bat
echo.
echo   O directamente:
echo     .venv\Scripts\activate
echo.
endlocal
exit /b 0

:error_venv
echo.
echo [ERROR] No se pudo crear el entorno virtual.
echo.
exit /b 1

:error_install
echo.
echo [ERROR] Fallo la instalacion de dependencias.
echo.
exit /b 1
