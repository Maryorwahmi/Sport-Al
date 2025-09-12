#!/usr/bin/env python3
"""
Professional-Grade SMC Forez Signal Quality Analysis Demo
Showcases institutional-level signal validation and quality scoring
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.analyzer import SMCAnalyzer
from smc_forez.signals.signal_quality_analyzer import QualityGrade

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise for demo
logger = logging.getLogger(__name__)


def create_realistic_data(symbol: str = "EURUSD", bars: int = 1000) -> pd.DataFrame:
    """Create realistic OHLC data with market structure patterns"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=bars, freq='1H')
    
    # Create more realistic price action with trends and ranges
    base_price = 1.1000
    prices = [base_price]
    
    # Add trending periods and ranging periods
    for i in range(1, bars):
        # Create trend cycles
        trend_cycle = 200  # bars
        trend_position = (i % trend_cycle) / trend_cycle
        
        if trend_position < 0.3:  # Uptrend
            move = np.random.normal(0.0001, 0.0005)
        elif trend_position < 0.7:  # Range
            move = np.random.normal(0, 0.0003)
        else:  # Downtrend  
            move = np.random.normal(-0.0001, 0.0005)
        
        prices.append(max(0.5, prices[-1] * (1 + move)))
    
    # Create OHLC data
    data = []
    for i, price in enumerate(prices):
        volatility = 0.002 * (1 + 0.5 * np.sin(i / 50))  # Varying volatility
        
        open_price = price
        high_price = price + np.random.uniform(0, volatility)
        low_price = price - np.random.uniform(0, volatility)
        close_price = price + np.random.uniform(-volatility/2, volatility/2)
        
        data.append({
            'Open': round(open_price, 5),
            'High': round(max(open_price, high_price, close_price), 5),
            'Low': round(min(open_price, low_price, close_price), 5),
            'Close': round(close_price, 5)
        })
    
    return pd.DataFrame(data, index=dates)


class MockDataSource:
    """Mock data source for demonstration"""
    def connect(self): return True
    def disconnect(self): pass
    def get_rates(self, symbol, timeframe, count):
        return create_realistic_data(symbol, count)


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_quality_report(quality_report: dict, symbol: str):
    """Print formatted quality report"""
    print(f"\n📊 INSTITUTIONAL-GRADE ANALYSIS REPORT: {symbol}")
    print("-" * 60)
    
    # Overall assessment
    score = quality_report.get('total_quality_score', 0)
    grade = quality_report.get('quality_grade', 'unknown')
    should_execute = quality_report.get('should_execute', False)
    
    print(f"🎯 Overall Quality Score: {score:.1f}/100")
    print(f"📈 Quality Grade: {grade.upper()}")
    print(f"⚡ Execution Status: {'✅ APPROVED' if should_execute else '❌ REJECTED'}")
    
    # Signal summary
    signal_summary = quality_report.get('signal_summary', {})
    if signal_summary:
        print(f"\n📋 Signal Details:")
        print(f"   Type: {signal_summary.get('type', 'unknown').upper()}")
        print(f"   Strength: {signal_summary.get('strength', 'unknown')}")
        print(f"   Entry: {signal_summary.get('entry_price', 0):.5f}")
        print(f"   Stop Loss: {signal_summary.get('stop_loss', 0):.5f}")
        print(f"   Take Profit: {signal_summary.get('take_profit', 0):.5f}")
    
    # Component analysis
    analysis_components = quality_report.get('analysis_components', {})
    
    if 'multi_timeframe' in analysis_components:
        mtf = analysis_components['multi_timeframe']
        print(f"\n🔍 Multi-Timeframe Analysis:")
        print(f"   Cascade Score: {mtf.get('cascade_score', 0):.1f}/100")
        print(f"   HTF Bias: {mtf.get('htf_bias', {}).get('direction', 'unknown')} ({mtf.get('htf_bias', {}).get('strength', 0):.1f}%)")
        print(f"   MTF Setup: {'✅ Confirmed' if mtf.get('mtf_confirmation', {}).get('confirmed', False) else '❌ Not confirmed'}")
        print(f"   LTF Trigger: {'✅ Valid' if mtf.get('ltf_trigger', {}).get('valid', False) else '❌ Invalid'}")
    
    if 'liquidity_positioning' in analysis_components:
        liq = analysis_components['liquidity_positioning']
        print(f"\n💧 Liquidity Positioning:")
        print(f"   Score: {liq.get('positioning_score', 0)}/100")
        if liq.get('nearest_high'):
            print(f"   Nearest High: {liq.get('nearest_high', 0):.5f}")
        if liq.get('nearest_low'):
            print(f"   Nearest Low: {liq.get('nearest_low', 0):.5f}")
        reasoning = liq.get('positioning_reason', [])
        if reasoning:
            print(f"   Reasoning: {', '.join(reasoning[:2])}")
    
    if 'confluence_scoring' in analysis_components:
        conf = analysis_components['confluence_scoring']
        print(f"\n🎯 Confluence Analysis:")
        print(f"   Score: {conf.get('total_score', 0):.1f}/100")
        print(f"   Factors Present: {conf.get('factors_present', 0)}")
        
        factor_details = conf.get('factor_details', {})
        if factor_details:
            print("   Factor Breakdown:")
            for factor, details in factor_details.items():
                if details.get('weighted_score', 0) > 0:
                    print(f"     • {factor}: {details.get('weighted_score', 0):.1f}")
    
    if 'risk_reward' in analysis_components:
        rr = analysis_components['risk_reward']
        print(f"\n⚖️ Risk-Reward Analysis:")
        print(f"   Valid: {'✅ Yes' if rr.get('valid', False) else '❌ No'}")
        print(f"   R:R Ratio: {rr.get('rr_ratio', 0):.2f}:1")
        print(f"   Risk Amount: {rr.get('risk_amount', 0):.5f}")
        print(f"   Reward Amount: {rr.get('reward_amount', 0):.5f}")
    
    # Decision reasoning
    reasoning = quality_report.get('decision_reasoning', [])
    if reasoning:
        print(f"\n💭 Decision Reasoning:")
        for i, reason in enumerate(reasoning[:5]):  # Show first 5 reasons
            print(f"   {i+1}. {reason}")
    
    print("-" * 60)


def demonstrate_institutional_analysis():
    """Demonstrate institutional-grade signal analysis"""
    print_header("INSTITUTIONAL-GRADE SIGNAL ANALYSIS DEMONSTRATION")
    
    # Setup enhanced analyzer
    settings = Settings()
    settings.quality.enable_quality_analysis = True
    settings.quality.enable_logging = False  # Disable logging for cleaner demo output
    
    analyzer = SMCAnalyzer(settings)
    analyzer.data_source = MockDataSource()
    
    print("🚀 Initialized Professional SMC Analyzer")
    print(f"   Quality Analysis: {'✅ Enabled' if analyzer.quality_analyzer else '❌ Disabled'}")
    print(f"   Timeframes: {[tf.value for tf in settings.timeframes]}")
    print(f"   Quality Thresholds: Institutional≥{settings.quality.min_institutional_score}, Professional≥{settings.quality.min_professional_score}")
    
    # Test multiple symbols
    test_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4]
    
    print(f"\n🔍 Analyzing {len(test_symbols)} symbols with institutional-grade quality validation...")
    
    all_results = []
    
    for symbol in test_symbols:
        print(f"\n📈 Processing {symbol}...")
        
        try:
            # Perform institutional-grade analysis
            result = analyzer.analyze_institutional_grade_signal(symbol, timeframes)
            
            if 'error' not in result:
                quality_report = result.get('quality_report', {})
                score = quality_report.get('total_quality_score', 0)
                grade = quality_report.get('quality_grade', 'unknown')
                
                print(f"   ✅ Analysis complete - Score: {score:.1f}/100 ({grade})")
                
                all_results.append({
                    'symbol': symbol,
                    'score': score,
                    'grade': grade,
                    'quality_report': quality_report
                })
            else:
                print(f"   ❌ Analysis failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {symbol}: {str(e)}")
    
    # Show detailed results for best signals
    if all_results:
        print_header("DETAILED QUALITY ANALYSIS RESULTS")
        
        # Sort by quality score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        for i, result in enumerate(all_results[:2]):  # Show top 2
            print_quality_report(result['quality_report'], result['symbol'])
        
        # Summary table
        print_header("QUALITY SUMMARY TABLE")
        print(f"{'Symbol':<10} {'Score':<8} {'Grade':<15} {'Status':<10}")
        print("-" * 50)
        
        for result in all_results:
            symbol = result['symbol']
            score = result['score']
            grade = result['grade'].capitalize()
            status = '✅ EXECUTE' if result['quality_report'].get('should_execute', False) else '❌ REJECT'
            print(f"{symbol:<10} {score:<8.1f} {grade:<15} {status:<10}")


def demonstrate_quality_grades():
    """Demonstrate different quality grades"""
    print_header("SIGNAL QUALITY GRADING SYSTEM")
    
    from smc_forez.signals.signal_quality_analyzer import SignalQualityAnalyzer
    
    quality_settings = {
        'min_institutional_score': 85.0,
        'min_professional_score': 70.0,
        'min_execution_score': 55.0
    }
    
    analyzer = SignalQualityAnalyzer(quality_settings)
    
    # Demo quality grades
    test_scores = [95, 82, 73, 62, 48, 35]
    
    print("📊 Quality Grade Classification:")
    print(f"{'Score':<8} {'Grade':<15} {'Description':<40}")
    print("-" * 70)
    
    descriptions = {
        'institutional': 'Highest quality - institutional standard',
        'professional': 'High quality - professional trader standard', 
        'intermediate': 'Moderate quality - acceptable for execution',
        'basic': 'Basic quality - proceed with caution',
        'poor': 'Poor quality - avoid execution'
    }
    
    for score in test_scores:
        grade = analyzer.determine_quality_grade(score)
        desc = descriptions.get(grade.value, 'Unknown')
        print(f"{score:<8} {grade.value.upper():<15} {desc:<40}")


def demonstrate_configuration():
    """Demonstrate configuration options"""
    print_header("CONFIGURATION & CUSTOMIZATION OPTIONS")
    
    settings = Settings()
    
    print("⚙️ Quality Analysis Configuration:")
    print(f"   Institutional Score Threshold: {settings.quality.min_institutional_score}")
    print(f"   Professional Score Threshold: {settings.quality.min_professional_score}")
    print(f"   Execution Score Threshold: {settings.quality.min_execution_score}")
    
    print(f"\n🎯 Multi-Timeframe Weights:")
    print(f"   Higher Timeframe (HTF): {settings.quality.htf_weight * 100:.0f}%")
    print(f"   Mid Timeframe (MTF): {settings.quality.mtf_weight * 100:.0f}%")
    print(f"   Lower Timeframe (LTF): {settings.quality.ltf_weight * 100:.0f}%")
    
    print(f"\n📊 Confluence Factor Weights:")
    print(f"   Trend Alignment: {settings.quality.trend_weight:.0f}/100")
    print(f"   Structure Breaks: {settings.quality.structure_weight:.0f}/100")
    print(f"   Order Blocks: {settings.quality.orderblock_weight:.0f}/100")
    print(f"   Liquidity Zones: {settings.quality.liquidity_weight:.0f}/100")
    print(f"   Fair Value Gaps: {settings.quality.fvg_weight:.0f}/100")
    print(f"   Supply/Demand: {settings.quality.supply_demand_weight:.0f}/100")
    
    print(f"\n⚖️ Risk Management:")
    print(f"   Minimum R:R Ratio: {settings.quality.min_rr_ratio}:1")
    print(f"   Maximum Risk per Trade: {settings.quality.max_risk_percentage * 100:.1f}%")
    
    print(f"\n🕐 Execution Filters:")
    print(f"   Allowed Sessions: {', '.join(settings.quality.allowed_sessions)}")
    print(f"   Max Concurrent Trades: {settings.quality.max_concurrent_trades}")
    print(f"   Duplicate Detection Window: {settings.quality.duplicate_time_window} hours")


def main():
    """Run the comprehensive demonstration"""
    print("🎯 SMC FOREZ - PROFESSIONAL SIGNAL QUALITY ANALYSIS")
    print("   Institutional-Grade Trading Signal Validation System")
    print("   Version 2.0 - Enhanced with Quality Analysis")
    
    try:
        # Core demonstrations
        demonstrate_quality_grades()
        demonstrate_configuration()
        demonstrate_institutional_analysis()
        
        # Summary
        print_header("SYSTEM CAPABILITIES SUMMARY")
        print("✅ Multi-timeframe bias confirmation (HTF→MTF→LTF cascade)")
        print("✅ Liquidity positioning analysis with proximity scoring")
        print("✅ Weighted confluence scoring system (0-100 scale)")
        print("✅ Risk-reward validation with structural reference points")
        print("✅ Execution readiness checks (duplicates, sessions, limits)")
        print("✅ Structured logging and transparency (JSON format)")
        print("✅ Configurable quality thresholds and factor weights")
        print("✅ Institutional-grade signal classification system")
        print("✅ Professional backtesting integrity with quality filtering")
        print("✅ Portfolio-level risk management integration")
        
        print_header("NEXT STEPS FOR PRODUCTION USE")
        print("1. 📊 Configure MT5 connection settings")
        print("2. ⚙️ Adjust quality thresholds to your trading style")
        print("3. 🎯 Customize confluence factor weights based on strategy")
        print("4. 📈 Test with historical data using backtesting engine")
        print("5. 💼 Deploy in paper trading environment first")
        print("6. 🚀 Go live with institutional-grade signal quality!")
        
        print("\n🎉 DEMONSTRATION COMPLETE! 🎉")
        print("The institutional-grade signal quality analysis system is operational.")
        
    except Exception as e:
        print(f"\n❌ Error in demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()