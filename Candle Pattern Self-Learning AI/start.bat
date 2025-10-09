@echo off
REM Candle Pattern Self-Learning AI - Windows Startup Script

echo Starting Candle Pattern Self-Learning AI
echo ============================================
echo.

REM Start backend
echo Starting Backend Server...
cd backend
start "Backend Server" cmd /k python api/server.py
cd ..

REM Wait for backend
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting Frontend Server...
cd frontend
start "Frontend Server" cmd /k npm start
cd ..

echo.
echo System Started Successfully!
echo ================================
echo Backend API: http://localhost:8000
echo Frontend:    http://localhost:3000
echo API Docs:    http://localhost:8000/docs
echo.
echo Press any key to exit...
pause > nul
