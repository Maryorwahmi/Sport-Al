#!/usr/bin/env python3
"""
Standalone backtest runner for SMC Forez strategies
This script allows you to run backtests without requiring MetaTrader5 connection
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.backtesting import BacktestEngine, Trade, PerformanceMetrics
from smc_forez.signals.signal_generator import SignalType
from smc_forez.config.settings import Timeframe

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_data(symbol: str = "EURUSD", days: int = 30, timeframe: str = "H1") -> pd.DataFrame:
    """
    Create sample OHLC data for testing
    
    Args:
        symbol: Currency pair symbol
        days: Number of days of data
        timeframe: Timeframe (H1, H4, D1)
        
    Returns:
        DataFrame with OHLC data
    """
    print(f"Creating sample {timeframe} data for {symbol} ({days} days)...")
    
    # Determine frequency
    freq_map = {
        'M1': '1min',
        'M5': '5min', 
        'M15': '15min',
        'H1': '1h',
        'H4': '4h',
        'D1': '1d'
    }
    
    freq = freq_map.get(timeframe, '1h')
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # Generate realistic price data with trending and ranging behavior
    np.random.seed(42)  # For reproducible results
    
    base_price = 1.1000
    price_changes = np.random.normal(0, 0.0002, len(dates))  # Small random changes
    
    # Add some trending behavior
    trend = np.linspace(-0.005, 0.005, len(dates))
    price_changes += trend
    
    # Calculate prices
    prices = [base_price]
    for change in price_changes[1:]:
        new_price = prices[-1] + change
        prices.append(max(0.8000, min(1.5000, new_price)))  # Keep within realistic bounds
    
    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        # Create realistic OHLC bars
        spread = np.random.uniform(0.0001, 0.0003)  # 1-3 pip spread
        
        open_price = price + np.random.uniform(-spread/2, spread/2)
        close_price = price + np.random.uniform(-spread/2, spread/2)
        
        high_price = max(open_price, close_price) + np.random.uniform(0, spread)
        low_price = min(open_price, close_price) - np.random.uniform(0, spread)
        
        data.append({
            'Open': round(open_price, 5),
            'High': round(high_price, 5), 
            'Low': round(low_price, 5),
            'Close': round(close_price, 5),
            'Volume': np.random.randint(50, 500)
        })
    
    df = pd.DataFrame(data, index=dates)
    print(f"✓ Created {len(df)} bars of sample data")
    return df


def create_sample_signals(data: pd.DataFrame, num_signals: int = 5) -> List[Dict]:
    """
    Create sample trading signals for testing
    
    Args:
        data: OHLC DataFrame
        num_signals: Number of signals to generate
        
    Returns:
        List of signal dictionaries
    """
    print(f"Creating {num_signals} sample signals...")
    
    signals = []
    dates = data.index.tolist()
    
    # Space signals evenly throughout the data
    signal_intervals = len(dates) // (num_signals + 1)
    
    for i in range(num_signals):
        signal_idx = (i + 1) * signal_intervals
        if signal_idx >= len(dates):
            break
            
        timestamp = dates[signal_idx]
        current_price = data.loc[timestamp, 'Close']
        
        # Alternate between buy and sell signals
        signal_type = SignalType.BUY if i % 2 == 0 else SignalType.SELL
        
        if signal_type == SignalType.BUY:
            entry_price = current_price
            stop_loss = current_price * 0.995  # 0.5% below
            take_profit = current_price * 1.015  # 1.5% above (3:1 R:R)
        else:
            entry_price = current_price
            stop_loss = current_price * 1.005  # 0.5% above
            take_profit = current_price * 0.985  # 1.5% below (3:1 R:R)
        
        signal = {
            'timestamp': timestamp,
            'signal_type': signal_type,
            'valid': True,
            'entry_price': round(entry_price, 5),
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'strength': 'STRONG',
            'confidence': 0.8
        }
        
        signals.append(signal)
    
    print(f"✓ Created {len(signals)} sample signals")
    return signals


def print_results(results: Dict):
    """Print backtest results in a formatted way"""
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    
    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return
    
    # Basic results
    print(f"💰 Initial Balance: ${results.get('final_balance', 0) - results.get('total_return', 0)/100 * results.get('final_balance', 0):.2f}")
    print(f"💰 Final Balance:   ${results['final_balance']:.2f}")
    print(f"📈 Total Return:    {results['total_return']:.2f}%")
    print(f"🔢 Total Trades:    {len(results['trades'])}")
    
    # Performance metrics
    metrics = results['performance_metrics']
    print(f"\n📊 PERFORMANCE METRICS")
    print(f"   Win Rate:        {metrics.win_rate:.1%}")
    print(f"   Profit Factor:   {metrics.profit_factor:.2f}")
    print(f"   Total P&L:       ${metrics.total_pnl:.2f}")
    print(f"   Total P&L Pips:  {metrics.total_pnl_pips:.1f}")
    print(f"   Max Drawdown:    ${metrics.max_drawdown:.2f} ({metrics.max_drawdown_pct:.1f}%)")
    print(f"   Avg Win:         ${metrics.avg_win:.2f}")
    print(f"   Avg Loss:        ${metrics.avg_loss:.2f}")
    print(f"   Largest Win:     ${metrics.largest_win:.2f}")
    print(f"   Largest Loss:    ${metrics.largest_loss:.2f}")
    print(f"   Consecutive Wins: {metrics.consecutive_wins}")
    print(f"   Consecutive Loss: {metrics.consecutive_losses}")
    
    # Trade details
    if results['trades']:
        print(f"\n📋 TRADE DETAILS")
        for i, trade in enumerate(results['trades'][:5], 1):  # Show first 5 trades
            status_emoji = "✅" if trade['pnl'] and trade['pnl'] > 0 else "❌"
            print(f"   {status_emoji} Trade {i}: {trade['signal_type'].upper()} @ {trade['entry_price']} → "
                  f"{trade['exit_price']} = ${trade['pnl']:.2f} ({trade['pnl_pips']:.1f} pips)")
        
        if len(results['trades']) > 5:
            print(f"   ... and {len(results['trades']) - 5} more trades")


def load_data_from_file(filepath: str) -> Optional[pd.DataFrame]:
    """
    Load OHLC data from CSV file
    
    Args:
        filepath: Path to CSV file with OHLC data
        
    Returns:
        DataFrame with OHLC data or None if failed
    """
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        
        # Validate required columns
        required_cols = ['Open', 'High', 'Low', 'Close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            return None
        
        print(f"✓ Loaded {len(df)} rows from {filepath}")
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None


def load_signals_from_file(filepath: str) -> Optional[List[Dict]]:
    """
    Load signals from JSON file
    
    Args:
        filepath: Path to JSON file with signals
        
    Returns:
        List of signal dictionaries or None if failed
    """
    try:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        with open(filepath, 'r') as f:
            signals_data = json.load(f)
        
        # Convert string timestamps back to datetime objects
        signals = []
        for signal in signals_data:
            signal_copy = signal.copy()
            signal_copy['timestamp'] = pd.to_datetime(signal['timestamp'])
            signal_copy['signal_type'] = SignalType(signal['signal_type'])
            signals.append(signal_copy)
        
        print(f"✓ Loaded {len(signals)} signals from {filepath}")
        return signals
        
    except Exception as e:
        print(f"❌ Error loading signals: {e}")
        return None


def main():
    """Main function to run backtests"""
    print("🚀 SMC FOREZ - STANDALONE BACKTEST RUNNER")
    print("="*60)
    
    # Configuration
    config = {
        'symbol': 'EURUSD',
        'timeframe': 'H1',
        'days': 30,
        'num_signals': 10,
        'initial_balance': 10000.0,
        'risk_per_trade': 0.02,  # 2%
        'commission': 0.00007,   # 0.7 pips
        'max_spread': 2.0        # 2 pips
    }
    
    print("📋 CONFIGURATION")
    print("-" * 30)
    for key, value in config.items():
        print(f"   {key}: {value}")
    print()
    
    # Initialize backtest engine
    print("🔧 INITIALIZING BACKTEST ENGINE")
    print("-" * 30)
    
    engine = BacktestEngine(
        initial_balance=config['initial_balance'],
        commission=config['commission'],
        risk_per_trade=config['risk_per_trade'],
        max_spread=config['max_spread']
    )
    print("✓ BacktestEngine initialized")
    print()
    
    # Option to load custom data/signals or use sample data
    data_file = None  # Set to path if you have custom data
    signals_file = None  # Set to path if you have custom signals
    
    if data_file and os.path.exists(data_file):
        data = load_data_from_file(data_file)
        if data is None:
            return
    else:
        # Create sample data
        print("📊 CREATING SAMPLE DATA")
        print("-" * 30)
        data = create_sample_data(
            symbol=config['symbol'],
            days=config['days'],
            timeframe=config['timeframe']
        )
        print()
    
    if signals_file and os.path.exists(signals_file):
        signals = load_signals_from_file(signals_file)
        if signals is None:
            return
    else:
        # Create sample signals
        print("🎯 CREATING SAMPLE SIGNALS")
        print("-" * 30)
        signals = create_sample_signals(data, config['num_signals'])
        print()
    
    # Run backtest
    print("⚡ RUNNING BACKTEST")
    print("-" * 30)
    print("Processing data and executing trades...")
    
    results = engine.run_backtest(data, signals)
    
    # Display results
    print_results(results)
    
    # Option to export results
    export_file = f"backtest_results_{config['symbol']}_{config['timeframe']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        engine.export_results(results, export_file)
        print(f"\n💾 Results exported to: {export_file}")
    except Exception as e:
        print(f"\n⚠️  Could not export results: {e}")
    
    print("\n✅ Backtest completed successfully!")
    print("\n💡 TIPS:")
    print("   - Modify the config dictionary to test different parameters")
    print("   - Use your own CSV data by setting data_file = 'path/to/your/data.csv'")
    print("   - Use your own signals by setting signals_file = 'path/to/your/signals.json'")
    print("   - Check the exported JSON file for detailed results")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()