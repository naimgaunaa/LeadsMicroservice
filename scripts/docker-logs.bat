@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM Muestra los logs del contenedor Docker del LeadsMicroservice.

set "CONTAINER_NAME=leads-microservice"

echo [INFO] Mostrando logs del contenedor %CONTAINER_NAME%...
docker logs -f %CONTAINER_NAME%

endlocal
