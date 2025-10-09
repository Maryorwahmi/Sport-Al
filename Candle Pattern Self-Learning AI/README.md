# Candle Pattern Self-Learning AI

## Institutional-Grade Algorithmic Trading Platform

A production-ready quantitative trading system combining Smart Money Concepts (SMC), statistical pattern recognition, machine learning, and robust risk management.

### Features

✅ **Machine Learning Pattern Recognition**
- LSTM/CNN-based candle pattern detection
- K-means clustering for pattern archetypes
- Self-learning from historical data
- Confidence-based prediction system

✅ **Smart Money Concepts (SMC)**
- Order Blocks detection and tracking
- Fair Value Gaps (FVG) identification
- Break of Structure (BOS) / Change of Character (CHOCH)
- Liquidity sweep detection

✅ **Multi-Timeframe Analysis**
- H4 bias confirmation
- H1 structure validation
- M15 entry precision
- Confluence scoring system

✅ **Advanced Risk Management**
- Dynamic position sizing
- Portfolio risk limits
- ATR-based stop losses
- R:R ratio optimization

✅ **Comprehensive Backtesting**
- Historical simulation with slippage
- Performance metrics (Sharpe, Sortino, Drawdown)
- Walk-forward validation
- Equity curve visualization

✅ **Professional Web Interface**
- Real-time signal monitoring
- Interactive backtesting
- Model training interface
- Progressive Web App (PWA) support

---

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python api/server.py
```

Backend will run on http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend will run on http://localhost:3000

---

## Architecture

### Backend (Python)
```
backend/
├── api/              # FastAPI server
├── config/           # Settings and configuration
├── data/             # Data ingestion and management
├── models/           # ML models and feature engineering
├── smc/              # Smart Money Concepts engine
├── risk/             # Risk management
├── backtesting/      # Backtest engine
└── engine.py         # Main trading engine
```

### Frontend (React)
```
frontend/
├── src/
│   ├── pages/       # Dashboard, Training, Backtest
│   ├── services/    # API client
│   └── App.js       # Main application
└── public/          # Static assets
```

---

## Usage

### 1. Train the Model

Navigate to the **Training** page and configure:
- Symbol: EURUSD (or your preferred pair)
- Timeframe: H1
- Number of Bars: 5000

Click "Start Training" to train the pattern recognition model on historical data.

### 2. Scan for Opportunities

On the **Dashboard**:
- Click "Scan Markets" to analyze multiple symbols
- View trading signals with entry, SL, TP levels
- Check confluence scores and pattern predictions

### 3. Run Backtests

On the **Backtest** page:
- Configure symbol and timeframe
- Set number of historical bars
- Click "Run Backtest"
- View equity curve and performance metrics

---

## Configuration

### Risk Settings (backend/config/settings.py)

```python
risk_per_trade = 0.01        # 1% risk per trade
max_portfolio_risk = 0.05    # 5% total exposure
max_concurrent_trades = 3    # Maximum open positions
min_rr_ratio = 2.0          # Minimum risk:reward ratio
```

### ML Settings

```python
window_size = 20            # Candles per pattern
n_clusters = 50             # Pattern archetypes
min_pattern_confidence = 0.6 # Minimum prediction confidence
```

### Confluence Weights

```python
h4_bias_weight = 0.20       # H4 timeframe bias
h1_structure_weight = 0.20  # H1 structure
m15_poi_weight = 0.20       # M15 point of interest
ob_proximity_weight = 0.15  # Order block proximity
fvg_presence_weight = 0.08  # Fair value gap presence
```

---

## API Endpoints

### Training
- `POST /api/train` - Train pattern recognition model
- `GET /api/model/info` - Get model information

### Analysis
- `POST /api/analyze` - Analyze symbol
- `POST /api/signal` - Generate trading signal
- `POST /api/scan` - Scan multiple symbols

### Backtesting
- `POST /api/backtest` - Run backtest

### System
- `GET /health` - Health check
- `GET /api/settings` - Get system settings

---

## Performance Metrics

### Backtest Results Include:
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss
- **Total Return**: Overall percentage return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
- **Average Win/Loss**: Average profit/loss per trade

---

## Mobile & Desktop Support

The application is built as a Progressive Web App (PWA):
- **Web**: Access via browser at localhost:3000
- **Mobile**: Install as PWA on iOS/Android
- **Desktop**: Download as standalone app (Electron packaging available)

---

## Technology Stack

### Backend
- Python 3.11+
- FastAPI (API server)
- Pandas, NumPy (data processing)
- Scikit-learn (ML models)
- Optional: TensorFlow/PyTorch (deep learning)

### Frontend
- React 19
- Material-UI (components)
- Recharts (visualizations)
- Axios (API client)

---

## Safety & Disclaimers

⚠️ **Important**: This software is for educational and research purposes.

**Always**:
- Start with paper trading
- Backtest thoroughly before live trading
- Use appropriate position sizing
- Never risk more than you can afford to lose
- Trading carries substantial risk

---

## Development

### Running Tests

```bash
# Backend
cd backend
python -m pytest

# Frontend
cd frontend
npm test
```

### Building for Production

```bash
# Backend
pip install -r requirements.txt

# Frontend
npm run build
```

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the documentation
- Review example configurations

---

**Candle Pattern Self-Learning AI v1.0.0**

*Institutional-grade trading platform for professional traders*
