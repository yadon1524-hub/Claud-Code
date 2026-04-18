@echo off
chcp 65001 > nul
title 株式投資ブログ AI作成アプリ

set PYTHON=C:\Users\user\AppData\Local\Python\bin\python.exe

echo ================================
echo  株式投資ブログ AI作成アプリ
echo ================================
echo.

cd /d "%~dp0"

:: アプリ起動
"%PYTHON%" gui_app.py

pause
