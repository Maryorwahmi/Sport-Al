"""
Multi-timeframe analysis coordinator that aligns signals across different timeframes
for stronger confirmation and higher probability trades
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from ..config.settings import Timeframe
from ..market_structure.structure_analyzer import MarketStructureAnalyzer, TrendDirection
from ..smart_money.smc_analyzer import SmartMoneyAnalyzer
from ..signals.signal_generator import SignalGenerator, SignalType, SignalStrength


logger = logging.getLogger(__name__)


class MultiTimeframeAnalyzer:
    """Coordinates analysis across multiple timeframes for signal confirmation"""
    
    def __init__(self, timeframes: List[Timeframe], settings: Dict):
        """
        Initialize multi-timeframe analyzer
        
        Args:
            timeframes: List of timeframes to analyze (ordered from highest to lowest)
            settings: Analysis settings dictionary
        """
        self.timeframes = sorted(timeframes, key=self._timeframe_priority, reverse=True)
        self.settings = settings
        
        # Initialize analyzers
        self.structure_analyzer = MarketStructureAnalyzer(
            swing_length=settings.get('swing_length', 10)
        )
        self.smc_analyzer = SmartMoneyAnalyzer(
            fvg_min_size=settings.get('fvg_min_size', 5.0),
            order_block_lookback=settings.get('order_block_lookback', 20),
            liquidity_threshold=settings.get('liquidity_threshold', 0.1)
        )
        self.signal_generator = SignalGenerator(
            min_confluence_factors=settings.get('min_confluence_factors', 2),
            min_rr_ratio=settings.get('min_rr_ratio', 1.5)
        )
        
    def _timeframe_priority(self, timeframe: Timeframe) -> int:
        """
        Get timeframe priority for sorting (higher timeframes have higher priority)
        
        Args:
            timeframe: Timeframe enum
            
        Returns:
            Integer priority value
        """
        priority_map = {
            Timeframe.D1: 6,
            Timeframe.H4: 5,
            Timeframe.H1: 4,
            Timeframe.M15: 3,
            Timeframe.M5: 2,
            Timeframe.M1: 1
        }
        return priority_map.get(timeframe, 0)
    
    def analyze_timeframe(self, data: pd.DataFrame, timeframe: Timeframe) -> Dict:
        """
        Analyze a single timeframe
        
        Args:
            data: OHLC data for the timeframe
            timeframe: Timeframe being analyzed
            
        Returns:
            Dictionary with complete analysis for the timeframe
        """
        try:
            logger.info(f"Analyzing timeframe: {timeframe.value}")
            
            # Market structure analysis
            market_structure = self.structure_analyzer.get_market_structure_levels(data)
            
            # Smart Money Concepts analysis
            smc_analysis = self.smc_analyzer.get_smart_money_analysis(data)
            
            # Generate signal for this timeframe
            current_price = data['Close'].iloc[-1]
            signal = self.signal_generator.generate_signal(
                market_structure, smc_analysis, current_price
            )
            
            return {
                'timeframe': timeframe,
                'market_structure': market_structure,
                'smc_analysis': smc_analysis,
                'signal': signal,
                'current_price': current_price,
                'analysis_timestamp': data.index[-1]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing timeframe {timeframe.value}: {str(e)}")
            return {
                'timeframe': timeframe,
                'error': str(e)
            }
    
    def get_trend_alignment(self, timeframe_analyses: Dict) -> Dict:
        """
        Check trend alignment across timeframes
        
        Args:
            timeframe_analyses: Dictionary of analyses for each timeframe
            
        Returns:
            Dictionary with trend alignment information
        """
        try:
            trends = {}
            trend_scores = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            
            for tf, analysis in timeframe_analyses.items():
                if 'market_structure' in analysis:
                    trend = analysis['market_structure'].get('trend_direction', TrendDirection.CONSOLIDATION)
                    trends[tf] = trend
                    
                    # Weight higher timeframes more heavily
                    weight = self._timeframe_priority(tf)
                    
                    if trend == TrendDirection.UPTREND:
                        trend_scores['bullish'] += weight
                    elif trend == TrendDirection.DOWNTREND:
                        trend_scores['bearish'] += weight
                    else:
                        trend_scores['neutral'] += weight
            
            # Determine overall trend alignment
            max_score = max(trend_scores.values())
            if trend_scores['bullish'] == max_score and max_score > 0:
                overall_trend = TrendDirection.UPTREND
            elif trend_scores['bearish'] == max_score and max_score > 0:
                overall_trend = TrendDirection.DOWNTREND
            else:
                overall_trend = TrendDirection.CONSOLIDATION
            
            # Calculate alignment strength (0-1)
            total_score = sum(trend_scores.values())
            alignment_strength = max_score / total_score if total_score > 0 else 0
            
            return {
                'individual_trends': trends,
                'trend_scores': trend_scores,
                'overall_trend': overall_trend,
                'alignment_strength': alignment_strength,
                'is_aligned': alignment_strength >= 0.6  # 60% threshold
            }
            
        except Exception as e:
            logger.error(f"Error checking trend alignment: {str(e)}")
            return {'overall_trend': TrendDirection.CONSOLIDATION, 'is_aligned': False}
    
    def get_signal_confluence(self, timeframe_analyses: Dict) -> Dict:
        """
        Check signal confluence across timeframes
        
        Args:
            timeframe_analyses: Dictionary of analyses for each timeframe
            
        Returns:
            Dictionary with signal confluence information
        """
        try:
            signals = {}
            signal_scores = {'buy': 0, 'sell': 0, 'wait': 0}
            
            for tf, analysis in timeframe_analyses.items():
                if 'signal' in analysis:
                    signal = analysis['signal']
                    signal_type = signal.get('signal_type', SignalType.WAIT)
                    signal_strength = signal.get('signal_strength', SignalStrength.WEAK)
                    
                    signals[tf] = {
                        'type': signal_type,
                        'strength': signal_strength,
                        'confluence_score': signal.get('confluence_score', 0)
                    }
                    
                    # Weight signals by timeframe priority and signal strength
                    tf_weight = self._timeframe_priority(tf)
                    strength_multiplier = signal_strength.value if hasattr(signal_strength, 'value') else 1
                    weight = tf_weight * strength_multiplier
                    
                    if signal_type == SignalType.BUY:
                        signal_scores['buy'] += weight
                    elif signal_type == SignalType.SELL:
                        signal_scores['sell'] += weight
                    else:
                        signal_scores['wait'] += weight
            
            # Determine overall signal
            max_score = max(signal_scores.values())
            if signal_scores['buy'] == max_score and max_score > 0:
                overall_signal = SignalType.BUY
            elif signal_scores['sell'] == max_score and max_score > 0:
                overall_signal = SignalType.SELL
            else:
                overall_signal = SignalType.WAIT
            
            # Calculate confluence strength
            total_score = sum(signal_scores.values())
            confluence_strength = max_score / total_score if total_score > 0 else 0
            
            return {
                'individual_signals': signals,
                'signal_scores': signal_scores,
                'overall_signal': overall_signal,
                'confluence_strength': confluence_strength,
                'has_confluence': confluence_strength >= 0.7  # 70% threshold
            }
            
        except Exception as e:
            logger.error(f"Error checking signal confluence: {str(e)}")
            return {'overall_signal': SignalType.WAIT, 'has_confluence': False}
    
    def get_entry_timeframe(self, timeframe_analyses: Dict, overall_signal: SignalType) -> Optional[Timeframe]:
        """
        Determine the best timeframe for entry based on signal quality
        
        Args:
            timeframe_analyses: Dictionary of analyses for each timeframe
            overall_signal: Overall signal direction
            
        Returns:
            Best timeframe for entry or None
        """
        try:
            if overall_signal == SignalType.WAIT:
                return None
            
            # Find timeframes with matching signals
            matching_timeframes = []
            
            for tf, analysis in timeframe_analyses.items():
                if 'signal' in analysis:
                    signal = analysis['signal']
                    if signal.get('signal_type') == overall_signal and signal.get('valid', False):
                        matching_timeframes.append({
                            'timeframe': tf,
                            'signal_strength': signal.get('signal_strength', SignalStrength.WEAK),
                            'confluence_score': signal.get('confluence_score', 0),
                            'rr_ratio': signal.get('risk_reward_ratio', 0)
                        })
            
            if not matching_timeframes:
                return None
            
            # Sort by signal quality (confluence score and R:R ratio)
            matching_timeframes.sort(
                key=lambda x: (x['confluence_score'], x['rr_ratio']),
                reverse=True
            )
            
            # Prefer lower timeframes for entries (better precision)
            # But ensure good signal quality
            best_entry = None
            for tf_info in matching_timeframes:
                if tf_info['confluence_score'] >= 3:  # Minimum confluence threshold
                    if best_entry is None:
                        best_entry = tf_info['timeframe']
                    elif self._timeframe_priority(tf_info['timeframe']) < self._timeframe_priority(best_entry):
                        best_entry = tf_info['timeframe']
            
            return best_entry or matching_timeframes[0]['timeframe']
            
        except Exception as e:
            logger.error(f"Error determining entry timeframe: {str(e)}")
            return None
    
    def analyze_multiple_timeframes(self, data_dict: Dict[Timeframe, pd.DataFrame]) -> Dict:
        """
        Perform comprehensive multi-timeframe analysis
        
        Args:
            data_dict: Dictionary mapping timeframes to their OHLC data
            
        Returns:
            Dictionary with complete multi-timeframe analysis
        """
        try:
            logger.info("Starting multi-timeframe analysis")
            
            # Analyze each timeframe
            timeframe_analyses = {}
            for timeframe in self.timeframes:
                if timeframe in data_dict:
                    analysis = self.analyze_timeframe(data_dict[timeframe], timeframe)
                    timeframe_analyses[timeframe] = analysis
            
            # Check trend alignment
            trend_alignment = self.get_trend_alignment(timeframe_analyses)
            
            # Check signal confluence
            signal_confluence = self.get_signal_confluence(timeframe_analyses)
            
            # Determine best entry timeframe
            entry_timeframe = self.get_entry_timeframe(
                timeframe_analyses, 
                signal_confluence['overall_signal']
            )
            
            # Generate final recommendation
            recommendation = self._generate_recommendation(
                trend_alignment, signal_confluence, entry_timeframe, timeframe_analyses
            )
            
            return {
                'timeframe_analyses': timeframe_analyses,
                'trend_alignment': trend_alignment,
                'signal_confluence': signal_confluence,
                'entry_timeframe': entry_timeframe,
                'recommendation': recommendation,
                'analysis_timestamp': pd.Timestamp.now()
            }
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {str(e)}")
            return {'error': str(e)}
    
    def _generate_recommendation(self, trend_alignment: Dict, signal_confluence: Dict,
                               entry_timeframe: Optional[Timeframe], 
                               timeframe_analyses: Dict) -> Dict:
        """
        Generate final trading recommendation based on multi-timeframe analysis
        
        Args:
            trend_alignment: Trend alignment analysis
            signal_confluence: Signal confluence analysis
            entry_timeframe: Recommended entry timeframe
            timeframe_analyses: Individual timeframe analyses
            
        Returns:
            Dictionary with trading recommendation
        """
        try:
            overall_signal = signal_confluence.get('overall_signal', SignalType.WAIT)
            overall_trend = trend_alignment.get('overall_trend', TrendDirection.CONSOLIDATION)
            
            # Determine recommendation strength
            strength_factors = []
            
            if trend_alignment.get('is_aligned', False):
                strength_factors.append("Trend alignment across timeframes")
            
            if signal_confluence.get('has_confluence', False):
                strength_factors.append("Signal confluence detected")
            
            if entry_timeframe is not None:
                strength_factors.append(f"Clear entry setup on {entry_timeframe.value}")
            
            # Get entry details from the recommended timeframe
            entry_details = {}
            if entry_timeframe and entry_timeframe in timeframe_analyses:
                entry_signal = timeframe_analyses[entry_timeframe].get('signal', {})
                entry_details = {
                    'entry_price': entry_signal.get('entry_price'),
                    'stop_loss': entry_signal.get('stop_loss'),
                    'take_profit': entry_signal.get('take_profit'),
                    'risk_reward_ratio': entry_signal.get('risk_reward_ratio'),
                    'confluence_factors': entry_signal.get('confluence_factors', [])
                }
            
            recommendation = {
                'action': overall_signal,
                'trend_direction': overall_trend,
                'strength_score': len(strength_factors),
                'strength_factors': strength_factors,
                'entry_timeframe': entry_timeframe,
                'entry_details': entry_details,
                'confidence': 'HIGH' if len(strength_factors) >= 2 else 'MODERATE' if len(strength_factors) == 1 else 'LOW'
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return {'action': SignalType.WAIT, 'confidence': 'LOW'}