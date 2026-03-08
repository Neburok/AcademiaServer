@echo off
title Mitzlia — Detener
echo.
echo  Deteniendo procesos de Mitzlia...
echo.

taskkill /FI "WindowTitle eq Mitzlia - API*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Mitzlia - Bot*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Mitzlia - Scheduler*" /T /F >nul 2>&1

echo  Mitzlia detenida.
echo.
pause
