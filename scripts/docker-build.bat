@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Construye la imagen Docker del LeadsMicroservice.

cd /d "%~dp0.."

set "IMAGE_NAME=leads-microservice"
set "IMAGE_TAG=latest"

echo [INFO] Construyendo imagen Docker %IMAGE_NAME%:%IMAGE_TAG%...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .

if errorlevel 1 (
    echo [ERROR] Fallo la construccion de la imagen Docker.
    exit /b 1
)

echo [OK] Imagen %IMAGE_NAME%:%IMAGE_TAG% construida correctamente.

endlocal
