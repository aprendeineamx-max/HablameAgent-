@echo off
title HABLAME API SERVER
echo ================================================================
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo  INICIANDO SERVIDOR API (NERVIO EXTERNO)...
echo ================================================================
echo.
echo  Endpoints disponibles en: http://localhost:8000/docs
echo.

cd /d "%~dp0"
python api/server.py

pause
