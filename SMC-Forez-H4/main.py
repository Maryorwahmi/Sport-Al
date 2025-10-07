#!/usr/bin/env python3
"""
SMC Forez - Main Backend Server
Simple FastAPI server that works with signal_runner_enhanced.py
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time

# FastAPI imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Pydantic models
from pydantic import BaseModel

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import your existing components
from signal_runner_enhanced import EnhancedSignalRunner
from smc_forez.config.settings import Settings
from smc_forez.execution.live_executor import ExecutionSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
signal_runner: Optional[EnhancedSignalRunner] = None
signal_runner_thread: Optional[threading.Thread] = None
websocket_connections: List[WebSocket] = []
recent_signals_list: List[Dict] = []
system_status = {
    'status': 'STOPPED',
    'mt5_connected': False,
    'last_scan': None,
    'signals_today': 0,
    'trades_today': 0,
    'uptime': datetime.now()
}

# Pydantic Models
class AccountInfoResponse(BaseModel):
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    profit: float
    connected: bool
    server: str
    leverage: int

class SystemStatusResponse(BaseModel):
    status: str
    mt5_connected: bool
    last_scan: Optional[str]
    signals_today: int
    trades_today: int
    uptime: str

# Create FastAPI app
app = FastAPI(
    title="SMC Forez Trading System",
    description="Professional Smart Money Concepts Trading System",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174", 
        "http://localhost:5175",
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SMC Forez Backend Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "signal_runner": "running" if signal_runner and signal_runner.is_running else "stopped"
    }

@app.get("/api/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get current system status"""
    global system_status, signal_runner_thread
    
    uptime_delta = datetime.now() - system_status['uptime']
    
    # Update status based on signal runner and thread state
    if (signal_runner and signal_runner.is_running and 
        signal_runner_thread and signal_runner_thread.is_alive()):
        system_status['status'] = 'RUNNING'
        system_status['mt5_connected'] = True
    else:
        system_status['status'] = 'STOPPED' 
        system_status['mt5_connected'] = False
    
    # Count today's signals
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_signals = sum(1 for signal in recent_signals_list 
                       if datetime.fromisoformat(signal['timestamp']) >= today_start)
    
    return SystemStatusResponse(
        status=system_status['status'],
        mt5_connected=system_status['mt5_connected'],
        last_scan=system_status['last_scan'],
        signals_today=today_signals,
        trades_today=system_status['trades_today'],
        uptime=str(uptime_delta)
    )

@app.get("/api/account/info", response_model=AccountInfoResponse)
async def get_account_info():
    """Get account information"""
    # Get real account info from signal runner if available
    if signal_runner and signal_runner.executor and hasattr(signal_runner.executor, 'risk_manager'):
        risk_manager = signal_runner.executor.risk_manager
        balance = risk_manager.current_balance if risk_manager else 10000.0
        equity = balance + 125.50  # Mock profit for demo
        profit = equity - balance
    else:
        balance = 10000.0
        equity = 10125.50
        profit = 125.50
    
    return AccountInfoResponse(
        balance=balance,
        equity=equity,
        margin=0.0,
        margin_free=equity,
        margin_level=999999.0 if equity > 0 else 0.0,
        profit=profit,
        connected=system_status['mt5_connected'],
        server="SMC-Forez-Server",
        leverage=100
    )

@app.get("/api/signals/recent")
async def get_recent_signals(limit: int = 10):
    """Get recent signals"""
    if recent_signals_list:
        return recent_signals_list[:limit]
    
    # Return mock signals if no real signals available
    mock_signals = [
        {
            "id": f"signal_{i}",
            "symbol": "EURUSDm",
            "type": "BUY",
            "strength": "HIGH",
            "entry_price": 1.0850 + (i * 0.0001),
            "stop_loss": 1.0820 + (i * 0.0001),
            "take_profit": 1.0910 + (i * 0.0001),
            "risk_reward_ratio": 2.0,
            "confidence": 0.85,
            "timeframes": ["H4", "H1", "M15"],
            "timestamp": (datetime.now() - timedelta(minutes=i*15)).isoformat(),
            "status": "ACTIVE"
        }
        for i in range(min(limit, 5))
    ]
    return mock_signals


@app.get("/api/positions/open")
async def get_open_positions():
    """Get open positions"""
    # Mock positions for demo
    return [
        {
            "ticket": 12345678,
            "symbol": "EURUSDm",
            "type": "BUY",
            "volume": 0.1,
            "open_price": 1.0850,
            "current_price": 1.0875,
            "stop_loss": 1.0820,
            "take_profit": 1.0910,
            "profit": 25.0,
            "pips": 25.0,
            "open_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "status": "OPEN"
        }
    ]

@app.post("/api/system/start")
async def start_system():
    """Start the trading system"""
    global signal_runner, system_status, signal_runner_thread
    
    try:
        if not signal_runner:
            # Initialize settings
            settings = Settings()
            execution_settings = ExecutionSettings(
                enable_execution=False,  # Start in signals-only mode
                refresh_interval_seconds=120  # 2 minutes for testing instead of 30 minutes
            )
            
            # Create signal runner
            signal_runner = EnhancedSignalRunner(settings, execution_settings)
            
        if not signal_runner.is_running:
            # Start signal runner in background thread
            def run_signal_runner():
                try:
                    logger.info("🔄 Starting signal runner thread...")
                    signal_runner.start()
                except Exception as e:
                    logger.error(f"❌ Error in signal runner thread: {e}")
                finally:
                    # Update status when runner stops
                    system_status['status'] = 'STOPPED'
                    system_status['mt5_connected'] = False
                    logger.info("🔄 Signal runner thread finished")
            
            signal_runner_thread = threading.Thread(target=run_signal_runner, daemon=False)
            signal_runner_thread.start()
            
            # Wait a bit to see if the runner actually starts
            await asyncio.sleep(1)
            
            system_status['status'] = 'RUNNING'
            system_status['mt5_connected'] = True
            
            await broadcast_to_websockets("SYSTEM_STATUS", system_status)
            
            logger.info("🚀 Trading system started")
            
        return {"message": "System started successfully", "status": system_status}
        
    except Exception as e:
        logger.error(f"❌ Error starting system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start system: {str(e)}")

@app.post("/api/system/stop")
async def stop_system():
    """Stop the trading system"""
    global signal_runner, signal_runner_thread, system_status
    
    try:
        if signal_runner:
            logger.info("🛑 Stopping signal runner...")
            signal_runner.stop()
            
            # Wait for thread to finish (with timeout)
            if signal_runner_thread and signal_runner_thread.is_alive():
                logger.info("⏳ Waiting for signal runner thread to finish...")
                signal_runner_thread.join(timeout=10)  # Wait max 10 seconds
                
                if signal_runner_thread.is_alive():
                    logger.warning("⚠️ Signal runner thread did not stop within timeout")
            
        system_status['status'] = 'STOPPED'
        system_status['mt5_connected'] = False
        
        await broadcast_to_websockets("SYSTEM_STATUS", system_status)
        
        logger.info("🛑 Trading system stopped")
        
        return {"message": "System stopped successfully", "status": system_status}
        
    except Exception as e:
        logger.error(f"❌ Error stopping system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop system: {str(e)}")


# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    logger.info(f"🔌 WebSocket client connected. Total connections: {len(websocket_connections)}")
    
    try:
        # Send initial system status
        await websocket.send_json({
            "type": "SYSTEM_STATUS",
            "data": system_status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                # Receive ping/pong messages
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        logger.info(f"🔌 WebSocket client disconnected. Remaining: {len(websocket_connections)}")

async def broadcast_to_websockets(message_type: str, data: Any):
    """Broadcast message to all connected WebSocket clients"""
    if not websocket_connections:
        return
        
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    # Remove disconnected clients
    active_connections = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
            active_connections.append(ws)
        except:
            pass  # Connection is closed
    
    websocket_connections[:] = active_connections

# Function to add signals to the list (called by signal runner)
def add_signal_to_list(signal_data: Dict):
    """Add a new signal to the recent signals list"""
    global recent_signals_list
    
    recent_signals_list.insert(0, signal_data)
    
    # Keep only last 50 signals
    if len(recent_signals_list) > 50:
        recent_signals_list.pop()
    
    # Update system status
    system_status['last_scan'] = datetime.now().isoformat()
    system_status['signals_today'] += 1
    
    # Broadcast to WebSocket clients
    asyncio.create_task(broadcast_to_websockets("SIGNAL", signal_data))

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 SMC Forez Backend Server starting up...")
    system_status['uptime'] = datetime.now()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global signal_runner
    
    logger.info("🛑 SMC Forez Backend Server shutting down...")
    
    if signal_runner:
        signal_runner.stop()
    
    # Close all WebSocket connections
    for ws in websocket_connections:
        await ws.close()


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SMC Forez Backend Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print("🚀 SMC FOREZ - BACKEND SERVER")
    print("=" * 50)
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"🔌 WebSocket: ws://{args.host}:{args.port}/ws")
    print(f"📚 API docs: http://{args.host}:{args.port}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )