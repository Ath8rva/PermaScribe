@echo off
title PermaScribe
echo Starting PermaScribe...
echo.
echo Dashboard will be at: http://localhost:5000
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
python -m permascribe.main
pause
