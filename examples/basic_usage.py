"""
Example usage of the SMC Forez analyzer
"""
import logging
from datetime import datetime
from smc_forez import SMCAnalyzer, Settings
from smc_forez.config.settings import Timeframe

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main example function"""
    
    # Create settings (customize as needed)
    settings = Settings()
    
    # Initialize analyzer
    analyzer = SMCAnalyzer(settings)
    
    print("SMC Forez - Professional Forex Analyzer")
    print("=" * 50)
    
    # Example 1: Single timeframe analysis
    print("\n1. Single Timeframe Analysis")
    print("-" * 30)
    
    # Note: This example uses dummy data since MT5 connection might not be available
    # In production, you would connect to MT5:
    # if analyzer.connect_data_source():
    #     analysis = analyzer.analyze_single_timeframe("EURUSD", Timeframe.H1)
    #     print(analyzer.get_analysis_summary(analysis))
    #     analyzer.disconnect_data_source()
    
    print("Connect to MT5 to analyze live data")
    print("Example: analyzer.analyze_single_timeframe('EURUSD', Timeframe.H1)")
    
    # Example 2: Multi-timeframe analysis
    print("\n2. Multi-Timeframe Analysis")
    print("-" * 30)
    print("Example: analyzer.analyze_multi_timeframe('EURUSD')")
    
    # Example 3: Opportunity scanning
    print("\n3. Opportunity Scanning")
    print("-" * 30)
    major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]
    print(f"Example: analyzer.get_current_opportunities({major_pairs})")
    
    # Example 4: Backtesting
    print("\n4. Backtesting")
    print("-" * 30)
    print("Example: analyzer.run_backtest('EURUSD', Timeframe.H1, '2023-01-01', '2023-12-31')")
    
    # Show configuration
    print("\n5. Current Configuration")
    print("-" * 30)
    print(f"Supported Timeframes: {[tf.value for tf in settings.timeframes]}")
    print(f"Risk per Trade: {settings.trading.risk_per_trade * 100}%")
    print(f"Min R:R Ratio: {settings.trading.min_rr_ratio}")
    print(f"Swing Length: {settings.analysis.swing_length}")
    print(f"FVG Min Size: {settings.analysis.fvg_min_size} pips")
    print(f"Order Block Lookback: {settings.analysis.order_block_lookback}")
    
    print("\nFor live trading, configure MT5 credentials in settings:")
    print("settings.mt5_login = your_login")
    print("settings.mt5_password = your_password")
    print("settings.mt5_server = your_server")

if __name__ == "__main__":
    main()