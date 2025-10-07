# SMC Forez - Comprehensive Backtesting System

## Overview

This backtesting system provides comprehensive performance analysis for the SMC Forez trading strategy, including all critical metrics for evaluating trading system quality and robustness.

## Features

### Performance Metrics

1. **Win Rate** - Percentage of profitable trades
2. **Profit Factor** - Ratio of gross profit to gross loss
3. **Expected Payoff** - Average profit/loss per trade
4. **Maximum Drawdown** - Largest peak-to-trough decline (absolute and percentage)
5. **Sharpe Ratio** - Risk-adjusted returns
6. **Recovery Factor** - Total return divided by maximum drawdown
7. **Average Trade Duration** - Mean time in trade (overall, winning, and losing)
8. **Consecutive Losses** - Stress test showing maximum consecutive losing trades

### Multi-Timeframe Robustness

The backtesting system uses **synchronous multi-timeframe analysis** to accurately simulate the live trading system:

- **H4, H1, M15 timeframes** are analyzed simultaneously
- Data is **cached for all timeframes** before signal generation
- **Aligned timestamps** ensure accurate multi-timeframe confluence
- Signals are generated using the same logic as live trading

This approach ensures the backtest accurately represents how the system performs in live trading conditions.

## Usage

### Quick Start

```bash
cd SMC-Forez-H4
python run_backtest.py
```

The script will present an interactive menu with the following options:

### Configuration Options

1. **Quick Run** (14 days, H1)
   - Fast validation test
   - Good for quick strategy iterations
   - Uses H4, H1, M15 multi-timeframe analysis

2. **Standard Run** (30 days, H1)
   - Comprehensive testing
   - Recommended for most scenarios
   - Uses H4, H1, M15 multi-timeframe analysis

3. **Long Run** (60 days, H4)
   - Thorough analysis with more data
   - Higher timeframe focus
   - Uses D1, H4, H1 multi-timeframe analysis

4. **Extended Run** (90 days, H4)
   - Deep validation for production systems
   - Maximum confidence in results
   - Uses D1, H4, H1 multi-timeframe analysis

5. **Custom Run**
   - User-defined parameters
   - Specify symbol, timeframe, days, and initial balance

### Example Usage

```python
from backtesting.backtest_runner import BacktestRunner, BacktestConfiguration

# Create a standard run configuration
config = BacktestConfiguration.standard_run(symbol="EURUSD")

# Run the backtest
runner = BacktestRunner(config)
results = runner.run()

# Print results
runner.print_results(results)

# Export to JSON
runner.export_results(results)
```

### Custom Configuration

```python
# Create custom configuration
config = BacktestConfiguration.custom_run(
    symbol="GBPUSD",
    timeframe="H4",
    days=45,
    initial_balance=10000.0
)

runner = BacktestRunner(config)
results = runner.run()
```

## Output

### Console Output

The backtest displays:
- Configuration summary
- Progress indicators
- Comprehensive results table with all metrics
- Multi-timeframe robustness information

### JSON Export

Results are automatically exported to JSON file with:
- Complete configuration
- All performance metrics
- Individual trade details
- Equity curve data
- Timestamps and metadata

Example filename: `backtest_EURUSD_H1_20240107_143022.json`

## Interpreting Results

### Good Trading System Indicators

- **Win Rate**: 40-60% (quality over quantity)
- **Profit Factor**: > 2.0 (professional level)
- **Expected Payoff**: Positive value
- **Max Drawdown**: < 20% of balance
- **Sharpe Ratio**: > 1.0 (good), > 2.0 (excellent)
- **Recovery Factor**: > 3.0
- **Max Consecutive Losses**: Monitor for risk management

### Multi-Timeframe Robustness

The system tests signal quality across multiple timeframes:
- Signals must align across H4, H1, and M15
- Higher timeframe bias is respected
- Lower timeframe provides precise entry
- All timeframes analyzed synchronously

## Architecture

### Components

1. **BacktestEngine** (`backtest_engine.py`)
   - Core backtesting logic
   - Trade execution simulation
   - Performance metrics calculation
   - Multi-timeframe data caching

2. **BacktestRunner** (`backtest_runner.py`)
   - Orchestrates backtest execution
   - Manages multi-timeframe signal generation
   - Results formatting and export
   - Configuration management

3. **BacktestConfiguration** (dataclass)
   - Predefined run types (Quick, Standard, Long, Extended)
   - Custom configuration support
   - Multi-timeframe settings

### Data Flow

```
1. Load historical data for all timeframes (H4, H1, M15)
   ↓
2. Cache data for synchronous access
   ↓
3. Iterate through primary timeframe bars
   ↓
4. For each bar:
   a. Get aligned data for all timeframes up to current time
   b. Run multi-timeframe SMC analysis
   c. Generate signal using same logic as live system
   d. Execute trade if signal valid (RR >= 2.0, quality >= 70%)
   ↓
5. Calculate comprehensive metrics
   ↓
6. Export results
```

## Requirements

- Python 3.8+
- pandas
- numpy
- MetaTrader5 (optional, will use mock data if unavailable)

## Notes

### Signal Quality

The backtest uses the same quality filters as live trading:
- Minimum confluence score: 7/15
- Minimum risk-reward ratio: 2.0
- Quality score threshold: 70%

### Commission and Slippage

- Default commission: 0.7 pips per trade
- Spread: Configurable maximum (default 2.0 pips)
- Slippage: Not modeled (conservative approach)

### Risk Management

- Position sizing based on stop loss distance
- Fixed risk per trade (default 1.5%)
- Automatic position size calculation

## Troubleshooting

### No Data Available

If MT5 is not connected, the system will use mock data. This is acceptable for testing the backtest system itself, but real historical data is needed for accurate results.

### Insufficient Data

Ensure enough historical bars are available:
- Quick run: ~500 bars minimum
- Standard run: ~1000 bars minimum
- Long run: ~2000 bars minimum

### Low Signal Count

If few signals are generated:
- Check timeframe alignment
- Verify confluence score settings
- Review signal quality thresholds

## Future Enhancements

- Walk-forward analysis
- Monte Carlo simulation
- Parameter optimization
- Multi-symbol backtesting
- Custom metrics plugins
- Advanced visualizations

## License

MIT License - See main repository LICENSE file
