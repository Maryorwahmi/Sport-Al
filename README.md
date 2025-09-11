# SMC-Forez
**Professional Forex Analyzer using Smart Money Concepts (SMC) and Structural Market Analysis**

A comprehensive, modular, and production-ready Python-based Forex analysis tool that detects high-probability trading opportunities using Smart Money Concepts, Market Structure Analysis, and Multi-Timeframe confluence.

## Features

### 🔗 Data Source Integration
- **MetaTrader 5 (MT5) Integration**: Fetch live and historical Forex data
- **Multiple Timeframes**: Support for M1, M5, M15, H1, H4, D1
- **Real-time Data**: Live market data with bid/ask prices and spreads
- **Symbol Information**: Access to currency pair specifications

### 📊 Market Structure Analysis
- **Swing Point Detection**: Identify swing highs and lows
- **Trend Analysis**: Detect uptrends, downtrends, and consolidation
- **Break of Structure (BOS)**: Identify structural market breaks
- **Change of Character (CHOCH)**: Detect trend changes
- **Support/Resistance Levels**: Key market structure levels

### 🧠 Smart Money Concepts (SMC)
- **Fair Value Gaps (FVGs)**: Detect and track price gaps
- **Order Blocks**: Identify institutional order zones
- **Liquidity Zones**: Find areas of clustered stops
- **Supply & Demand Zones**: Detect institutional accumulation/distribution areas
- **Confluence Analysis**: Multi-factor confirmation system

### 📈 Signal Generation
- **High-Probability Signals**: Confluence-based entry signals
- **Risk Management**: Automated stop loss and take profit calculation
- **Multi-Factor Confirmation**: Combine trend, structure, and SMC analysis
- **Risk/Reward Optimization**: Minimum R:R ratio filtering

### ⏱️ Multi-Timeframe Analysis
- **Cross-Timeframe Alignment**: Align signals across multiple timeframes
- **Trend Confirmation**: Higher timeframe trend with lower timeframe entries
- **Entry Precision**: Optimal timeframe selection for entries
- **Confluence Scoring**: Weighted timeframe analysis

### 🔙 Backtesting & Performance Analysis
- **Historical Testing**: Comprehensive backtesting on MT5 data
- **Performance Metrics**: Win rate, profit factor, drawdown, Sharpe ratio
- **Trade Analysis**: Detailed trade breakdown and statistics
- **Export Options**: CSV and JSON result export

## Installation

### Prerequisites
- Python 3.8 or higher
- MetaTrader 5 terminal (for live data)
- Required Python packages (see requirements.txt)

### Install from Source
```bash
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez
pip install -r requirements.txt
pip install -e .
```

### Dependencies
```
MetaTrader5>=5.0.40
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
scipy>=1.9.0
plotly>=5.10.0
yfinance>=0.1.87
ta-lib>=0.4.0
dataclasses-json>=0.5.7
python-dotenv>=0.19.0
```

## Quick Start

### Basic Usage
```python
from smc_forez import SMCAnalyzer, Settings
from smc_forez.config.settings import Timeframe

# Initialize analyzer with default settings
analyzer = SMCAnalyzer()

# Connect to MT5 (configure credentials first)
if analyzer.connect_data_source():
    
    # Single timeframe analysis
    analysis = analyzer.analyze_single_timeframe("EURUSD", Timeframe.H1)
    print(analyzer.get_analysis_summary(analysis))
    
    # Multi-timeframe analysis
    mtf_analysis = analyzer.analyze_multi_timeframe("EURUSD")
    print(analyzer.get_analysis_summary(mtf_analysis))
    
    # Scan for opportunities
    major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    opportunities = analyzer.get_current_opportunities(major_pairs)
    
    for opp in opportunities:
        print(f"Opportunity: {opp['symbol']} - {opp['recommendation']['action']}")
    
    analyzer.disconnect_data_source()
```

### MT5 Configuration
```python
from smc_forez import Settings

# Configure MT5 connection
settings = Settings()
settings.mt5_login = your_mt5_login
settings.mt5_password = "your_mt5_password"
settings.mt5_server = "your_mt5_server"

analyzer = SMCAnalyzer(settings)
```

### Backtesting
```python
# Run backtest on historical data
results = analyzer.run_backtest(
    symbol="EURUSD",
    timeframe=Timeframe.H1,
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Display results
metrics = results['performance_metrics']
print(f"Total Return: {results['total_return']:.2f}%")
print(f"Win Rate: {metrics.win_rate * 100:.1f}%")
print(f"Profit Factor: {metrics.profit_factor:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")

# Export results
analyzer.backtest_engine.export_results(results, "backtest_results.json")
```

## Configuration

### Settings Customization
```python
from smc_forez import Settings
from smc_forez.config.settings import Timeframe

settings = Settings()

# Trading settings
settings.trading.risk_per_trade = 0.02  # 2% risk per trade
settings.trading.min_rr_ratio = 2.0     # Minimum 2:1 R:R ratio
settings.trading.max_spread = 3.0       # Maximum 3 pip spread

# Analysis settings
settings.analysis.swing_length = 15         # Swing detection period
settings.analysis.fvg_min_size = 8.0       # Minimum FVG size in pips
settings.analysis.order_block_lookback = 25 # Order block detection period
settings.analysis.liquidity_threshold = 0.15 # Liquidity zone sensitivity

# Timeframes
settings.timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]

# Backtesting settings
settings.backtest.initial_balance = 25000.0
settings.backtest.commission = 0.00008  # 0.8 pips commission

analyzer = SMCAnalyzer(settings)
```

## Examples

### Running Examples
```bash
# Basic usage example
python examples/basic_usage.py

# Backtesting example with sample data
python examples/backtest_example.py
```

### Market Structure Analysis
```python
# Analyze market structure
market_structure = analyzer.structure_analyzer.get_market_structure_levels(data)

print(f"Trend Direction: {market_structure['trend_direction']}")
print(f"Swing Highs: {len(market_structure['swing_high_levels'])}")
print(f"Swing Lows: {len(market_structure['swing_low_levels'])}")
print(f"Structure Breaks: {len(market_structure['structure_breaks'])}")
```

### Smart Money Concepts Analysis
```python
# Analyze SMC patterns
smc_analysis = analyzer.smc_analyzer.get_smart_money_analysis(data)

print(f"Active FVGs: {len(smc_analysis['fair_value_gaps']['active'])}")
print(f"Valid Order Blocks: {len(smc_analysis['order_blocks']['valid'])}")
print(f"Unswept Liquidity: {len(smc_analysis['liquidity_zones']['unswept'])}")
print(f"Supply/Demand Zones: {len(smc_analysis['supply_demand_zones']['valid'])}")
```

## API Reference

### Main Classes

#### `SMCAnalyzer`
Main analyzer class that coordinates all components.

**Methods:**
- `connect_data_source()`: Connect to MT5
- `analyze_single_timeframe(symbol, timeframe)`: Single TF analysis
- `analyze_multi_timeframe(symbol, timeframes)`: Multi-TF analysis
- `get_current_opportunities(symbols)`: Scan for opportunities
- `run_backtest(symbol, timeframe, start_date, end_date)`: Run backtest

#### `MarketStructureAnalyzer`
Analyzes market structure and trends.

**Methods:**
- `find_swing_points(df)`: Detect swing highs/lows
- `identify_trend_direction(df, swing_points)`: Determine trend
- `detect_structure_breaks(df, swing_points)`: Find BOS/CHOCH

#### `SmartMoneyAnalyzer`
Analyzes Smart Money Concepts patterns.

**Methods:**
- `detect_fair_value_gaps(df)`: Find FVGs
- `detect_order_blocks(df)`: Identify order blocks
- `detect_liquidity_zones(df)`: Find liquidity areas
- `detect_supply_demand_zones(df)`: Identify S/D zones

#### `SignalGenerator`
Generates trading signals based on confluence.

**Methods:**
- `generate_signal(market_structure, smc_analysis, price)`: Generate signal
- `calculate_confluence_score(...)`: Calculate confluence
- `get_signal_summary(signal)`: Human-readable summary

#### `BacktestEngine`
Backtesting and performance analysis.

**Methods:**
- `run_backtest(data, signals)`: Execute backtest
- `export_results(results, filename)`: Export results

## Performance Metrics

The backtesting engine provides comprehensive performance metrics:

- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss
- **Total Return**: Overall percentage return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
- **Average Win/Loss**: Average profit/loss per trade
- **Consecutive Wins/Losses**: Maximum consecutive streaks
- **Recovery Factor**: Total return / Maximum drawdown

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and research purposes only. Trading forex carries a high level of risk and may not be suitable for all investors. Past performance is not indicative of future results. Always conduct your own research and consider seeking advice from licensed financial advisors before making trading decisions.

## Support

For support, feature requests, or bug reports, please open an issue on GitHub or contact the development team.

---

**SMC-Forez** - Professional Forex Analysis with Smart Money Concepts
