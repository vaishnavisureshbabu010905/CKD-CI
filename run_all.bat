@echo off
REM Runs CKD-CI quick test and complete pipeline in sequence (standalone patched scripts).

cd /d "%~dp0"

set PYTHON_EXE=.venv312\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    echo [ERROR] %PYTHON_EXE% not found.
    echo Create the environment first with: py -3.12 -m venv .venv312
    exit /b 1
)

echo ========================================================================
echo CKD-CI Sequential Runner
echo 1) quick_test.py
echo 2) run_complete_pipeline.py
echo ========================================================================
echo.

echo [RUN] quick_test.py
"%PYTHON_EXE%" quick_test.py
if errorlevel 1 (
    echo [FAILED] quick_test.py
    exit /b 1
)

echo.
echo [RUN] run_complete_pipeline.py
"%PYTHON_EXE%" run_complete_pipeline.py
if errorlevel 1 (
    echo [FAILED] run_complete_pipeline.py
    exit /b 1
)

echo.
echo [SUCCESS] Both scripts completed.
exit /b 0
