@echo off
title UNO Multiplayer Server
echo ===================================================
echo           UNO! Online Multiplayer Game
echo ===================================================
echo.
echo Starting UNO Game Server...
py -m pip install -r requirements.txt
py app.py
pause
