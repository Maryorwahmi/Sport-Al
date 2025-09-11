"""
Example backtesting script for the SMC Forez analyzer
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from smc_forez import SMCAnalyzer, Settings
from smc_forez.config.settings import Timeframe

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    Create sample OHLC data for testing when MT5 is not available
    
    Args:
        symbol: Currency pair symbol
        days: Number of days of data to generate
        
    Returns:
        DataFrame with sample OHLC data
    """
    # Generate sample data with realistic forex movements
    np.random.seed(42)  # For reproducible results
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         end=datetime.now(), freq='H')
    
    # Starting price based on symbol
    if symbol == "EURUSD":
        start_price = 1.1000
    elif symbol == "GBPUSD":
        start_price = 1.3000
    elif symbol == "USDJPY":
        start_price = 110.00
    else:
        start_price = 1.0000
    
    # Generate price movements
    returns = np.random.normal(0, 0.0005, len(dates))  # Small random movements
    
    # Add some trend and volatility
    trend = np.sin(np.arange(len(dates)) * 0.01) * 0.0002
    volatility = np.abs(np.sin(np.arange(len(dates)) * 0.1)) * 0.0003
    
    price_changes = returns + trend + np.random.normal(0, volatility)
    prices = start_price * np.exp(np.cumsum(price_changes))
    
    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        # Create realistic OHLC based on close price
        spread = price * 0.0001  # 1 pip spread
        
        high = price + np.random.uniform(0, spread * 5)
        low = price - np.random.uniform(0, spread * 5)
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'Open': open_price,
            'High': max(open_price, price, high),
            'Low': min(open_price, price, low),
            'Close': price,
            'Volume': np.random.randint(100, 1000)
        })
    
    df = pd.DataFrame(data, index=dates)
    return df

def run_backtest_example():
    """Run a comprehensive backtesting example"""
    
    print("SMC Forez - Backtesting Example")
    print("=" * 40)
    
    # Create settings
    settings = Settings()
    settings.backtest.initial_balance = 10000
    settings.trading.risk_per_trade = 0.01  # 1% risk
    settings.trading.min_rr_ratio = 1.5
    
    # Initialize analyzer
    analyzer = SMCAnalyzer(settings)
    
    # Test symbols
    symbols = ["EURUSD", "GBPUSD"]
    timeframes = [Timeframe.H4, Timeframe.H1]
    
    print(f"\nTesting {len(symbols)} symbols on {len(timeframes)} timeframes")
    print(f"Initial Balance: ${settings.backtest.initial_balance:,.2f}")
    print(f"Risk per Trade: {settings.trading.risk_per_trade * 100}%")
    
    results_summary = []
    
    for symbol in symbols:
        print(f"\nBacktesting {symbol}...")
        
        for timeframe in timeframes:
            print(f"  Timeframe: {timeframe.value}")
            
            try:
                # For demo purposes, create sample data
                # In production, this would use real MT5 data
                sample_data = create_sample_data(symbol, days=180)  # 6 months
                
                # Simulate the backtest workflow
                print(f"    Generated {len(sample_data)} data points")
                
                # Analyze the data to get signals
                signals = []
                window_size = 200
                
                for i in range(window_size, len(sample_data), 50):  # Check every 50 bars
                    window_data = sample_data.iloc[i-window_size:i+1]
                    
                    # Perform analysis
                    market_structure = analyzer.structure_analyzer.get_market_structure_levels(window_data)
                    smc_analysis = analyzer.smc_analyzer.get_smart_money_analysis(window_data)
                    
                    # Generate signal
                    current_price = window_data['Close'].iloc[-1]
                    signal = analyzer.signal_generator.generate_signal(
                        market_structure, smc_analysis, current_price
                    )
                    
                    # Add timestamp and save valid signals
                    if signal.get('valid', False):
                        signal['timestamp'] = sample_data.index[i]
                        signals.append(signal)
                
                print(f"    Generated {len(signals)} valid signals")
                
                if signals:
                    # Run backtest
                    results = analyzer.backtest_engine.run_backtest(sample_data, signals)
                    
                    if 'error' not in results:
                        metrics = results['performance_metrics']
                        
                        print(f"    Final Balance: ${results['final_balance']:,.2f}")
                        print(f"    Total Return: {results['total_return']:.2f}%")
                        print(f"    Win Rate: {metrics.win_rate * 100:.1f}%")
                        print(f"    Profit Factor: {metrics.profit_factor:.2f}")
                        print(f"    Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
                        
                        results_summary.append({
                            'symbol': symbol,
                            'timeframe': timeframe.value,
                            'final_balance': results['final_balance'],
                            'total_return': results['total_return'],
                            'win_rate': metrics.win_rate * 100,
                            'total_trades': metrics.total_trades,
                            'profit_factor': metrics.profit_factor,
                            'max_drawdown': metrics.max_drawdown_pct
                        })
                    else:
                        print(f"    Error: {results['error']}")
                else:
                    print("    No valid signals generated")
                    
            except Exception as e:
                print(f"    Error: {str(e)}")
    
    # Summary
    if results_summary:
        print("\n" + "=" * 60)
        print("BACKTEST SUMMARY")
        print("=" * 60)
        
        df_summary = pd.DataFrame(results_summary)
        
        print(f"\nBest Performance by Return:")
        best_return = df_summary.loc[df_summary['total_return'].idxmax()]
        print(f"  {best_return['symbol']} {best_return['timeframe']}: {best_return['total_return']:.2f}%")
        
        print(f"\nBest Win Rate:")
        best_winrate = df_summary.loc[df_summary['win_rate'].idxmax()]
        print(f"  {best_winrate['symbol']} {best_winrate['timeframe']}: {best_winrate['win_rate']:.1f}%")
        
        print(f"\nLowest Drawdown:")
        best_dd = df_summary.loc[df_summary['max_drawdown'].idxmin()]
        print(f"  {best_dd['symbol']} {best_dd['timeframe']}: {best_dd['max_drawdown']:.2f}%")
        
        print(f"\nAverage Performance:")
        print(f"  Average Return: {df_summary['total_return'].mean():.2f}%")
        print(f"  Average Win Rate: {df_summary['win_rate'].mean():.1f}%")
        print(f"  Average Profit Factor: {df_summary['profit_factor'].mean():.2f}")
        
        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.csv"
        df_summary.to_csv(filename, index=False)
        print(f"\nResults exported to: {filename}")
    
    print("\nNote: This example uses simulated data.")
    print("Connect to MT5 for real historical data backtesting.")

if __name__ == "__main__":
    run_backtest_example()