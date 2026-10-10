@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Ejecuta el contenedor Docker del LeadsMicroservice.

cd /d "%~dp0.."

set "IMAGE_NAME=leads-microservice"
set "IMAGE_TAG=latest"
set "CONTAINER_NAME=leads-microservice"
set "HOST_PORT=8000"
set "CONTAINER_PORT=8000"

echo [INFO] Deteniendo contenedor existente (si existe)...
docker rm -f %CONTAINER_NAME% 2>nul

echo [INFO] Ejecutando contenedor %CONTAINER_NAME% en el puerto %HOST_PORT%...
docker run -d --name %CONTAINER_NAME% -p %HOST_PORT%:%CONTAINER_PORT% --env-file .env %IMAGE_NAME%:%IMAGE_TAG%

if errorlevel 1 (
    echo [ERROR] No se pudo iniciar el contenedor.
    echo [INFO] Asegurate de tener el archivo .env configurado y la imagen construida.
    exit /b 1
)

echo [OK] Contenedor %CONTAINER_NAME% iniciado.
echo [INFO] Logs disponibles con: docker logs -f %CONTAINER_NAME%
echo [INFO] API disponible en: http://localhost:%HOST_PORT%

endlocal
