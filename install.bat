@echo off
title PermaScribe Setup
echo ============================================
echo         PermaScribe Setup Wizard
echo ============================================
echo.

REM ---- Always work from the folder this script is in ----
cd /d "%~dp0"

REM ---- Check Python ----
echo [Step 1/4] Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is NOT installed on this computer.
    echo.
    echo HOW TO FIX:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download Python 3.11 or newer
    echo   3. IMPORTANT: During install, check the box that says
    echo      "Add Python to PATH" at the bottom of the first screen
    echo   4. Finish the install, then run this script again
    echo.
    pause
    exit /b 1
)
echo    OK - Python found:
python --version
echo.

REM ---- Check Ollama ----
echo [Step 2/4] Checking if Ollama is installed...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Ollama is NOT installed on this computer.
    echo.
    echo HOW TO FIX:
    echo   1. Go to https://ollama.com/download
    echo   2. Download and install Ollama for Windows
    echo   3. Open Ollama and sign in with your Ollama Pro account
    echo   4. Run this script again
    echo.
    pause
    exit /b 1
)
echo    OK - Ollama found:
ollama --version
echo.

REM ---- Install Python packages ----
echo [Step 3/4] Installing Python packages (this may take a few minutes)...
echo.
pip install sounddevice numpy scipy faster-whisper flask pyyaml schedule markdown
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python packages.
    echo Try running this script as Administrator, or run manually:
    echo   pip install sounddevice numpy scipy faster-whisper flask pyyaml schedule markdown
    echo.
    pause
    exit /b 1
)
echo.
echo    OK - All Python packages installed.
echo.

REM ---- Verify packages actually imported ----
echo Verifying packages...
python -c "import sounddevice, numpy, scipy, faster_whisper, flask, yaml, schedule, markdown; print('    OK - All packages verified')"
if errorlevel 1 (
    echo.
    echo ERROR: Packages installed but cannot be imported.
    echo You may have multiple Python versions. Try:
    echo   python -m pip install sounddevice numpy scipy faster-whisper flask pyyaml schedule markdown
    echo.
    pause
    exit /b 1
)
echo.

REM ---- Pull Ollama model ----
echo [Step 4/4] Pulling the AI summarization model...
echo This may take a while depending on your internet speed.
echo.
echo Pulling model: deepseek-v3.1:671b-cloud
ollama pull deepseek-v3.1:671b-cloud
if errorlevel 1 (
    echo.
    echo WARNING: Could not pull the Ollama model.
    echo Make sure Ollama is running and you are signed in to Ollama Pro.
    echo You can pull it manually later:
    echo   ollama pull deepseek-v3.1:671b-cloud
    echo.
    echo PermaScribe will still work for recording and transcription,
    echo but summarization will fail until the model is available.
    echo.
)

REM ---- Create data directories ----
mkdir data\audio 2>nul
mkdir data\transcripts 2>nul
mkdir data\summaries 2>nul

echo.
echo ============================================
echo         Setup Complete!
echo ============================================
echo.
echo NEXT STEPS:
echo.
echo   1. Edit config.yaml if you want to change settings
echo      (the defaults work fine for most people)
echo.
echo   2. To start PermaScribe:
echo      Double-click  start.bat
echo.
echo   3. To make it start automatically when the laptop turns on:
echo      Right-click setup_autostart.bat and "Run as Administrator"
echo.
echo   4. Open your browser to http://localhost:5000 to see the dashboard
echo.
pause
