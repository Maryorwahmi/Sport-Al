#!/usr/bin/env python3
"""
Simple example showing how to use the BacktestEngine directly
This is a minimal example for developers who want to integrate the engine into their own code
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the BacktestEngine components
from smc_forez.backtesting import BacktestEngine
from smc_forez.signals.signal_generator import SignalType


def simple_backtest_example():
    """Simple example of using BacktestEngine"""
    
    print("Simple BacktestEngine Example")
    print("=" * 40)
    
    # 1. Create sample OHLC data
    print("1. Creating sample data...")
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1h')
    
    # Generate sample price data
    np.random.seed(42)
    base_price = 1.1000
    price_changes = np.cumsum(np.random.normal(0, 0.0001, len(dates)))
    
    data = pd.DataFrame({
        'Open': base_price + price_changes,
        'High': base_price + price_changes + np.random.uniform(0.0001, 0.0005, len(dates)),
        'Low': base_price + price_changes - np.random.uniform(0.0001, 0.0005, len(dates)),
        'Close': base_price + price_changes + np.random.normal(0, 0.0001, len(dates)),
    }, index=dates)
    
    print(f"   Created {len(data)} bars of data")
    
    # 2. Create signals
    print("2. Creating signals...")
    signals = [
        {
            'timestamp': dates[20],
            'signal_type': SignalType.BUY,
            'valid': True,
            'entry_price': 1.1010,
            'stop_loss': 1.0990,
            'take_profit': 1.1040
        },
        {
            'timestamp': dates[50],
            'signal_type': SignalType.SELL,
            'valid': True,
            'entry_price': 1.1000,
            'stop_loss': 1.1020,
            'take_profit': 1.0970
        }
    ]
    print(f"   Created {len(signals)} signals")
    
    # 3. Initialize BacktestEngine
    print("3. Initializing BacktestEngine...")
    engine = BacktestEngine(
        initial_balance=1000.0,  # $1000 starting balance
        commission=0.00007,      # 0.7 pips commission
        risk_per_trade=0.02,     # 2% risk per trade
        max_spread=2.0           # Maximum 2 pip spread
    )
    print("   BacktestEngine initialized")
    
    # 4. Run backtest
    print("4. Running backtest...")
    results = engine.run_backtest(data, signals)
    
    # 5. Display results
    print("5. Results:")
    if 'error' in results:
        print(f"   Error: {results['error']}")
        return
        
    print(f"   Initial Balance: ${engine.initial_balance:.2f}")
    print(f"   Final Balance:   ${results['final_balance']:.2f}")
    print(f"   Total Return:    {results['total_return']:.2f}%")
    print(f"   Number of Trades: {len(results['trades'])}")
    
    # Show performance metrics
    metrics = results['performance_metrics']
    print(f"   Win Rate:        {metrics.win_rate:.1%}")
    print(f"   Total P&L:       ${metrics.total_pnl:.2f}")
    print(f"   Profit Factor:   {metrics.profit_factor:.2f}")
    
    print("\n✅ Backtest completed successfully!")


def advanced_example():
    """More advanced example with custom position sizing and multiple signals"""
    
    print("\nAdvanced BacktestEngine Example")
    print("=" * 40)
    
    # Create engine with custom settings
    engine = BacktestEngine(
        initial_balance=10000.0,
        commission=0.00005,     # Lower commission
        risk_per_trade=0.015,   # 1.5% risk
        max_spread=1.5          # Tighter spread requirement
    )
    
    # Create more comprehensive data
    dates = pd.date_range(start='2023-01-01', periods=500, freq='4h')
    np.random.seed(123)
    
    # Simulate trending market
    trend = np.linspace(0, 0.02, len(dates))  # 2% uptrend over period
    noise = np.cumsum(np.random.normal(0, 0.0002, len(dates)))
    prices = 1.1000 + trend + noise
    
    data = pd.DataFrame({
        'Open': prices,
        'High': prices + np.random.uniform(0.0001, 0.0008, len(dates)),
        'Low': prices - np.random.uniform(0.0001, 0.0008, len(dates)),
        'Close': prices + np.random.normal(0, 0.0001, len(dates)),
    }, index=dates)
    
    # Create multiple signals with varying R:R ratios
    signals = []
    for i in range(0, len(dates), 50):
        if i + 5 < len(dates):
            timestamp = dates[i + 5]
            current_price = data.loc[timestamp, 'Close']
            
            # Alternate signal types
            signal_type = SignalType.BUY if i % 100 == 0 else SignalType.SELL
            
            if signal_type == SignalType.BUY:
                entry = current_price
                stop_loss = current_price * 0.998  # 0.2% stop
                take_profit = current_price * 1.006  # 0.6% target (3:1 R:R)
            else:
                entry = current_price
                stop_loss = current_price * 1.002  # 0.2% stop
                take_profit = current_price * 0.994  # 0.6% target (3:1 R:R)
            
            signals.append({
                'timestamp': timestamp,
                'signal_type': signal_type,
                'valid': True,
                'entry_price': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
    
    print(f"Running backtest with {len(signals)} signals on {len(data)} bars...")
    
    # Run backtest
    results = engine.run_backtest(data, signals)
    
    # Detailed results
    if 'error' not in results:
        print(f"\nResults Summary:")
        print(f"  Period:          {dates[0].date()} to {dates[-1].date()}")
        print(f"  Initial Balance: ${engine.initial_balance:,.2f}")
        print(f"  Final Balance:   ${results['final_balance']:,.2f}")
        print(f"  Total Return:    {results['total_return']:.2f}%")
        print(f"  Total Trades:    {len(results['trades'])}")
        
        metrics = results['performance_metrics']
        print(f"\nPerformance Metrics:")
        print(f"  Win Rate:        {metrics.win_rate:.1%}")
        print(f"  Profit Factor:   {metrics.profit_factor:.2f}")
        print(f"  Max Drawdown:    ${metrics.max_drawdown:.2f} ({metrics.max_drawdown_pct:.1f}%)")
        print(f"  Sharpe Ratio:    {metrics.sharpe_ratio:.2f}")
        print(f"  Avg Win:         ${metrics.avg_win:.2f}")
        print(f"  Avg Loss:        ${metrics.avg_loss:.2f}")
        
        # Export results for further analysis
        export_filename = "advanced_backtest_results.json"
        engine.export_results(results, export_filename)
        print(f"\n📁 Detailed results exported to: {export_filename}")
    
    else:
        print(f"Backtest failed: {results['error']}")


if __name__ == "__main__":
    try:
        # Run simple example first
        simple_backtest_example()
        
        # Then run advanced example
        advanced_example()
        
        print("\n🎉 All examples completed successfully!")
        print("\n💡 You can now use these patterns to integrate BacktestEngine into your own code")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()