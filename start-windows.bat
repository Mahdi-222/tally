@echo off
REM Tally - one-step setup ^& run (Windows)
REM Double-click this file.

cd /d "%~dp0"

echo.
echo   Tally - starting up
echo   ===================
echo.

REM 1. Find Python
where python >nul 2>&1
if %errorlevel%==0 (
  set PY=python
) else (
  where py >nul 2>&1
  if %errorlevel%==0 (
    set PY=py
  ) else (
    echo   X Python isn't installed.
    echo     Install it from https://www.python.org/downloads/
    echo     IMPORTANT: tick "Add Python to PATH" during install, then run this again.
    echo.
    pause
    exit /b 1
  )
)
echo   Found Python.

REM 2. Virtual environment (first run only)
if not exist ".venv" (
  echo   - Setting up a private environment (first run only)...
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat

REM 3. Dependencies
echo   - Installing dependencies (first run may take a minute)...
python -m pip install --quiet --upgrade pip >nul 2>&1
python -m pip install --quiet -r requirements.txt

REM 4. API key
set NEEDKEY=1
if exist ".env" (
  findstr /C:"sk-ant" .env >nul 2>&1 && set NEEDKEY=0
)
if "%NEEDKEY%"=="1" (
  echo.
  echo   ------------------------------------------------
  echo   One thing needed: your Anthropic API key.
  echo   Get it at  https://console.anthropic.com  -^>  API keys
  echo   ------------------------------------------------
  echo.
  set /p KEY="  Paste your key here and press Enter: "
  echo ANTHROPIC_API_KEY=%KEY%> .env
  echo   Saved. You won't be asked again.
)

REM 5. Run
echo.
echo   Ready. Opening http://localhost:5000 ...
echo   (Leave this window open while you use Tally. Close it to stop.)
echo.
start "" http://localhost:5000
python app.py
