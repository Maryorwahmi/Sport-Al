"""
Test suite for Candle Pattern Self-Learning AI
"""
import sys
sys.path.append('backend')

import pandas as pd
import numpy as np
from datetime import datetime

def test_data_manager():
    """Test data ingestion"""
    print("Testing Data Manager...")
    from data.data_manager import DataManager
    
    dm = DataManager()
    df = dm.fetch_ohlcv("EURUSD", "H1", n_bars=100)
    
    assert len(df) == 100, "Should fetch 100 bars"
    assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']), "Should have OHLCV columns"
    print("  ✓ Data Manager works correctly")

def test_features():
    """Test feature extraction"""
    print("Testing Feature Extraction...")
    from data.data_manager import DataManager
    from models.features import extract_candle_features, create_pattern_windows
    
    dm = DataManager()
    df = dm.fetch_ohlcv("EURUSD", "H1", n_bars=100)
    df_feat = extract_candle_features(df)
    
    assert 'body' in df_feat.columns, "Should extract body feature"
    assert 'rsi_14' in df_feat.columns, "Should calculate RSI"
    
    windows = create_pattern_windows(df_feat, window_size=20)
    assert len(windows) > 0, "Should create pattern windows"
    print("  ✓ Feature extraction works correctly")

def test_smc_engine():
    """Test SMC detection"""
    print("Testing SMC Engine...")
    from data.data_manager import DataManager
    from smc.smc_engine import SMCEngine
    
    dm = DataManager()
    df = dm.fetch_ohlcv("EURUSD", "H1", n_bars=200)
    
    smc = SMCEngine()
    analysis = smc.get_smc_analysis(df)
    
    assert 'order_blocks' in analysis, "Should detect order blocks"
    assert 'fair_value_gaps' in analysis, "Should detect FVGs"
    assert 'structure' in analysis, "Should analyze structure"
    print("  ✓ SMC Engine works correctly")

def test_pattern_recognition():
    """Test pattern recognition"""
    print("Testing Pattern Recognition...")
    from data.data_manager import DataManager
    from models.features import extract_candle_features, create_pattern_windows
    from models.pattern_recognition import PatternRecognitionEngine
    
    dm = DataManager()
    df = dm.fetch_ohlcv("EURUSD", "H1", n_bars=200)
    df_feat = extract_candle_features(df)
    windows = create_pattern_windows(df_feat, window_size=20)
    
    # Create outcomes
    outcomes = np.random.choice([-1, 0, 1], size=len(windows))
    
    engine = PatternRecognitionEngine()
    results = engine.train(windows[:50], outcomes[:50], n_clusters=10)
    
    assert engine.is_trained, "Model should be trained"
    assert results['n_clusters'] > 0, "Should create clusters"
    
    # Test prediction
    pred = engine.predict(windows[0])
    assert 'prediction' in pred, "Should make prediction"
    assert 'confidence' in pred, "Should have confidence"
    print("  ✓ Pattern Recognition works correctly")

def test_signal_generation():
    """Test signal generation"""
    print("Testing Signal Generation...")
    from models.signal_generator import SignalGenerator
    
    generator = SignalGenerator()
    
    # Create minimal mtf_data
    mtf_data = {
        'H4': {'features': {'rsi_14': 50, 'atr': 0.001}, 'smc': {}, 'structure': {'bos': []}},
        'H1': {'features': {'rsi_14': 50, 'atr': 0.001}, 'smc': {}, 'structure': {'bos': []}},
        'M15': {'features': {'rsi_14': 50, 'atr': 0.001}, 'smc': {}, 'structure': {'bos': []}}
    }
    
    pattern_pred = {'prediction': 1, 'confidence': 0.7}
    signal = generator.generate_signal("EURUSD", mtf_data, pattern_pred, 1.1000)
    
    assert signal.symbol == "EURUSD", "Should have symbol"
    assert signal.action in ['BUY', 'SELL', 'WAIT', 'IGNORE'], "Should have valid action"
    assert signal.entry_price > 0, "Should have entry price"
    print("  ✓ Signal Generation works correctly")

def test_risk_manager():
    """Test risk management"""
    print("Testing Risk Manager...")
    from risk.risk_manager import RiskManager
    
    rm = RiskManager()
    position_size, risk_data = rm.calculate_position_size(10000, 1.1000, 1.0950)
    
    assert position_size > 0, "Should calculate position size"
    assert risk_data['risk_pct'] <= 0.02, "Should respect risk limit"
    
    can_trade, reason = rm.can_trade("EURUSD", 10000)
    assert can_trade, "Should allow trading"
    print("  ✓ Risk Manager works correctly")

def test_backtest_engine():
    """Test backtesting"""
    print("Testing Backtest Engine...")
    from backtesting.backtest_engine import BacktestEngine
    
    engine = BacktestEngine()
    
    # Create sample signals
    signals = [
        {
            'symbol': 'EURUSD',
            'action': 'BUY',
            'entry_price': 1.1000,
            'stop_loss': 1.0950,
            'take_profit': 1.1100,
            'confidence': 0.7
        }
    ]
    
    df = pd.DataFrame({
        'Open': [1.1000],
        'High': [1.1100],
        'Low': [1.0950],
        'Close': [1.1050],
        'Volume': [1000]
    })
    
    results = engine.run_backtest(signals, df)
    
    assert 'metrics' in results, "Should have metrics"
    assert 'equity_curve' in results, "Should have equity curve"
    print("  ✓ Backtest Engine works correctly")

def test_trading_engine():
    """Test main trading engine"""
    print("Testing Trading Engine...")
    from engine import TradingEngine
    
    engine = TradingEngine()
    
    # Test analysis
    mtf_data = engine.analyze_symbol("EURUSD", ["H4", "H1", "M15"])
    assert 'H4' in mtf_data, "Should analyze H4"
    assert 'H1' in mtf_data, "Should analyze H1"
    assert 'M15' in mtf_data, "Should analyze M15"
    
    # Test model info
    info = engine.get_model_info()
    assert 'pattern_engine_trained' in info, "Should have model info"
    print("  ✓ Trading Engine works correctly")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_data_manager,
        test_features,
        test_smc_engine,
        test_pattern_recognition,
        test_signal_generation,
        test_risk_manager,
        test_backtest_engine,
        test_trading_engine,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {str(e)}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
