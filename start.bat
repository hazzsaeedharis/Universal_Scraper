@echo off
REM Universal Scraper Startup Script for Windows
REM This script starts both the backend and frontend servers

echo ==================================
echo   Universal Scraper Startup
echo ==================================
echo.

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Please create a .env file with your API keys.
    echo See README.md for configuration details.
    echo.
    
    if exist .env.template (
        echo Would you like to copy .env.template to .env? (Y/N^)
        set /p response=
        if /i "%response%"=="Y" (
            copy .env.template .env
            echo Created .env file from template
            echo WARNING: Please edit .env and add your API keys before continuing
            pause
            exit /b 1
        )
    )
    
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created
    echo.
    
    echo Installing Python dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
    echo Dependencies installed
    echo.
) else (
    call venv\Scripts\activate
)

REM Check if node_modules exists in frontend
if not exist frontend\node_modules (
    echo Frontend dependencies not found. Installing...
    cd frontend
    call npm install
    cd ..
    echo Frontend dependencies installed
    echo.
)

REM Create log directory if it doesn't exist
if not exist logs mkdir logs

REM Start Backend in a new window
echo Starting Backend Server...
start "Universal Scraper - Backend" cmd /k "venv\Scripts\activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 5 /nobreak > nul

echo Backend server started
echo   API: http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo.

REM Start Frontend in a new window
echo Starting Frontend Server...
cd frontend
start "Universal Scraper - Frontend" cmd /k "npm run dev"
cd ..

REM Wait a bit for frontend to start
timeout /t 5 /nobreak > nul

echo Frontend server started
echo   App: http://localhost:5173
echo.

echo ==================================
echo   Universal Scraper is running!
echo ==================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Two terminal windows have been opened for backend and frontend.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this window...
pause > nul


