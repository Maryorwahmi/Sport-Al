# SMC-Forez-React

React frontend application for the SMC-Forez-H4 trading system with real-time signal monitoring, backtest visualization, and system configuration.

## Features

### ✅ Dashboard
- **Live Signal Monitoring**: Real-time trading signals with entry, stop loss, and take profit levels
- **Performance Metrics**: Win rate, profit factor, total trades display
- **Signal Quality Indicators**: Institutional, Professional, Standard quality grades
- **Multi-Timeframe Display**: H4, H1, M15 timeframe alignment
- **Auto-Refresh**: Configurable refresh interval (default 30s)

### ✅ Backtest Results
- **Interactive Backtesting**: Run backtests with custom configurations
- **Performance Visualization**: Equity curve charts with Recharts
- **Comprehensive Metrics**: Win rate, profit factor, drawdown, Sharpe ratio
- **Multiple Configurations**: 14-day, 30-day, 60-day, 90-day periods
- **JSON Export**: Download backtest results for analysis
- **Signal Quality Filtering**: Configurable minimum quality threshold

### ✅ Settings Configuration
- **Trading Parameters**: Risk per trade, R:R ratios, spread limits
- **Analysis Settings**: Swing length, FVG size, order block parameters
- **Backtest Configuration**: Initial balance, commission rates
- **UI Preferences**: Refresh interval, theme selection, notifications

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The application will open at http://localhost:3000

## Backend Setup

To use the full functionality, start the SMC-Forez-H4 backend:

```bash
cd ../SMC-Forez-H4
python api_server.py
```

Backend will run on http://localhost:8000

## Project Structure

```
smc-forez-react/
├── src/
│   ├── pages/
│   │   ├── Dashboard.js         # Live signals and performance
│   │   ├── BacktestResults.js   # Backtest visualization
│   │   └── Settings.js          # System configuration
│   ├── services/
│   │   └── api.js              # Backend API client
│   └── App.js                  # Main app with routing
├── package.json
└── README.md
```

## Environment Configuration

Create `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## Documentation

See full documentation in the main README for:
- Detailed feature descriptions
- API integration guide
- Troubleshooting tips
- Development guidelines

---

**SMC-Forez-React v1.0.0**
*Professional React Frontend for Smart Money Concepts Trading*
