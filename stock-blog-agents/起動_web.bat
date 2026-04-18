@echo off
chcp 65001 > nul
title 株式投資ブログ AI - Web版

set PYTHON=C:\Users\user\AppData\Local\Python\bin\python.exe

cd /d "%~dp0"

echo.
echo  ================================
echo   株式投資ブログ AI作成 Web版
echo  ================================
echo.
echo  ブラウザが自動で開きます...
echo  終了するにはこのウィンドウを閉じてください
echo.

"%PYTHON%" web_app.py
