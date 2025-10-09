"""
Demo script - Train model and run analysis
"""
import sys
sys.path.append('backend')

from engine import TradingEngine
from config.settings import Settings

def main():
    print("=" * 60)
    print("Candle Pattern Self-Learning AI - Demo")
    print("=" * 60)
    print()
    
    # Initialize engine
    print("1. Initializing Trading Engine...")
    engine = TradingEngine()
    print("   ✓ Engine initialized")
    print()
    
    # Train model
    print("2. Training Pattern Recognition Model...")
    print("   (This may take 2-5 minutes)")
    results = engine.train_pattern_model(symbol="EURUSD", timeframe="H1", n_bars=2000)
    if results:
        print(f"   ✓ Model trained with {results['n_patterns']} patterns")
    print()
    
    # Analyze symbol
    print("3. Analyzing EURUSD...")
    mtf_data = engine.analyze_symbol("EURUSD", ["H4", "H1", "M15"])
    print("   ✓ Multi-timeframe analysis complete")
    print()
    
    # Generate signal
    print("4. Generating Trading Signal...")
    signal = engine.generate_signal("EURUSD")
    print(f"   Symbol: {signal.symbol}")
    print(f"   Action: {signal.action}")
    print(f"   Entry: {signal.entry_price:.5f}")
    print(f"   Stop Loss: {signal.stop_loss:.5f}")
    print(f"   Take Profit: {signal.take_profit:.5f}")
    print(f"   Risk:Reward: {signal.risk_reward:.2f}")
    print(f"   Confluence Score: {signal.confluence_score:.2%}")
    print(f"   Confidence: {signal.confidence:.2%}")
    print()
    
    # Scan opportunities
    print("5. Scanning Multiple Symbols...")
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    opportunities = engine.scan_opportunities(symbols)
    print(f"   ✓ Found {len(opportunities)} opportunities")
    for opp in opportunities:
        print(f"   - {opp.symbol}: {opp.action} @ {opp.entry_price:.5f} "
              f"(Confluence: {opp.confluence_score:.2%})")
    print()
    
    # Run backtest
    print("6. Running Backtest...")
    backtest_results = engine.run_backtest("EURUSD", "H1", n_bars=500)
    print("   ✓ Backtest complete")
    print()
    
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start the backend: python backend/api/server.py")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Open http://localhost:3000 in your browser")

if __name__ == "__main__":
    main()
