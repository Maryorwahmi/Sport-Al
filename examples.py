#!/usr/bin/env python3
"""
SMC Forex Analyzer Example Usage
Demonstrates how to use the analyzer for various trading scenarios
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smc_analyzer import ForexAnalyzer
from smc_analyzer.mt5_connector import Timeframe


def create_sample_data(symbol: str = "EURUSD", bars: int = 1000) -> pd.DataFrame:
    """
    Create sample OHLCV data for demonstration when MT5 is not available
    This simulates realistic forex price movements
    """
    print(f"📊 Creating sample data for {symbol}...")
    
    # Create time index
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=bars)
    time_index = pd.date_range(start=start_time, end=end_time, periods=bars)
    
    # Generate realistic price data with trends and volatility
    np.random.seed(42)  # For reproducible results
    
    # Starting price
    base_price = 1.0500 if symbol == "EURUSD" else 1.2500
    
    # Generate price movements with trend and noise
    returns = np.random.normal(0.0001, 0.002, bars)  # Small drift with volatility
    
    # Add some trend periods
    trend_periods = [
        (100, 200, 0.001),   # Bullish trend
        (300, 400, -0.0015), # Bearish trend
        (600, 700, 0.0008),  # Another bullish trend
    ]
    
    for start, end, trend in trend_periods:
        if start < bars and end <= bars:
            returns[start:end] += trend
    
    # Calculate prices
    prices = [base_price]
    for i in range(1, bars):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)
    
    # Generate OHLC from closing prices
    df_data = []
    for i, close in enumerate(prices):
        # Generate realistic OHLC
        volatility = np.random.uniform(0.0005, 0.002)
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = prices[i-1] if i > 0 else close
        
        # Ensure OHLC relationships are valid
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        volume = np.random.randint(1000, 10000)
        
        df_data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(df_data, index=time_index)
    print(f"✅ Created {len(df)} bars of sample data")
    return df


def example_single_symbol_analysis():
    """Example: Analyze a single symbol"""
    print("\n" + "="*50)
    print("📈 EXAMPLE 1: Single Symbol Analysis")
    print("="*50)
    
    # Initialize analyzer
    analyzer = ForexAnalyzer(
        swing_strength=3,
        structure_confirmation=2,
        min_rr_ratio=1.5,
        min_confluence=3
    )
    
    # Try to connect to MT5 (will use sample data if fails)
    if not analyzer.connect_mt5():
        print("⚠️  MT5 not available, using sample data for demonstration")
        
        # Create sample data and inject it into the analyzer
        sample_data = create_sample_data("EURUSD", 1000)
        
        # Mock the MT5 connector's get_historical_data method
        def mock_get_historical_data(symbol, timeframe, count):
            return sample_data.tail(count)
        
        analyzer.mt5_connector.get_historical_data = mock_get_historical_data
        analyzer.mt5_connector.is_connected = True
    
    # Analyze EURUSD on H1
    print("\n🔍 Analyzing EURUSD on H1 timeframe...")
    result = analyzer.analyze_symbol("EURUSD", Timeframe.H1, 500)
    
    if result:
        # Display analysis summary
        print(analyzer.export_analysis(result, 'summary'))
        
        # Show detailed signal information
        if result.trading_signals:
            print("\n🎯 DETAILED SIGNAL ANALYSIS:")
            for i, signal in enumerate(result.trading_signals[:3], 1):
                print(f"\n--- SIGNAL {i} ---")
                print(analyzer.signal_generator.format_signal_output(signal))
        
        # Market structure insights
        print(f"\n📊 MARKET STRUCTURE INSIGHTS:")
        print(f"• Current trend: {result.trend.value.upper()}")
        print(f"• Total swing points identified: {len(result.swing_points)}")
        print(f"• Recent structure breaks: {len([b for b in result.structure_breaks[-5:]])}")
        print(f"• Market health score: {result.market_health['overall_health']:.1%}")
        
        # Liquidity analysis
        print(f"\n💧 LIQUIDITY ANALYSIS:")
        print(f"• Order blocks identified: {len(result.order_blocks)}")
        print(f"• Active supply/demand zones: {len([z for z in result.supply_demand_zones if z.is_active])}")
        print(f"• Unfilled Fair Value Gaps: {len([f for f in result.fair_value_gaps if not f.filled])}")
    
    analyzer.disconnect_mt5()


def example_multi_timeframe_analysis():
    """Example: Multi-timeframe analysis"""
    print("\n" + "="*50)
    print("⏰ EXAMPLE 2: Multi-Timeframe Analysis")
    print("="*50)
    
    analyzer = ForexAnalyzer()
    
    # Mock MT5 connection if needed
    if not analyzer.connect_mt5():
        print("⚠️  Using sample data for demonstration")
        
        def mock_get_historical_data(symbol, timeframe, count):
            return create_sample_data(symbol, count)
        
        analyzer.mt5_connector.get_historical_data = mock_get_historical_data
        analyzer.mt5_connector.is_connected = True
    
    # Analyze GBPUSD across multiple timeframes
    print("\n🔍 Analyzing GBPUSD across multiple timeframes...")
    timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1]
    results = analyzer.analyze_multiple_timeframes("GBPUSD", timeframes, 300)
    
    if results:
        print(f"\n📊 MULTI-TIMEFRAME ANALYSIS RESULTS:")
        print(f"Timeframes analyzed: {len(results)}")
        
        for tf_name, result in results.items():
            signal_count = len(result.trading_signals)
            high_conf = len([s for s in result.trading_signals if s.confidence >= 0.7])
            
            print(f"\n{tf_name}:")
            print(f"  • Trend: {result.trend.value}")
            print(f"  • Signals: {signal_count} ({high_conf} high confidence)")
            print(f"  • Health: {result.market_health['overall_health']:.1%}")
            print(f"  • Recommendation: {result.analysis_summary['recommendation']}")
    
    analyzer.disconnect_mt5()


def example_market_scanner():
    """Example: Market scanner for multiple symbols"""
    print("\n" + "="*50)
    print("🔍 EXAMPLE 3: Market Scanner")
    print("="*50)
    
    analyzer = ForexAnalyzer(min_confluence=2, min_rr_ratio=1.2)
    
    # Mock MT5 if needed
    if not analyzer.connect_mt5():
        print("⚠️  Using sample data for demonstration")
        
        # Create different sample data for different symbols
        sample_data_cache = {}
        
        def mock_get_historical_data(symbol, timeframe, count):
            if symbol not in sample_data_cache:
                # Create unique data for each symbol
                seed = hash(symbol) % 1000
                np.random.seed(seed)
                sample_data_cache[symbol] = create_sample_data(symbol, count)
            return sample_data_cache[symbol].tail(count)
        
        analyzer.mt5_connector.get_historical_data = mock_get_historical_data
        analyzer.mt5_connector.is_connected = True
    
    # Scan major currency pairs
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
    print(f"\n🔍 Scanning {len(symbols)} currency pairs...")
    
    results = analyzer.scan_multiple_symbols(symbols, Timeframe.H1, 400)
    
    if results:
        print(f"\n📊 SCAN RESULTS:")
        print(f"Symbols scanned: {len(results)}")
        
        # Create summary table
        print(f"\n{'Symbol':<8} {'Trend':<10} {'Signals':<8} {'Health':<8} {'Top Signal':<15}")
        print("-" * 65)
        
        all_signals = []
        for symbol, result in results.items():
            signals = len(result.trading_signals)
            health = result.market_health['overall_health']
            trend = result.trend.value.title()
            
            top_signal = "None"
            if result.trading_signals:
                best_signal = max(result.trading_signals, key=lambda x: x.confidence)
                top_signal = f"{best_signal.signal_type.value} ({best_signal.confidence:.1%})"
                all_signals.extend(result.trading_signals)
            
            print(f"{symbol:<8} {trend:<10} {signals:<8} {health:<8.1%} {top_signal:<15}")
        
        # Show top opportunities across all symbols
        if all_signals:
            all_signals.sort(key=lambda x: x.confidence, reverse=True)
            print(f"\n🏆 TOP 3 OPPORTUNITIES ACROSS ALL SYMBOLS:")
            for i, signal in enumerate(all_signals[:3], 1):
                print(f"\n{i}. {signal.symbol} - {signal.signal_type.value.upper()}")
                print(f"   Entry: {signal.entry_price:.5f}")
                print(f"   Stop Loss: {signal.stop_loss:.5f}")
                print(f"   Take Profit: {signal.take_profit[0]:.5f}")
                print(f"   Risk/Reward: {signal.risk_reward_ratio:.2f}")
                print(f"   Confidence: {signal.confidence:.1%}")
                print(f"   Confluence: {', '.join(signal.confluence_factors)}")
    
    analyzer.disconnect_mt5()


def example_live_monitoring():
    """Example: Live signal monitoring"""
    print("\n" + "="*50)
    print("⚡ EXAMPLE 4: Live Signal Monitoring")
    print("="*50)
    
    analyzer = ForexAnalyzer(min_confluence=2)
    
    # Mock MT5 if needed
    if not analyzer.connect_mt5():
        print("⚠️  Using sample data for demonstration")
        
        def mock_get_historical_data(symbol, timeframe, count):
            return create_sample_data(symbol, count)
        
        analyzer.mt5_connector.get_historical_data = mock_get_historical_data
        analyzer.mt5_connector.is_connected = True
    
    # Get live signals
    print("\n⚡ Getting live signals across multiple symbols and timeframes...")
    
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    timeframes = [Timeframe.H1, Timeframe.H4]
    
    live_signals = analyzer.get_live_signals(symbols, timeframes, min_confidence=0.5)
    
    if live_signals:
        print(f"\n🎯 LIVE TRADING SIGNALS ({len(live_signals)} found):")
        
        for i, signal in enumerate(live_signals, 1):
            confidence_emoji = "🟢" if signal.confidence >= 0.8 else "🟡" if signal.confidence >= 0.6 else "🔴"
            signal_emoji = "📈" if "BUY" in signal.signal_type.value.upper() else "📉"
            
            print(f"\n{confidence_emoji} {signal_emoji} SIGNAL {i}:")
            print(f"Symbol: {signal.symbol} | Timeframe: {signal.timeframe}")
            print(f"Type: {signal.signal_type.value.upper()}")
            print(f"Entry: {signal.entry_price:.5f}")
            print(f"Stop Loss: {signal.stop_loss:.5f}")
            print(f"Take Profit: {', '.join([f'{tp:.5f}' for tp in signal.take_profit])}")
            print(f"Risk/Reward: {signal.risk_reward_ratio:.2f}")
            print(f"Confidence: {signal.confidence:.1%}")
            print(f"Risk: {signal.risk_amount:.5f} points")
    else:
        print("No live signals found meeting the criteria.")
    
    # Market overview
    print(f"\n🌍 MARKET OVERVIEW:")
    overview = analyzer.get_market_overview()
    
    print(f"Analysis Time: {overview['timestamp']}")
    print(f"Symbols Analyzed: {overview['symbols_analyzed']}")
    print(f"Total Signals: {overview['total_signals']}")
    print(f"High Confidence Signals: {overview['high_confidence_signals']}")
    
    analyzer.disconnect_mt5()


def main():
    """Run all examples"""
    print("🚀 SMC Forex Analyzer - Example Usage")
    print("====================================")
    print("This script demonstrates the key features of the SMC Forex Analyzer")
    print("Note: If MT5 is not available, sample data will be used for demonstration")
    
    try:
        # Run examples
        example_single_symbol_analysis()
        example_multi_timeframe_analysis()
        example_market_scanner()
        example_live_monitoring()
        
        print("\n" + "="*50)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\nNext steps:")
        print("1. Install MetaTrader 5 for live data")
        print("2. Configure your MT5 account credentials")
        print("3. Use the CLI tool: python cli.py --help")
        print("4. Integrate the analyzer into your trading workflow")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()