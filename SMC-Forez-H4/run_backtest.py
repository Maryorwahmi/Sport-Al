#!/usr/bin/env python3
"""
Main entry point for SMC Forez Backtesting System
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backtesting.backtest_runner import (
    BacktestRunner,
    BacktestConfiguration,
    interactive_selection
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


def main():
    """Main function"""
    print("\n" + "="*80)
    print("🚀 SMC FOREZ - COMPREHENSIVE BACKTESTING SYSTEM")
    print("="*80)
    print("\nFeatures:")
    print("  ✓ Win Rate")
    print("  ✓ Profit Factor")
    print("  ✓ Expected Payoff")
    print("  ✓ Maximum Drawdown")
    print("  ✓ Sharpe Ratio")
    print("  ✓ Recovery Factor")
    print("  ✓ Average Trade Duration")
    print("  ✓ Consecutive Losses (Stress Test)")
    print("  ✓ Multi-Timeframe Robustness (H4, H1, M15 synchronous)")
    print()
    
    # Interactive configuration
    config = interactive_selection()
    
    # Create and run backtest
    runner = BacktestRunner(config)
    results = runner.run()
    
    # Display results
    runner.print_results(results)
    
    # Export results
    runner.export_results(results)
    
    print("✅ Backtest completed successfully!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest cancelled by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        logging.exception("Backtest failed")
        sys.exit(1)
