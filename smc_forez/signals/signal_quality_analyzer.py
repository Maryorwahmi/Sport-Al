"""
Professional-grade signal quality analyzer that implements institutional-level 
signal validation using Smart Money Concepts and multi-timeframe analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import json
from datetime import datetime, timedelta

from ..config.settings import Timeframe
from ..market_structure.structure_analyzer import TrendDirection, StructureType
from ..smart_money.smc_analyzer import ZoneType, OrderBlockType
from .signal_generator import SignalType, SignalStrength, ConfluenceFactor

logger = logging.getLogger(__name__)


class QualityGrade(Enum):
    """Signal quality grades based on institutional standards"""
    INSTITUTIONAL = "institutional"  # 85-100 score
    PROFESSIONAL = "professional"    # 70-84 score
    INTERMEDIATE = "intermediate"     # 55-69 score
    BASIC = "basic"                  # 40-54 score
    POOR = "poor"                    # <40 score


class TimeframeRole(Enum):
    """Role of timeframe in signal analysis"""
    HTF = "higher_timeframe"  # H4, D1 - Bias and macro context
    MTF = "mid_timeframe"     # H1, M15 - Setup confirmation
    LTF = "lower_timeframe"   # M5, M1 - Trigger execution


class SignalQualityAnalyzer:
    """
    Institutional-grade signal quality analyzer that validates signals using
    multi-timeframe confirmation, liquidity positioning, and confluence scoring.
    """
    
    def __init__(self, quality_settings: Dict):
        """
        Initialize signal quality analyzer
        
        Args:
            quality_settings: Dictionary with quality analysis settings
        """
        self.settings = quality_settings
        self.signal_history = {}  # Track signals for duplicate detection
        
        # Quality thresholds
        self.min_institutional_score = quality_settings.get('min_institutional_score', 85)
        self.min_professional_score = quality_settings.get('min_professional_score', 70)
        self.min_execution_score = quality_settings.get('min_execution_score', 55)
        
        # Multi-timeframe weights
        self.timeframe_weights = {
            TimeframeRole.HTF: quality_settings.get('htf_weight', 0.4),
            TimeframeRole.MTF: quality_settings.get('mtf_weight', 0.35),
            TimeframeRole.LTF: quality_settings.get('ltf_weight', 0.25)
        }
        
        # Confluence factor weights (0-100 scale)
        self.factor_weights = {
            ConfluenceFactor.TREND_ALIGNMENT: quality_settings.get('trend_weight', 25),
            ConfluenceFactor.STRUCTURE_BREAK: quality_settings.get('structure_weight', 20),
            ConfluenceFactor.ORDER_BLOCK: quality_settings.get('orderblock_weight', 15),
            ConfluenceFactor.LIQUIDITY_ZONE: quality_settings.get('liquidity_weight', 20),
            ConfluenceFactor.FAIR_VALUE_GAP: quality_settings.get('fvg_weight', 10),
            ConfluenceFactor.SUPPLY_DEMAND: quality_settings.get('supply_demand_weight', 10)
        }
        
        # Risk validation settings
        self.min_rr_ratio = quality_settings.get('min_rr_ratio', 2.0)
        self.max_risk_percentage = quality_settings.get('max_risk_percentage', 0.02)
        
        # Session and execution filters
        self.allowed_sessions = quality_settings.get('allowed_sessions', ['london', 'newyork', 'overlap'])
        self.max_concurrent_trades = quality_settings.get('max_concurrent_trades', 5)
        self.duplicate_time_window = quality_settings.get('duplicate_time_window', 4)  # hours
        
    def _classify_timeframe_role(self, timeframe: Timeframe) -> TimeframeRole:
        """
        Classify timeframe into its role for multi-timeframe analysis
        
        Args:
            timeframe: Timeframe to classify
            
        Returns:
            TimeframeRole classification
        """
        htf_timeframes = [Timeframe.D1, Timeframe.H4]
        mtf_timeframes = [Timeframe.H1, Timeframe.M15]
        
        if timeframe in htf_timeframes:
            return TimeframeRole.HTF
        elif timeframe in mtf_timeframes:
            return TimeframeRole.MTF
        else:
            return TimeframeRole.LTF
    
    def analyze_multi_timeframe_bias(self, timeframe_analyses: Dict) -> Dict:
        """
        Analyze multi-timeframe bias confirmation using HTF→MTF→LTF cascade
        
        Args:
            timeframe_analyses: Dictionary of analyses by timeframe
            
        Returns:
            Dictionary with bias analysis results
        """
        try:
            # Organize analyses by timeframe role
            htf_analyses = []
            mtf_analyses = []
            ltf_analyses = []
            
            for tf, analysis in timeframe_analyses.items():
                role = self._classify_timeframe_role(tf)
                if role == TimeframeRole.HTF:
                    htf_analyses.append(analysis)
                elif role == TimeframeRole.MTF:
                    mtf_analyses.append(analysis)
                else:
                    ltf_analyses.append(analysis)
            
            # Establish HTF bias
            htf_bias = self._establish_htf_bias(htf_analyses)
            
            # Validate MTF setup alignment
            mtf_confirmation = self._validate_mtf_setup(mtf_analyses, htf_bias)
            
            # Check LTF trigger quality
            ltf_trigger = self._assess_ltf_trigger(ltf_analyses, htf_bias, mtf_confirmation)
            
            # Calculate cascade score
            cascade_score = self._calculate_cascade_score(htf_bias, mtf_confirmation, ltf_trigger)
            
            return {
                'htf_bias': htf_bias,
                'mtf_confirmation': mtf_confirmation,
                'ltf_trigger': ltf_trigger,
                'cascade_score': cascade_score,
                'is_aligned': cascade_score >= 70  # 70% threshold for alignment
            }
            
        except Exception as e:
            logger.error(f"Error analyzing multi-timeframe bias: {str(e)}")
            return {
                'htf_bias': {'direction': 'neutral', 'strength': 0},
                'mtf_confirmation': {'confirmed': False, 'strength': 0},
                'ltf_trigger': {'valid': False, 'strength': 0},
                'cascade_score': 0,
                'is_aligned': False
            }
    
    def _establish_htf_bias(self, htf_analyses: List[Dict]) -> Dict:
        """Establish higher timeframe directional bias"""
        if not htf_analyses:
            return {'direction': 'neutral', 'strength': 0, 'reason': 'No HTF data'}
        
        # Weight D1 higher than H4
        total_weight = 0
        bullish_score = 0
        bearish_score = 0
        
        for analysis in htf_analyses:
            weight = 2 if analysis.get('timeframe') == Timeframe.D1 else 1
            trend = analysis.get('market_structure', {}).get('trend_direction', TrendDirection.CONSOLIDATION)
            
            if trend == TrendDirection.UPTREND:
                bullish_score += weight
            elif trend == TrendDirection.DOWNTREND:
                bearish_score += weight
            
            total_weight += weight
        
        # Determine bias
        if bullish_score > bearish_score:
            direction = 'bullish'
            strength = (bullish_score / total_weight) * 100
        elif bearish_score > bullish_score:
            direction = 'bearish'
            strength = (bearish_score / total_weight) * 100
        else:
            direction = 'neutral'
            strength = 0
        
        return {
            'direction': direction,
            'strength': strength,
            'reason': f'HTF analysis with {len(htf_analyses)} timeframes'
        }
    
    def _validate_mtf_setup(self, mtf_analyses: List[Dict], htf_bias: Dict) -> Dict:
        """Validate mid-timeframe setup confirmation"""
        if not mtf_analyses or htf_bias['direction'] == 'neutral':
            return {'confirmed': False, 'strength': 0, 'reason': 'No MTF data or neutral HTF bias'}
        
        confirmed_setups = 0
        total_setups = len(mtf_analyses)
        
        for analysis in mtf_analyses:
            market_structure = analysis.get('market_structure', {})
            smc_analysis = analysis.get('smc_analysis', {})
            
            # Check for structure break alignment
            recent_breaks = market_structure.get('structure_breaks', [])
            if recent_breaks:
                latest_break = recent_breaks[-1]
                break_direction = latest_break.get('direction', 'neutral')
                
                if break_direction == htf_bias['direction']:
                    confirmed_setups += 1
                    continue
            
            # Check for order block alignment
            order_blocks = smc_analysis.get('order_blocks', {}).get('valid', [])
            for ob in order_blocks:
                ob_direction = 'bullish' if ob['type'] == OrderBlockType.BULLISH else 'bearish'
                if ob_direction == htf_bias['direction']:
                    confirmed_setups += 1
                    break
        
        strength = (confirmed_setups / total_setups) * 100 if total_setups > 0 else 0
        
        return {
            'confirmed': confirmed_setups > 0,
            'strength': strength,
            'reason': f'{confirmed_setups}/{total_setups} MTF setups aligned'
        }
    
    def _assess_ltf_trigger(self, ltf_analyses: List[Dict], htf_bias: Dict, mtf_confirmation: Dict) -> Dict:
        """Assess lower timeframe trigger quality"""
        if not ltf_analyses or not mtf_confirmation['confirmed']:
            return {'valid': False, 'strength': 0, 'reason': 'No LTF data or MTF not confirmed'}
        
        valid_triggers = 0
        total_triggers = len(ltf_analyses)
        
        for analysis in ltf_analyses:
            signal = analysis.get('signal', {})
            
            # Check signal alignment with HTF bias
            if signal.get('signal_type') == SignalType.WAIT:
                continue
            
            signal_direction = 'bullish' if signal.get('signal_type') == SignalType.BUY else 'bearish'
            
            if signal_direction == htf_bias['direction']:
                # Additional checks for trigger quality
                confluence_score = signal.get('confluence_score', 0)
                rr_ratio = signal.get('risk_reward_ratio', 0)
                
                if confluence_score >= 3 and rr_ratio >= self.min_rr_ratio:
                    valid_triggers += 1
        
        strength = (valid_triggers / total_triggers) * 100 if total_triggers > 0 else 0
        
        return {
            'valid': valid_triggers > 0,
            'strength': strength,
            'reason': f'{valid_triggers}/{total_triggers} LTF triggers aligned'
        }
    
    def _calculate_cascade_score(self, htf_bias: Dict, mtf_confirmation: Dict, ltf_trigger: Dict) -> float:
        """Calculate overall cascade score"""
        htf_score = htf_bias['strength'] * self.timeframe_weights[TimeframeRole.HTF]
        mtf_score = mtf_confirmation['strength'] * self.timeframe_weights[TimeframeRole.MTF]
        ltf_score = ltf_trigger['strength'] * self.timeframe_weights[TimeframeRole.LTF]
        
        return htf_score + mtf_score + ltf_score
    
    def analyze_liquidity_positioning(self, smc_analysis: Dict, current_price: float) -> Dict:
        """
        Analyze liquidity positioning quality
        
        Args:
            smc_analysis: Smart money concepts analysis
            current_price: Current market price
            
        Returns:
            Dictionary with liquidity positioning analysis
        """
        try:
            liquidity_zones = smc_analysis.get('liquidity_zones', {})
            unswept_liquidity = liquidity_zones.get('unswept', [])
            swept_liquidity = liquidity_zones.get('swept', [])
            
            # Find nearest liquidity levels
            nearest_high = None
            nearest_low = None
            
            for lz in unswept_liquidity:
                level = lz.get('level', 0)
                zone_type = lz.get('type')
                
                if zone_type == ZoneType.LIQUIDITY_HIGH:
                    if nearest_high is None or abs(level - current_price) < abs(nearest_high - current_price):
                        nearest_high = level
                elif zone_type == ZoneType.LIQUIDITY_LOW:
                    if nearest_low is None or abs(level - current_price) < abs(nearest_low - current_price):
                        nearest_low = level
            
            # Calculate positioning score
            positioning_score = 0
            positioning_reason = []
            
            # Check if near liquidity (good for entries)
            if nearest_high and nearest_low:
                distance_to_high = abs(current_price - nearest_high) / current_price
                distance_to_low = abs(current_price - nearest_low) / current_price
                
                min_distance = min(distance_to_high, distance_to_low)
                
                if min_distance <= 0.002:  # Within 0.2%
                    positioning_score += 30
                    positioning_reason.append("Near key liquidity level")
                elif min_distance <= 0.005:  # Within 0.5%
                    positioning_score += 20
                    positioning_reason.append("Approaching liquidity level")
                
                # Bonus for being between liquidity levels (range setup)
                if nearest_low < current_price < nearest_high:
                    range_position = (current_price - nearest_low) / (nearest_high - nearest_low)
                    if 0.2 <= range_position <= 0.8:  # Not at extremes
                        positioning_score += 15
                        positioning_reason.append("In optimal range position")
            
            # Check for recent liquidity sweeps (good for reversals)
            recent_sweeps = [lz for lz in swept_liquidity if lz.get('swept_recently', False)]
            if recent_sweeps:
                positioning_score += 25
                positioning_reason.append(f"{len(recent_sweeps)} recent liquidity sweeps")
            
            # Penalty for being in no-man's land (far from liquidity)
            if nearest_high and nearest_low:
                min_distance = min(distance_to_high, distance_to_low)
                if min_distance > 0.01:  # More than 1% away
                    positioning_score -= 20
                    positioning_reason.append("Far from key liquidity levels")
            
            return {
                'positioning_score': max(0, min(100, positioning_score)),
                'nearest_high': nearest_high,
                'nearest_low': nearest_low,
                'distance_to_high': distance_to_high if nearest_high else None,
                'distance_to_low': distance_to_low if nearest_low else None,
                'positioning_reason': positioning_reason
            }
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity positioning: {str(e)}")
            return {
                'positioning_score': 0,
                'nearest_high': None,
                'nearest_low': None,
                'distance_to_high': None,
                'distance_to_low': None,
                'positioning_reason': ['Error in liquidity analysis']
            }
    
    def calculate_weighted_confluence_score(self, confluence_factors: List[Dict]) -> Dict:
        """
        Calculate weighted confluence score (0-100 scale)
        
        Args:
            confluence_factors: List of confluence factors
            
        Returns:
            Dictionary with weighted confluence analysis
        """
        try:
            total_score = 0
            max_possible_score = 0
            factor_details = {}
            
            # Calculate score for each factor type
            for factor_type, weight in self.factor_weights.items():
                factor_score = 0
                factor_count = 0
                
                for cf in confluence_factors:
                    if cf.get('factor') == factor_type:
                        factor_score += cf.get('score', 0)
                        factor_count += 1
                
                # Normalize factor score (cap at 1.0 for each factor type)
                normalized_factor_score = min(1.0, factor_score / max(1, factor_count) if factor_count > 0 else 0)
                
                # Apply weight
                weighted_score = normalized_factor_score * weight
                total_score += weighted_score
                max_possible_score += weight
                
                factor_details[factor_type.value] = {
                    'raw_score': factor_score,
                    'factor_count': factor_count,
                    'normalized_score': normalized_factor_score,
                    'weighted_score': weighted_score,
                    'weight': weight
                }
            
            # Calculate final score as percentage
            final_score = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
            
            return {
                'total_score': round(final_score, 2),
                'factor_details': factor_details,
                'factors_present': len([cf for cf in confluence_factors if cf.get('score', 0) > 0])
            }
            
        except Exception as e:
            logger.error(f"Error calculating weighted confluence score: {str(e)}")
            return {'total_score': 0, 'factor_details': {}, 'factors_present': 0}
    
    def validate_risk_reward(self, signal: Dict) -> Dict:
        """
        Validate risk-reward setup using structural reference points
        
        Args:
            signal: Signal dictionary with entry, SL, TP levels
            
        Returns:
            Dictionary with risk-reward validation results
        """
        try:
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            take_profit = signal.get('take_profit', 0)
            
            if not all([entry_price, stop_loss, take_profit]):
                return {
                    'valid': False,
                    'rr_ratio': 0,
                    'risk_amount': 0,
                    'reward_amount': 0,
                    'reason': 'Missing entry, SL, or TP levels'
                }
            
            # Calculate risk and reward
            risk_amount = abs(entry_price - stop_loss)
            reward_amount = abs(take_profit - entry_price)
            
            # Calculate R:R ratio
            rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            
            # Validate minimum R:R ratio
            rr_valid = rr_ratio >= self.min_rr_ratio
            
            # Calculate risk percentage (basic validation)
            risk_percentage = risk_amount / entry_price if entry_price > 0 else 0
            risk_percentage_valid = risk_percentage <= self.max_risk_percentage
            
            # Overall validation
            is_valid = rr_valid and risk_percentage_valid
            
            reasons = []
            if not rr_valid:
                reasons.append(f"R:R ratio {rr_ratio:.2f} below minimum {self.min_rr_ratio}")
            if not risk_percentage_valid:
                reasons.append(f"Risk percentage {risk_percentage:.4f} above maximum {self.max_risk_percentage}")
            
            return {
                'valid': is_valid,
                'rr_ratio': round(rr_ratio, 2),
                'risk_amount': risk_amount,
                'reward_amount': reward_amount,
                'risk_percentage': risk_percentage,
                'reason': reasons if reasons else ['Risk-reward parameters valid']
            }
            
        except Exception as e:
            logger.error(f"Error validating risk-reward: {str(e)}")
            return {
                'valid': False,
                'rr_ratio': 0,
                'risk_amount': 0,
                'reward_amount': 0,
                'reason': ['Error in risk-reward calculation']
            }
    
    def check_execution_readiness(self, signal: Dict, symbol: str) -> Dict:
        """
        Check if signal is ready for execution (duplicates, sessions, limits)
        
        Args:
            signal: Signal dictionary
            symbol: Trading symbol
            
        Returns:
            Dictionary with execution readiness analysis
        """
        try:
            ready_for_execution = True
            blocking_reasons = []
            
            # Check for duplicate signals
            if self._is_duplicate_signal(signal, symbol):
                ready_for_execution = False
                blocking_reasons.append("Duplicate signal detected")
            
            # Check trading session
            if not self._is_valid_trading_session():
                ready_for_execution = False
                blocking_reasons.append("Outside allowed trading sessions")
            
            # Check concurrent trades limit
            if self._exceeds_concurrent_limit():
                ready_for_execution = False
                blocking_reasons.append("Maximum concurrent trades reached")
            
            # Check signal validity
            if not signal.get('valid', False):
                ready_for_execution = False
                blocking_reasons.append("Signal marked as invalid")
            
            return {
                'ready_for_execution': ready_for_execution,
                'blocking_reasons': blocking_reasons,
                'checks_performed': [
                    'duplicate_detection',
                    'trading_session',
                    'concurrent_limits',
                    'signal_validity'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error checking execution readiness: {str(e)}")
            return {
                'ready_for_execution': False,
                'blocking_reasons': ['Error in execution readiness check'],
                'checks_performed': []
            }
    
    def _is_duplicate_signal(self, signal: Dict, symbol: str) -> bool:
        """Check if signal is duplicate within time window"""
        if symbol not in self.signal_history:
            return False
        
        current_time = signal.get('timestamp', datetime.now())
        signal_type = signal.get('signal_type')
        entry_price = signal.get('entry_price', 0)
        
        for hist_signal in self.signal_history[symbol]:
            time_diff = abs((current_time - hist_signal['timestamp']).total_seconds() / 3600)
            
            if time_diff <= self.duplicate_time_window:
                if (hist_signal['signal_type'] == signal_type and
                    abs(hist_signal['entry_price'] - entry_price) / entry_price < 0.001):
                    return True
        
        return False
    
    def _is_valid_trading_session(self) -> bool:
        """Check if current time is within allowed trading sessions"""
        # Simplified session check - can be enhanced with timezone logic
        current_hour = datetime.now().hour
        
        # London session: 8-16 UTC
        # New York session: 13-21 UTC  
        # Overlap: 13-16 UTC
        
        london_session = 8 <= current_hour <= 16
        newyork_session = 13 <= current_hour <= 21
        overlap_session = 13 <= current_hour <= 16
        
        if 'london' in self.allowed_sessions and london_session:
            return True
        if 'newyork' in self.allowed_sessions and newyork_session:
            return True
        if 'overlap' in self.allowed_sessions and overlap_session:
            return True
        
        return False
    
    def _exceeds_concurrent_limit(self) -> bool:
        """Check if adding new trade would exceed concurrent limit"""
        # This would integrate with actual position tracking
        # For now, return False (no limit exceeded)
        return False
    
    def add_signal_to_history(self, signal: Dict, symbol: str):
        """Add signal to history for duplicate tracking"""
        if symbol not in self.signal_history:
            self.signal_history[symbol] = []
        
        self.signal_history[symbol].append({
            'timestamp': signal.get('timestamp', datetime.now()),
            'signal_type': signal.get('signal_type'),
            'entry_price': signal.get('entry_price', 0)
        })
        
        # Keep only recent signals
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.signal_history[symbol] = [
            s for s in self.signal_history[symbol] 
            if s['timestamp'] > cutoff_time
        ]
    
    def determine_quality_grade(self, total_score: float) -> QualityGrade:
        """
        Determine signal quality grade based on total score
        
        Args:
            total_score: Total quality score (0-100)
            
        Returns:
            QualityGrade enum
        """
        if total_score >= self.min_institutional_score:
            return QualityGrade.INSTITUTIONAL
        elif total_score >= self.min_professional_score:
            return QualityGrade.PROFESSIONAL
        elif total_score >= self.min_execution_score:
            return QualityGrade.INTERMEDIATE
        elif total_score >= 40:
            return QualityGrade.BASIC
        else:
            return QualityGrade.POOR
    
    def analyze_signal_quality(self, signal: Dict, timeframe_analyses: Dict, 
                              symbol: str) -> Dict:
        """
        Comprehensive signal quality analysis
        
        Args:
            signal: Primary signal from signal generator
            timeframe_analyses: Multi-timeframe analysis results
            symbol: Trading symbol
            
        Returns:
            Dictionary with complete quality analysis
        """
        try:
            logger.info(f"Analyzing signal quality for {symbol}")
            
            # 1. Multi-timeframe bias confirmation
            mtf_analysis = self.analyze_multi_timeframe_bias(timeframe_analyses)
            
            # 2. Liquidity positioning analysis
            primary_smc = list(timeframe_analyses.values())[0].get('smc_analysis', {})
            liquidity_analysis = self.analyze_liquidity_positioning(
                primary_smc, signal.get('current_price', 0)
            )
            
            # 3. Weighted confluence scoring
            confluence_analysis = self.calculate_weighted_confluence_score(
                signal.get('confluence_factors', [])
            )
            
            # 4. Risk-reward validation
            rr_analysis = self.validate_risk_reward(signal)
            
            # 5. Execution readiness check
            execution_analysis = self.check_execution_readiness(signal, symbol)
            
            # Calculate total quality score
            total_score = self._calculate_total_quality_score(
                mtf_analysis, liquidity_analysis, confluence_analysis, rr_analysis
            )
            
            # Determine quality grade
            quality_grade = self.determine_quality_grade(total_score)
            
            # Should signal be executed?
            should_execute = (
                total_score >= self.min_execution_score and
                execution_analysis['ready_for_execution'] and
                rr_analysis['valid']
            )
            
            # Create detailed analysis report
            quality_report = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'total_quality_score': round(total_score, 2),
                'quality_grade': quality_grade.value,
                'should_execute': should_execute,
                'signal_summary': {
                    'type': signal.get('signal_type', SignalType.WAIT).value,
                    'strength': signal.get('signal_strength', SignalStrength.WEAK).name,
                    'entry_price': signal.get('entry_price', 0),
                    'stop_loss': signal.get('stop_loss', 0),
                    'take_profit': signal.get('take_profit', 0)
                },
                'analysis_components': {
                    'multi_timeframe': mtf_analysis,
                    'liquidity_positioning': liquidity_analysis,
                    'confluence_scoring': confluence_analysis,
                    'risk_reward': rr_analysis,
                    'execution_readiness': execution_analysis
                },
                'decision_reasoning': self._generate_decision_reasoning(
                    mtf_analysis, liquidity_analysis, confluence_analysis, 
                    rr_analysis, execution_analysis, should_execute
                )
            }
            
            # Add to signal history if valid
            if should_execute:
                self.add_signal_to_history(signal, symbol)
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error in signal quality analysis: {str(e)}")
            return {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'total_quality_score': 0,
                'quality_grade': QualityGrade.POOR.value,
                'should_execute': False,
                'error': str(e)
            }
    
    def _calculate_total_quality_score(self, mtf_analysis: Dict, liquidity_analysis: Dict,
                                     confluence_analysis: Dict, rr_analysis: Dict) -> float:
        """Calculate total quality score from all components"""
        # Component weights
        mtf_weight = 0.35      # Multi-timeframe alignment (35%)
        liquidity_weight = 0.25  # Liquidity positioning (25%)
        confluence_weight = 0.25 # Confluence factors (25%)
        rr_weight = 0.15        # Risk-reward (15%)
        
        # Component scores
        mtf_score = mtf_analysis.get('cascade_score', 0)
        liquidity_score = liquidity_analysis.get('positioning_score', 0)
        confluence_score = confluence_analysis.get('total_score', 0)
        rr_score = 100 if rr_analysis.get('valid', False) else 0
        
        # Calculate weighted total
        total_score = (
            mtf_score * mtf_weight +
            liquidity_score * liquidity_weight +
            confluence_score * confluence_weight +
            rr_score * rr_weight
        )
        
        return min(100, max(0, total_score))
    
    def _generate_decision_reasoning(self, mtf_analysis: Dict, liquidity_analysis: Dict,
                                   confluence_analysis: Dict, rr_analysis: Dict,
                                   execution_analysis: Dict, should_execute: bool) -> List[str]:
        """Generate human-readable decision reasoning"""
        reasoning = []
        
        # Multi-timeframe reasoning
        if mtf_analysis.get('is_aligned', False):
            reasoning.append(f"✓ Multi-timeframe alignment confirmed ({mtf_analysis.get('cascade_score', 0):.1f}/100)")
        else:
            reasoning.append(f"✗ Multi-timeframe alignment weak ({mtf_analysis.get('cascade_score', 0):.1f}/100)")
        
        # Liquidity reasoning
        liquidity_score = liquidity_analysis.get('positioning_score', 0)
        if liquidity_score >= 70:
            reasoning.append(f"✓ Excellent liquidity positioning ({liquidity_score}/100)")
        elif liquidity_score >= 40:
            reasoning.append(f"⚠ Moderate liquidity positioning ({liquidity_score}/100)")
        else:
            reasoning.append(f"✗ Poor liquidity positioning ({liquidity_score}/100)")
        
        # Confluence reasoning
        confluence_score = confluence_analysis.get('total_score', 0)
        factors_count = confluence_analysis.get('factors_present', 0)
        reasoning.append(f"Confluence: {confluence_score:.1f}/100 ({factors_count} factors)")
        
        # Risk-reward reasoning
        if rr_analysis.get('valid', False):
            rr_ratio = rr_analysis.get('rr_ratio', 0)
            reasoning.append(f"✓ Risk-reward valid (R:R {rr_ratio}:1)")
        else:
            reasoning.append(f"✗ Risk-reward invalid: {', '.join(rr_analysis.get('reason', []))}")
        
        # Execution reasoning
        if execution_analysis.get('ready_for_execution', False):
            reasoning.append("✓ Ready for execution")
        else:
            reasons = execution_analysis.get('blocking_reasons', [])
            reasoning.append(f"✗ Execution blocked: {', '.join(reasons)}")
        
        # Final decision
        if should_execute:
            reasoning.append("🎯 SIGNAL APPROVED FOR EXECUTION")
        else:
            reasoning.append("❌ SIGNAL REJECTED")
        
        return reasoning