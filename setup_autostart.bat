@echo off
echo === PermaScribe Auto-Start Setup ===
echo.

set "SCRIPT_DIR=%~dp0"

echo Registering PermaScribe to start on login...
schtasks /create /tn "PermaScribe" /tr "pythonw \"%SCRIPT_DIR%run.pyw\"" /sc onlogon /rl highest /f

if errorlevel 1 (
    echo.
    echo ERROR: Could not create scheduled task. Try running as Administrator.
    pause
    exit /b 1
)

echo.
echo PermaScribe will now start automatically when you log in.
echo.
echo To remove auto-start, run:
echo   schtasks /delete /tn "PermaScribe" /f
echo.
pause
