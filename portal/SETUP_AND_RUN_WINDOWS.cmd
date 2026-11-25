@echo off
setlocal
cd /d "%~dp0"
py -3.12 nawa.py setup --stop-running
if errorlevel 1 (
  echo.
  echo Setup did not finish. Review the message above. Your saved data was not deleted.
  pause
  exit /b 1
)
py -3.12 nawa.py run --auto-ports
if errorlevel 1 pause
