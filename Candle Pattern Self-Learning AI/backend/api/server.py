"""
FastAPI Backend Server for Candle Pattern AI
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import TradingEngine
from config.settings import Settings

app = FastAPI(
    title="Candle Pattern Self-Learning AI API",
    description="Institutional-grade algorithmic trading platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global trading engine instance
engine = TradingEngine()


# Request/Response models
class TrainRequest(BaseModel):
    symbol: str = "EURUSD"
    timeframe: str = "H1"
    n_bars: int = 5000


class AnalysisRequest(BaseModel):
    symbol: str
    timeframes: Optional[List[str]] = None


class ScanRequest(BaseModel):
    symbols: Optional[List[str]] = None


class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "H1"
    n_bars: int = 1000


# API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Candle Pattern Self-Learning AI",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_info = engine.get_model_info()
    return {
        "status": "healthy",
        "pattern_engine_trained": model_info['pattern_engine_trained'],
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/train")
async def train_model(request: TrainRequest, background_tasks: BackgroundTasks):
    """Train the pattern recognition model"""
    def train_task():
        try:
            result = engine.train_pattern_model(
                symbol=request.symbol,
                timeframe=request.timeframe,
                n_bars=request.n_bars
            )
            print(f"Training completed: {result}")
        except Exception as e:
            print(f"Training error: {str(e)}")
    
    background_tasks.add_task(train_task)
    
    return {
        "message": "Training started in background",
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "n_bars": request.n_bars
    }


@app.post("/api/analyze")
async def analyze_symbol(request: AnalysisRequest):
    """Analyze a symbol across multiple timeframes"""
    try:
        analysis = engine.analyze_symbol(
            symbol=request.symbol,
            timeframes=request.timeframes
        )
        
        # Convert to serializable format
        result = {}
        for tf, data in analysis.items():
            result[tf] = {
                'features': data['features'],
                'smc_summary': {
                    'active_order_blocks': len(data['smc']['order_blocks']['active']),
                    'active_fvgs': len(data['smc']['fair_value_gaps']['active']),
                    'confirmed_sweeps': len(data['smc']['liquidity_sweeps']['confirmed'])
                }
            }
        
        return {
            "symbol": request.symbol,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signal")
async def get_signal(request: AnalysisRequest):
    """Generate trading signal for a symbol"""
    try:
        signal = engine.generate_signal(
            symbol=request.symbol,
            timeframes=request.timeframes
        )
        
        return {
            "signal": signal.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scan")
async def scan_opportunities(request: ScanRequest):
    """Scan multiple symbols for trading opportunities"""
    try:
        opportunities = engine.scan_opportunities(symbols=request.symbols)
        
        return {
            "opportunities": [signal.to_dict() for signal in opportunities],
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest on historical data"""
    try:
        results = engine.run_backtest(
            symbol=request.symbol,
            timeframe=request.timeframe,
            n_bars=request.n_bars
        )
        
        # Convert results to serializable format
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "initial_balance": results['initial_balance'],
            "final_balance": results['final_balance'],
            "metrics": results['metrics'],
            "equity_curve": results['equity_curve'],
            "n_trades": len(results['trades']),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/model/info")
async def get_model_info():
    """Get information about loaded models"""
    try:
        info = engine.get_model_info()
        return {
            "model_info": info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def get_settings():
    """Get current system settings"""
    return {
        "data": engine.settings.data.__dict__,
        "ml": engine.settings.ml.__dict__,
        "smc": engine.settings.smc.__dict__,
        "risk": engine.settings.risk.__dict__,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("Starting Candle Pattern Self-Learning AI Backend Server...")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
