@echo off
chcp 65001 >nul
echo ========================================
echo Sales SaaS App Startup
echo ========================================

REM Check for virtual environment
if not exist "venv" (
    echo [ERROR] Virtual environment not found
    echo        Run setup_venv.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check API key
if not defined OPENAI_API_KEY (
    echo [WARN] OPENAI_API_KEY is not set
    echo        Set an .env file or environment variable
    echo.
    set /p choice=Continue anyway? (Y/N) :
    if /i not "%choice%"=="Y" (
        echo Startup cancelled
        pause
        exit /b 1
    )
) else (
    echo [INFO] OpenAI API key detected
)

REM Launch Streamlit
echo Starting Streamlit...
echo.
echo Open http://localhost:8501 in your browser
echo Press Ctrl+C to stop.
echo.

streamlit run "app/ui.py" --server.headless true --server.port 8501

pause
