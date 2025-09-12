# SMC-Forez v2.0 🚀
**Professional Forex Analyzer using Smart Money Concepts (SMC) and Structural Market Analysis**

A comprehensive, modular, and **production-ready** Python-based Forex analysis tool that detects high-probability trading opportunities using Smart Money Concepts, Market Structure Analysis, and Multi-Timeframe confluence.

---

## 🆕 Version 2.0 - Production Ready!

### **🔥 Major New Features:**
- **Live Trading Execution** with real-time MT5 integration
- **Professional Logging System** with JSON/CSV export
- **Advanced Risk Management** with portfolio controls
- **Visual Chart Analysis** with SMC pattern overlays
- **Production CLI** with multiple operation modes
- **Comprehensive Session Reporting** and performance tracking

---

## ⚡ Quick Start

### **1. Analysis Mode (Safe)**
```bash
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez
pip install pandas numpy
python production_runner.py --mode analyze --symbols EURUSD GBPUSD
```

### **2. Live Signal Monitoring**
```bash
python production_runner.py --mode live --symbols EURUSD GBPUSD USDJPY
```

### **3. Backtesting**
```bash
python production_runner.py --mode backtest --symbol EURUSD --timeframe H1 --days 60
```

---

## 🎯 Core Features

### 🔗 **Data Source Integration**
- **MetaTrader 5 (MT5) Integration**: Live and historical data
- **Multiple Timeframes**: M1, M5, M15, H1, H4, D1
- **Real-time Data**: Live ticks with spread monitoring
- **Graceful Fallback**: Mock data when MT5 unavailable

### 📊 **Market Structure Analysis**
- **Swing Point Detection**: Automatic high/low identification
- **Trend Analysis**: Uptrend, downtrend, consolidation detection
- **Break of Structure (BOS)**: Structural market breaks
- **Change of Character (CHOCH)**: Trend reversal signals
- **Support/Resistance**: Dynamic level identification

### 🧠 **Smart Money Concepts (SMC)**
- **Fair Value Gaps (FVGs)**: Price gap detection and tracking
- **Order Blocks**: Institutional order zone identification
- **Liquidity Zones**: Stop hunt area detection
- **Supply & Demand Zones**: Accumulation/distribution areas
- **Confluence Analysis**: Multi-factor signal confirmation

### 📈 **Live Trading System** ⭐ **NEW**
- **Real-time Execution**: Live order placement via MT5
- **Continuous Monitoring**: 30-second refresh cycles
- **Risk Management**: Position sizing and portfolio controls
- **Signal Filtering**: High-quality signal detection only
- **Graceful Shutdown**: Clean exit with Ctrl+C

### 📋 **Professional Logging** ⭐ **NEW**
- **Structured Logging**: INFO, DEBUG, WARNING, ERROR levels
- **JSON Export**: All signals and trades for analysis
- **CSV Export**: Spreadsheet-compatible data
- **Session Reports**: Comprehensive performance summaries
- **Real-time Console**: Professional formatted output

### 🛡️ **Advanced Risk Management** ⭐ **NEW**
- **Portfolio Risk Control**: Maximum 5% total exposure
- **Position Sizing**: Dynamic calculation based on account
- **Correlation Management**: Currency pair correlation matrix
- **Daily Limits**: Trade count and loss limits
- **Risk Profiles**: Conservative, Moderate, Aggressive

### 📊 **Visual Analysis** ⭐ **NEW**
- **Professional Charts**: Candlesticks with SMC overlays
- **Pattern Visualization**: FVGs, Order Blocks, Liquidity zones
- **Backtesting Charts**: Equity curves and performance metrics
- **Market Structure**: Trend lines and support/resistance

### ⏱️ **Multi-Timeframe Analysis**
- **Cross-Timeframe Alignment**: Signal confluence across timeframes
- **Trend Confirmation**: Higher TF trend with lower TF entries
- **Entry Precision**: Optimal timeframe selection
- **Confluence Scoring**: Weighted analysis results

### 🔙 **Enhanced Backtesting** ✅ **IMPROVED**
- **Historical Testing**: Comprehensive backtesting engine
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio
- **Trade Analysis**: Detailed breakdown and statistics
- **Export Options**: JSON and CSV result export
- **Sample Data**: Built-in data generator for testing

---

## 🚀 Production Runner

The new `production_runner.py` provides three professional operation modes:

### **1. Live Mode** - Real-time trading
```bash
# Signal monitoring only (SAFE)
python production_runner.py --mode live --symbols EURUSD GBPUSD

# Live trading execution (requires confirmation)
python production_runner.py --mode live --symbols EURUSD --execute
```

### **2. Analysis Mode** - One-time analysis
```bash
python production_runner.py --mode analyze --symbols EURUSD GBPUSD USDJPY
```

### **3. Backtest Mode** - Historical testing
```bash
python production_runner.py --mode backtest --symbol EURUSD --timeframe H1 --days 60
```

---

## 📊 Professional Output Examples

### **Live Signal Monitoring:**
```
🚀 LIVE SYSTEM STARTED
📈 Mode: SIGNAL ONLY
📊 Monitoring 3 symbols
⏱️ Refresh: 30s

01:15:30 | INFO | 🔍 Scanning 3 symbols for opportunities...
01:15:35 | INFO | 🎯 Found 2 potential opportunities
01:15:35 | INFO | 📡 SIGNAL: EURUSD BUY @1.0850 | Confidence: HIGH | R:R 2.50
01:15:35 | INFO | 📡 SIGNAL: GBPUSD SELL @1.2750 | Confidence: MODERATE | R:R 2.00
```

### **Risk Management Report:**
```
📊 RISK MANAGEMENT REPORT
═══════════════════════════════════════
💰 Account Balance:     $10,000.00
📈 Daily P&L:           $+125.50 (+1.26%)
🎯 Risk Level:          CONSERVATIVE

📍 POSITION RISK
Open Positions:         2/3
Portfolio Risk:         2.45%
Remaining Capacity:     2.55%
Leverage Ratio:         1.25x
```

### **Session Summary:**
```
🎯 SMC FOREZ SESSION SUMMARY
═══════════════════════════════════════
📅 Session: 2024-01-15 09:00:00 - 17:30:00
⏱️ Uptime: 510.0 minutes

📊 SIGNAL STATISTICS
Total Signals Generated: 47
Symbols Analyzed: 12
High Confidence Signals: 23

💼 TRADING STATISTICS
Trades Executed: 8
Winning Trades: 6
Losing Trades: 2
Win Rate: 75.0%
Total P&L: $487.50
```

---

## 🔧 Installation

### **Quick Install (Testing Only):**
```bash
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez
pip install pandas numpy
python production_runner.py --mode analyze --symbols EURUSD
```

### **Full Installation:**
```bash
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez
pip install -r requirements.txt
pip install -e .
```

### **Dependencies:**
```
MetaTrader5>=5.0.40    # For live trading
pandas>=1.5.0          # Data processing
numpy>=1.21.0          # Numerical computing
matplotlib>=3.5.0      # Charting (optional)
scipy>=1.9.0           # Statistical analysis
```

---

## ⚙️ Configuration

### **Risk Profiles:**
```python
# Conservative (Default)
settings.trading.risk_per_trade = 0.01      # 1% per trade
settings.execution.max_open_trades = 3       # 3 positions max

# Moderate  
settings.trading.risk_per_trade = 0.02      # 2% per trade
settings.execution.max_open_trades = 5       # 5 positions max

# Aggressive
settings.trading.risk_per_trade = 0.03      # 3% per trade
settings.execution.max_open_trades = 8       # 8 positions max
```

### **Analysis Settings:**
```python
settings.analysis.swing_length = 20         # Swing detection period
settings.analysis.fvg_min_size = 8.0       # Minimum FVG size in pips
settings.analysis.order_block_lookback = 30 # Order block detection period
```

---

## 🛡️ Safety Features

### **Multiple Safety Layers:**
1. **Default Signal-Only Mode** - No execution unless explicitly enabled
2. **Confirmation Prompts** - Must type 'CONFIRM' for live trading
3. **Conservative Defaults** - 1% risk, 2:1 R:R minimum
4. **Daily Limits** - Automatic shutdown at risk limits
5. **Graceful Shutdown** - Clean exit with Ctrl+C

### **Risk Management:**
- Portfolio risk limit: 5% maximum exposure
- Daily loss limit: 2% maximum daily loss
- Position correlation monitoring
- Dynamic position sizing

---

## 📈 API Reference

### **Quick Usage:**
```python
from smc_forez import SMCAnalyzer, Settings
from smc_forez.execution import LiveExecutor, ExecutionSettings

# Analysis
analyzer = SMCAnalyzer()
analysis = analyzer.analyze_multi_timeframe("EURUSD")
print(analyzer.get_analysis_summary(analysis))

# Live execution (signal only)
settings = ExecutionSettings(enable_execution=False)
executor = LiveExecutor(execution_settings=settings)
executor.start_live_execution(['EURUSD', 'GBPUSD'])
```

### **Risk Management:**
```python
from smc_forez.utils.risk_manager import create_risk_manager

risk_manager = create_risk_manager('conservative', 10000)
can_trade, reason = risk_manager.can_trade('EURUSD')
position_size, risk_data = risk_manager.calculate_position_size(
    'EURUSD', 1.0850, 1.0800, confidence=0.8
)
```

---

## 📊 Performance Metrics

### **Real-time Tracking:**
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Risk-Adjusted Returns**: Sharpe ratio calculation
- **Maximum Drawdown**: Peak-to-trough decline
- **Signal Quality**: Confidence and confluence scores

### **Session Reporting:**
- JSON export for detailed analysis
- CSV data for spreadsheet compatibility
- Real-time console monitoring
- Comprehensive performance summaries

---

## 📚 Documentation

- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** - Complete production documentation
- **[BACKTEST_GUIDE.md](BACKTEST_GUIDE.md)** - Backtesting documentation
- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - Feature details

---

## ⚠️ Risk Disclaimer

**Important**: This software is for educational and research purposes. Forex trading carries high risk and may not be suitable for all investors. Features provided:

- ✅ **Comprehensive risk management tools**
- ✅ **Conservative default settings**
- ✅ **Signal-only mode for safe testing**
- ✅ **Extensive backtesting capabilities**
- ✅ **Professional logging and monitoring**

**Always**:
- Start with signal-only mode
- Backtest strategies thoroughly
- Use appropriate position sizing
- Monitor risk metrics continuously
- Never risk more than you can afford to lose

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

For support, feature requests, or bug reports:
- Open an issue on GitHub
- Check the documentation files
- Review example scripts in `/examples`

---

**SMC-Forez v2.0** - Professional Forex Analysis with Smart Money Concepts

*Built for traders who demand institutional-grade analysis and risk management.*

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

### 🔙 Backtesting & Performance Analysis ✅ **READY TO USE**
- **Standalone Backtest Runner**: Run backtests without MT5 connection
- **Historical Testing**: Comprehensive backtesting on any OHLC data
- **Performance Metrics**: Win rate, profit factor, drawdown, Sharpe ratio
- **Trade Analysis**: Detailed trade breakdown and statistics
- **Export Options**: CSV and JSON result export
- **Sample Data**: Built-in sample data generator for testing

#### Quick Start Backtesting
```bash
# Run a complete backtest with sample data (no MT5 required)
python run_backtest.py

# Or use the examples
python examples/backtest_examples.py
```

## Installation

### Prerequisites
- Python 3.8 or higher
- MetaTrader 5 terminal (for live data - **optional for backtesting**)
- Required Python packages (see requirements.txt)

### Quick Install (Backtesting Only)
```bash
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez

# Install minimal dependencies for backtesting
pip install pandas numpy

# Test that backtesting works
python run_backtest.py
```

### Full Install (All Features)
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
