"""
Quick demonstration of SMC Forez capabilities
"""
import sys
import os

# Add project to path
sys.path.insert(0, '/home/runner/work/SMC-Forez/SMC-Forez')

from smc_forez.config.settings import Settings, Timeframe, TradingSettings, AnalysisSettings

def demonstrate_features():
    """Demonstrate the key features of SMC Forez"""
    
    print("🚀 SMC FOREZ - PROFESSIONAL FOREX ANALYZER")
    print("=" * 60)
    print("Smart Money Concepts & Multi-Timeframe Analysis")
    print()
    
    # 1. Configuration System
    print("📋 1. CONFIGURATION SYSTEM")
    print("-" * 30)
    
    settings = Settings()
    print(f"✓ Default Timeframes: {[tf.value for tf in settings.timeframes]}")
    print(f"✓ Risk per Trade: {settings.trading.risk_per_trade * 100}%")
    print(f"✓ Min R:R Ratio: {settings.trading.min_rr_ratio}")
    print(f"✓ Swing Length: {settings.analysis.swing_length} bars")
    print(f"✓ FVG Min Size: {settings.analysis.fvg_min_size} pips")
    print(f"✓ Initial Balance: ${settings.backtest.initial_balance:,.2f}")
    print()
    
    # 2. Customization Example
    print("⚙️  2. CUSTOM CONFIGURATION EXAMPLE")
    print("-" * 30)
    
    custom_settings = Settings()
    custom_settings.trading.risk_per_trade = 0.02  # 2% risk
    custom_settings.trading.min_rr_ratio = 2.5     # 2.5:1 R:R
    custom_settings.analysis.swing_length = 15     # 15-bar swings
    custom_settings.timeframes = [Timeframe.H4, Timeframe.H1]  # Focus on H4/H1
    
    print(f"✓ Custom Risk: {custom_settings.trading.risk_per_trade * 100}%")
    print(f"✓ Custom R:R: {custom_settings.trading.min_rr_ratio}")
    print(f"✓ Custom Swings: {custom_settings.analysis.swing_length} bars")
    print(f"✓ Custom Timeframes: {[tf.value for tf in custom_settings.timeframes]}")
    print()
    
    # 3. Available Components
    print("🧩 3. ANALYSIS COMPONENTS")
    print("-" * 30)
    
    components = [
        ("MT5DataSource", "Live/Historical data from MetaTrader 5"),
        ("MarketStructureAnalyzer", "Swing points, trends, BOS/CHOCH detection"),
        ("SmartMoneyAnalyzer", "FVGs, Order Blocks, Liquidity zones"),
        ("SignalGenerator", "Confluence-based trading signals"),
        ("MultiTimeframeAnalyzer", "Cross-timeframe analysis & confirmation"),
        ("BacktestEngine", "Historical performance testing"),
    ]
    
    for component, description in components:
        print(f"✓ {component:25} - {description}")
    print()
    
    # 4. Smart Money Concepts
    print("🧠 4. SMART MONEY CONCEPTS")
    print("-" * 30)
    
    smc_features = [
        "Fair Value Gaps (FVGs) - Price imbalances",
        "Order Blocks - Institutional order zones", 
        "Liquidity Zones - Stop hunting areas",
        "Supply/Demand Zones - Accumulation/Distribution",
        "Break of Structure (BOS) - Trend continuation",
        "Change of Character (CHOCH) - Trend reversal"
    ]
    
    for feature in smc_features:
        print(f"✓ {feature}")
    print()
    
    # 5. Signal Generation
    print("📊 5. SIGNAL GENERATION FEATURES")
    print("-" * 30)
    
    signal_features = [
        "Multi-factor confluence scoring",
        "Automatic entry/SL/TP calculation", 
        "Risk/reward ratio optimization",
        "Signal strength classification",
        "Cross-timeframe confirmation",
        "Real-time opportunity scanning"
    ]
    
    for feature in signal_features:
        print(f"✓ {feature}")
    print()
    
    # 6. Performance Metrics
    print("📈 6. BACKTESTING METRICS")
    print("-" * 30)
    
    metrics = [
        "Win Rate & Profit Factor",
        "Maximum Drawdown & Recovery Factor",
        "Sharpe Ratio & Risk-Adjusted Returns", 
        "Average Win/Loss & R:R Ratios",
        "Consecutive Win/Loss Streaks",
        "Trade Duration Analysis"
    ]
    
    for metric in metrics:
        print(f"✓ {metric}")
    print()
    
    # 7. Usage Examples
    print("💻 7. USAGE EXAMPLES")
    print("-" * 30)
    
    print("Single Timeframe Analysis:")
    print("  analyzer.analyze_single_timeframe('EURUSD', Timeframe.H1)")
    print()
    
    print("Multi-Timeframe Analysis:")
    print("  analyzer.analyze_multi_timeframe('EURUSD')")
    print()
    
    print("Opportunity Scanning:")
    print("  analyzer.get_current_opportunities(['EURUSD', 'GBPUSD'])")
    print()
    
    print("Backtesting:")
    print("  analyzer.run_backtest('EURUSD', Timeframe.H1, '2023-01-01', '2023-12-31')")
    print()
    
    # 8. Installation
    print("📦 8. INSTALLATION & SETUP")
    print("-" * 30)
    
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    
    print("2. Configure MT5 connection:")
    print("   settings.mt5_login = your_login")
    print("   settings.mt5_password = 'your_password'")
    print("   settings.mt5_server = 'your_server'")
    print()
    
    print("3. Initialize and run:")
    print("   analyzer = SMCAnalyzer(settings)")
    print("   analyzer.connect_data_source()")
    print()
    
    print("🎯 READY FOR PRODUCTION TRADING!")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_features()