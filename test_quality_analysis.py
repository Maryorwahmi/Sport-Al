#!/usr/bin/env python3
"""
Test the enhanced SMC Forez analyzer with institutional-grade signal quality analysis
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.analyzer import SMCAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_data(symbol: str = "EURUSD", bars: int = 1000) -> pd.DataFrame:
    """Create sample OHLC data for testing"""
    np.random.seed(42)  # For reproducible results
    
    dates = pd.date_range(start='2023-01-01', periods=bars, freq='1H')
    
    # Generate realistic price movement
    base_price = 1.1000
    returns = np.random.normal(0, 0.0005, bars)  # Small random moves
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Create OHLC data with realistic spreads
    data = []
    for i, price in enumerate(prices):
        spread = 0.00015  # 1.5 pip spread
        
        open_price = price
        high_price = price + np.random.uniform(0, 0.002)  # Up to 20 pips high
        low_price = price - np.random.uniform(0, 0.002)   # Up to 20 pips low
        close_price = price + np.random.uniform(-0.001, 0.001)  # ±10 pips close
        
        data.append({
            'Open': round(open_price, 5),
            'High': round(max(open_price, high_price, close_price), 5),
            'Low': round(min(open_price, low_price, close_price), 5),
            'Close': round(close_price, 5)
        })
    
    return pd.DataFrame(data, index=dates)


def test_quality_settings():
    """Test quality settings configuration"""
    print("\n" + "="*60)
    print("TESTING QUALITY SETTINGS CONFIGURATION")
    print("="*60)
    
    settings = Settings()
    
    # Test quality settings
    print(f"✓ Quality analysis enabled: {settings.quality.enable_quality_analysis}")
    print(f"✓ Institutional score threshold: {settings.quality.min_institutional_score}")
    print(f"✓ Professional score threshold: {settings.quality.min_professional_score}")
    print(f"✓ Execution score threshold: {settings.quality.min_execution_score}")
    print(f"✓ Multi-timeframe weights: HTF={settings.quality.htf_weight}, MTF={settings.quality.mtf_weight}, LTF={settings.quality.ltf_weight}")
    print(f"✓ Factor weights configured: {len([w for w in [settings.quality.trend_weight, settings.quality.structure_weight] if w > 0])} factors")
    
    return True


def test_signal_quality_analyzer():
    """Test the signal quality analyzer directly"""
    print("\n" + "="*60)
    print("TESTING SIGNAL QUALITY ANALYZER")
    print("="*60)
    
    try:
        from smc_forez.signals.signal_quality_analyzer import SignalQualityAnalyzer, QualityGrade
        
        quality_settings = {
            'min_institutional_score': 85.0,
            'min_professional_score': 70.0,
            'min_execution_score': 55.0,
            'htf_weight': 0.4,
            'mtf_weight': 0.35,
            'ltf_weight': 0.25,
            'trend_weight': 25.0,
            'structure_weight': 20.0,
            'orderblock_weight': 15.0,
            'liquidity_weight': 20.0,
            'fvg_weight': 10.0,
            'supply_demand_weight': 10.0,
            'min_rr_ratio': 2.0,
            'max_risk_percentage': 0.02,
            'allowed_sessions': ['london', 'newyork', 'overlap'],
            'max_concurrent_trades': 5,
            'duplicate_time_window': 4
        }
        
        analyzer = SignalQualityAnalyzer(quality_settings)
        print("✓ SignalQualityAnalyzer initialized successfully")
        
        # Test quality grade determination
        grades = [
            (90, QualityGrade.INSTITUTIONAL),
            (75, QualityGrade.PROFESSIONAL), 
            (60, QualityGrade.INTERMEDIATE),
            (45, QualityGrade.BASIC),
            (30, QualityGrade.POOR)
        ]
        
        for score, expected_grade in grades:
            grade = analyzer.determine_quality_grade(score)
            print(f"✓ Score {score} → {grade.value} (expected: {expected_grade.value})")
            assert grade == expected_grade, f"Expected {expected_grade.value}, got {grade.value}"
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing SignalQualityAnalyzer: {str(e)}")
        return False


def test_enhanced_analyzer():
    """Test the enhanced SMC analyzer with quality analysis"""
    print("\n" + "="*60)
    print("TESTING ENHANCED SMC ANALYZER")
    print("="*60)
    
    try:
        # Initialize analyzer with quality analysis enabled
        settings = Settings()
        settings.quality.enable_quality_analysis = True
        
        # Mock the data source to avoid MT5 dependency
        class MockDataSource:
            def connect(self): return True
            def disconnect(self): pass
            def get_rates(self, symbol, timeframe, count):
                return create_sample_data(symbol, count)
            def get_historical_data(self, symbol, timeframe, count, start_date=None, end_date=None):
                return create_sample_data(symbol, count)
        
        analyzer = SMCAnalyzer(settings)
        analyzer.data_source = MockDataSource()  # Mock data source
        
        print("✓ Enhanced SMCAnalyzer initialized successfully")
        print(f"✓ Quality analyzer available: {analyzer.quality_analyzer is not None}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing enhanced analyzer: {str(e)}")
        return False


def test_institutional_grade_analysis():
    """Test institutional-grade signal analysis"""
    print("\n" + "="*60)
    print("TESTING INSTITUTIONAL-GRADE ANALYSIS")
    print("="*60)
    
    try:
        # Setup analyzer
        settings = Settings()
        settings.quality.enable_quality_analysis = True
        
        class MockDataSource:
            def connect(self): return True
            def disconnect(self): pass
            def get_rates(self, symbol, timeframe, count):
                return create_sample_data(symbol, count)
            def get_historical_data(self, symbol, timeframe, count, start_date=None, end_date=None):
                return create_sample_data(symbol, count)
        
        analyzer = SMCAnalyzer(settings)
        analyzer.data_source = MockDataSource()
        
        # Test single timeframe analysis first
        print("Testing single timeframe analysis...")
        single_result = analyzer.analyze_single_timeframe("EURUSD", Timeframe.H1, 500)
        
        if 'error' not in single_result:
            print("✓ Single timeframe analysis successful")
            print(f"  Signal type: {single_result['signal']['signal_type']}")
            print(f"  Signal strength: {single_result['signal']['signal_strength']}")
            print(f"  Confluence score: {single_result['signal']['confluence_score']}")
        else:
            print(f"✗ Single timeframe analysis failed: {single_result['error']}")
            return False
        
        # Test institutional-grade analysis if quality analyzer is available
        if analyzer.quality_analyzer:
            print("Testing institutional-grade analysis...")
            
            timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4]
            institutional_result = analyzer.analyze_institutional_grade_signal("EURUSD", timeframes)
            
            if 'error' not in institutional_result:
                print("✓ Institutional-grade analysis successful")
                
                quality_report = institutional_result.get('quality_report', {})
                print(f"  Quality score: {quality_report.get('total_quality_score', 0)}")
                print(f"  Quality grade: {quality_report.get('quality_grade', 'unknown')}")
                print(f"  Should execute: {quality_report.get('should_execute', False)}")
                print(f"  Timeframes analyzed: {len(institutional_result.get('timeframes_analyzed', []))}")
                
                # Print decision reasoning
                reasoning = quality_report.get('decision_reasoning', [])
                if reasoning:
                    print("  Decision reasoning:")
                    for reason in reasoning[:3]:  # Show first 3 reasons
                        print(f"    • {reason}")
                
            else:
                print(f"✗ Institutional-grade analysis failed: {institutional_result['error']}")
                return False
        else:
            print("⚠ Quality analyzer not available, skipping institutional-grade test")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing institutional-grade analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_opportunities_scanning():
    """Test enhanced opportunities scanning"""
    print("\n" + "="*60)
    print("TESTING ENHANCED OPPORTUNITIES SCANNING")
    print("="*60)
    
    try:
        settings = Settings()
        settings.quality.enable_quality_analysis = True
        
        class MockDataSource:
            def connect(self): return True
            def disconnect(self): pass
            def get_rates(self, symbol, timeframe, count):
                return create_sample_data(symbol, count)
            def get_historical_data(self, symbol, timeframe, count, start_date=None, end_date=None):
                return create_sample_data(symbol, count)
        
        analyzer = SMCAnalyzer(settings)
        analyzer.data_source = MockDataSource()
        
        # Test with small symbol list
        test_symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        timeframes = [Timeframe.H1, Timeframe.H4]
        
        print(f"Scanning {len(test_symbols)} symbols with quality analysis...")
        opportunities = analyzer.get_current_opportunities(
            test_symbols, timeframes, use_quality_analysis=True
        )
        
        print(f"✓ Found {len(opportunities)} opportunities")
        
        for i, opp in enumerate(opportunities[:2]):  # Show first 2
            print(f"  Opportunity {i+1}:")
            print(f"    Symbol: {opp.get('symbol', 'unknown')}")
            print(f"    Analysis type: {opp.get('analysis_type', 'unknown')}")
            
            if opp.get('analysis_type') == 'institutional_grade':
                print(f"    Quality score: {opp.get('quality_score', 0)}")
                print(f"    Quality grade: {opp.get('quality_grade', 'unknown')}")
                print(f"    Should execute: {opp.get('should_execute', False)}")
            else:
                rec = opp.get('recommendation', {})
                print(f"    Confidence: {rec.get('confidence', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing opportunities scanning: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("SMC FOREZ - INSTITUTIONAL-GRADE SIGNAL QUALITY TESTS")
    print("="*60)
    
    tests = [
        ("Quality Settings Configuration", test_quality_settings),
        ("Signal Quality Analyzer", test_signal_quality_analyzer),
        ("Enhanced Analyzer", test_enhanced_analyzer),
        ("Institutional-Grade Analysis", test_institutional_grade_analysis),
        ("Enhanced Opportunities Scanning", test_opportunities_scanning)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ CRITICAL ERROR in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("The institutional-grade signal quality analysis system is ready!")
    else:
        print(f"\n⚠ {total - passed} tests failed. Review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)