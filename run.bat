@echo off
title Steam Account Creator - 1-Click Runner
color 0b

echo =============================================================
echo                    STEAM ACCOUNT CREATOR 
echo =============================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system!
    echo Please download and install Python from https://www.python.org/
    echo Make sure to check the box 'Add Python to PATH' during installation.
    echo.
    pause
    exit /b
)

:: Install / verify dependencies
echo [*] Verifying required libraries (pip)...
pip install -r requirements.txt --quiet --disable-pip-version-check

echo [+] Libraries verified! Launching bot...
echo.
python steam_creator.py

echo.
echo Process finished. Press any key to exit.
pause >nul
