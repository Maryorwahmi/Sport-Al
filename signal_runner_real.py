#!/usr/bin/env python3
"""
Enhanced Continuous Signal Runner for SMC Forez using Real Multi-Timeframe Analysis
Generates high-quality signals using the actual SMC analyzer with professional market structure analysis
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

from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Settings, Timeframe
from smc_forez.signals.signal_generator import SignalType, SignalStrength

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_runner_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignalQualityFilter:
    """Enhanced signal quality filtering using real SMC analysis results"""
    
    def __init__(self, min_confidence: float = 0.65, min_rr_ratio: float = 1.8):
        self.min_confidence = min_confidence
        self.min_rr_ratio = min_rr_ratio
        self.signal_history = {}
    
    def evaluate_signal_quality(self, signal: Dict, analysis: Dict) -> float:
        """
        Evaluate signal quality based on real SMC analysis
        
        Args:
            signal: Signal dictionary from SMC analyzer
            analysis: Multi-timeframe analysis results
            
        Returns:
            Quality score (0-1, higher is better)
        """
        score = 0.0
        
        # Base signal strength (30% weight)
        signal_strength = signal.get('signal_strength', SignalStrength.WEAK)
        if signal_strength == SignalStrength.STRONG:
            score += 0.30
        elif signal_strength == SignalStrength.MODERATE:
            score += 0.20
        else:
            score += 0.10
        
        # Confluence factors (25% weight)
        confluence_score = signal.get('confluence_score', 0)
        score += min(0.25, confluence_score / 10 * 0.25)
        
        # Multi-timeframe alignment (25% weight)
        recommendation = analysis.get('recommendation', {})
        confidence = recommendation.get('confidence', 'LOW')
        if confidence == 'HIGH':
            score += 0.25
        elif confidence == 'MODERATE':
            score += 0.15
        else:
            score += 0.05
        
        # Risk-reward ratio (20% weight)
        rr_ratio = signal.get('risk_reward_ratio', 1.0)
        score += min(0.20, (rr_ratio / 3.0) * 0.20)
        
        return min(1.0, score)
    
    def filter_signals(self, signals_with_analysis: List[tuple], symbol: str) -> List[Dict]:
        """
        Filter signals based on quality and remove duplicates
        
        Args:
            signals_with_analysis: List of (signal, analysis) tuples
            symbol: Currency pair symbol
            
        Returns:
            List of high-quality signals
        """
        filtered_signals = []
        
        for signal, analysis in signals_with_analysis:
            if not signal.get('valid', False):
                continue
            
            # Calculate quality score
            quality_score = self.evaluate_signal_quality(signal, analysis)
            
            # Apply filters
            if (quality_score >= 0.5 and  # Minimum quality threshold
                signal.get('risk_reward_ratio', 0) >= self.min_rr_ratio):
                
                # Add quality metadata
                enhanced_signal = signal.copy()
                enhanced_signal.update({
                    'symbol': symbol,
                    'quality_score': round(quality_score, 3),
                    'analysis_timestamp': datetime.now(),
                    'timeframe_alignment': analysis.get('trend_alignment', {}),
                    'signal_confluence': analysis.get('signal_confluence', {}),
                    'recommendation_confidence': analysis.get('recommendation', {}).get('confidence', 'LOW')
                })
                
                filtered_signals.append(enhanced_signal)
        
        # Sort by quality score
        filtered_signals.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Limit to top signals per symbol
        return filtered_signals[:3]  # Max 3 signals per symbol


class EnhancedSignalRunner:
    """Enhanced signal runner using real SMC multi-timeframe analysis"""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the enhanced signal runner"""
        self.settings = settings or Settings()
        
        # Configure for real-time analysis
        self.settings.timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]
        
        # Initialize SMC analyzer
        self.analyzer = SMCAnalyzer(self.settings)
        
        # Initialize quality filter
        self.quality_filter = SignalQualityFilter(
            min_confidence=0.65,
            min_rr_ratio=1.8
        )
        
        # Currency pairs to analyze
        self.symbols = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURJPY', 'EURGBP', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
            'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
            'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
            'NZDJPY', 'NZDCHF', 'NZDCAD',
            'CADJPY', 'CADCHF', 'CHFJPY'
        ]
        
        self.is_running = False
        
    def connect_data_source(self) -> bool:
        """Connect to data source"""
        return self.analyzer.connect_data_source()
    
    def disconnect_data_source(self):
        """Disconnect from data source"""
        self.analyzer.disconnect_data_source()
    
    def scan_symbol_for_opportunities(self, symbol: str) -> List[tuple]:
        """
        Scan a single symbol for trading opportunities using real SMC analysis
        
        Args:
            symbol: Currency pair to analyze
            
        Returns:
            List of (signal, analysis) tuples
        """
        try:
            logger.debug(f"Analyzing {symbol} with multi-timeframe SMC analysis")
            
            # Perform real multi-timeframe analysis
            analysis = self.analyzer.analyze_multi_timeframe(symbol)
            
            if 'error' in analysis:
                logger.warning(f"Analysis error for {symbol}: {analysis['error']}")
                return []
            
            opportunities = []
            
            # Check if there's a valid trading recommendation
            recommendation = analysis.get('recommendation', {})
            if recommendation.get('action') and hasattr(recommendation['action'], 'value'):
                action = recommendation['action'].value
            else:
                action = 'wait'
            
            if action != 'wait' and recommendation.get('entry_details'):
                # Extract signal from the recommendation
                entry_details = recommendation['entry_details']
                
                signal = {
                    'signal_type': SignalType.BUY if action == 'buy' else SignalType.SELL,
                    'valid': True,
                    'entry_price': entry_details.get('entry_price', 0),
                    'stop_loss': entry_details.get('stop_loss', 0),
                    'take_profit': entry_details.get('take_profit', 0),
                    'risk_reward_ratio': entry_details.get('risk_reward_ratio', 1.0),
                    'signal_strength': getattr(SignalStrength, recommendation.get('strength', 'WEAK').upper(), SignalStrength.WEAK),
                    'confluence_score': len(recommendation.get('strength_factors', [])),
                    'confidence': recommendation.get('confidence', 'LOW'),
                    'timeframe': recommendation.get('entry_timeframe', Timeframe.H1).value if hasattr(recommendation.get('entry_timeframe', Timeframe.H1), 'value') else 'H1',
                    'timestamp': analysis.get('analysis_timestamp', datetime.now())
                }
                
                opportunities.append((signal, analysis))
                
                logger.info(f"✓ Real signal generated for {symbol}: {action.upper()} @ {entry_details.get('entry_price', 0):.5f}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return []
    
    def run_signal_cycle(self) -> List[Dict]:
        """
        Run a single signal generation cycle using real SMC analysis
        
        Returns:
            List of high-quality signals
        """
        logger.info("=" * 80)
        logger.info("STARTING ENHANCED SIGNAL GENERATION CYCLE")
        logger.info("=" * 80)
        logger.info(f"Scanning {len(self.symbols)} symbols with real SMC analysis...")
        
        all_signals = []
        processed_count = 0
        
        for symbol in self.symbols:
            try:
                # Get real trading opportunities
                opportunities = self.scan_symbol_for_opportunities(symbol)
                
                if opportunities:
                    # Filter for quality
                    quality_signals = self.quality_filter.filter_signals(opportunities, symbol)
                    all_signals.extend(quality_signals)
                    
                    for signal in quality_signals:
                        logger.info(f"✓ Quality signal for {symbol}: {signal['signal_type'].value.upper()} "
                                  f"@ {signal['entry_price']:.5f} (Quality: {signal['quality_score']:.2f})")
                
                processed_count += 1
                
                if processed_count % 5 == 0:
                    logger.info(f"Processed {processed_count}/{len(self.symbols)} symbols...")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"✓ {len(all_signals)} high-quality signals generated using real SMC analysis")
        return all_signals
    
    def save_signals(self, signals: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save signals to JSON file
        
        Args:
            signals: List of signals to save
            filename: Custom filename (optional)
            
        Returns:
            Filename of saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enhanced_signals_{timestamp}.json"
        
        # Create directory if it doesn't exist
        Path("live_signals").mkdir(exist_ok=True)
        filepath = Path("live_signals") / filename
        
        # Convert signals to JSON-serializable format
        serializable_signals = []
        for signal in signals:
            serializable_signal = {}
            for key, value in signal.items():
                if isinstance(value, (datetime, pd.Timestamp)):
                    serializable_signal[key] = value.isoformat()
                elif hasattr(value, 'value'):  # Enum
                    serializable_signal[key] = value.value
                elif hasattr(value, 'name'):  # Enum
                    serializable_signal[key] = value.name
                else:
                    serializable_signal[key] = value
                    
            serializable_signals.append(serializable_signal)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(serializable_signals, f, indent=2, default=str)
        
        logger.info(f"✓ Signals saved to: {filepath}")
        return str(filepath)
    
    def print_signal_summary(self, signals: List[Dict]):
        """Print a formatted summary of generated signals"""
        print("\n" + "="*80)
        print("ENHANCED SIGNAL GENERATION SUMMARY - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*80)
        
        if not signals:
            print("⚠️  No quality signals generated")
            return
        
        # Statistics
        buy_signals = [s for s in signals if s['signal_type'] == SignalType.BUY]
        sell_signals = [s for s in signals if s['signal_type'] == SignalType.SELL]
        
        avg_confidence = np.mean([s.get('quality_score', 0) for s in signals])
        avg_rr = np.mean([s.get('risk_reward_ratio', 0) for s in signals])
        
        print(f"📊 Signal Statistics:")
        print(f"   Total Signals: {len(signals)}")
        print(f"   Buy Signals: {len(buy_signals)}")
        print(f"   Sell Signals: {len(sell_signals)}")
        print(f"   Symbols with Signals: {len(set(s['symbol'] for s in signals))}")
        print(f"   Average Quality Score: {avg_confidence:.2f}")
        print(f"   Average R:R Ratio: {avg_rr:.2f}")
        
        # Top signals
        print(f"\n📋 Top Quality Signals:")
        print("Symbol   Type Entry      Quality R:R    Confidence")
        print("-" * 70)
        
        # Sort by quality score and show top 10
        top_signals = sorted(signals, key=lambda x: x.get('quality_score', 0), reverse=True)[:10]
        
        for signal in top_signals:
            symbol = signal['symbol'][:8]
            signal_type = signal['signal_type'].value.upper()[:4]
            entry_price = signal.get('entry_price', 0)
            quality = signal.get('quality_score', 0)
            rr = signal.get('risk_reward_ratio', 0)
            conf = signal.get('recommendation_confidence', 'LOW')[:3]
            
            print(f"{symbol:<8} {signal_type:<4} {entry_price:<10.5f} {quality:<7.2f} {rr:<6.2f} {conf}")
        
        if len(signals) > 10:
            print(f"... and {len(signals) - 10} more signals")
    
    def run_continuous(self, interval_minutes: int = 30):
        """
        Run continuous signal generation
        
        Args:
            interval_minutes: Minutes between signal generation cycles
        """
        logger.info("🚀 STARTING ENHANCED CONTINUOUS SIGNAL RUNNER")
        logger.info(f"Configuration: {len(self.symbols)} symbols, {interval_minutes}-minute intervals")
        logger.info(f"Symbols: {', '.join(self.symbols[:10])}{'...' if len(self.symbols) > 10 else ''}")
        
        self.is_running = True
        cycle_count = 0
        
        # Connect to data source
        if not self.connect_data_source():
            logger.error("Failed to connect to data source")
            return
        
        try:
            while self.is_running:
                cycle_count += 1
                logger.info(f"⏰ Starting cycle {cycle_count}")
                
                # Generate signals
                signals = self.run_signal_cycle()
                
                # Print summary
                self.print_signal_summary(signals)
                
                # Save signals
                if signals:
                    filename = self.save_signals(signals)
                    logger.info(f"💾 Saved {len(signals)} signals to {filename}")
                
                logger.info(f"✅ Cycle {cycle_count} completed")
                
                if self.is_running:
                    logger.info(f"⏱️  Waiting {interval_minutes} minutes until next cycle...")
                    time.sleep(interval_minutes * 60)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Enhanced signal runner stopped by user")
        finally:
            self.is_running = False
            self.disconnect_data_source()
            logger.info("📝 Enhanced signal runner finished")


def main():
    """Main function to run enhanced signal generation"""
    print("🚀 SMC FOREZ - ENHANCED CONTINUOUS SIGNAL RUNNER")
    print("="*80)
    
    # Initialize settings
    settings = Settings()
    
    # Create enhanced signal runner
    runner = EnhancedSignalRunner(settings)
    
    print(f"📋 ENHANCED CONFIGURATION")
    print("-" * 40)
    print(f"   Symbols: {len(runner.symbols)} currency pairs")
    print(f"   Analysis: Real SMC Multi-Timeframe")
    print(f"   Timeframes: {[tf.value for tf in settings.timeframes]}")
    print(f"   Quality Filtering: Advanced")
    print(f"   Min Quality Score: 0.50")
    print(f"   Min R:R Ratio: 1.8:1")
    print()
    
    try:
        # Option for single run or continuous
        mode = input("Run mode? (1) Single cycle, (2) Continuous: ").strip()
        
        if mode == "1":
            print("Running single enhanced signal generation cycle...")
            
            if runner.connect_data_source():
                signals = runner.run_signal_cycle()
                runner.print_signal_summary(signals)
                
                if signals:
                    filename = runner.save_signals(signals)
                    print(f"\n💾 Signals saved to: {filename}")
                
                runner.disconnect_data_source()
                print(f"\n✅ Single cycle completed - {len(signals)} quality signals generated")
            else:
                print("❌ Failed to connect to data source")
                
        else:
            print("Starting enhanced continuous signal generation...")
            print("Press Ctrl+C to stop")
            runner.run_continuous(interval_minutes=30)
    
    except KeyboardInterrupt:
        print("\n⏹️ Enhanced signal runner interrupted")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()