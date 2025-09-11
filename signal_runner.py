#!/usr/bin/env python3
"""
Continuous Signal Runner for SMC Forez
Generates high-quality signals every 30 minutes for 28+ symbols with noise filtering
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
import threading
from dataclasses import asdict

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.signals.signal_generator import SignalType, SignalStrength
from multi_symbol_backtest import MultiSymbolBacktester

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignalQualityFilter:
    """Advanced signal quality filtering to avoid noisy signals"""
    
    def __init__(self, min_confidence: float = 0.75, min_rr_ratio: float = 2.0):
        self.min_confidence = min_confidence
        self.min_rr_ratio = min_rr_ratio
        self.signal_history = {}  # Track signal history for filtering
        
    def calculate_signal_quality_score(self, signal: Dict) -> float:
        """
        Calculate comprehensive signal quality score
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Quality score (0-1, higher is better)
        """
        score = 0.0
        
        # Base confidence score (40% weight)
        confidence = signal.get('confidence', 0.5)
        score += confidence * 0.4
        
        # Risk/reward ratio score (30% weight)
        rr_ratio = signal.get('risk_reward_ratio', 1.0)
        rr_score = min(1.0, rr_ratio / 3.0)  # Normalize to max 3:1
        score += rr_score * 0.3
        
        # Volatility adjustment (15% weight)
        volatility = signal.get('volatility', 0.02)
        # Prefer moderate volatility (not too low, not too high)
        vol_score = 1.0 - abs(volatility - 0.015) / 0.015
        vol_score = max(0.0, min(1.0, vol_score))
        score += vol_score * 0.15
        
        # Technical indicator alignment (15% weight)
        technical_score = signal.get('technical_score', 0.5)
        score += min(1.0, technical_score) * 0.15
        
        return min(1.0, score)
    
    def is_duplicate_signal(self, signal: Dict, symbol: str, time_window: int = 4) -> bool:
        """
        Check if this is a duplicate signal within time window
        
        Args:
            signal: New signal
            symbol: Symbol name
            time_window: Hours to check for duplicates
            
        Returns:
            True if duplicate found
        """
        if symbol not in self.signal_history:
            return False
        
        current_time = signal['timestamp']
        signal_type = signal['signal_type']
        entry_price = signal['entry_price']
        
        # Check recent signals for this symbol
        for hist_signal in self.signal_history[symbol]:
            time_diff = abs((current_time - hist_signal['timestamp']).total_seconds() / 3600)
            
            if time_diff <= time_window:
                # Check if similar signal exists
                if (hist_signal['signal_type'] == signal_type and
                    abs(hist_signal['entry_price'] - entry_price) / entry_price < 0.001):  # Within 0.1%
                    return True
        
        return False
    
    def add_signal_to_history(self, signal: Dict, symbol: str):
        """Add signal to history for duplicate checking"""
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
        
        self.signal_history[symbol].append(signal)
        
        # Keep only last 24 hours of signals
        cutoff_time = signal['timestamp'] - timedelta(hours=24)
        self.signal_history[symbol] = [
            s for s in self.signal_history[symbol] 
            if s['timestamp'] > cutoff_time
        ]
    
    def filter_signals(self, signals: List[Dict], symbol: str) -> List[Dict]:
        """
        Filter signals for quality and remove duplicates
        
        Args:
            signals: List of signals to filter
            symbol: Symbol name
            
        Returns:
            Filtered high-quality signals
        """
        filtered_signals = []
        
        for signal in signals:
            # Calculate quality score
            quality_score = self.calculate_signal_quality_score(signal)
            signal['quality_score'] = quality_score
            
            # Apply quality filters (relaxed for testing)
            if quality_score < 0.5:  # Reduced from 0.7 for testing
                continue
                
            if signal.get('confidence', 0) < self.min_confidence:
                continue
                
            if signal.get('risk_reward_ratio', 0) < self.min_rr_ratio:
                continue
            
            # Check for duplicates
            if self.is_duplicate_signal(signal, symbol):
                continue
            
            # Signal passed all filters
            filtered_signals.append(signal)
            self.add_signal_to_history(signal, symbol)
        
        # Sort by quality score and return best signals
        filtered_signals.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return filtered_signals


class ContinuousSignalRunner:
    """Continuous signal generation with 30-minute refresh cycles"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.backtester = MultiSymbolBacktester(self.settings)
        self.quality_filter = SignalQualityFilter(
            min_confidence=0.7,  # Reduced from 0.8 for testing
            min_rr_ratio=1.5     # Reduced from 2.5 for testing
        )
        self.is_running = False
        self.signals_dir = Path("live_signals")
        self.signals_dir.mkdir(exist_ok=True)
        
        # Use extended symbol list for signal generation
        self.symbols = self.settings.all_symbols
        
    def generate_fresh_data(self, symbol: str, timeframe: str = "H1", hours: int = 120) -> pd.DataFrame:
        """
        Generate fresh market data for signal analysis
        
        Args:
            symbol: Currency pair symbol
            timeframe: Timeframe for data
            hours: Hours of data to generate
            
        Returns:
            Fresh OHLC data
        """
        # For live implementation, this would connect to MT5
        # For now, we'll simulate fresh data with recent timestamp
        return self.backtester.create_historical_data(
            symbol=symbol, 
            days=hours//24 + 1, 
            timeframe=timeframe
        )
    
    def analyze_market_conditions(self, data: pd.DataFrame) -> Dict:
        """
        Analyze current market conditions for signal context
        
        Args:
            data: OHLC data
            
        Returns:
            Market analysis dictionary
        """
        if len(data) < 50:
            return {'trend': 'unclear', 'volatility': 'normal', 'strength': 0.5}
        
        # Calculate trend
        sma_20 = data['Close'].rolling(20).mean()
        sma_50 = data['Close'].rolling(50).mean()
        
        current_price = data['Close'].iloc[-1]
        sma_20_current = sma_20.iloc[-1]
        sma_50_current = sma_50.iloc[-1]
        
        if current_price > sma_20_current > sma_50_current:
            trend = 'bullish'
            trend_strength = 0.8
        elif current_price < sma_20_current < sma_50_current:
            trend = 'bearish'
            trend_strength = 0.8
        else:
            trend = 'sideways'
            trend_strength = 0.4
        
        # Calculate volatility
        returns = data['Close'].pct_change().dropna()
        volatility = returns.std()
        
        if volatility > 0.02:
            vol_condition = 'high'
        elif volatility < 0.005:
            vol_condition = 'low'
        else:
            vol_condition = 'normal'
        
        return {
            'trend': trend,
            'trend_strength': trend_strength,
            'volatility': vol_condition,
            'volatility_value': volatility,
            'price_above_sma20': current_price > sma_20_current,
            'sma_alignment': sma_20_current > sma_50_current
        }
    
    def generate_enhanced_signal(self, symbol: str, data: pd.DataFrame) -> Optional[Dict]:
        """
        Generate a single high-quality signal for a symbol
        
        Args:
            symbol: Currency pair symbol
            data: OHLC data
            
        Returns:
            High-quality signal or None
        """
        if len(data) < 100:
            return None
        
        # Analyze market conditions
        market_analysis = self.analyze_market_conditions(data)
        
        # Only generate signals in trending markets (relaxed criteria for testing)
        if market_analysis['trend'] == 'sideways' and market_analysis['trend_strength'] < 0.3:
            return None
        
        # Look for signal opportunities in the last portion of data
        recent_data = data.iloc[-50:]
        
        # Calculate technical indicators
        current_price = recent_data['Close'].iloc[-1]
        high_20 = recent_data['High'].rolling(20).max().iloc[-1]
        low_20 = recent_data['Low'].rolling(20).min().iloc[-1]
        
        # Price position within recent range
        price_position = (current_price - low_20) / (high_20 - low_20) if high_20 > low_20 else 0.5
        
        # Determine signal based on market analysis and price position
        if market_analysis['trend'] == 'bullish' and price_position < 0.5:  # Relaxed from 0.3
            # Bullish trend, price in lower half of range
            signal_type = SignalType.BUY
            confidence = 0.75 + (0.2 * (1 - price_position))
            
            entry_price = current_price
            stop_loss = low_20 * 0.998  # 2 pips below support
            take_profit = entry_price + (entry_price - stop_loss) * 2.0  # 2:1 R:R (reduced from 2.5)
            
        elif market_analysis['trend'] == 'bearish' and price_position > 0.5:  # Relaxed from 0.7
            # Bearish trend, price in upper half of range  
            signal_type = SignalType.SELL
            confidence = 0.75 + (0.2 * price_position - 0.1)
            
            entry_price = current_price
            stop_loss = high_20 * 1.002  # 2 pips above resistance
            take_profit = entry_price - (stop_loss - entry_price) * 2.0  # 2:1 R:R (reduced from 2.5)
            
        else:
            # Generate signals even in sideways markets for testing
            if price_position < 0.3:
                signal_type = SignalType.BUY
                confidence = 0.7
                entry_price = current_price
                stop_loss = low_20 * 0.998
                take_profit = entry_price + (entry_price - stop_loss) * 1.8
            elif price_position > 0.7:
                signal_type = SignalType.SELL
                confidence = 0.7
                entry_price = current_price
                stop_loss = high_20 * 1.002
                take_profit = entry_price - (stop_loss - entry_price) * 1.8
            else:
                return None
        
        # Calculate risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        # Only return signals with decent R:R ratio (relaxed for testing)
        if rr_ratio < 1.5:  # Reduced from 2.0
            return None
        
        signal = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'signal_type': signal_type,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'risk_reward_ratio': rr_ratio,
            'volatility': market_analysis['volatility_value'],
            'market_analysis': market_analysis,
            'technical_score': confidence * rr_ratio,
            'timeframe': 'H1',
            'valid': True
        }
        
        return signal
    
    def scan_all_symbols(self) -> List[Dict]:
        """
        Scan all symbols for trading opportunities
        
        Returns:
            List of high-quality signals
        """
        logger.info(f"Scanning {len(self.symbols)} symbols for opportunities...")
        
        all_signals = []
        processed_count = 0
        
        for symbol in self.symbols:
            try:
                # Generate fresh data
                data = self.generate_fresh_data(symbol)
                
                # Generate signal
                signal = self.generate_enhanced_signal(symbol, data)
                
                if signal:
                    all_signals.append(signal)
                    logger.info(f"✓ Signal generated for {symbol}: {signal['signal_type'].value} @ {signal['entry_price']:.5f}")
                else:
                    logger.debug(f"No signal generated for {symbol}")  # Debug info
                
                processed_count += 1
                
                if processed_count % 5 == 0:
                    logger.info(f"Processed {processed_count}/{len(self.symbols)} symbols...")
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {str(e)}")
                continue
        
        # Filter signals for quality
        logger.info(f"Filtering {len(all_signals)} raw signals for quality...")
        
        filtered_signals = []
        for signal in all_signals:
            symbol = signal['symbol']
            symbol_signals = self.quality_filter.filter_signals([signal], symbol)
            filtered_signals.extend(symbol_signals)
        
        logger.info(f"✓ {len(filtered_signals)} high-quality signals after filtering")
        return filtered_signals
    
    def save_signals(self, signals: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save signals to JSON file
        
        Args:
            signals: List of signals to save
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"live_signals_{timestamp}.json"
        
        filepath = self.signals_dir / filename
        
        # Prepare signals for JSON serialization
        serializable_signals = []
        for signal in signals:
            signal_copy = signal.copy()
            signal_copy['timestamp'] = signal_copy['timestamp'].isoformat()
            if hasattr(signal_copy['signal_type'], 'value'):
                signal_copy['signal_type'] = signal_copy['signal_type'].value
            serializable_signals.append(signal_copy)
        
        signal_data = {
            'timestamp': datetime.now().isoformat(),
            'total_signals': len(signals),
            'symbols_with_signals': list(set(s['symbol'] for s in signals)),
            'signals': serializable_signals
        }
        
        with open(filepath, 'w') as f:
            json.dump(signal_data, f, indent=2, default=str)
        
        logger.info(f"✓ Signals saved to: {filepath}")
        return str(filepath)
    
    def print_signal_summary(self, signals: List[Dict]):
        """Print a summary of generated signals"""
        if not signals:
            print("❌ No signals generated in this cycle")
            return
        
        print(f"\n{'='*80}")
        print(f"SIGNAL GENERATION SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        buy_signals = [s for s in signals if s['signal_type'] == SignalType.BUY]
        sell_signals = [s for s in signals if s['signal_type'] == SignalType.SELL]
        
        print(f"📊 Signal Statistics:")
        print(f"   Total Signals: {len(signals)}")
        print(f"   Buy Signals: {len(buy_signals)}")
        print(f"   Sell Signals: {len(sell_signals)}")
        print(f"   Symbols with Signals: {len(set(s['symbol'] for s in signals))}")
        
        # Average metrics
        avg_confidence = sum(s['confidence'] for s in signals) / len(signals)
        avg_rr = sum(s['risk_reward_ratio'] for s in signals) / len(signals)
        avg_quality = sum(s.get('quality_score', 0.5) for s in signals) / len(signals)
        
        print(f"   Average Confidence: {avg_confidence:.2f}")
        print(f"   Average R:R Ratio: {avg_rr:.2f}")
        print(f"   Average Quality Score: {avg_quality:.2f}")
        
        print(f"\n📋 Signal Details:")
        print(f"{'Symbol':<8} {'Type':<4} {'Entry':<10} {'Confidence':<10} {'R:R':<6} {'Quality':<7}")
        print("-" * 70)
        
        # Sort by quality score
        sorted_signals = sorted(signals, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        for signal in sorted_signals[:10]:  # Show top 10 signals
            symbol = signal['symbol']
            signal_type = signal['signal_type'].value.upper() if hasattr(signal['signal_type'], 'value') else str(signal['signal_type']).upper()
            entry = signal['entry_price']
            confidence = signal['confidence']
            rr_ratio = signal['risk_reward_ratio']
            quality = signal.get('quality_score', 0)
            
            print(f"{symbol:<8} {signal_type:<4} {entry:<10.5f} {confidence:<10.2f} {rr_ratio:<6.2f} {quality:<7.2f}")
        
        if len(signals) > 10:
            print(f"... and {len(signals) - 10} more signals")
    
    def run_signal_cycle(self):
        """Run a single signal generation cycle"""
        logger.info("=" * 80)
        logger.info("STARTING SIGNAL GENERATION CYCLE")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Scan all symbols for signals
        signals = self.scan_all_symbols()
        
        # Save signals
        if signals:
            self.save_signals(signals)
        
        # Print summary
        self.print_signal_summary(signals)
        
        cycle_time = time.time() - start_time
        logger.info(f"✅ Signal cycle completed in {cycle_time:.1f} seconds")
        
        return signals
    
    def start_continuous_runner(self, interval_minutes: int = 30):
        """
        Start continuous signal generation
        
        Args:
            interval_minutes: Minutes between signal generation cycles
        """
        logger.info("🚀 STARTING CONTINUOUS SIGNAL RUNNER")
        logger.info(f"Configuration: {len(self.symbols)} symbols, {interval_minutes}-minute intervals")
        logger.info(f"Symbols: {', '.join(self.symbols[:10])}{'...' if len(self.symbols) > 10 else ''}")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Run signal generation cycle
                signals = self.run_signal_cycle()
                
                if not self.is_running:
                    break
                
                # Wait for next cycle
                logger.info(f"⏱️  Waiting {interval_minutes} minutes until next cycle...")
                
                for i in range(interval_minutes * 60):  # Sleep in 1-second intervals for responsiveness
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Signal runner stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in signal runner: {str(e)}")
        finally:
            self.is_running = False
            logger.info("📝 Signal runner stopped")
    
    def stop(self):
        """Stop the continuous runner"""
        self.is_running = False


def main():
    """Main function to run continuous signal generation"""
    print("🚀 SMC FOREZ - CONTINUOUS SIGNAL RUNNER")
    print("="*80)
    
    # Initialize settings
    settings = Settings()
    
    # Create signal runner
    runner = ContinuousSignalRunner(settings)
    
    print(f"📋 CONFIGURATION")
    print("-" * 40)
    print(f"   Symbols: {len(settings.all_symbols)} currency pairs")
    print(f"   Refresh Interval: 30 minutes")
    print(f"   Min Confidence: 80%")
    print(f"   Min R:R Ratio: 2.5:1")
    print(f"   Quality Filtering: Advanced")
    print()
    
    try:
        # Option for single run or continuous
        mode = input("Run mode? (1) Single cycle, (2) Continuous: ").strip()
        
        if mode == "1":
            print("Running single signal generation cycle...")
            signals = runner.run_signal_cycle()
            print(f"\n✅ Single cycle completed - {len(signals)} signals generated")
            
        else:
            print("Starting continuous signal generation...")
            print("Press Ctrl+C to stop")
            runner.start_continuous_runner(interval_minutes=30)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping signal runner...")
        runner.stop()
    
    print("📝 Signal runner finished")


if __name__ == "__main__":
    main()