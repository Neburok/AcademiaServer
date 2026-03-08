@echo off
title Mitzlia — Arranque
echo.
echo  Iniciando Mitzlia en rubenpc...
echo  Red Tailscale requerida para acceso remoto.
echo.

cd /d "%~dp0"

REM Verificar que existe el .env
if not exist ".env" (
    echo  ERROR: No se encontro el archivo .env
    echo  Copia .env.example como .env y configura los valores.
    pause
    exit /b 1
)

echo  [1/3] Iniciando API REST...
start "Mitzlia - API" cmd /k "python run_api.py"
timeout /t 2 /nobreak >nul

echo  [2/3] Iniciando bot de Telegram...
start "Mitzlia - Bot" cmd /k "python run_bot.py"
timeout /t 2 /nobreak >nul

echo  [3/3] Iniciando scheduler de recordatorios...
start "Mitzlia - Scheduler" cmd /k "python run_scheduler.py"

echo.
echo  Mitzlia activa. Tres ventanas abiertas (API, Bot, Scheduler).
echo  Para detener: ejecuta stop_mitzlia.bat
echo.
pause
