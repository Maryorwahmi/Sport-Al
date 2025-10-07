# SMC Forez Development Server Launcher
# PowerShell script to start both API and frontend servers

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🚀 SMC FOREZ DEVELOPMENT LAUNCHER" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

# Check if virtual environment exists
$venvPath = ".\.venv\Scripts\python.exe"
if (Test-Path $venvPath) {
    $pythonCmd = $venvPath
    Write-Host "✅ Using virtual environment Python" -ForegroundColor Green
} else {
    $pythonCmd = "python"
    Write-Host "⚠️  Using system Python" -ForegroundColor Yellow
}

# Install frontend dependencies if needed
if (-not (Test-Path ".\frontend\node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Blue
    Set-Location ".\frontend"
    npm install
    Set-Location ".."
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🌟 Starting development servers..." -ForegroundColor Yellow

# Start API server in background
Write-Host "🚀 Starting API server on http://localhost:3001..." -ForegroundColor Blue
$apiJob = Start-Job -ScriptBlock {
    param($pythonPath)
    & $pythonPath -m uvicorn api_server:app --host 127.0.0.1 --port 3001 --reload
} -ArgumentList $pythonCmd

# Wait a moment for API server to start
Start-Sleep -Seconds 3

# Start frontend server in background
Write-Host "🎨 Starting frontend development server on http://localhost:5173..." -ForegroundColor Blue
$frontendJob = Start-Job -ScriptBlock {
    Set-Location ".\frontend"
    npm run dev
}

# Wait for servers to start
Write-Host ""
Write-Host "⏳ Waiting for servers to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🎉 SERVERS STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "🔌 API Server: http://localhost:3001" -ForegroundColor White
Write-Host "📚 API Docs: http://localhost:3001/docs" -ForegroundColor White
Write-Host "🔌 WebSocket: ws://localhost:3001/ws" -ForegroundColor White
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

# Open browser
Write-Host ""
Write-Host "🌐 Opening frontend in your browser..." -ForegroundColor Blue
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "💡 To stop servers, press Ctrl+C" -ForegroundColor Yellow
Write-Host "💡 Both servers support hot-reloading for development" -ForegroundColor Yellow
Write-Host "💡 Check job status with: Get-Job" -ForegroundColor Yellow

try {
    # Keep the script running and show job status
    while ($true) {
        Start-Sleep -Seconds 10
        
        # Check if jobs are still running
        $apiStatus = (Get-Job -Id $apiJob.Id).State
        $frontendStatus = (Get-Job -Id $frontendJob.Id).State
        
        if ($apiStatus -eq "Failed" -or $frontendStatus -eq "Failed") {
            Write-Host "❌ One or more servers failed" -ForegroundColor Red
            break
        }
        
        # Optional: Show a heartbeat every 30 seconds
        # Write-Host "💓 Servers running..." -ForegroundColor Green
    }
}
catch {
    Write-Host ""
    Write-Host ""
    Write-Host "🛑 Shutting down servers..." -ForegroundColor Red
    
    # Stop the jobs
    Stop-Job -Id $apiJob.Id -ErrorAction SilentlyContinue
    Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    
    # Remove the jobs
    Remove-Job -Id $apiJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    
    Write-Host "✅ Servers stopped" -ForegroundColor Green
}