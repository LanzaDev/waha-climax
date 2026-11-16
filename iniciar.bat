@echo off
chcp 65001 >nul
title API Clima Windy
cd /d "%~dp0"

if not exist ".env" (
  echo.
  echo  [!] Arquivo .env nao encontrado - criando a partir do modelo...
  copy .env.example .env >nul
  echo.
  echo      Criado: .env
  echo      1^) Edite o .env e coloque seus dados (numero WhatsApp, sessao WAHA)
  echo      2^) Execute este arquivo de novo
  echo.
  pause
  exit /b 1
)

echo ==========================================
echo  API CLIMA WINDY (Windy -^> n8n -^> WAHA)
echo  Ctrl+C para parar
echo ==========================================

rem Escolhe o executavel ANTES de rodar (evita rodar duas vezes)
set "PY="
python --version >nul 2>nul
if not errorlevel 1 set "PY=python"
if not defined PY (
  py --version >nul 2>nul
  if not errorlevel 1 set "PY=py"
)
if not defined PY (
  echo.
  echo  [!] Python nao encontrado.
  echo      Instale em https://www.python.org/downloads/ e marque
  echo      "Add python.exe to PATH" durante a instalacao.
  echo.
  pause
  exit /b 1
)

echo  Python: %PY%
%PY% api.py
pause
