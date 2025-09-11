#!/usr/bin/env python3
"""
SMC Forex Analyzer Command Line Interface
"""

import argparse
import sys
import os
from typing import List, Optional
import logging

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smc_analyzer import ForexAnalyzer, MT5Connector
from smc_analyzer.mt5_connector import Timeframe


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_timeframe(tf_string: str) -> Timeframe:
    """Parse timeframe string to Timeframe enum"""
    tf_map = {
        'M1': Timeframe.M1,
        'M5': Timeframe.M5,
        'M15': Timeframe.M15,
        'M30': Timeframe.M30,
        'H1': Timeframe.H1,
        'H4': Timeframe.H4,
        'D1': Timeframe.D1
    }
    
    if tf_string.upper() not in tf_map:
        raise ValueError(f"Invalid timeframe: {tf_string}. Valid options: {list(tf_map.keys())}")
    
    return tf_map[tf_string.upper()]


def analyze_command(args):
    """Handle analyze command"""
    print("🚀 Starting SMC Forex Analysis...")
    
    # Initialize analyzer
    analyzer = ForexAnalyzer(
        mt5_account=args.account,
        mt5_password=args.password,
        mt5_server=args.server,
        min_rr_ratio=args.min_rr,
        min_confluence=args.min_confluence
    )
    
    # Connect to MT5
    if not analyzer.connect_mt5():
        print("❌ Failed to connect to MetaTrader 5")
        print("Note: MT5 connection is optional for demo purposes")
        print("Continuing with simulated data analysis...\n")
    else:
        print("✅ Connected to MetaTrader 5\n")
    
    try:
        if args.symbol:
            # Analyze single symbol
            timeframe = parse_timeframe(args.timeframe)
            print(f"📊 Analyzing {args.symbol} on {args.timeframe}...")
            
            result = analyzer.analyze_symbol(args.symbol, timeframe, args.bars)
            if result:
                print(analyzer.export_analysis(result, 'summary'))
                
                if result.trading_signals:
                    print("\n🎯 TRADING SIGNALS:")
                    for i, signal in enumerate(result.trading_signals, 1):
                        print(f"\n{i}. {analyzer.signal_generator.format_signal_output(signal)}")
                else:
                    print("No trading signals found at this time.")
            else:
                print("❌ Analysis failed. Check symbol and MT5 connection.")
        
        elif args.scan:
            # Scan multiple symbols
            print("🔍 Scanning multiple symbols for opportunities...")
            
            symbols = args.symbols.split(',') if args.symbols else None
            timeframe = parse_timeframe(args.timeframe)
            
            results = analyzer.scan_multiple_symbols(symbols, timeframe, args.bars)
            
            if results:
                print(f"\n📈 SCAN RESULTS ({len(results)} symbols analyzed):")
                
                total_signals = 0
                for symbol, result in results.items():
                    signal_count = len(result.trading_signals)
                    high_conf_count = len([s for s in result.trading_signals if s.confidence >= 0.7])
                    total_signals += signal_count
                    
                    status_emoji = "🟢" if high_conf_count > 0 else "🟡" if signal_count > 0 else "🔴"
                    print(f"{status_emoji} {symbol}: {signal_count} signals ({high_conf_count} high confidence)")
                    print(f"   Trend: {result.trend.value}, Health: {result.market_health['overall_health']:.1%}")
                
                print(f"\n📊 Total signals found: {total_signals}")
                
                # Show top opportunities
                all_signals = []
                for result in results.values():
                    all_signals.extend(result.trading_signals)
                
                if all_signals:
                    all_signals.sort(key=lambda x: x.confidence, reverse=True)
                    print("\n🏆 TOP OPPORTUNITIES:")
                    for i, signal in enumerate(all_signals[:5], 1):
                        print(f"{i}. {signal.symbol} - {signal.signal_type.value.upper()}")
                        print(f"   Entry: {signal.entry_price:.5f}, Confidence: {signal.confidence:.1%}")
            else:
                print("❌ No analysis results obtained.")
        
        elif args.live:
            # Get live signals
            print("⚡ Getting live trading signals...")
            
            symbols = args.symbols.split(',') if args.symbols else None
            timeframes = [parse_timeframe(tf) for tf in args.timeframes.split(',')] if args.timeframes else None
            
            signals = analyzer.get_live_signals(symbols, timeframes, args.min_confidence)
            
            if signals:
                print(f"\n🎯 LIVE SIGNALS ({len(signals)} found):")
                for i, signal in enumerate(signals, 1):
                    print(f"\n{i}. {analyzer.signal_generator.format_signal_output(signal)}")
            else:
                print("No live signals meet the confidence criteria.")
        
        elif args.overview:
            # Market overview
            print("🌍 Getting market overview...")
            
            overview = analyzer.get_market_overview()
            
            print(f"\n📊 MARKET OVERVIEW")
            print(f"Analysis Time: {overview['timestamp']}")
            print(f"Symbols Analyzed: {overview['symbols_analyzed']}")
            print(f"Total Signals: {overview['total_signals']}")
            print(f"High Confidence Signals: {overview['high_confidence_signals']}")
            
            print("\n📈 MARKET CONDITIONS:")
            for symbol, condition in overview['market_conditions'].items():
                trend_emoji = "📈" if condition['trend'] == 'bullish' else "📉" if condition['trend'] == 'bearish' else "➡️"
                health_emoji = "🟢" if condition['health'] >= 0.7 else "🟡" if condition['health'] >= 0.4 else "🔴"
                print(f"{trend_emoji} {health_emoji} {symbol}: {condition['trend'].title()} "
                      f"(Health: {condition['health']:.1%}, Signals: {condition['signals']})")
            
            if overview['top_opportunities']:
                print("\n🏆 TOP OPPORTUNITIES:")
                for i, opp in enumerate(overview['top_opportunities'], 1):
                    print(f"{i}. {opp['symbol']} - {opp['type'].upper()}")
                    print(f"   Entry: {opp['entry']:.5f}, Confidence: {opp['confidence']:.1%}, RR: {opp['rr_ratio']:.2f}")
    
    finally:
        analyzer.disconnect_mt5()
        print("\n✅ Analysis complete!")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="SMC Forex Analyzer - A-grade Forex analysis with Smart Money Concepts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single symbol
  python cli.py analyze --symbol EURUSD --timeframe H1
  
  # Scan multiple symbols
  python cli.py scan --symbols EURUSD,GBPUSD,USDJPY --timeframe H4
  
  # Get live signals
  python cli.py live --min-confidence 0.7
  
  # Market overview
  python cli.py overview
        """
    )
    
    # Global arguments
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--account', type=int, help='MT5 account number')
    parser.add_argument('--password', help='MT5 password')
    parser.add_argument('--server', help='MT5 server')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze single symbol')
    analyze_parser.add_argument('--symbol', required=True, help='Currency pair symbol (e.g., EURUSD)')
    analyze_parser.add_argument('--timeframe', default='H1', help='Timeframe (M1,M5,M15,M30,H1,H4,D1)')
    analyze_parser.add_argument('--bars', type=int, default=1000, help='Number of bars to analyze')
    analyze_parser.add_argument('--min-rr', type=float, default=1.5, help='Minimum risk-reward ratio')
    analyze_parser.add_argument('--min-confluence', type=int, default=3, help='Minimum confluence factors')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan multiple symbols')
    scan_parser.add_argument('--symbols', help='Comma-separated symbols (default: major pairs)')
    scan_parser.add_argument('--timeframe', default='H1', help='Timeframe (M1,M5,M15,M30,H1,H4,D1)')
    scan_parser.add_argument('--bars', type=int, default=500, help='Number of bars to analyze')
    scan_parser.add_argument('--min-rr', type=float, default=1.5, help='Minimum risk-reward ratio')
    scan_parser.add_argument('--min-confluence', type=int, default=3, help='Minimum confluence factors')
    
    # Live signals command
    live_parser = subparsers.add_parser('live', help='Get live trading signals')
    live_parser.add_argument('--symbols', help='Comma-separated symbols (default: major pairs)')
    live_parser.add_argument('--timeframes', default='H1,H4', help='Comma-separated timeframes')
    live_parser.add_argument('--min-confidence', type=float, default=0.6, help='Minimum signal confidence')
    live_parser.add_argument('--min-rr', type=float, default=1.5, help='Minimum risk-reward ratio')
    live_parser.add_argument('--min-confluence', type=int, default=3, help='Minimum confluence factors')
    
    # Overview command
    overview_parser = subparsers.add_parser('overview', help='Get market overview')
    overview_parser.add_argument('--min-rr', type=float, default=1.5, help='Minimum risk-reward ratio')
    overview_parser.add_argument('--min-confluence', type=int, default=3, help='Minimum confluence factors')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return
    
    # Map commands to functions
    command_map = {
        'analyze': analyze_command,
        'scan': lambda args: setattr(args, 'scan', True) or analyze_command(args),
        'live': lambda args: setattr(args, 'live', True) or analyze_command(args),
        'overview': lambda args: setattr(args, 'overview', True) or analyze_command(args)
    }
    
    # Execute command
    try:
        command_map[args.command](args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()