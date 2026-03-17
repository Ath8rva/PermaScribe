@echo off
title PermaScribe - Setup Check
echo ============================================
echo      PermaScribe Setup Diagnostics
echo ============================================
echo.

set ERRORS=0

REM ---- Python ----
echo [1/6] Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    FAIL - Python not found. Install from https://www.python.org/downloads/
    set /a ERRORS+=1
) else (
    echo    OK   - Python found
    python --version
)
echo.

REM ---- pip packages ----
echo [2/6] Python packages...
python -c "import sounddevice, numpy, scipy, faster_whisper, flask, yaml, schedule, markdown" 2>nul
if errorlevel 1 (
    echo    FAIL - Some packages are missing. Run install.bat first.
    set /a ERRORS+=1
) else (
    echo    OK   - All packages installed
)
echo.

REM ---- Ollama ----
echo [3/6] Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo    FAIL - Ollama not found. Install from https://ollama.com/download
    set /a ERRORS+=1
) else (
    echo    OK   - Ollama found
    ollama --version
)
echo.

REM ---- Ollama running ----
echo [4/6] Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo    WARN - Ollama is not running. Start it from the system tray or run: ollama serve
    set /a ERRORS+=1
) else (
    echo    OK   - Ollama is running
)
echo.

REM ---- Microphone ----
echo [5/6] Microphone...
python -c "import sounddevice; d = sounddevice.query_devices(kind='input'); print(f'    OK   - Mic found: {d[\"name\"]}')" 2>nul
if errorlevel 1 (
    echo    FAIL - No microphone detected. Plug in a mic and try again.
    set /a ERRORS+=1
)
echo.

REM ---- Config file ----
echo [6/6] Config file...
if exist "%~dp0config.yaml" (
    echo    OK   - config.yaml found
) else (
    echo    FAIL - config.yaml not found in PermaScribe folder
    set /a ERRORS+=1
)
echo.

echo ============================================
if %ERRORS%==0 (
    echo    ALL CHECKS PASSED - Ready to go!
    echo    Run start.bat to begin recording.
) else (
    echo    %ERRORS% issue(s) found. Fix them and run this again.
)
echo ============================================
echo.
pause
