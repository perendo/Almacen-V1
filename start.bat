@echo off
chcp 65001 >nul
setlocal
title WMS - Entorno de Pruebas

cd /d "%~dp0"

echo ============================================
echo   WMS - Iniciando entorno de pruebas
echo ============================================
echo   Raiz del proyecto: %CD%
echo.

rem --- Comprobaciones previas -------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en "env\Scripts\python.exe".
    echo         Cree el entorno con:
    echo             python -m venv env
    echo             env\Scripts\python.exe -m pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "backend\app\main.py" (
    echo [ERROR] No se encontro backend\app\main.py
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo [ERROR] No se encontro frontend\package.json
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Faltan las dependencias del frontend.
    echo         Ejecute:
    echo             cd frontend
    echo             npm install
    echo.
    pause
    exit /b 1
)

if not exist "start_wms.py" (
    echo [ERROR] No se encontro start_wms.py
    pause
    exit /b 1
)

rem --- Arranque ----------------------------------------------------------
echo [1/3] Iniciando backend FastAPI (puerto 8000) y frontend Next.js (puerto 3000)...
echo [2/3] Esperando a que los servicios esten listos...
echo [3/3] Abriendo navegador en http://localhost:3000
echo.
echo Presiona Ctrl+C para detener ambos servidores.
echo ============================================
echo.

".venv\Scripts\python.exe" "start_wms.py"

echo.
echo [INFO] Los servidores se han detenido.
pause
endlocal
