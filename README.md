# SMC-Forez: A-Grade Forex Analyzer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional-grade Forex analyzer that integrates **Smart Money Concepts (SMC)** and **Structural Market Analysis (SMA)** to provide comprehensive market insights and high-probability trading signals.

## 🚀 Features

### Core Analysis Capabilities
- **Multi-Timeframe Analysis** (M1 to D1) with MetaTrader 5 integration
- **Market Structure Detection**: Swing highs/lows, Break of Structure (BOS), Change of Character (CHOCH)
- **Liquidity Zone Mapping**: Order blocks, supply/demand areas, Fair Value Gaps (FVGs)
- **Smart Signal Generation**: Confluence-based entry signals with risk management
- **Real-Time Monitoring**: Live market scanning and signal alerts

### Smart Money Concepts Integration
- **Order Block Detection**: Institutional order flow analysis
- **Liquidity Mapping**: High-probability reversal zones
- **Market Structure Shifts**: Trend change identification
- **Fair Value Gap Analysis**: Price imbalance opportunities
- **Confluence Analysis**: Multi-factor signal confirmation

### Advanced Features
- **Risk Management**: Automated stop-loss and take-profit calculation
- **Market Health Scoring**: Overall market condition assessment
- **Multi-Symbol Scanning**: Portfolio-wide opportunity identification
- **Export Capabilities**: JSON and summary report formats
- **CLI Interface**: Command-line tools for automation

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- MetaTrader 5 terminal (optional, for live data)

### Install Dependencies
```bash
# Clone the repository
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez

# Install required packages
pip install -r requirements.txt

# Install the package
pip install -e .
```

### MetaTrader 5 Setup (Optional)
1. Download and install [MetaTrader 5](https://www.metatrader5.com/)
2. Open a demo or live account with a forex broker
3. Enable algorithmic trading in MT5 settings
4. Note your account credentials for configuration

## 🎯 Quick Start

### Basic Usage
```python
from smc_analyzer import ForexAnalyzer
from smc_analyzer.mt5_connector import Timeframe

# Initialize analyzer
analyzer = ForexAnalyzer()

# Connect to MT5 (optional)
if analyzer.connect_mt5():
    print("Connected to MetaTrader 5")

# Analyze a single symbol
result = analyzer.analyze_symbol("EURUSD", Timeframe.H1)

if result:
    # Display analysis summary
    print(analyzer.export_analysis(result, 'summary'))
    
    # Show trading signals
    for signal in result.trading_signals:
        print(analyzer.signal_generator.format_signal_output(signal))

analyzer.disconnect_mt5()
```

### Command Line Interface
```bash
# Analyze single symbol
python cli.py analyze --symbol EURUSD --timeframe H1

# Scan multiple symbols
python cli.py scan --symbols EURUSD,GBPUSD,USDJPY --timeframe H4

# Get live signals
python cli.py live --min-confidence 0.7

# Market overview
python cli.py overview
```

### Run Examples
```bash
# Run comprehensive examples
python examples.py
```

## 📊 Analysis Components

### 1. Market Structure Analysis
```python
from smc_analyzer.market_structure import MarketStructureAnalyzer

analyzer = MarketStructureAnalyzer(swing_strength=3)
structure = analyzer.analyze_structure(df)

# Results include:
# - Swing points identification
# - Trend direction analysis
# - BOS/CHOCH detection
# - Structure break confirmation
```

### 2. Liquidity Zone Mapping
```python
from smc_analyzer.liquidity_zones import LiquidityZoneMapper

mapper = LiquidityZoneMapper()
liquidity = mapper.analyze_liquidity(df, swing_points)

# Results include:
# - Order block identification
# - Supply/demand zones
# - Fair Value Gap detection
# - Zone strength analysis
```

### 3. Signal Generation
```python
from smc_analyzer.signal_generator import SignalGenerator

generator = SignalGenerator(min_rr_ratio=1.5, min_confluence=3)
signals = generator.generate_signals(
    df, trend, structure_breaks, order_blocks, 
    supply_demand_zones, fair_value_gaps, 
    "EURUSD", "H1"
)

# Signals include:
# - Entry price and direction
# - Stop loss calculation
# - Take profit targets
# - Confluence factors
# - Confidence scoring
```

## 🔧 Configuration

### Analyzer Parameters
```python
analyzer = ForexAnalyzer(
    swing_strength=3,           # Swing detection sensitivity
    structure_confirmation=2,    # Structure break confirmation bars
    min_rr_ratio=1.5,           # Minimum risk-reward ratio
    min_confluence=3            # Minimum confluence factors
)
```

### MT5 Connection
```python
# With credentials
analyzer = ForexAnalyzer(
    mt5_account=12345678,
    mt5_password="your_password",
    mt5_server="broker_server"
)

# Or connect later
analyzer.mt5_connector.account = 12345678
analyzer.mt5_connector.password = "your_password"
analyzer.mt5_connector.server = "broker_server"
analyzer.connect_mt5()
```

## 📈 Advanced Usage

### Multi-Timeframe Analysis
```python
# Analyze across multiple timeframes
timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1]
results = analyzer.analyze_multiple_timeframes("EURUSD", timeframes)

for tf_name, result in results.items():
    print(f"{tf_name}: {len(result.trading_signals)} signals")
```

### Market Scanning
```python
# Scan multiple symbols
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
results = analyzer.scan_multiple_symbols(symbols, Timeframe.H1)

# Get best opportunities
all_signals = []
for result in results.values():
    all_signals.extend(result.trading_signals)

# Sort by confidence
all_signals.sort(key=lambda x: x.confidence, reverse=True)
print(f"Top signal: {all_signals[0].symbol} - {all_signals[0].signal_type.value}")
```

### Live Monitoring
```python
# Get live signals with filtering
live_signals = analyzer.get_live_signals(
    symbols=['EURUSD', 'GBPUSD'],
    timeframes=[Timeframe.H1, Timeframe.H4],
    min_confidence=0.7
)

for signal in live_signals:
    print(f"ALERT: {signal.symbol} {signal.signal_type.value} at {signal.entry_price}")
```

## 📋 Signal Analysis

### Signal Components
Each trading signal includes:
- **Entry Price**: Optimal entry level
- **Stop Loss**: Risk management level
- **Take Profit**: Target levels (multiple)
- **Risk/Reward Ratio**: Risk-to-reward calculation
- **Confidence Score**: Signal strength (0-1)
- **Confluence Factors**: Supporting analysis elements

### Confluence Factors
- Bullish/Bearish Order Blocks
- Supply/Demand Zone Alignment
- Fair Value Gap Confluence
- Structure Break Confirmation
- Multi-Timeframe Agreement

### Example Signal Output
```
=== BUY SIGNAL ===
Symbol: EURUSD
Timeframe: H1
Signal Type: BUY_LIMIT
Entry Price: 1.05450
Stop Loss: 1.05280
Take Profits: 1.05720, 1.05850, 1.05980
Risk/Reward: 2.35
Confidence: 78.5%
Risk Amount: 0.00170 points
Confluence Factors: bullish_order_block, demand_zone_confluence, bullish_fvg
```

## 🛠️ API Reference

### ForexAnalyzer Class
The main analyzer class that coordinates all components.

#### Methods
- `analyze_symbol(symbol, timeframe, bars=1000)`: Analyze single symbol
- `analyze_multiple_timeframes(symbol, timeframes)`: Multi-TF analysis
- `scan_multiple_symbols(symbols, timeframe)`: Multi-symbol scan
- `get_live_signals(symbols, timeframes, min_confidence)`: Live signal feed
- `get_market_overview()`: Overall market condition summary

### MT5Connector Class
Handles MetaTrader 5 data connection and retrieval.

#### Methods
- `connect()`: Establish MT5 connection
- `get_historical_data(symbol, timeframe, count)`: Retrieve price data
- `get_live_data(symbol)`: Current market data
- `is_market_open(symbol)`: Check trading session status

### Analysis Result Structure
```python
AnalysisResult:
    symbol: str
    timeframe: str
    current_price: float
    trend: TrendDirection
    trading_signals: List[TradingSignal]
    market_health: Dict
    analysis_summary: Dict
```

## 🚨 Risk Disclaimer

**Important**: This software is for educational and analysis purposes only. 

- **Not Financial Advice**: This analyzer does not provide financial or investment advice
- **Risk Warning**: Forex trading involves substantial risk of loss
- **No Guarantees**: Past performance does not guarantee future results
- **Use at Your Own Risk**: Always implement proper risk management
- **Test First**: Thoroughly test any strategy before live trading

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

### Development Setup
```bash
# Clone repository
git clone https://github.com/Maryorwahmi/SMC-Forez.git
cd SMC-Forez

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Run examples
python examples.py
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Maryorwahmi/SMC-Forez/issues)
- **Documentation**: See examples and docstrings in code
- **Community**: Join our discussions for trading insights

## 🎯 Roadmap

- [ ] **Web Dashboard**: Browser-based analysis interface
- [ ] **Alert System**: Email/SMS signal notifications
- [ ] **Backtesting Engine**: Historical strategy testing
- [ ] **Machine Learning**: AI-enhanced signal detection
- [ ] **Mobile App**: iOS/Android companion app
- [ ] **Additional Brokers**: Beyond MT5 integration
- [ ] **Portfolio Management**: Multi-account tracking

---

**Happy Trading! 📈📉**

*Remember: The best traders combine technical analysis with proper risk management and emotional discipline.*
