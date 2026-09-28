@echo off
set PYTHONIOENCODING=utf-8
chcp 65001 > nul
title UNO Multiplayer Server
echo ===================================================
echo           UNO! Online Multiplayer Game
echo ===================================================
echo.
echo Installing requirements (if needed)...
py -m pip install -r requirements.txt
echo.
echo Launching browser at http://localhost:5000 ...
start http://localhost:5000
echo Starting UNO Game Server...
py app.py
pause
