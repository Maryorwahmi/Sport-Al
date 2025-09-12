#!/usr/bin/env python3
"""
Enhanced backtest runner for SMC Forez strategies using real multi-timeframe analysis
This script integrates the actual SMC analysis pipeline instead of using dummy signals
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

from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Settings, Timeframe
from smc_forez.backtesting import BacktestEngine, Trade, PerformanceMetrics
from smc_forez.signals.signal_generator import SignalType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def run_enhanced_backtest(symbol: str = "EURUSD", days: int = 30, timeframe: str = "H1") -> Dict:
    """
    Run backtest using real SMC multi-timeframe analysis
    
    Args:
        symbol: Currency pair symbol
        days: Number of days to backtest
        timeframe: Primary timeframe for backtesting
        
    Returns:
        Dictionary with backtest results
    """
    print(f"🚀 ENHANCED SMC BACKTEST - Using Real Multi-Timeframe Analysis")
    print("="*70)
    
    try:
        # Initialize SMC Analyzer with production settings
        settings = Settings()
        
        # Configure for multi-timeframe analysis
        if timeframe == "H1":
            settings.timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]
        elif timeframe == "H4":
            settings.timeframes = [Timeframe.D1, Timeframe.H4, Timeframe.H1]
        elif timeframe == "D1":
            settings.timeframes = [Timeframe.D1, Timeframe.H4]
        else:
            settings.timeframes = [Timeframe.H1, Timeframe.M15]
        
        # Create analyzer
        analyzer = SMCAnalyzer(settings)
        
        # Connect to data source (will use mock data if MT5 not available)
        data_connected = analyzer.connect_data_source()
        if not data_connected:
            print("⚠️  Using mock data for analysis (MT5 not available)")
        else:
            print("✓ Connected to live data source")
        
        print(f"\n📊 BACKTEST CONFIGURATION")
        print(f"   Symbol: {symbol}")
        print(f"   Primary Timeframe: {timeframe}")
        print(f"   Multi-Timeframes: {[tf.value for tf in settings.timeframes]}")
        print(f"   Period: {days} days")
        print(f"   Analysis Mode: Real SMC Multi-Timeframe")
        print(f"   Risk per Trade: {settings.trading.risk_per_trade * 100:.1f}%")
        print(f"   Min R:R Ratio: {settings.trading.min_rr_ratio:.1f}:1")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Run the actual backtest using SMC analyzer
        print(f"\n⚡ RUNNING SMC BACKTEST")
        print("-" * 40)
        
        tf_enum = {
            'M1': Timeframe.M1, 'M5': Timeframe.M5, 'M15': Timeframe.M15,
            'H1': Timeframe.H1, 'H4': Timeframe.H4, 'D1': Timeframe.D1
        }.get(timeframe.upper(), Timeframe.H1)
        
        results = analyzer.run_backtest(
            symbol=symbol,
            timeframe=tf_enum,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        analyzer.disconnect_data_source()
        
        if 'error' in results:
            print(f"❌ Backtest failed: {results['error']}")
            return results
        
        # Enhance results with analysis details
        results['analysis_type'] = 'SMC Multi-Timeframe Analysis'
        results['timeframes_used'] = [tf.value for tf in settings.timeframes]
        results['enhanced_features'] = [
            'Market Structure Analysis',
            'Smart Money Concepts (FVG, Order Blocks, Liquidity)',
            'Multi-Timeframe Confluence',
            'Signal Quality Filtering',
            'Risk Management Integration'
        ]
        
        return results
        
    except Exception as e:
        logger.error(f"Error in enhanced backtest: {str(e)}")
        return {'error': str(e)}


def print_enhanced_results(results: Dict):
    """Print enhanced backtest results with analysis details"""
    print("\n" + "="*80)
    print("📈 SMC ENHANCED BACKTEST RESULTS")
    print("="*80)
    
    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return
    
    # Basic results
    print(f"💰 Initial Balance: ${results.get('initial_balance', 0):,.2f}")
    print(f"💰 Final Balance:   ${results.get('final_balance', 0):,.2f}")
    print(f"📈 Total Return:    {results.get('total_return_pct', 0):.2f}%")
    print(f"🔢 Total Trades:    {results.get('total_trades', 0)}")
    print(f"📊 Signals Generated: {results.get('signals_generated', 0)}")
    
    # Analysis details
    print(f"\n🔍 ANALYSIS DETAILS")
    print(f"   Analysis Type: {results.get('analysis_type', 'Standard')}")
    print(f"   Timeframes: {', '.join(results.get('timeframes_used', []))}")
    print(f"   Symbol: {results.get('symbol', 'Unknown')}")
    print(f"   Period: {results.get('start_date', 'Unknown')} to {results.get('end_date', 'Unknown')}")
    print(f"   Data Points: {results.get('data_points', 0)}")
    
    # Enhanced features used
    enhanced_features = results.get('enhanced_features', [])
    if enhanced_features:
        print(f"\n✨ ENHANCED FEATURES USED")
        for feature in enhanced_features:
            print(f"   ✓ {feature}")
    
    # Performance metrics
    metrics = results.get('performance_metrics', {})
    if metrics:
        print(f"\n📊 PERFORMANCE METRICS")
        # Handle both dict and object types
        if hasattr(metrics, '__dict__'):
            metrics_dict = metrics.__dict__
        elif hasattr(metrics, 'to_dict'):
            metrics_dict = metrics.to_dict()
        else:
            metrics_dict = metrics
            
        print(f"   Win Rate:        {metrics_dict.get('win_rate', 0)*100:.1f}%")
        print(f"   Profit Factor:   {metrics_dict.get('profit_factor', 0):.2f}")
        print(f"   Total P&L:       ${metrics_dict.get('total_pnl', 0):.2f}")
        print(f"   Total P&L Pips:  {metrics_dict.get('total_pnl_pips', 0):.1f}")
        print(f"   Max Drawdown:    ${metrics_dict.get('max_drawdown', 0):.2f} ({metrics_dict.get('max_drawdown_pct', 0):.1f}%)")
        print(f"   Avg Win:         ${metrics_dict.get('avg_win', 0):.2f}")
        print(f"   Avg Loss:        ${metrics_dict.get('avg_loss', 0):.2f}")
        print(f"   Largest Win:     ${metrics_dict.get('largest_win', 0):.2f}")
        print(f"   Largest Loss:    ${metrics_dict.get('largest_loss', 0):.2f}")
        print(f"   Sharpe Ratio:    {metrics_dict.get('sharpe_ratio', 0):.2f}")
    else:
        print(f"\n📊 PERFORMANCE METRICS")
        print("   No trades executed - no performance metrics available")
    
    # Trade details
    trades = results.get('trades', [])
    if trades:
        print(f"\n📋 TRADE SAMPLE (First 5 trades)")
        for i, trade in enumerate(trades[:5], 1):
            status_emoji = "✅" if trade.get('pnl', 0) > 0 else "❌"
            signal_type = trade.get('signal_type', 'unknown')
            if hasattr(signal_type, 'value'):
                signal_type = signal_type.value
            elif hasattr(signal_type, 'name'):
                signal_type = signal_type.name
                
            print(f"   {status_emoji} Trade {i}: {str(signal_type).upper()} @ {trade.get('entry_price', 0):.5f} → "
                  f"{trade.get('exit_price', 0):.5f} = ${trade.get('pnl', 0):.2f} ({trade.get('pnl_pips', 0):.1f} pips)")
        
        if len(trades) > 5:
            print(f"   ... and {len(trades) - 5} more trades")


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
    """Main function to run enhanced backtests with real SMC analysis"""
    print("🚀 SMC FOREZ - ENHANCED BACKTEST RUNNER WITH MULTI-TIMEFRAME ANALYSIS")
    print("="*80)
    
    # Configuration options
    config_options = [
        {
            'name': 'Quick Test',
            'symbol': 'EURUSD',
            'timeframe': 'H1',
            'days': 7,
            'description': 'Quick 7-day test with H1 timeframe'
        },
        {
            'name': 'Standard Test',
            'symbol': 'EURUSD', 
            'timeframe': 'H1',
            'days': 30,
            'description': '30-day comprehensive test'
        },
        {
            'name': 'Extended Test',
            'symbol': 'GBPUSD',
            'timeframe': 'H4', 
            'days': 60,
            'description': '60-day extended test with H4 focus'
        }
    ]
    
    print("📋 BACKTEST CONFIGURATION OPTIONS")
    print("-" * 50)
    for i, config in enumerate(config_options, 1):
        print(f"   {i}. {config['name']}: {config['description']}")
    
    print(f"   4. Custom Configuration")
    print()
    
    # Get user selection
    try:
        choice = input("Select configuration (1-4) or press Enter for default: ").strip()
        
        if choice == "" or choice == "2":
            # Default to standard test
            config = config_options[1]
        elif choice == "1":
            config = config_options[0]
        elif choice == "3":
            config = config_options[2]
        elif choice == "4":
            # Custom configuration
            print("\n🔧 CUSTOM CONFIGURATION")
            symbol = input("Enter symbol (default EURUSD): ").strip() or "EURUSD"
            timeframe = input("Enter timeframe (M15/H1/H4/D1, default H1): ").strip() or "H1"
            days = int(input("Enter days to backtest (default 30): ").strip() or "30")
            
            config = {
                'symbol': symbol.upper(),
                'timeframe': timeframe.upper(),
                'days': days,
                'name': 'Custom'
            }
        else:
            config = config_options[1]  # Default fallback
            
    except (ValueError, KeyboardInterrupt):
        print("\nUsing default configuration...")
        config = config_options[1]
    
    print(f"\n✓ Selected: {config['name']}")
    print(f"   Symbol: {config['symbol']}")
    print(f"   Timeframe: {config['timeframe']}")
    print(f"   Days: {config['days']}")
    print()
    
    # Run the enhanced backtest
    results = run_enhanced_backtest(
        symbol=config['symbol'],
        timeframe=config['timeframe'],
        days=config['days']
    )
    
    # Display results
    print_enhanced_results(results)
    
    # Export results
    if 'error' not in results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"enhanced_backtest_{config['symbol']}_{config['timeframe']}_{timestamp}.json"
        
        try:
            # Make results JSON serializable
            export_results = {}
            for key, value in results.items():
                if isinstance(value, (datetime, pd.Timestamp)):
                    export_results[key] = value.isoformat()
                elif hasattr(value, 'to_dict'):
                    export_results[key] = value.to_dict()
                elif hasattr(value, '__dict__'):
                    export_results[key] = value.__dict__
                else:
                    export_results[key] = value
            
            with open(filename, 'w') as f:
                json.dump(export_results, f, indent=2, default=str)
            
            print(f"\n💾 Enhanced results exported to: {filename}")
            
        except Exception as e:
            print(f"\n⚠️  Could not export results: {e}")
    
    print("\n✅ Enhanced backtest completed!")
    print("\n💡 KEY IMPROVEMENTS:")
    print("   ✓ Real SMC multi-timeframe analysis (not dummy data)")
    print("   ✓ Market structure analysis integration")
    print("   ✓ Smart Money Concepts (FVG, Order Blocks, Liquidity)")
    print("   ✓ Signal quality filtering and confluence")
    print("   ✓ Professional risk management")
    print("\n📚 COMPARE WITH:")
    print("   - run_backtest.py: Enhanced SMC analysis")  
    print("   - production_runner.py --mode backtest: Production system")
    print("   - signal_runner.py: Live signal generation")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()