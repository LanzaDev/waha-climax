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
echo  Porta: 8000   (Ctrl+C para parar)
echo ==========================================
python api.py
if errorlevel 1 (
  echo.
  echo  [!] 'python' nao encontrado. Tentando 'py'...
  py api.py
)
pause
