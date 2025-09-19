#!/usr/bin/env python3
"""
AI-SMC Engine Demonstration Script
Demonstrates the institutional-grade SMC analysis capabilities
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add AI-SMC to path
ai_smc_path = Path(__file__).parent / "AI-SMC"
sys.path.insert(0, str(ai_smc_path))

try:
    from analyzer import SMCAnalyzer
    from config.settings import Settings, create_settings
    from config.constants import QualityGrade
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure AI-SMC package is properly set up")
    sys.exit(1)

def generate_sample_data(symbol: str = "EURUSD", periods: int = 500) -> dict:
    """Generate sample OHLC data for testing"""
    print(f"📊 Generating sample data for {symbol}")
    
    # Base price
    base_price = 1.1000 if 'EUR' in symbol else 1.0000
    
    # Generate realistic price data
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='1H')
    
    data = {}
    
    for timeframe in ['H4', 'H1', 'M15']:
        # Adjust periods based on timeframe
        tf_periods = periods // (4 if timeframe == 'H4' else 1 if timeframe == 'H1' else periods * 4)
        tf_periods = max(100, min(tf_periods, 1000))  # Reasonable range
        
        # Generate price movement
        returns = np.random.normal(0, 0.001, tf_periods)  # Small returns
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create OHLC from prices
        ohlc_data = []
        for i in range(len(prices)):
            price = prices[i]
            volatility = np.random.uniform(0.0005, 0.002)
            
            high = price + volatility * np.random.uniform(0.3, 1.0)
            low = price - volatility * np.random.uniform(0.3, 1.0)
            open_price = price + np.random.uniform(-volatility/2, volatility/2)
            close = price + np.random.uniform(-volatility/2, volatility/2)
            volume = np.random.randint(1000, 10000)
            
            ohlc_data.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close,
                'Volume': volume
            })
        
        tf_dates = pd.date_range(end=datetime.now(), periods=tf_periods, 
                               freq='4H' if timeframe == 'H4' else '1H' if timeframe == 'H1' else '15T')
        
        data[timeframe] = pd.DataFrame(ohlc_data, index=tf_dates)
    
    return data

def demonstrate_smc_analysis():
    """Demonstrate comprehensive SMC analysis"""
    print("🎯 AI-SMC ENGINE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize settings
    print("\n1. Initializing AI-SMC Engine...")
    settings = create_settings(
        risk_level="moderate",
        trading_mode="signals_only",
        enable_api=False
    )
    
    # Create analyzer
    analyzer = SMCAnalyzer(settings)
    print("✅ AI-SMC Engine initialized successfully")
    
    # Test symbols
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    for symbol in symbols:
        print(f"\n2. Analyzing {symbol}...")
        print("-" * 40)
        
        # Generate sample data
        symbol_data = generate_sample_data(symbol)
        current_price = symbol_data['H1'].iloc[-1]['Close']
        
        print(f"📈 Current Price: {current_price:.5f}")
        print(f"📊 Data Points: H4={len(symbol_data['H4'])}, H1={len(symbol_data['H1'])}, M15={len(symbol_data['M15'])}")
        
        # Perform analysis
        try:
            analysis = analyzer.analyze_symbol(symbol, symbol_data, current_price)
            
            print("\n🔍 SMC ANALYSIS RESULTS:")
            print(f"   Symbol: {analysis['symbol']}")
            print(f"   Timestamp: {analysis['timestamp']}")
            print(f"   Current Price: {analysis['current_price']:.5f}")
            
            # Timeframe analysis
            timeframe_analysis = analysis.get('timeframe_analysis', {})
            print(f"\n📊 TIMEFRAME ANALYSIS:")
            for tf, tf_analysis in timeframe_analysis.items():
                print(f"   {tf} Timeframe:")
                print(f"     • Order Blocks: {len(tf_analysis.get('order_blocks', []))}")
                print(f"     • Fair Value Gaps: {len(tf_analysis.get('fair_value_gaps', []))}")
                print(f"     • Liquidity Zones: {len(tf_analysis.get('liquidity_zones', []))}")
                print(f"     • CHoCH Signals: {len(tf_analysis.get('choch_signals', []))}")
                print(f"     • MSS Signals: {len(tf_analysis.get('mss_signals', []))}")
            
            # SMC Confluence
            confluence = analysis.get('smc_confluence', {})
            print(f"\n🎯 SMC CONFLUENCE:")
            print(f"   Total Score: {confluence.get('total_score', 0):.2f}")
            print(f"   Bias: {confluence.get('bias', 'neutral').upper()}")
            print(f"   Strength: {confluence.get('strength', 'weak').upper()}")
            print(f"   Active Factors: {', '.join(confluence.get('active_factors', []))}")
            
            # Signals
            signals = analysis.get('signals', [])
            print(f"\n📡 GENERATED SIGNALS: {len(signals)}")
            for i, signal in enumerate(signals[:3]):  # Show first 3 signals
                quality_score = signal.get('quality_score', 0) * 100
                print(f"   Signal {i+1}:")
                print(f"     • Type: {signal.get('type', 'UNKNOWN')}")
                print(f"     • Entry: {signal.get('entry_price', 0):.5f}")
                print(f"     • Quality: {quality_score:.1f}%")
                print(f"     • Confluence: {signal.get('confluence_score', 0):.1f}")
            
            # Get market bias
            bias = analyzer.get_market_bias(symbol, symbol_data)
            print(f"\n📈 MARKET BIAS:")
            print(f"   Bias: {bias.get('bias', 'neutral').upper()}")
            print(f"   Strength: {bias.get('strength', 'weak').upper()}")
            print(f"   Confidence: {bias.get('confidence', 0):.1f}%")
            print(f"   Timeframe Agreement: {bias.get('timeframe_agreement', {}).get('agreement_percentage', 0):.1f}%")
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {str(e)}")
    
    print(f"\n3. Multi-Symbol Opportunity Analysis...")
    print("-" * 40)
    
    # Demonstrate opportunity scanning
    def sample_data_provider(symbol):
        return generate_sample_data(symbol, periods=300)
    
    try:
        opportunities = analyzer.get_trading_opportunities(symbols, sample_data_provider)
        
        print(f"🎯 FOUND {len(opportunities)} TRADING OPPORTUNITIES:")
        for i, opp in enumerate(opportunities[:5]):  # Show top 5
            signal = opp['signal']
            quality_grade = opp['quality_grade']
            
            print(f"\n   Opportunity #{i+1}:")
            print(f"     Symbol: {opp['symbol']}")
            print(f"     Quality Grade: {quality_grade.value}")
            print(f"     Quality Score: {signal.get('quality_score', 0)*100:.1f}%")
            print(f"     Type: {signal.get('type', 'UNKNOWN')}")
            print(f"     Confluence: {signal.get('confluence_score', 0):.1f}")
            
    except Exception as e:
        print(f"❌ Error scanning opportunities: {str(e)}")
    
    print(f"\n✅ AI-SMC ENGINE DEMONSTRATION COMPLETED")
    print("=" * 60)
    print(f"🎯 Key Features Demonstrated:")
    print(f"   • Institutional-grade SMC component detection")
    print(f"   • Multi-timeframe analysis (H4/H1/M15)")
    print(f"   • SMC confluence calculation")
    print(f"   • Market bias determination")
    print(f"   • Quality-based signal filtering")
    print(f"   • Multi-symbol opportunity scanning")
    print(f"\n💡 Next Steps:")
    print(f"   • Connect to live MT5 data feed")
    print(f"   • Implement 12-point quality filter")
    print(f"   • Add session-based timing optimization")
    print(f"   • Build real-time execution system")
    print(f"   • Deploy with API and monitoring")

def test_individual_components():
    """Test individual SMC components"""
    print("\n🧪 TESTING INDIVIDUAL SMC COMPONENTS")
    print("=" * 60)
    
    # Generate test data
    sample_data = generate_sample_data("EURUSD", periods=200)['H1']
    
    # Test Order Blocks
    print("\n1. Testing Order Block Detection...")
    try:
        from smc_components.order_blocks import OrderBlockDetector
        ob_detector = OrderBlockDetector()
        order_blocks = ob_detector.detect_order_blocks(sample_data, "EURUSD")
        print(f"✅ Found {len(order_blocks)} order blocks")
        
        for i, ob in enumerate(order_blocks[:3]):
            print(f"   OB #{i+1}: {ob.type.value} @ {ob.top:.5f}-{ob.bottom:.5f} ({ob.displacement_pips:.1f} pips)")
            
    except Exception as e:
        print(f"❌ Order Block test failed: {e}")
    
    # Test Fair Value Gaps
    print("\n2. Testing Fair Value Gap Detection...")
    try:
        from smc_components.fair_value_gaps import FairValueGapAnalyzer
        fvg_analyzer = FairValueGapAnalyzer()
        fvgs = fvg_analyzer.detect_fair_value_gaps(sample_data, "EURUSD")
        print(f"✅ Found {len(fvgs)} fair value gaps")
        
        for i, fvg in enumerate(fvgs[:3]):
            print(f"   FVG #{i+1}: {fvg.type.value} @ {fvg.top:.5f}-{fvg.bottom:.5f} ({fvg.size_pips:.1f} pips)")
            
    except Exception as e:
        print(f"❌ FVG test failed: {e}")
    
    # Test Liquidity Zones
    print("\n3. Testing Liquidity Zone Detection...")
    try:
        from smc_components.liquidity_zones import LiquidityZoneMapper
        lz_mapper = LiquidityZoneMapper()
        liquidity_zones = lz_mapper.detect_liquidity_zones(sample_data, "EURUSD")
        print(f"✅ Found {len(liquidity_zones)} liquidity zones")
        
        for i, lz in enumerate(liquidity_zones[:3]):
            print(f"   LZ #{i+1}: {lz.type.value} @ {lz.price_level:.5f} ({lz.touch_count} touches)")
            
    except Exception as e:
        print(f"❌ Liquidity Zone test failed: {e}")
    
    # Test CHoCH Detection
    print("\n4. Testing CHoCH Detection...")
    try:
        from smc_components.choch_detector import CHoCHDetector
        choch_detector = CHoCHDetector()
        choch_signals = choch_detector.detect_choch_signals(sample_data, "EURUSD")
        print(f"✅ Found {len(choch_signals)} CHoCH signals")
        
        for i, choch in enumerate(choch_signals[:3]):
            print(f"   CHoCH #{i+1}: {choch.type.value} @ {choch.break_level:.5f} ({choch.displacement_pips:.1f} pips)")
            
    except Exception as e:
        print(f"❌ CHoCH test failed: {e}")
    
    # Test MSS Detection
    print("\n5. Testing MSS Detection...")
    try:
        from smc_components.mss_detector import MSSDetector
        mss_detector = MSSDetector()
        mss_signals = mss_detector.detect_mss_signals(sample_data, "EURUSD")
        print(f"✅ Found {len(mss_signals)} MSS signals")
        
        for i, mss in enumerate(mss_signals[:3]):
            print(f"   MSS #{i+1}: {mss.type.value} @ {mss.break_level:.5f} ({mss.displacement_pips:.1f} pips)")
            
    except Exception as e:
        print(f"❌ MSS test failed: {e}")

if __name__ == "__main__":
    try:
        # Test individual components first
        test_individual_components()
        
        # Then demonstrate full system
        demonstrate_smc_analysis()
        
    except KeyboardInterrupt:
        print("\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()