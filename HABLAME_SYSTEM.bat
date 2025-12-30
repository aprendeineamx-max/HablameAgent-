@echo off
title HABLAME - AGENTE DE ACCESIBILIDAD SUPREMO
color 0b
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo.
echo  ================================================================
echo   INICIANDO SISTEMA NERVIOSO DIGITAL...
echo  ================================================================
echo.

cd /d "%~dp0"

:: Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python no encontrado. Por favor instala Python 3.10+.
    pause
    exit
)

echo  [SYSTEM] Cargando modulos del nucleo...
echo  [SYSTEM] Conectando con SambaNova y HuggingFace...
echo.

python main.py

if %errorlevel% neq 0 (
    color 0c
    echo.
    echo  [CRITICAL FAILURE] El sistema se detuvo inesperadamente.
    echo  Revisa el archivo nervous_system.log para mas detalles.
    pause
)
