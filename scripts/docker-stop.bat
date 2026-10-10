@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Detiene y elimina el contenedor Docker del LeadsMicroservice.

set "CONTAINER_NAME=leads-microservice"

echo [INFO] Deteniendo contenedor %CONTAINER_NAME%...
docker stop %CONTAINER_NAME% 2>nul
docker rm %CONTAINER_NAME% 2>nul

echo [OK] Contenedor %CONTAINER_NAME% detenido y eliminado.

endlocal
