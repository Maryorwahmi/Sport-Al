# SMC-Forez-H4 Complete System Guide

## Quick Start Guide

This guide walks you through using the complete SMC-Forez-H4 system with backtesting and React frontend.

## System Architecture

```
SMC-Forez-H4 Complete System
├── Backend (Python)
│   ├── SMC Analysis Engine
│   ├── Backtesting System
│   └── API Server (FastAPI)
├── Frontend (React)
│   ├── Dashboard
│   ├── Backtest Results
│   └── Settings
└── Data Layer
    ├── MT5 Integration (Live)
    └── Mock Data (Testing)
```

## Installation

### 1. Backend Setup

```bash
# Navigate to SMC-Forez-H4 directory
cd SMC-Forez-H4

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, numpy; print('✅ Dependencies installed')"
```

### 2. Frontend Setup

```bash
# Navigate to React app directory
cd ../smc-forez-react

# Install Node.js dependencies
npm install

# Verify installation
npm run build
```

## Usage Scenarios

### Scenario 1: Run Standalone Backtest

**Use Case**: Test trading strategies on historical data without UI

```bash
cd SMC-Forez-H4/backtesting
python backtest_runner.py
```

**Interactive Prompts**:
1. Select Configuration (1-5)
   - 1: Quick Test (14 days)
   - 2: Standard Test (30 days) ← Recommended
   - 3: Long Test (60 days)
   - 4: Extended Test (90 days)
   - 5: Custom dates

2. Select Symbol (1-7)
   - 1: EURUSD ← Most popular
   - 2: GBPUSD
   - 3: USDJPY
   - ... and more

3. Select Timeframe (1-4)
   - 1: M15 (15 Minutes)
   - 2: H1 (1 Hour) ← Recommended
   - 3: H4 (4 Hours)
   - 4: D1 (Daily)

4. Enter Quality Threshold
   - Default: 0.70 (Professional)
   - Range: 0.50-0.85

**Output**:
- Console display of results
- JSON file saved to `backtesting/results/`

**Example Output**:
```
💰 Financial Performance:
   Total Return:        15.95%
   Final Balance:       $11,595.08
   Max Drawdown:        8.2%

📊 Trade Statistics:
   Total Trades:        47
   Winning Trades:      30
   Losing Trades:       17
   Win Rate:            63.8%

⚡ Performance Metrics:
   Profit Factor:       2.15
   Sharpe Ratio:        1.78
   Recovery Factor:     1.94
```

### Scenario 2: Run Backtest via Python Script

**Use Case**: Automated testing, batch processing

```python
# create_backtest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Timeframe, create_default_settings

# Create analyzer
settings, _ = create_default_settings()
analyzer = SMCAnalyzer(settings)

# Run backtest
results = analyzer.run_backtest(
    symbol='EURUSD',
    timeframe=Timeframe.H1,
    start_date='2024-01-01',
    end_date='2024-12-07',
    min_signal_quality=0.70
)

# Display results
if 'error' not in results:
    metrics = results['performance_metrics']
    print(f"Win Rate: {metrics.win_rate * 100:.1f}%")
    print(f"Profit Factor: {metrics.profit_factor:.2f}")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Trades: {metrics.total_trades}")
else:
    print(f"Error: {results['error']}")
```

### Scenario 3: Use React UI (Full System)

**Use Case**: Interactive monitoring and backtesting with visualization

#### Step 1: Start Backend API

```bash
cd SMC-Forez-H4
python api_server.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### Step 2: Start React Frontend

```bash
# In a new terminal
cd smc-forez-react
npm start
```

Expected output:
```
Compiled successfully!
Local:            http://localhost:3000
```

#### Step 3: Use the Interface

**Dashboard** (http://localhost:3000/dashboard)
- View live trading signals
- Monitor performance metrics
- Check system status
- Auto-refreshes every 30 seconds

**Backtest Results** (http://localhost:3000/backtest)
- Configure backtest parameters
- Run historical tests
- Visualize equity curve
- Download results as JSON

**Settings** (http://localhost:3000/settings)
- Adjust trading parameters
- Configure analysis settings
- Set backtest defaults
- Customize UI preferences

### Scenario 4: Production Deployment

**Backend Deployment**:
```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=/path/to/SMC-Forez-H4
export ENV=production

# Run with Gunicorn (recommended)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app
```

**Frontend Deployment**:
```bash
# Build for production
cd smc-forez-react
npm run build

# Serve with nginx or any static server
serve -s build -l 3000
```

## Configuration

### Backend Configuration

**File**: `SMC-Forez-H4/config.ini`

```ini
[Trading]
risk_per_trade = 0.01
min_rr_ratio = 2.0
max_spread = 3.0

[Analysis]
swing_length = 15
fvg_min_size = 8.0
order_block_lookback = 25

[Backtest]
initial_balance = 10000.0
commission = 0.00007
```

### Frontend Configuration

**File**: `smc-forez-react/.env`

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_REFRESH_INTERVAL=30000
REACT_APP_THEME=light
```

## Common Workflows

### Workflow 1: Daily Strategy Validation

```bash
# Morning: Run overnight backtest
cd SMC-Forez-H4/backtesting
python backtest_runner.py
# Select: Standard Test (30 days)
# Review: Win rate and profit factor

# If results good, proceed to live monitoring
cd ..
python api_server.py
# In another terminal:
cd ../smc-forez-react
npm start
```

### Workflow 2: Multi-Symbol Analysis

```python
# multi_symbol_test.py
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']

for symbol in symbols:
    print(f"\n{'='*50}")
    print(f"Testing {symbol}")
    print('='*50)
    
    results = analyzer.run_backtest(
        symbol=symbol,
        timeframe=Timeframe.H1,
        start_date='2024-11-01',
        end_date='2024-12-07',
        min_signal_quality=0.70
    )
    
    # Compare results across symbols
```

### Workflow 3: Strategy Optimization

```python
# optimize_quality.py
quality_levels = [0.50, 0.60, 0.70, 0.80, 0.85]

best_pf = 0
best_quality = 0

for quality in quality_levels:
    results = analyzer.run_backtest(
        symbol='EURUSD',
        timeframe=Timeframe.H1,
        start_date='2024-01-01',
        end_date='2024-12-07',
        min_signal_quality=quality
    )
    
    pf = results['performance_metrics'].profit_factor
    if pf > best_pf:
        best_pf = pf
        best_quality = quality
    
    print(f"Quality {quality}: PF = {pf:.2f}")

print(f"\nOptimal Quality: {best_quality} (PF: {best_pf:.2f})")
```

## Troubleshooting

### Issue 1: Module Import Errors

**Problem**: `ModuleNotFoundError: No module named 'pandas'`

**Solution**:
```bash
pip install -r requirements.txt
# or install specific packages:
pip install pandas numpy scipy pandas-ta
```

### Issue 2: React Build Fails

**Problem**: Build errors or warnings

**Solution**:
```bash
cd smc-forez-react
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue 3: Backend API Not Responding

**Problem**: Frontend shows "Backend offline"

**Solution**:
1. Check if API is running: http://localhost:8000/health
2. Verify .env file has correct API_URL
3. Check for CORS errors in browser console
4. Restart API server

### Issue 4: No Signals Generated

**Problem**: Backtest shows 0 signals

**Solution**:
1. Lower quality threshold (try 0.50)
2. Use longer time period (60 or 90 days)
3. Try different symbols
4. This is normal in some market conditions

### Issue 5: Low Performance Metrics

**Problem**: Backtest shows poor results

**Solution**:
1. Increase quality threshold (0.85)
2. Review signal generation logic
3. Test different timeframes
4. Analyze market conditions during period

## Best Practices

### 1. Backtesting
- ✅ Start with 30-day standard tests
- ✅ Use professional quality (0.70)
- ✅ Test multiple symbols
- ✅ Compare different timeframes
- ✅ Save and document results

### 2. Live Monitoring
- ✅ Start in signal-only mode
- ✅ Verify signals match backtest quality
- ✅ Monitor for consistent performance
- ✅ Keep detailed logs
- ✅ Review daily performance

### 3. System Maintenance
- ✅ Update dependencies regularly
- ✅ Review backtest results weekly
- ✅ Optimize settings based on performance
- ✅ Monitor system health
- ✅ Keep backups of configurations

## Performance Expectations

### Typical Backtest Results

**Good Performance**:
- Win Rate: > 55%
- Profit Factor: > 1.5
- Max Drawdown: < 15%
- Sharpe Ratio: > 1.0

**Excellent Performance**:
- Win Rate: > 65%
- Profit Factor: > 2.0
- Max Drawdown: < 10%
- Sharpe Ratio: > 1.5

### Signal Quality Distribution

- **Institutional (0.85+)**: 10-20% of signals
- **Professional (0.70-0.84)**: 40-60% of signals
- **Standard (0.50-0.69)**: 20-30% of signals

## Advanced Features

### Custom Backtest Script

```python
# advanced_backtest.py
from datetime import datetime, timedelta

# Multi-timeframe comparison
timeframes = [Timeframe.H1, Timeframe.H4, Timeframe.D1]

for tf in timeframes:
    results = analyzer.run_backtest(
        symbol='EURUSD',
        timeframe=tf,
        start_date='2024-01-01',
        end_date='2024-12-07',
        min_signal_quality=0.70
    )
    
    print(f"{tf.value}: {results['total_return']:.2f}%")
```

### Batch Processing

```python
# batch_backtest.py
import json
from pathlib import Path

output_dir = Path('batch_results')
output_dir.mkdir(exist_ok=True)

configs = [
    {'symbol': 'EURUSD', 'tf': Timeframe.H1, 'quality': 0.70},
    {'symbol': 'GBPUSD', 'tf': Timeframe.H4, 'quality': 0.70},
    {'symbol': 'USDJPY', 'tf': Timeframe.H1, 'quality': 0.85},
]

for config in configs:
    results = analyzer.run_backtest(
        symbol=config['symbol'],
        timeframe=config['tf'],
        start_date='2024-01-01',
        end_date='2024-12-07',
        min_signal_quality=config['quality']
    )
    
    # Save to file
    filename = f"{config['symbol']}_{config['tf'].value}.json"
    with open(output_dir / filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
```

## Support Resources

### Documentation
- Main README: `SMC-Forez-H4/README.md`
- Backtesting Guide: `SMC-Forez-H4/backtesting/README.md`
- React App Guide: `smc-forez-react/README.md`
- Testing Guide: `SMC-Forez-H4/TESTING_VALIDATION.md`

### Example Scripts
- `SMC-Forez-H4/examples/`
- `SMC-Forez-H4/backtesting/backtest_runner.py`

### Community
- GitHub Issues
- Documentation updates
- Feature requests

## Summary

The SMC-Forez-H4 system provides:

1. **Comprehensive Backtesting**
   - Multiple configurations (14-90 days)
   - Interactive CLI
   - JSON export
   - Detailed metrics

2. **Professional React UI**
   - Live signal monitoring
   - Visual backtesting
   - Settings management
   - Real-time updates

3. **Complete Documentation**
   - Installation guides
   - Usage examples
   - Troubleshooting
   - Best practices

**Get Started**:
```bash
# Quickest way to test
cd SMC-Forez-H4/backtesting
python backtest_runner.py
```

**For Full System**:
```bash
# Terminal 1: Backend
cd SMC-Forez-H4
python api_server.py

# Terminal 2: Frontend
cd smc-forez-react
npm start
```

---

**SMC-Forez-H4 Complete System v2.0**
*Professional Smart Money Concepts Trading with Comprehensive Backtesting*
