@echo off
REM CKD-CI System - Easy Launcher
REM Navigate to VS Code integrated terminal and copy-paste one of these commands:

REM ============================================================================
REM OPTION 1: QUICK TEST (Start here - 5-10 minutes)
REM ============================================================================
REM .\.venv\Scripts\python.exe quick_test.py


REM ============================================================================
REM OPTION 2: COMPLETE PIPELINE (Full analysis - 15-20 minutes)
REM ============================================================================
REM .\.venv\Scripts\python.exe run_complete_pipeline.py


REM ============================================================================
REM OPTION 3: INTERACTIVE DASHBOARD (Real-time predictions)
REM ============================================================================
REM .\.venv\Scripts\python.exe -m streamlit run deployment/dashboard.py


REM ============================================================================
REM OPTION 4: JUPYTER NOTEBOOK (Interactive analysis)
REM ============================================================================
REM .\.venv\Scripts\python.exe -m jupyter notebook notebooks/01_data_generation_eda.ipynb


echo ========================================================================
echo CKD-CI System - Choose an option:
echo ========================================================================
echo.
echo 1 = Quick Test (300 patients, 5-10 min)
echo 2 = Complete Pipeline (2000 patients, 15-20 min)
echo 3 = Dashboard (Interactive clinician interface)
echo 4 = Jupyter Notebook (Exploratory analysis)
echo 5 = Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo Launching Quick Test...
    .\.venv312\Scripts\python.exe quick_test.py
    pause
    exit /b
)

if "%choice%"=="2" (
    echo Launching Complete Pipeline...
    .\.venv312\Scripts\python.exe run_complete_pipeline.py
    pause
    exit /b
)

if "%choice%"=="3" (
    echo Launching Dashboard (opening browser)...
    .\.venv312\Scripts\python.exe -m streamlit run dashboard.py
    exit /b
)

if "%choice%"=="4" (
    echo Launching Jupyter Notebook...
    .\.venv312\Scripts\python.exe -m jupyter notebook notebooks/01_data_generation_eda.ipynb
    exit /b
)

if "%choice%"=="5" (
    exit /b
)

echo Invalid choice!
pause
