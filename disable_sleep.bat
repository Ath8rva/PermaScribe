@echo off
title PermaScribe - Disable Sleep
echo ============================================
echo     Disable Sleep for Always-On Recording
echo ============================================
echo.
echo This will prevent the laptop from sleeping so PermaScribe
echo can record 24/7. The screen will still turn off to save power.
echo.
echo Setting sleep to NEVER (plugged in)...
powercfg /change standby-timeout-ac 0
echo Setting sleep to NEVER (on battery)...
powercfg /change standby-timeout-dc 0
echo Setting hibernate to NEVER (plugged in)...
powercfg /change hibernate-timeout-ac 0
echo Setting hibernate to NEVER (on battery)...
powercfg /change hibernate-timeout-dc 0
echo.
echo Screen will turn off after 5 minutes to save power...
powercfg /change monitor-timeout-ac 5
powercfg /change monitor-timeout-dc 5
echo.
echo ============================================
echo Done. This laptop will no longer sleep.
echo Screen will turn off after 5 min (saves power).
echo PermaScribe will keep recording with screen off.
echo ============================================
echo.
echo To undo this later, go to:
echo   Settings - System - Power - Sleep
echo   and set it back to your preferred time.
echo.
pause
