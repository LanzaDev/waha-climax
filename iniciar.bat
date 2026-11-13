@echo off
chcp 65001 >nul
title API Clima Windy - porta 8000
echo ==========================================
echo  API CLIMA WINDY (Windy -^> n8n -^> WAHA)
echo  Porta: 8000   (Ctrl+C para parar)
echo ==========================================
cd /d "%~dp0"
python api.py
pause
