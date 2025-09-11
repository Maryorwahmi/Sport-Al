#!/usr/bin/env python3
"""
Simple test script to generate sample signals for testing the executor
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.signals.signal_generator import SignalType
from smc_forez.config.settings import Settings

def generate_test_signals():
    """Generate sample test signals"""
    settings = Settings()
    
    # Create some realistic test signals
    test_signals = []
    
    # Major pairs with different signal types
    signals_data = [
        {
            'symbol': 'EURUSD',
            'signal_type': 'BUY',
            'entry_price': 1.1050,
            'stop_loss': 1.1000,
            'take_profit': 1.1150,
            'confidence': 0.85,
        },
        {
            'symbol': 'GBPUSD',
            'signal_type': 'SELL',
            'entry_price': 1.2850,
            'stop_loss': 1.2900,
            'take_profit': 1.2750,
            'confidence': 0.80,
        },
        {
            'symbol': 'USDJPY',
            'signal_type': 'BUY',
            'entry_price': 149.50,
            'stop_loss': 148.80,
            'take_profit': 151.20,
            'confidence': 0.78,
        },
        {
            'symbol': 'AUDUSD',
            'signal_type': 'BUY',
            'entry_price': 0.6650,
            'stop_loss': 0.6600,
            'take_profit': 0.6750,
            'confidence': 0.75,
        },
        {
            'symbol': 'USDCAD',
            'signal_type': 'SELL',
            'entry_price': 1.3520,
            'stop_loss': 1.3570,
            'take_profit': 1.3420,
            'confidence': 0.82,
        }
    ]
    
    for signal_data in signals_data:
        # Calculate risk/reward ratio
        entry = signal_data['entry_price']
        stop_loss = signal_data['stop_loss']
        take_profit = signal_data['take_profit']
        
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        signal = {
            'timestamp': datetime.now().isoformat(),
            'symbol': signal_data['symbol'],
            'signal_type': signal_data['signal_type'],
            'entry_price': signal_data['entry_price'],
            'stop_loss': signal_data['stop_loss'],
            'take_profit': signal_data['take_profit'],
            'confidence': signal_data['confidence'],
            'risk_reward_ratio': rr_ratio,
            'volatility': 0.015,
            'market_analysis': {
                'trend': 'bullish' if signal_data['signal_type'] == 'BUY' else 'bearish',
                'trend_strength': 0.8,
                'volatility': 'normal'
            },
            'technical_score': signal_data['confidence'] * rr_ratio,
            'timeframe': 'H1',
            'valid': True,
            'quality_score': signal_data['confidence'] * 0.8
        }
        
        test_signals.append(signal)
    
    return test_signals

def save_test_signals(signals):
    """Save test signals to file"""
    signals_dir = Path("live_signals")
    signals_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"live_signals_{timestamp}.json"
    filepath = signals_dir / filename
    
    signal_data = {
        'timestamp': datetime.now().isoformat(),
        'total_signals': len(signals),
        'symbols_with_signals': list(set(s['symbol'] for s in signals)),
        'signals': signals
    }
    
    with open(filepath, 'w') as f:
        json.dump(signal_data, f, indent=2, default=str)
    
    print(f"✓ Test signals saved to: {filepath}")
    return str(filepath)

def main():
    print("🧪 GENERATING TEST SIGNALS FOR SMC FOREZ")
    print("="*50)
    
    # Generate test signals
    signals = generate_test_signals()
    
    print(f"📊 Generated {len(signals)} test signals:")
    for signal in signals:
        print(f"   {signal['symbol']} {signal['signal_type']} @ {signal['entry_price']:.5f} (R:R {signal['risk_reward_ratio']:.1f})")
    
    # Save signals
    filepath = save_test_signals(signals)
    
    print(f"\n✅ Test signals ready for execution!")
    print(f"💡 Use 'python mt5_executor.py' to execute these signals")

if __name__ == "__main__":
    main()