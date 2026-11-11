@echo off
rem ============================================================
rem  DeepSeek Harness - Lanzador de espacio de trabajo
rem ============================================================
rem  Uso:
rem    start.bat                    Inicia DSH en la carpeta de este archivo.
rem    start.bat "H:\MiProyecto"    Inicia DSH en otro espacio de trabajo.
rem    start.bat --port 8080        Pasa opciones a "dsh web" (carpeta actual).
rem    start.bat "H:\MiProyecto" --port 8080   (combina espacio y opciones)
rem
rem  Nota: si el puerto por defecto esta ocupado, usa: start.bat --port 0
rem        (0 hace que el sistema elija un puerto libre).
rem
rem  Copia este archivo en la raiz del espacio de trabajo y haz doble clic.
rem ============================================================
setlocal EnableExtensions
chcp 65001 >nul
title DeepSeek Harness

rem --- 1. Espacio de trabajo ---------------------------------
set "WORKSPACE="

if not "%~1"=="" if exist "%~1\" (
    set "WORKSPACE=%~1"
    shift
)
if "%WORKSPACE%"=="" set "WORKSPACE=%~dp0"

if not exist "%WORKSPACE%\" (
    echo [ERROR] No existe el espacio de trabajo: "%WORKSPACE%"
    pause
    exit /b 1
)

pushd "%WORKSPACE%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se puede entrar en: "%WORKSPACE%"
    pause
    exit /b 1
)

rem --- 2. Opciones restantes para "dsh web" ------------------
set "DSH_ARGS="
:collect_args
if "%~1"=="" goto :args_collected
set "DSH_ARGS=%DSH_ARGS% %1"
shift
goto :collect_args
:args_collected

echo ============================================================
echo   DeepSeek Harness
echo ============================================================
echo   Espacio de trabajo: %CD%
echo.

rem --- 3. Localizar el lanzador de DSH -----------------------
where dsh >nul 2>&1
if not errorlevel 1 goto :launch_dsh

if exist "%APPDATA%\npm\dsh.cmd" goto :launch_global

where npx >nul 2>&1
if errorlevel 1 goto :no_launcher
goto :launch_npx

:launch_dsh
echo [INFO] Lanzando: dsh web %DSH_ARGS%
echo.
dsh web %DSH_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"
goto :done

:launch_global
echo [INFO] Lanzando: dsh web %DSH_ARGS%
echo.
call "%APPDATA%\npm\dsh.cmd" web %DSH_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"
goto :done

:launch_npx
echo [INFO] Lanzando: npx --yes @deepseek-ai/dsh web %DSH_ARGS%
echo.
npx --yes @deepseek-ai/dsh web %DSH_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"
goto :done

:no_launcher
echo [ERROR] No se encontro "dsh" ni "npx" en el PATH.
echo         Instala DSH con:
echo             npm install -g @deepseek-ai/dsh
set "EXIT_CODE=1"

:done
popd
echo.
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] DeepSeek Harness termino con codigo %EXIT_CODE%.
) else (
    echo [INFO] DeepSeek Harness se ha detenido.
)
pause
endlocal
exit /b %EXIT_CODE%
