@echo off
set PYTHONIOENCODING=utf-8
chcp 65001 > nul
title UNO Multiplayer Server

cls
echo =====================================================================
echo                 🎴 UNO! ONLINE MULTIPLAYER GAME 🎴
echo =====================================================================
echo.
echo Checking dependencies...
py -m pip install -q -r requirements.txt

echo.
echo Opening game in your browser at http://localhost:5000 ...
start http://localhost:5000

echo.
echo =====================================================================
echo  [SUCCESS] UNO GAME SERVER IS RUNNING AT: http://localhost:5000
echo  (Keep this console window open while playing with your friends!)
echo =====================================================================
echo.

py app.py
pause
