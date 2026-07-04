@echo off
REM DataDesk V2 launcher (RunDataDeskV2.bat) - separate from the existing
REM RunDataDesk.bat, which still launches the V1 Streamlit app untouched.
REM
REM Starts the FastAPI server (which serves both the API and the built
REM React frontend from one process) and opens it in the browser.
REM
REM REQUIREMENT: frontend/dist must exist. If you've changed any frontend
REM code, run "npm run build" inside the frontend folder first, or this
REM will start the backend with no UI to serve.

cd /d "%~dp0"

REM Activate the Python virtual environment
call venv\Scripts\activate.bat

REM Open the browser after a short delay, giving uvicorn time to start
start "" cmd /c "timeout /t 2 >nul && start http://localhost:8000"

REM Start the server (this window stays open while DataDesk runs -
REM closing it, or pressing Ctrl+C, stops the app)
uvicorn main:app --port 8000

pause