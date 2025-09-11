# BacktestEngine Usage Guide

The SMC Forez BacktestEngine is fully runnable and ready to use! This guide shows you how to run backtests in different ways.

## Quick Start

### Option 1: Use the Standalone Runner (Easiest)

Run a complete backtest with sample data:

```bash
python run_backtest.py
```

This will:
- Generate sample OHLC data
- Create sample trading signals
- Run a complete backtest
- Display formatted results
- Export results to JSON

### Option 2: Use the Example Scripts

```bash
python examples/backtest_examples.py
```

This shows both simple and advanced usage patterns for developers.

### Option 3: Use BacktestEngine Directly in Your Code

```python
from smc_forez.backtesting import BacktestEngine
from smc_forez.signals.signal_generator import SignalType
import pandas as pd

# Create your OHLC data
data = pd.DataFrame({
    'Open': [1.1000, 1.1010, 1.1020],
    'High': [1.1015, 1.1025, 1.1035], 
    'Low': [1.0995, 1.1005, 1.1015],
    'Close': [1.1010, 1.1020, 1.1030],
}, index=pd.date_range('2023-01-01', periods=3, freq='1h'))

# Create your signals
signals = [{
    'timestamp': data.index[1],
    'signal_type': SignalType.BUY,
    'valid': True,
    'entry_price': 1.1020,
    'stop_loss': 1.1000,
    'take_profit': 1.1040
}]

# Run backtest
engine = BacktestEngine(initial_balance=1000.0)
results = engine.run_backtest(data, signals)

print(f"Final Balance: ${results['final_balance']:.2f}")
print(f"Total Return: {results['total_return']:.2f}%")
```

## Features

✅ **Fully Functional**: The BacktestEngine works out of the box  
✅ **No External Dependencies**: Runs without MetaTrader5 or live data  
✅ **Comprehensive Metrics**: Win rate, profit factor, drawdown, Sharpe ratio, etc.  
✅ **Flexible Input**: Supports custom OHLC data and signals  
✅ **Risk Management**: Built-in position sizing and risk controls  
✅ **Export Results**: Save results to JSON/CSV for further analysis  

## Configuration Options

```python
engine = BacktestEngine(
    initial_balance=10000.0,    # Starting balance
    commission=0.00007,         # Commission per trade (0.7 pips)
    risk_per_trade=0.02,        # Risk 2% per trade
    max_spread=2.0              # Maximum 2 pip spread
)
```

## Data Format

### OHLC Data (Required)
```python
data = pd.DataFrame({
    'Open': [1.1000, 1.1010],
    'High': [1.1015, 1.1025], 
    'Low': [1.0995, 1.1005],
    'Close': [1.1010, 1.1020],
}, index=pd.DatetimeIndex(['2023-01-01 00:00', '2023-01-01 01:00']))
```

### Signals Format (Required)
```python
signals = [{
    'timestamp': pd.Timestamp('2023-01-01 01:00'),
    'signal_type': SignalType.BUY,  # or SignalType.SELL
    'valid': True,
    'entry_price': 1.1020,
    'stop_loss': 1.1000,
    'take_profit': 1.1040
}]
```

## Results Structure

```python
results = {
    'performance_metrics': PerformanceMetrics(),  # Detailed metrics
    'trades': [...],                              # List of executed trades
    'equity_curve': [...],                        # Balance over time
    'final_balance': 10500.0,                     # Final account balance
    'total_return': 5.0                           # Total return percentage
}
```

## Performance Metrics

The engine calculates comprehensive performance metrics:

- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss
- **Total P&L**: Total profit/loss in account currency
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
- **Average Win/Loss**: Average profit/loss per trade
- **Consecutive Wins/Losses**: Maximum streaks
- **Recovery Factor**: Profit / Maximum drawdown

## Custom Data Sources

### From CSV File
```python
# Your CSV should have columns: Open, High, Low, Close
# and datetime index
data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)
```

### From Your Own Data Source
```python
# Convert your data to the required DataFrame format
data = pd.DataFrame({
    'Open': your_open_prices,
    'High': your_high_prices,
    'Low': your_low_prices,
    'Close': your_close_prices,
}, index=your_datetime_index)
```

## Tips for Success

1. **Use Realistic Data**: Include spread and slippage in your data
2. **Test Different Timeframes**: H1, H4, D1 for different strategies
3. **Validate Your Signals**: Ensure entry/SL/TP levels are logical
4. **Monitor Drawdown**: Keep maximum drawdown under 20%
5. **Export Results**: Save results for comparison and analysis

## Troubleshooting

### Import Error
If you get import errors, ensure you're running from the project root:
```bash
cd /path/to/SMC-Forez
python run_backtest.py
```

### No Trades Executed
Check that your signals have:
- Valid timestamps that exist in your data
- Logical entry/stop/target prices
- `valid: True` flag

### Poor Performance
- Verify your signal logic
- Check if spreads are too wide
- Ensure proper risk management
- Review your entry/exit criteria

## Next Steps

1. **Test with Real Data**: Use historical data from your broker
2. **Validate Signals**: Test your signal generation logic
3. **Optimize Parameters**: Experiment with different settings
4. **Paper Trade**: Test signals in a demo environment
5. **Live Trading**: Only after thorough backtesting validation

---

🎯 **The BacktestEngine is ready to use and fully functional!**

For more examples and advanced usage, check the `/examples` directory.