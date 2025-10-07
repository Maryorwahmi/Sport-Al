# SMC-Forez-H4 Backtesting System

## Overview

The SMC-Forez-H4 Backtesting System provides comprehensive historical validation of Smart Money Concepts (SMC) trading strategies with multi-timeframe analysis capabilities.

## Features

✅ **Multi-Timeframe Analysis**
- Synchronous analysis across H4, H1, and M15 timeframes
- Historical data caching for efficient backtesting
- Weighted scoring system (H4=50%, H1=30%, M15=20%)

✅ **Comprehensive Performance Metrics**
- Win Rate, Profit Factor, Sharpe Ratio
- Maximum Drawdown tracking
- Risk/Reward analysis
- Trade quality statistics
- Signal quality breakdown

✅ **Predefined Configurations**
- Quick Test (14 days) - Fast validation
- Standard Test (30 days) - General validation
- Long Test (60 days) - Thorough analysis
- Extended Test (90 days) - Complete validation
- Custom - User-defined date ranges

✅ **Interactive CLI**
- User-friendly command-line interface
- Step-by-step configuration selection
- Real-time progress updates
- Formatted results display

✅ **JSON Export**
- Complete backtest results
- Trade-by-trade breakdown
- Performance metrics
- Equity curve data

## Installation

### Prerequisites

```bash
# From SMC-Forez-H4 directory
cd /path/to/SMC-Forez-H4
pip install -r requirements.txt
```

### Required Packages
- pandas >= 1.5.0
- numpy >= 1.21.0
- Python 3.8+

## Quick Start

### Method 1: Interactive Runner (Recommended)

```bash
cd SMC-Forez-H4/backtesting
python backtest_runner.py
```

Follow the interactive prompts to:
1. Select backtest configuration (14/30/60/90 days or custom)
2. Choose currency pair
3. Select timeframe
4. Set signal quality threshold
5. Run backtest and view results

### Method 2: Direct Python Import

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    end_date='2024-12-31',
    min_signal_quality=0.70
)

# Access results
print(f"Win Rate: {results['performance_metrics'].win_rate * 100:.1f}%")
print(f"Profit Factor: {results['performance_metrics'].profit_factor:.2f}")
```

## Backtest Configurations

### 1. Quick Test (14 Days)
**Purpose**: Fast validation for development and testing
- **Duration**: 14 days
- **Use Case**: Quick strategy validation, code testing
- **Typical Signals**: 10-30 depending on timeframe

### 2. Standard Test (30 Days)
**Purpose**: Standard backtesting for general validation
- **Duration**: 30 days
- **Use Case**: Regular strategy evaluation
- **Typical Signals**: 20-60 depending on timeframe

### 3. Long Test (60 Days)
**Purpose**: Comprehensive analysis with various market conditions
- **Duration**: 60 days
- **Use Case**: Thorough strategy validation
- **Typical Signals**: 40-120 depending on timeframe

### 4. Extended Test (90 Days)
**Purpose**: Complete validation across multiple market phases
- **Duration**: 90 days
- **Use Case**: Final validation before live trading
- **Typical Signals**: 60-180 depending on timeframe

### 5. Custom Configuration
**Purpose**: User-defined date ranges
- **Duration**: Any range
- **Use Case**: Specific period analysis, historical events

## Supported Timeframes

| Timeframe | Code | Description | Bars per Day |
|-----------|------|-------------|--------------|
| M15 | Timeframe.M15 | 15 Minutes | 96 |
| H1 | Timeframe.H1 | 1 Hour | 24 |
| H4 | Timeframe.H4 | 4 Hours | 6 |
| D1 | Timeframe.D1 | Daily | 1 |

## Supported Currency Pairs

### Major Pairs
- EURUSD - Euro / US Dollar
- GBPUSD - British Pound / US Dollar
- USDJPY - US Dollar / Japanese Yen
- AUDUSD - Australian Dollar / US Dollar
- USDCAD - US Dollar / Canadian Dollar
- NZDUSD - New Zealand Dollar / US Dollar
- USDCHF - US Dollar / Swiss Franc

### Custom Symbols
You can enter any valid MetaTrader 5 symbol when selecting "Custom Symbol"

## Signal Quality Thresholds

The system filters signals based on quality scores:

| Quality Level | Threshold | Description |
|---------------|-----------|-------------|
| Standard | 0.50 | Basic quality signals |
| **Professional** | **0.70** | **Recommended default** |
| Institutional | 0.85 | Highest quality only |

**Recommendation**: Start with 0.70 for professional-grade signals with good balance between quantity and quality.

## Performance Metrics Explained

### Financial Metrics

**Total Return**
- Percentage gain/loss from initial balance
- Formula: `(Final Balance - Initial Balance) / Initial Balance * 100`

**Final Balance**
- Account balance at end of backtest period
- Starts from $10,000 default

**Max Drawdown**
- Largest peak-to-trough decline
- Lower is better
- Formula: `(Peak - Trough) / Peak * 100`

### Trade Statistics

**Win Rate**
- Percentage of profitable trades
- Formula: `Winning Trades / Total Trades * 100`
- Good: >55%, Excellent: >65%

**Profit Factor**
- Ratio of gross profit to gross loss
- Formula: `Gross Profit / Gross Loss`
- Good: >1.5, Excellent: >2.0

**Sharpe Ratio**
- Risk-adjusted return measure
- Good: >1.0, Excellent: >2.0

**Recovery Factor**
- Ability to recover from drawdowns
- Formula: `Total Return / Max Drawdown`
- Good: >2.0, Excellent: >5.0

### Trade Quality

**Average Win/Loss**
- Average profit/loss per trade in dollars and pips
- Higher average win relative to loss is better

**Largest Win/Loss**
- Best and worst single trades
- Helps identify outliers

**Consecutive Wins/Losses**
- Maximum consecutive winning/losing streaks
- Indicates consistency

## Output Files

### Results Directory
All backtest results are saved to: `SMC-Forez-H4/backtesting/results/`

### File Format
```
backtest_{SYMBOL}_{TIMEFRAME}_{TIMESTAMP}.json
```

Example: `backtest_EURUSD_H1_20241215_143022.json`

### JSON Structure
```json
{
  "metadata": {
    "symbol": "EURUSD",
    "timeframe": "H1",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "generated_at": "2024-12-15T14:30:22"
  },
  "performance_metrics": {
    "total_trades": 45,
    "winning_trades": 28,
    "losing_trades": 17,
    "win_rate": 0.622,
    "profit_factor": 2.15,
    ...
  },
  "trades": [...],
  "equity_curve": [...],
  "total_return": 15.95,
  "final_balance": 11595.08
}
```

## Advanced Usage

### Custom Backtest Script

```python
#!/usr/bin/env python3
"""Custom backtest script"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Timeframe, create_default_settings

def run_multi_symbol_backtest():
    """Run backtest across multiple symbols"""
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    settings, _ = create_default_settings()
    analyzer = SMCAnalyzer(settings)
    
    results = {}
    for symbol in symbols:
        print(f"\nTesting {symbol}...")
        result = analyzer.run_backtest(
            symbol=symbol,
            timeframe=Timeframe.H1,
            start_date='2024-01-01',
            end_date='2024-12-31',
            min_signal_quality=0.70
        )
        results[symbol] = result
    
    # Compare results
    for symbol, result in results.items():
        metrics = result['performance_metrics']
        print(f"\n{symbol}:")
        print(f"  Win Rate: {metrics.win_rate * 100:.1f}%")
        print(f"  Profit Factor: {metrics.profit_factor:.2f}")
        print(f"  Total Return: {result['total_return']:.2f}%")

if __name__ == '__main__':
    run_multi_symbol_backtest()
```

### Batch Processing

```python
#!/usr/bin/env python3
"""Batch backtest multiple configurations"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Timeframe, create_default_settings

def run_batch_backtests():
    """Run multiple backtests with different parameters"""
    settings, _ = create_default_settings()
    analyzer = SMCAnalyzer(settings)
    
    # Test different quality thresholds
    quality_levels = [0.50, 0.70, 0.85]
    
    for quality in quality_levels:
        print(f"\n{'='*50}")
        print(f"Testing with quality threshold: {quality:.2f}")
        print(f"{'='*50}")
        
        results = analyzer.run_backtest(
            symbol='EURUSD',
            timeframe=Timeframe.H1,
            start_date='2024-01-01',
            end_date='2024-12-31',
            min_signal_quality=quality
        )
        
        metrics = results['performance_metrics']
        print(f"Signals Generated: {results['signals_generated']}")
        print(f"Win Rate: {metrics.win_rate * 100:.1f}%")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")

if __name__ == '__main__':
    run_batch_backtests()
```

## Troubleshooting

### Issue: Import Errors

```bash
# Make sure you're in the correct directory
cd SMC-Forez-H4/backtesting
python backtest_runner.py
```

### Issue: No Data Available

The system uses mock data for backtesting when MT5 is not available. This is normal and expected.

### Issue: Low Number of Signals

- Try lowering the signal quality threshold (e.g., from 0.70 to 0.50)
- Use a longer backtest period (60 or 90 days)
- Check that the timeframe is appropriate for your testing needs

### Issue: High Drawdown

- Review signal quality settings
- Consider using higher quality threshold (0.85)
- Analyze individual trades to identify losing patterns

## Performance Optimization

### Data Caching

The system caches historical data for multi-timeframe analysis:
- H4 data cached for trend analysis
- H1 data cached for signal timeframe
- M15 data cached for entry timing

This significantly improves backtest performance.

### Memory Management

For long backtests (>90 days):
- Consider running in smaller chunks
- Export results periodically
- Clear old result files

## Integration with Live Trading

After successful backtesting:

1. Review backtest results thoroughly
2. Understand key performance metrics
3. Test on different market conditions
4. Start with signal-only mode in live trading
5. Gradually transition to live execution

## Best Practices

### 1. Start Conservative
- Begin with 14-day quick tests
- Use professional quality threshold (0.70)
- Test on familiar currency pairs

### 2. Validate Thoroughly
- Run 60-90 day backtests before live trading
- Test across different market conditions
- Validate across multiple currency pairs

### 3. Document Results
- Keep backtest results organized
- Compare different configurations
- Track improvements over time

### 4. Continuous Improvement
- Review losing trades
- Identify patterns in winning trades
- Adjust signal quality thresholds based on results

## Support

For issues, questions, or feature requests:
1. Check this README first
2. Review the main SMC-Forez-H4 README
3. Open an issue on GitHub
4. Check example scripts in the repository

## Version History

**v2.0** - Current
- ✅ Multi-timeframe synchronous backtesting
- ✅ Interactive CLI runner
- ✅ Comprehensive performance metrics
- ✅ JSON export functionality
- ✅ Predefined configurations (14/30/60/90 days)
- ✅ Signal quality filtering
- ✅ Historical data caching

## License

This backtesting system is part of the SMC-Forez-H4 project and follows the same license terms.

## Disclaimer

**Important**: Backtesting results are based on historical data and do not guarantee future performance. Always:
- Test thoroughly before live trading
- Start with small position sizes
- Use proper risk management
- Monitor performance continuously
- Never risk more than you can afford to lose

---

**SMC-Forez-H4 Backtesting System v2.0**
*Professional Smart Money Concepts Backtesting*
