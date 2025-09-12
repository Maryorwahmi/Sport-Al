#!/usr/bin/env python3
"""
SMC FOREZ - PRODUCTION LIVE SYSTEM
Professional Forex Analyzer with Smart Money Concepts
Live execution, backtesting, and comprehensive monitoring
"""
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.execution.live_executor import LiveExecutor, ExecutionSettings
from smc_forez.utils.logger import get_logger, cleanup_logger
from smc_forez.analyzer import SMCAnalyzer


def print_banner():
    """Print the application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                            SMC FOREZ v2.0                                   ║
║                  Professional Forex Analyzer & Live Executor                ║
║                     Smart Money Concepts + Market Structure                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

🚀 Production-Ready Features:
   • Live MT5 execution with risk management
   • Continuous signal monitoring (30-second refresh)
   • Smart Money Concepts analysis (FVG, Order Blocks, Liquidity)
   • Multi-timeframe confluence analysis
   • Professional logging with JSON/CSV export
   • Backtesting engine with performance metrics
   • Graceful shutdown and error handling

💡 Mode Options:
   1. LIVE TRADING  - Execute real trades on MT5
   2. SIGNAL ONLY   - Generate signals without execution
   3. BACKTEST      - Historical analysis and performance testing

⚠️  RISK DISCLAIMER: Use only with proper risk management!
"""
    print(banner)


def create_default_settings() -> tuple[Settings, ExecutionSettings]:
    """Create default settings for production use"""
    
    # Main analyzer settings
    settings = Settings()
    
    # Production-optimized analysis settings
    settings.analysis.swing_length = 20  # More stable swing detection
    settings.analysis.fvg_min_size = 8.0  # Larger FVGs for reliability
    settings.analysis.order_block_lookback = 30
    settings.analysis.liquidity_threshold = 0.12
    
    # Conservative trading settings
    settings.trading.risk_per_trade = 0.01  # 1% risk per trade
    settings.trading.min_rr_ratio = 2.0  # Minimum 2:1 R:R
    settings.trading.max_spread = 3.0  # Max 3 pip spread
    
    # Multi-timeframe setup
    settings.timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]
    
    # Execution settings
    execution_settings = ExecutionSettings(
        refresh_interval_seconds=30,  # Check every 30 seconds
        max_open_trades=3,  # Conservative position count
        max_trades_per_symbol=1,  # One trade per symbol
        max_daily_trades=10,  # Daily limit
        max_spread_multiplier=1.2,
        slippage_pips=2.0,
        magic_number=987654321,
        enable_execution=False  # Default to signal-only for safety
    )
    
    return settings, execution_settings


def run_live_mode(symbols: list, enable_execution: bool = False):
    """Run live trading/signal mode"""
    logger = get_logger(log_level="INFO")
    
    try:
        logger.info("🔥 STARTING LIVE MODE")
        logger.info(f"📊 Symbols: {', '.join(symbols)}")
        logger.info(f"💼 Execution: {'ENABLED' if enable_execution else 'DISABLED (Signal Only)'}")
        
        # Create settings
        settings, execution_settings = create_default_settings()
        execution_settings.enable_execution = enable_execution
        
        # Create and start live executor
        executor = LiveExecutor(settings, execution_settings)
        
        print(f"\n🚀 LIVE SYSTEM STARTED")
        print(f"📈 Mode: {'LIVE TRADING' if enable_execution else 'SIGNAL ONLY'}")
        print(f"📊 Monitoring {len(symbols)} symbols")
        print(f"⏱️ Refresh: {execution_settings.refresh_interval_seconds}s")
        print(f"📁 Logs: logs/")
        print("🔄 Press Ctrl+C to stop gracefully\n")
        
        # Start live execution
        executor.start_live_execution(symbols)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Live mode stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in live mode: {str(e)}")
    finally:
        cleanup_logger()


def run_backtest_mode(symbol: str, timeframe: str, days: int = 30):
    """Run backtesting mode"""
    logger = get_logger(log_level="INFO")
    
    try:
        logger.info("📊 STARTING BACKTEST MODE")
        
        # Create analyzer
        settings, _ = create_default_settings()
        analyzer = SMCAnalyzer(settings)
        
        # Convert timeframe string to enum
        tf_map = {
            'M1': Timeframe.M1, 'M5': Timeframe.M5, 'M15': Timeframe.M15,
            'H1': Timeframe.H1, 'H4': Timeframe.H4, 'D1': Timeframe.D1
        }
        tf = tf_map.get(timeframe.upper(), Timeframe.H1)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=days)
        
        print(f"\n📊 BACKTESTING PARAMETERS")
        print(f"Symbol: {symbol}")
        print(f"Timeframe: {tf.value}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Duration: {days} days\n")
        
        # Run backtest
        results = analyzer.run_backtest(
            symbol=symbol,
            timeframe=tf,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if 'error' in results:
            logger.error(f"❌ Backtest failed: {results['error']}")
            return
        
        # Display results
        print("="*80)
        print("📈 BACKTEST RESULTS")
        print("="*80)
        
        metrics = results.get('performance_metrics', {})
        print(f"💰 Initial Balance: ${results.get('initial_balance', 0):,.2f}")
        print(f"💰 Final Balance:   ${results.get('final_balance', 0):,.2f}")
        print(f"📈 Total Return:    {results.get('total_return_pct', 0):.2f}%")
        print(f"🔢 Total Trades:    {results.get('total_trades', 0)}")
        print(f"✅ Win Rate:        {metrics.get('win_rate', 0)*100:.1f}%")
        print(f"⚡ Profit Factor:   {metrics.get('profit_factor', 0):.2f}")
        print(f"📉 Max Drawdown:    {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"💎 Sharpe Ratio:    {metrics.get('sharpe_ratio', 0):.2f}")
        
        # Save results
        filename = f"backtest_{symbol}_{tf.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analyzer.backtest_engine.export_results(results, filename)
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Error in backtest mode: {str(e)}")
    finally:
        cleanup_logger()


def run_analysis_mode(symbols: list):
    """Run one-time analysis mode"""
    logger = get_logger(log_level="INFO")
    
    try:
        logger.info("🔍 STARTING ANALYSIS MODE")
        
        # Create analyzer
        settings, _ = create_default_settings()
        analyzer = SMCAnalyzer(settings)
        
        # Connect to data source
        if not analyzer.connect_data_source():
            logger.warning("⚠️ Data source connection failed - using sample data")
        
        print(f"\n🔍 ANALYZING {len(symbols)} SYMBOLS")
        print("="*60)
        
        # Analyze each symbol
        for symbol in symbols:
            try:
                print(f"\n📊 {symbol}")
                print("-" * 40)
                
                # Get multi-timeframe analysis
                analysis = analyzer.analyze_multi_timeframe(symbol)
                
                if 'error' in analysis:
                    print(f"❌ Error: {analysis['error']}")
                    continue
                
                # Print summary
                summary = analyzer.get_analysis_summary(analysis)
                print(summary)
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {symbol}: {str(e)}")
                continue
        
        analyzer.disconnect_data_source()
        
    except Exception as e:
        logger.error(f"❌ Error in analysis mode: {str(e)}")
    finally:
        cleanup_logger()


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="SMC Forez - Professional Forex Analyzer with Smart Money Concepts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Live signal monitoring (safe mode)
  python production_runner.py --mode live --symbols EURUSD GBPUSD USDJPY
  
  # Live trading with execution (RISKY!)
  python production_runner.py --mode live --symbols EURUSD GBPUSD --execute
  
  # Backtest EURUSD on H1 for 60 days
  python production_runner.py --mode backtest --symbol EURUSD --timeframe H1 --days 60
  
  # Quick analysis of major pairs
  python production_runner.py --mode analyze --symbols EURUSD GBPUSD USDJPY AUDUSD
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['live', 'backtest', 'analyze'], 
        required=True,
        help='Operation mode'
    )
    
    parser.add_argument(
        '--symbols', 
        nargs='+', 
        default=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
        help='Currency pairs to analyze (space-separated)'
    )
    
    parser.add_argument(
        '--symbol', 
        default='EURUSD',
        help='Single symbol for backtesting'
    )
    
    parser.add_argument(
        '--timeframe', 
        choices=['M1', 'M5', 'M15', 'H1', 'H4', 'D1'], 
        default='H1',
        help='Timeframe for backtesting'
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=30,
        help='Number of days for backtesting'
    )
    
    parser.add_argument(
        '--execute', 
        action='store_true',
        help='Enable live trade execution (USE WITH CAUTION!)'
    )
    
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Validate execution mode
    if args.mode == 'live' and args.execute:
        response = input("⚠️  WARNING: Live execution enabled! Type 'CONFIRM' to proceed: ")
        if response != 'CONFIRM':
            print("❌ Live execution cancelled.")
            return
    
    # Run selected mode
    try:
        if args.mode == 'live':
            run_live_mode(args.symbols, args.execute)
        elif args.mode == 'backtest':
            run_backtest_mode(args.symbol, args.timeframe, args.days)
        elif args.mode == 'analyze':
            run_analysis_mode(args.symbols)
    
    except KeyboardInterrupt:
        print("\n⏹️ Application stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")


if __name__ == "__main__":
    main()