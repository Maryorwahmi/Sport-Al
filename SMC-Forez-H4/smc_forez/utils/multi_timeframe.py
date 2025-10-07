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
            min_confluence_score=settings.get('min_confluence_score', 7),  # Increased for quality
            min_rr_ratio=settings.get('min_rr_ratio', 2.0)  # Increased for quality
        )
        
    def _timeframe_priority(self, timeframe: Timeframe) -> int:
        """Return priority order for timeframes (higher number = higher priority/timeframe)"""
        priority_map = {
            Timeframe.M1: 1,
            Timeframe.M5: 2,
            Timeframe.M15: 3,
            Timeframe.H1: 4, 
            Timeframe.H4: 5,
            Timeframe.D1: 6,
            Timeframe.W1: 7
        }
        return priority_map.get(timeframe, 0)
        
    def _get_timeframe_weight(self, timeframe: Timeframe) -> float:
        """
        Get weighted percentage for timeframe importance in trend aggregation
        H4 = 50%, H1 = 30%, M15 = 20% as suggested for proper bias hierarchy
        
        Args:
            timeframe: Timeframe enum
            
        Returns:
            Float weight (0.0 to 1.0)
        """
        weight_map = {
            Timeframe.D1: 0.6,   # Daily gets highest weight
            Timeframe.H4: 0.5,   # H4 gets 50% weight
            Timeframe.H1: 0.3,   # H1 gets 30% weight  
            Timeframe.M15: 0.2,  # M15 gets 20% weight
            Timeframe.M5: 0.1,
            Timeframe.M1: 0.05
        }
        return weight_map.get(timeframe, 0.0)
    
    def analyze_timeframe(self, data: pd.DataFrame, timeframe: Timeframe, market_bias: Optional[str] = None) -> Dict:
        """
        Analyze a single timeframe
        
        Args:
            data: OHLC data for the timeframe
            timeframe: Timeframe being analyzed
            market_bias: Pre-calculated market bias from higher timeframe analysis
            
        Returns:
            Dictionary with complete analysis for the timeframe
        """
        try:
            logger.info(f"Analyzing timeframe: {timeframe.value}")
            
            # Use timeframe-specific swing length
            timeframe_swing_lengths = getattr(self.settings, 'timeframe_swing_lengths', {})
            swing_length = timeframe_swing_lengths.get(timeframe.value, self.settings.get('swing_length', 15))
            
            # Create timeframe-specific structure analyzer
            structure_analyzer = MarketStructureAnalyzer(swing_length=swing_length)
            
            # Market structure analysis with timeframe-specific settings
            market_structure = structure_analyzer.get_market_structure_levels(data)
            logger.info(f"  - Market structure: Trend={market_structure.get('trend_direction', 'N/A')}, "
                       f"Strength={market_structure.get('trend_strength', 0.0):.2f}, "
                       f"Breaks={len(market_structure.get('structure_breaks', []))}")
            
            # Smart Money Concepts analysis
            smc_analysis = self.smc_analyzer.get_smart_money_analysis(data)
            order_blocks = smc_analysis.get('order_blocks', {})
            liquidity_zones = smc_analysis.get('liquidity_zones', {})
            fvgs = smc_analysis.get('fair_value_gaps', {})
            supply_demand = smc_analysis.get('supply_demand_zones', {})
            
            logger.info(f"  - SMC Analysis:")
            logger.info(f"    • Order Blocks: {len(order_blocks.get('valid', []))} valid")
            logger.info(f"    • Liquidity Zones: {len(liquidity_zones.get('all', []))} total")
            logger.info(f"    • Fair Value Gaps: {len(fvgs.get('active', []))} active")
            logger.info(f"    • Supply/Demand: {len(supply_demand.get('valid', []))} valid")
            
            # Generate signal for this timeframe with bias
            current_price = data['Close'].iloc[-1]
            logger.info(f"  - Generating signal at price: {current_price:.5f}")
            
            signal = self.signal_generator.generate_signal(
                market_structure, smc_analysis, current_price, timeframe.value, market_bias
            )
            
            logger.info(f"  - Signal Result:")
            logger.info(f"    • Type: {signal.get('signal_type', 'N/A')}")
            logger.info(f"    • Valid: {signal.get('valid', False)}")
            logger.info(f"    • Confluence Score: {signal.get('confluence_score', 0)}")
            logger.info(f"    • Quality: {signal.get('analysis_quality', 'N/A')}")
            logger.info(f"    • Entry Details: {bool(signal.get('entry_details', {}))}")
            
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
            weighted_scores = {'bullish': 0.0, 'bearish': 0.0, 'neutral': 0.0}
            total_weight = 0.0
            
            for tf, analysis in timeframe_analyses.items():
                if 'market_structure' in analysis:
                    # Fixed: Use 'trend_direction' key (not 'trend') as returned by MarketStructureAnalyzer
                    trend = analysis['market_structure'].get('trend_direction', TrendDirection.CONSOLIDATION)
                    trends[tf] = trend
                    
                    # Use weighted percentage system: H4=50%, H1=30%, M15=20%
                    weight = self._get_timeframe_weight(tf)
                    total_weight += weight
                    
                    if trend == TrendDirection.UPTREND:
                        weighted_scores['bullish'] += weight
                    elif trend == TrendDirection.DOWNTREND:
                        weighted_scores['bearish'] += weight
                    else:
                        weighted_scores['neutral'] += weight
            
            # Normalize to percentages
            if total_weight > 0:
                weighted_scores = {k: v/total_weight for k, v in weighted_scores.items()}
            
            # Determine overall trend with weighted logic
            # Require >50% weight for directional bias (prevents M15 from overriding H4+H1)
            max_score = max(weighted_scores.values())
            if weighted_scores['bullish'] >= 0.5:  # 50% threshold for bullish
                overall_trend = TrendDirection.UPTREND
            elif weighted_scores['bearish'] >= 0.5:  # 50% threshold for bearish
                overall_trend = TrendDirection.DOWNTREND
            else:
                overall_trend = TrendDirection.CONSOLIDATION
            
            # Calculate alignment strength (0-1) - how confident we are
            alignment_strength = max_score
            
            logger.info(f"Trend Aggregation: H4={trends.get(Timeframe.H4, 'N/A')}, "
                       f"H1={trends.get(Timeframe.H1, 'N/A')}, M15={trends.get(Timeframe.M15, 'N/A')} "
                       f"→ Weighted: Bull={weighted_scores['bullish']:.1%}, "
                       f"Bear={weighted_scores['bearish']:.1%}, Neutral={weighted_scores['neutral']:.1%} "
                       f"→ Overall: {overall_trend}")
            
            return {
                'individual_trends': trends,
                'weighted_scores': weighted_scores,  # Changed from trend_scores
                'overall_trend': overall_trend,
                'alignment_strength': alignment_strength,
                'is_aligned': alignment_strength >= 0.6  # 60% confidence threshold
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
            
            # Determine overall signal - FIXED: Don't let WAIT signals override real signals
            # Only consider actual trading signals (BUY/SELL) for the overall decision
            active_signal_scores = {k: v for k, v in signal_scores.items() if k != 'wait' and v > 0}
            
            if active_signal_scores:
                max_active_score = max(active_signal_scores.values())
                if signal_scores['buy'] == max_active_score:
                    overall_signal = SignalType.BUY
                elif signal_scores['sell'] == max_active_score:
                    overall_signal = SignalType.SELL
                else:
                    overall_signal = SignalType.WAIT
            else:
                overall_signal = SignalType.WAIT
                
            logger.info(f"DEBUG SIGNAL CONFLUENCE: Scores={signal_scores}, ActiveSignals={active_signal_scores}, OverallSignal={overall_signal}")
            
            # Calculate confluence strength - FIXED to exclude WAIT signals
            # Only consider actual trading signals (BUY/SELL) for confluence calculation
            active_signals_score = signal_scores['buy'] + signal_scores['sell']
            if active_signals_score > 0 and active_signal_scores:
                max_active_score = max(active_signal_scores.values())
                confluence_strength = max_active_score / active_signals_score
            else:
                confluence_strength = 0
            
            # Count how many timeframes agree with the overall signal
            confluence_count = 0
            active_timeframes = 0  # Count timeframes with actual signals (not WAIT)
            
            for tf, signal_info in signals.items():
                if signal_info['type'] != SignalType.WAIT:
                    active_timeframes += 1
                    if signal_info['type'] == overall_signal:
                        confluence_count += 1
            
            # Alternative confluence calculation: percentage of active timeframes agreeing
            if active_timeframes > 0:
                agreement_percentage = confluence_count / active_timeframes
            else:
                agreement_percentage = 0
            
            # Use the better of the two confluence measures
            final_confluence_strength = max(confluence_strength, agreement_percentage)
            
            return {
                'individual_signals': signals,
                'signal_scores': signal_scores,
                'overall_signal': overall_signal,
                'confluence_strength': final_confluence_strength,
                'confluence_count': confluence_count,
                'active_timeframes': active_timeframes,
                'has_confluence': final_confluence_strength >= 0.6 or confluence_count >= 2  # More flexible threshold
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
            
            # First pass: Extract trends for bias calculation
            trend_data = {}
            for timeframe in self.timeframes:
                if timeframe in data_dict:
                    # Quick market structure analysis just for trend
                    swing_length = getattr(self.settings, 'timeframe_swing_lengths', {}).get(timeframe.value, 15)
                    structure_analyzer = MarketStructureAnalyzer(swing_length=swing_length)
                    market_structure = structure_analyzer.get_market_structure_levels(data_dict[timeframe])
                    trend_data[timeframe.value] = {'trend': market_structure.get('trend_direction')}
            
            # Calculate market bias early using available trend data
            from ..filters.bias_filter import BiasFilter
            bias_filter = BiasFilter()
            market_bias = bias_filter.get_market_bias(trend_data)
            bias_value = market_bias.value if market_bias else None
            logger.info(f"Calculated market bias: {bias_value}")
            
            # Analyze each timeframe with bias
            timeframe_analyses = {}
            for timeframe in self.timeframes:
                if timeframe in data_dict:
                    analysis = self.analyze_timeframe(data_dict[timeframe], timeframe, bias_value)
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
                trend_alignment, signal_confluence, entry_timeframe, timeframe_analyses, bias_value
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
    
    def _calculate_confidence_score(self, trend_alignment: Dict, signal_confluence: Dict, entry_timeframe: Optional[Timeframe]) -> float:
        """Calculates the confidence score for a potential recommendation."""
        confidence_score = 0
        
        if trend_alignment.get('is_aligned', False):
            confidence_score += 0.3

        if signal_confluence.get('has_confluence', False):
            confidence_score += 0.3
        
        if entry_timeframe is not None:
            confidence_score += 0.2

        # Add confluence count to confidence
        confidence_score += signal_confluence.get('confluence_count', 0) * 0.05
        confidence_score = min(1.0, confidence_score) # Cap at 1.0
        
        return confidence_score

    def _generate_recommendation(self, trend_alignment: Dict, signal_confluence: Dict,
                               entry_timeframe: Optional[Timeframe], 
                               timeframe_analyses: Dict, market_bias: str = 'NEUTRAL') -> Dict:
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
            
            logger.info(f"🎯 Generating recommendation:")
            logger.info(f"   - Overall signal: {overall_signal}")
            logger.info(f"   - Overall trend: {overall_trend}")
            logger.info(f"   - Trend aligned: {trend_alignment.get('is_aligned', False)}")
            logger.info(f"   - Signal confluence: {signal_confluence.get('has_confluence', False)}")
            logger.info(f"   - Entry timeframe: {entry_timeframe}")
            logger.info(f"   - Confluence count: {signal_confluence.get('confluence_count', 0)}")
            logger.info(f"   - Signal scores: {signal_confluence.get('signal_scores', {})}")
            
            # DEBUG: Show detailed signal analysis
            for tf, analysis in timeframe_analyses.items():
                if 'signal' in analysis:
                    signal = analysis['signal']
                    logger.info(f"   - {tf}: {signal.get('signal_type', 'N/A')} (score: {signal.get('confluence_score', 0)})")
            
            # ENHANCED: Check for trend-signal contradiction with SMC pullback consideration
            if overall_signal != SignalType.WAIT:
                
                # Get setup context to understand if this is a pullback or breakout
                setup_type = None
                confluence_factors = []
                
                # Extract setup information from the entry timeframe analysis
                if entry_timeframe and entry_timeframe in timeframe_analyses:
                    entry_signal = timeframe_analyses[entry_timeframe].get('signal', {})
                    confluence_factors = entry_signal.get('confluence_factors', [])
                    
                    # Determine setup type from confluence factors
                    has_structure_break = any('STRUCTURE_BREAK' in str(factor) for factor in confluence_factors)
                    has_order_block = any('ORDER_BLOCK' in str(factor) for factor in confluence_factors)
                    has_fair_value_gap = any('FVG' in str(factor) or 'FAIR_VALUE_GAP' in str(factor) for factor in confluence_factors)
                    
                    if has_structure_break:
                        setup_type = 'breakout'
                    elif has_order_block or has_fair_value_gap:
                        setup_type = 'pullback'
                    else:
                        setup_type = 'pullback'  # Default to pullback for SMC
                
                # SMC-aware trend-signal validation
                if overall_trend == TrendDirection.DOWNTREND and overall_signal == SignalType.BUY:
                    if setup_type == 'pullback' and signal_confluence.get('confluence_count', 0) >= 3:
                        # Allow BUY in downtrend if it's a strong pullback setup (potential reversal or bounce)
                        logger.info(f"✅ PULLBACK: BUY signal in DOWNTREND with strong confluence ({signal_confluence.get('confluence_count', 0)}) - ALLOWING")
                    elif setup_type == 'breakout':
                        # Block BUY breakouts in downtrend (against momentum)
                        logger.warning(f"❌ BREAKOUT CONTRADICTION: BUY breakout against DOWNTREND - overriding to WAIT")
                        overall_signal = SignalType.WAIT
                        entry_timeframe = None
                    else:
                        # Weak pullback setup - require very high confluence
                        if signal_confluence.get('confluence_count', 0) >= 4:
                            logger.info(f"✅ WEAK PULLBACK: BUY signal in DOWNTREND with very high confluence ({signal_confluence.get('confluence_count', 0)}) - ALLOWING")
                        else:
                            logger.warning(f"❌ WEAK SETUP: BUY signal in DOWNTREND lacks confluence ({signal_confluence.get('confluence_count', 0)}) - overriding to WAIT")
                            overall_signal = SignalType.WAIT
                            entry_timeframe = None
                            
                elif overall_trend == TrendDirection.UPTREND and overall_signal == SignalType.SELL:
                    if setup_type == 'pullback' and signal_confluence.get('confluence_count', 0) >= 3:
                        # Allow SELL in uptrend if it's a strong pullback setup (potential reversal or retracement)
                        logger.info(f"✅ PULLBACK: SELL signal in UPTREND with strong confluence ({signal_confluence.get('confluence_count', 0)}) - ALLOWING")
                    elif setup_type == 'breakout':
                        # Block SELL breakouts in uptrend (against momentum)
                        logger.warning(f"❌ BREAKOUT CONTRADICTION: SELL breakout against UPTREND - overriding to WAIT")
                        overall_signal = SignalType.WAIT
                        entry_timeframe = None
                    else:
                        # Weak pullback setup - require very high confluence
                        if signal_confluence.get('confluence_count', 0) >= 4:
                            logger.info(f"✅ WEAK PULLBACK: SELL signal in UPTREND with very high confluence ({signal_confluence.get('confluence_count', 0)}) - ALLOWING")
                        else:
                            logger.warning(f"❌ WEAK SETUP: SELL signal in UPTREND lacks confluence ({signal_confluence.get('confluence_count', 0)}) - overriding to WAIT")
                            overall_signal = SignalType.WAIT
                            entry_timeframe = None
                            
                elif overall_trend == TrendDirection.DOWNTREND and overall_signal == SignalType.SELL:
                    logger.info(f"✅ TREND ALIGNED: SELL signal aligns with DOWNTREND")
                elif overall_trend == TrendDirection.UPTREND and overall_signal == SignalType.BUY:
                    logger.info(f"✅ TREND ALIGNED: BUY signal aligns with UPTREND")
                elif overall_trend == TrendDirection.CONSOLIDATION:
                    # In consolidation, allow signals but require higher confluence or confidence
                    confluence_count = signal_confluence.get('confluence_count', 0)
                    confidence_score = self._calculate_confidence_score(trend_alignment, signal_confluence, entry_timeframe)

                    if confluence_count < 2 and confidence_score < 0.7:
                        logger.warning(f"⚠️  CONSOLIDATION: {overall_signal} signal needs more confluence or higher confidence - overriding to WAIT")
                        overall_signal = SignalType.WAIT
                        entry_timeframe = None
                    else:
                        logger.info(f"✅ CONSOLIDATION: {overall_signal} signal has sufficient confluence ({confluence_count}) or confidence ({confidence_score:.2f})")
            
            # Enhanced strength factors with detailed context
            strength_factors = []
            
            # 1. Trend alignment details
            if trend_alignment.get('is_aligned', False):
                trend_strength = trend_alignment.get('alignment_strength', 0)
                overall_trend = trend_alignment.get('overall_trend', TrendDirection.CONSOLIDATION)
                strength_factors.append(f"Strong {overall_trend.value.lower()} alignment ({trend_strength:.1%} confidence)")

            # 2. Signal confluence details  
            if signal_confluence.get('has_confluence', False):
                confluence_count = signal_confluence.get('confluence_count', 0)
                strength_factors.append(f"Multi-TF confluence ({confluence_count} timeframes aligned)")
            
            # 3. Entry setup details with RR ratio
            if entry_timeframe and entry_timeframe in timeframe_analyses:
                entry_signal = timeframe_analyses[entry_timeframe].get('signal', {})
                entry_details_temp = entry_signal.get('entry_details', {})
                rr_ratio = entry_details_temp.get('risk_reward_ratio', 0)
                confluence_score = entry_signal.get('confluence_score', 0)
                
                if rr_ratio >= 2.0:
                    strength_factors.append(f"Excellent RR ratio ({rr_ratio:.1f}:1) on {entry_timeframe.value}")
                elif rr_ratio >= 1.5:
                    strength_factors.append(f"Good RR ratio ({rr_ratio:.1f}:1) on {entry_timeframe.value}")
                
                if confluence_score >= 10:
                    strength_factors.append(f"High confluence setup ({confluence_score}/15) on {entry_timeframe.value}")
            
            # 4. SMC structure details (from entry timeframe)
            if entry_timeframe and entry_timeframe in timeframe_analyses:
                smc_analysis = timeframe_analyses[entry_timeframe].get('smc_analysis', {})
                
                # Order blocks presence
                order_blocks = smc_analysis.get('order_blocks', {}).get('valid', [])
                if len(order_blocks) >= 5:
                    strength_factors.append(f"Strong OB presence ({len(order_blocks)} valid blocks)")
                
                # Fair Value Gap confirmation
                fvgs = smc_analysis.get('fair_value_gaps', {}).get('active', [])
                if len(fvgs) >= 3:
                    strength_factors.append(f"FVG confluence ({len(fvgs)} active gaps)")
                
                # Liquidity considerations
                liquidity_zones = smc_analysis.get('liquidity_zones', {})
                if isinstance(liquidity_zones, list) and len(liquidity_zones) <= 6:  # After pruning
                    strength_factors.append("Clean liquidity environment (low noise)")
                
                # Structure breaks
                market_structure = timeframe_analyses[entry_timeframe].get('market_structure', {})
                structure_breaks = market_structure.get('structure_breaks', [])
                if len(structure_breaks) >= 3:
                    strength_factors.append(f"Recent structure activity ({len(structure_breaks)} breaks)")
            
            # 5. Missing elements as cautions
            if entry_timeframe and entry_timeframe in timeframe_analyses:
                smc_analysis = timeframe_analyses[entry_timeframe].get('smc_analysis', {})
                
                # Check for sweep detection
                liquidity_sweeps = smc_analysis.get('liquidity_sweeps', [])
                if len(liquidity_sweeps) == 0:
                    strength_factors.append("No recent sweeps detected (caution)")
                
                # Check for breaker blocks
                breaker_blocks = smc_analysis.get('breaker_blocks', [])
                if len(breaker_blocks) == 0:
                    strength_factors.append("No breaker blocks active")

            confidence_score = self._calculate_confidence_score(trend_alignment, signal_confluence, entry_timeframe)

            logger.info(f"   - Strength factors: {strength_factors}")
            
            # Get entry details and signal strength from the recommended timeframe
            entry_details = {}
            signal_strength = SignalStrength.WEAK
            if entry_timeframe and entry_timeframe in timeframe_analyses:
                entry_signal = timeframe_analyses[entry_timeframe].get('signal', {})
                signal_entry_details = entry_signal.get('entry_details', {})
                signal_strength = entry_signal.get('signal_strength', SignalStrength.WEAK)
                entry_details = {
                    'entry_price': signal_entry_details.get('entry_price'),
                    'stop_loss': signal_entry_details.get('stop_loss'),
                    'take_profit': signal_entry_details.get('take_profit'),
                    'risk_reward_ratio': signal_entry_details.get('risk_reward_ratio'),
                    'confluence_factors': signal_entry_details.get('confluence_factors', [])
                }
                logger.info(f"   - Entry details from {entry_timeframe.value}: {entry_details}")

            def get_confidence_label(score):
                if score >= 0.8: return "HIGH"
                if score >= 0.6: return "MODERATE"
                return "LOW"

            # Create standardized recommendation structure
            from ..utils.signal_structures import SignalRecommendation, EntryDetails
            
            # Convert trend direction to string
            trend_dir_str = overall_trend.value if hasattr(overall_trend, 'value') else str(overall_trend)
            
            # Convert entry timeframe to string
            entry_tf_str = entry_timeframe.value if entry_timeframe and hasattr(entry_timeframe, 'value') else "M15"
            
            # Create standardized entry details
            std_entry_details = EntryDetails(
                entry_price=entry_details.get('entry_price', 0.0),
                stop_loss=entry_details.get('stop_loss', 0.0),
                take_profit=entry_details.get('take_profit', 0.0),
                risk_reward_ratio=entry_details.get('risk_reward_ratio', 0.0),
                setup_type="pullback",  # Default SMC setup type
                confluence_factors=entry_details.get('confluence_factors', [])
            )
            
            # Create standardized recommendation
            recommendation = SignalRecommendation(
                action=overall_signal,
                confidence=get_confidence_label(confidence_score),
                entry_timeframe=entry_tf_str,
                strength_factors=strength_factors,
                strength_score=confidence_score * 10,  # Scale to 0-10 range
                confluence_score=signal_confluence.get('confluence_strength', 0.0) * 10,
                entry_details=std_entry_details,
                trend_direction=trend_dir_str,
                setup_type="pullback",
                is_valid=overall_signal != SignalType.WAIT,
                trend_aligned=trend_alignment.get('is_aligned', False),
                signal_confluence=signal_confluence.get('has_confluence', False)
            )
            
            # Return both standardized and legacy formats
            return {
                'standardized': recommendation,
                'legacy': recommendation.to_dict(),
                # Keep original fields for backward compatibility
                'action': overall_signal,
                'trend_direction': overall_trend,
                'strength': signal_strength,
                'strength_factors': strength_factors,
                'entry_timeframe': entry_timeframe,
                'entry_details': entry_details,
                'confidence': get_confidence_label(confidence_score),
                'confidence_score': confidence_score,
                'market_bias': market_bias,  # Fix: Include calculated market bias
                'signal_confluence': signal_confluence,  # Fix: Include signal confluence data
                'timeframe_analyses': timeframe_analyses  # Fix: Include timeframe analyses
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return {'action': SignalType.WAIT, 'confidence': 'LOW'}