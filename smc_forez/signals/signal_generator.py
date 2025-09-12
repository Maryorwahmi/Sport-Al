"""
Signal generation system that combines market structure and Smart Money Concepts
to identify high-probability trading opportunities
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from enum import Enum
import logging
from ..market_structure.structure_analyzer import TrendDirection, StructureType
from ..smart_money.smc_analyzer import ZoneType, OrderBlockType


logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    WAIT = "wait"


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


class ConfluenceFactor(Enum):
    TREND_ALIGNMENT = "trend_alignment"
    STRUCTURE_BREAK = "structure_break"
    ORDER_BLOCK = "order_block"
    LIQUIDITY_ZONE = "liquidity_zone"
    FAIR_VALUE_GAP = "fair_value_gap"
    SUPPLY_DEMAND = "supply_demand"


class SignalGenerator:
    """Enhanced signal generator with 70%+ quality standards and specialized entry logic"""
    
    def __init__(self, min_confluence_factors: int = 3, min_rr_ratio: float = 2.5, 
                 enhanced_mode: bool = True):
        """
        Initialize enhanced signal generator
        
        Args:
            min_confluence_factors: Minimum number of confluence factors required (ENHANCED to 3)
            min_rr_ratio: Minimum risk/reward ratio for signals (ENHANCED to 2.5)
            enhanced_mode: Enable enhanced signal generation with quality analysis
        """
        self.min_confluence_factors = min_confluence_factors
        self.min_rr_ratio = min_rr_ratio
        self.enhanced_mode = enhanced_mode
        self.pattern_validators = self._initialize_pattern_validators()
        
    def _initialize_pattern_validators(self) -> Dict:
        """Initialize pattern validation methods"""
        return {
            'breakout': self._validate_breakout_pattern,
            'bos': self._validate_bos_pattern,  
            'reversal': self._validate_reversal_pattern,
            'trend_continuation': self._validate_trend_pattern
        }
    
    def _validate_breakout_pattern(self, market_structure: Dict, smc_analysis: Dict) -> Dict:
        """Validate breakout pattern with waiting logic"""
        validation = {'valid': False, 'confidence': 0.0, 'entry_type': 'breakout'}
        
        # Check for structure break with volume confirmation
        structure_breaks = market_structure.get('structure_breaks', [])
        if not structure_breaks:
            return validation
            
        latest_break = structure_breaks[-1]
        break_strength = latest_break.get('strength', 0.0)
        
        # Require strong break with potential retest setup
        if break_strength >= 0.75:
            validation.update({
                'valid': True,
                'confidence': break_strength,
                'entry_strategy': 'wait_for_retest',
                'structure_break': latest_break
            })
            
        return validation
    
    def _validate_bos_pattern(self, market_structure: Dict, smc_analysis: Dict) -> Dict:
        """Validate Break of Structure (BOS) pattern"""
        validation = {'valid': False, 'confidence': 0.0, 'entry_type': 'bos'}
        
        # Look for confirmed BOS with order block presence
        bos_signals = market_structure.get('bos_signals', [])
        order_blocks = smc_analysis.get('order_blocks', {}).get('valid', [])
        
        if bos_signals and order_blocks:
            latest_bos = bos_signals[-1]
            bos_confidence = latest_bos.get('confidence', 0.0)
            
            # Require high confidence BOS with nearby order block
            if bos_confidence >= 0.8:
                validation.update({
                    'valid': True,
                    'confidence': bos_confidence,
                    'entry_strategy': 'bos_confirmation',
                    'bos_signal': latest_bos,
                    'supporting_blocks': len(order_blocks)
                })
                
        return validation
    
    def _validate_reversal_pattern(self, market_structure: Dict, smc_analysis: Dict) -> Dict:
        """Validate reversal pattern with liquidity zones"""
        validation = {'valid': False, 'confidence': 0.0, 'entry_type': 'reversal'}
        
        # Check for liquidity sweep and reversal signals
        liquidity_zones = smc_analysis.get('liquidity_zones', [])
        swing_points = market_structure.get('swing_points', {})
        
        if liquidity_zones and swing_points:
            # Look for recent liquidity sweep with reversal setup
            recent_sweep = any(lz.get('swept', False) for lz in liquidity_zones[-3:])
            
            if recent_sweep:
                # Check for confluence with swing point rejection
                swing_highs = swing_points.get('swing_highs', pd.Series())
                swing_lows = swing_points.get('swing_lows', pd.Series())
                
                if not swing_highs.empty or not swing_lows.empty:
                    validation.update({
                        'valid': True,
                        'confidence': 0.85,  # High confidence for liquidity reversal
                        'entry_strategy': 'reversal_confirmation',
                        'liquidity_sweep': True
                    })
                    
        return validation
    
    def _validate_trend_pattern(self, market_structure: Dict, smc_analysis: Dict) -> Dict:
        """Validate trend continuation pattern"""
        validation = {'valid': False, 'confidence': 0.0, 'entry_type': 'trend'}
        
        # Check for strong trend with pullback to demand/supply
        trend = market_structure.get('trend_direction', TrendDirection.CONSOLIDATION)
        trend_strength = market_structure.get('trend_strength', 0.0)
        
        if trend != TrendDirection.CONSOLIDATION and trend_strength >= 0.7:
            # Look for demand/supply zones aligned with trend
            zones = smc_analysis.get('supply_demand_zones', [])
            aligned_zones = [z for z in zones if z.get('trend_aligned', False)]
            
            if aligned_zones:
                validation.update({
                    'valid': True,
                    'confidence': trend_strength,
                    'entry_strategy': 'trend_pullback',
                    'trend_direction': trend.value,
                    'aligned_zones': len(aligned_zones)
                })
                
        return validation
        self.pattern_validators = self._initialize_pattern_validators()
        
    def calculate_confluence_score(self, market_structure: Dict, smc_analysis: Dict,
                                  current_price: float) -> Dict:
        """
        Enhanced confluence calculation with pattern validation and 70%+ standards
        
        Args:
            market_structure: Market structure analysis results
            smc_analysis: Smart Money Concepts analysis results
            current_price: Current market price
            
        Returns:
            Dictionary with confluence factors and enhanced scores
        """
        confluence_factors = []
        total_score = 0
        pattern_validations = {}
        
        try:
            # Enhanced Factor 1: Trend Alignment (Higher weight)
            trend = market_structure.get('trend_direction', TrendDirection.CONSOLIDATION)
            trend_strength = market_structure.get('trend_strength', 0.0)
            
            if trend == TrendDirection.UPTREND and trend_strength >= 0.7:
                confluence_factors.append({
                    'factor': ConfluenceFactor.TREND_ALIGNMENT,
                    'direction': 'bullish',
                    'score': 3,  # ENHANCED scoring
                    'strength': trend_strength
                })
                total_score += 3
            elif trend == TrendDirection.DOWNTREND and trend_strength >= 0.7:
                confluence_factors.append({
                    'factor': ConfluenceFactor.TREND_ALIGNMENT,
                    'direction': 'bearish', 
                    'score': 3,  # ENHANCED scoring
                    'strength': trend_strength
                })
                total_score += 3
            
            # Enhanced Factor 2: Pattern Validation
            for pattern_type, validator in self.pattern_validators.items():
                validation = validator(market_structure, smc_analysis)
                pattern_validations[pattern_type] = validation
                
                if validation['valid'] and validation['confidence'] >= 0.75:
                    confluence_factors.append({
                        'factor': f'PATTERN_{pattern_type.upper()}',
                        'direction': self._get_pattern_direction(validation),
                        'score': 4,  # HIGH score for valid patterns
                        'confidence': validation['confidence']
                    })
                    total_score += 4
            
            # Enhanced Factor 3: Structure Breaks with confirmation
            structure_breaks = market_structure.get('structure_breaks', [])
            recent_breaks = [sb for sb in structure_breaks 
                           if sb.get('timestamp') and sb.get('confirmed', False)]
            if recent_breaks:
                latest_break = recent_breaks[-1]
                break_strength = latest_break.get('strength', 0.0)
                
                if break_strength >= 0.8:  # ENHANCED threshold
                    confluence_factors.append({
                        'factor': ConfluenceFactor.STRUCTURE_BREAK,
                        'direction': latest_break.get('direction', 'neutral'),
                        'score': 3,  # ENHANCED scoring
                        'strength': break_strength
                    })
                    total_score += 3
            
            # Enhanced Factor 4: Order Blocks with quality filtering
            order_blocks = smc_analysis.get('order_blocks', {}).get('valid', [])
            high_quality_obs = []
            
            for ob in order_blocks:
                ob_top = ob.get('top', 0)
                ob_bottom = ob.get('bottom', 0)
                ob_strength = ob.get('strength', 0.0)
                
                # Enhanced distance and quality check
                distance_to_ob = min(abs(current_price - ob_top), abs(current_price - ob_bottom))
                if (distance_to_ob <= current_price * 0.0015 and  # Within 0.15%
                    ob_strength >= 0.75):  # High quality only
                    high_quality_obs.append(ob)
            
            if high_quality_obs:
                for ob in high_quality_obs[:2]:  # Limit to top 2 for quality
                    direction = 'bullish' if ob['type'] == OrderBlockType.BULLISH else 'bearish'
                    confluence_factors.append({
                        'factor': ConfluenceFactor.ORDER_BLOCK,
                        'direction': direction,
                        'score': 3,  # ENHANCED scoring
                        'strength': ob.get('strength', 0.0)
                    })
                    total_score += 3
            
            # Enhanced Factor 5: Liquidity Zones with sweep confirmation
            liquidity_zones = smc_analysis.get('liquidity_zones', [])
            swept_zones = [lz for lz in liquidity_zones if lz.get('swept', False)]
            
            if swept_zones:
                for zone in swept_zones[-2:]:  # Recent sweeps only
                    zone_strength = zone.get('strength', 0.0)
                    if zone_strength >= 0.8:
                        confluence_factors.append({
                            'factor': ConfluenceFactor.LIQUIDITY_ZONE,
                            'direction': zone.get('direction', 'neutral'),
                            'score': 2,
                            'strength': zone_strength
                        })
                        total_score += 2
            
            # Enhanced Factor 6: Fair Value Gaps with quality filter
            fvgs = smc_analysis.get('fair_value_gaps', [])
            quality_fvgs = [fvg for fvg in fvgs 
                          if fvg.get('size', 0) >= 5.0 and fvg.get('unfilled', True)]
            
            if quality_fvgs:
                for fvg in quality_fvgs[-1:]:  # Most recent quality FVG
                    confluence_factors.append({
                        'factor': ConfluenceFactor.FAIR_VALUE_GAP,
                        'direction': fvg.get('direction', 'neutral'),
                        'score': 1,
                        'size': fvg.get('size', 0)
                    })
                    total_score += 1
            
            # Calculate final confluence metrics
            num_factors = len(confluence_factors)
            avg_score = total_score / max(1, num_factors)
            
            return {
                'factors': confluence_factors,
                'total_score': total_score,
                'num_factors': num_factors,
                'avg_score': avg_score,
                'pattern_validations': pattern_validations,
                'meets_threshold': num_factors >= self.min_confluence_factors and avg_score >= 2.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating confluence score: {str(e)}")
            return {
                'factors': [],
                'total_score': 0,
                'num_factors': 0,
                'avg_score': 0.0,
                'pattern_validations': {},
                'meets_threshold': False
            }
    
    def _get_pattern_direction(self, validation: Dict) -> str:
        """Get direction from pattern validation"""
        entry_type = validation.get('entry_type', '')
        
        # Default direction based on pattern type and context
        if 'bos' in entry_type and validation.get('bos_signal', {}).get('direction'):
            return validation['bos_signal']['direction']
        elif 'trend' in entry_type and validation.get('trend_direction'):
            return validation['trend_direction']
        elif validation.get('structure_break', {}).get('direction'):
            return validation['structure_break']['direction']
        else:
            return 'neutral'
            
    def generate_signal(self, market_structure: Dict, smc_analysis: Dict,
                       current_price: float, timeframe: Optional = None) -> Dict:
        """
        Enhanced signal generation with 70%+ quality standards
        
        Args:
            market_structure: Market structure analysis results
            smc_analysis: Smart Money Concepts analysis results
            current_price: Current market price
            timeframe: Optional timeframe for enhanced analysis
            
        Returns:
            Dictionary with enhanced signal information
        """
        try:
            # Calculate enhanced confluence
            confluence = self.calculate_confluence_score(market_structure, smc_analysis, current_price)
            
            # Enhanced signal direction analysis
            bullish_factors = [cf for cf in confluence['factors'] if cf.get('direction') == 'bullish']
            bearish_factors = [cf for cf in confluence['factors'] if cf.get('direction') == 'bearish']
            
            bullish_score = sum(cf['score'] for cf in bullish_factors)
            bearish_score = sum(cf['score'] for cf in bearish_factors)
            
            # Enhanced signal determination with pattern validation
            signal_type = SignalType.WAIT
            signal_strength = SignalStrength.WEAK
            entry_strategy = None
            
            # Check if meets enhanced threshold requirements
            if confluence['meets_threshold']:
                # Determine direction with enhanced criteria
                score_difference = abs(bullish_score - bearish_score)
                dominant_score = max(bullish_score, bearish_score)
                
                if dominant_score >= 6 and score_difference >= 3:  # ENHANCED thresholds
                    if bullish_score > bearish_score:
                        signal_type = SignalType.BUY
                        entry_strategy = self._determine_entry_strategy(bullish_factors, confluence['pattern_validations'])
                    else:
                        signal_type = SignalType.SELL
                        entry_strategy = self._determine_entry_strategy(bearish_factors, confluence['pattern_validations'])
                    
                    # Enhanced strength determination
                    if dominant_score >= 12 and confluence['avg_score'] >= 3.0:
                        signal_strength = SignalStrength.VERY_STRONG
                    elif dominant_score >= 9 and confluence['avg_score'] >= 2.5:
                        signal_strength = SignalStrength.STRONG
                    elif dominant_score >= 6 and confluence['avg_score'] >= 2.0:
                        signal_strength = SignalStrength.MODERATE
                    else:
                        signal_strength = SignalStrength.WEAK
            
            # Enhanced risk/reward calculation
            entry_details = self._calculate_enhanced_entry_details(
                signal_type, current_price, confluence, market_structure, smc_analysis
            )
            
            return {
                'signal_type': signal_type,
                'signal_strength': signal_strength,
                'entry_strategy': entry_strategy,
                'confluence_score': confluence['num_factors'],
                'confluence_quality': confluence['avg_score'],
                'total_score': confluence['total_score'],
                'pattern_validations': confluence['pattern_validations'],
                'entry_details': entry_details,
                'valid': signal_type != SignalType.WAIT and entry_details.get('risk_reward_ratio', 0) >= self.min_rr_ratio,
                'analysis_quality': self._assess_analysis_quality(confluence),
                'timeframe': timeframe.value if timeframe else 'UNKNOWN'
            }
            
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return {
                'signal_type': SignalType.WAIT,
                'signal_strength': SignalStrength.WEAK,
                'confluence_score': 0,
                'valid': False,
                'error': str(e)
            }
    
    def _determine_entry_strategy(self, dominant_factors: List[Dict], pattern_validations: Dict) -> str:
        """Determine the best entry strategy based on confluence factors and patterns"""
        factor_types = [cf['factor'] for cf in dominant_factors]
        
        # Check for specific pattern-based strategies
        for pattern_type, validation in pattern_validations.items():
            if validation['valid'] and validation['confidence'] >= 0.75:
                return validation.get('entry_strategy', f'{pattern_type}_entry')
        
        # Fallback to factor-based strategy
        if 'STRUCTURE_BREAK' in factor_types:
            return 'breakout_retest'
        elif ConfluenceFactor.ORDER_BLOCK in factor_types:
            return 'orderblock_rejection'
        elif ConfluenceFactor.LIQUIDITY_ZONE in factor_types:
            return 'liquidity_sweep'
        else:
            return 'confluence_entry'
    
    def _calculate_enhanced_entry_details(self, signal_type: SignalType, current_price: float,
                                        confluence: Dict, market_structure: Dict, smc_analysis: Dict) -> Dict:
        """Calculate enhanced entry details with improved risk management"""
        if signal_type == SignalType.WAIT:
            return {}
        
        # Enhanced stop loss calculation
        stop_loss = self._calculate_enhanced_stop_loss(signal_type, current_price, confluence, market_structure)
        
        # Enhanced take profit calculation  
        take_profit = self._calculate_enhanced_take_profit(signal_type, current_price, stop_loss, confluence)
        
        # Risk/reward calculation
        if signal_type == SignalType.BUY:
            risk = current_price - stop_loss
            reward = take_profit - current_price
        else:
            risk = stop_loss - current_price
            reward = current_price - take_profit
        
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        return {
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'risk_pips': round(abs(risk) * 10000, 1),  # Assuming 4-digit pairs
            'reward_pips': round(abs(reward) * 10000, 1)
        }
    
    def _calculate_enhanced_stop_loss(self, signal_type: SignalType, current_price: float,
                                    confluence: Dict, market_structure: Dict) -> float:
        """Calculate enhanced stop loss based on market structure"""
        # Use swing points for structural stop loss
        swing_points = market_structure.get('swing_points', {})
        
        if signal_type == SignalType.BUY:
            swing_lows = swing_points.get('swing_lows', pd.Series())
            if not swing_lows.empty:
                recent_low = swing_lows.iloc[-1] if len(swing_lows) > 0 else current_price * 0.999
                return recent_low - (current_price * 0.0005)  # 5 pip buffer
            else:
                return current_price * 0.998  # 2% default
        else:
            swing_highs = swing_points.get('swing_highs', pd.Series())
            if not swing_highs.empty:
                recent_high = swing_highs.iloc[-1] if len(swing_highs) > 0 else current_price * 1.001
                return recent_high + (current_price * 0.0005)  # 5 pip buffer
            else:
                return current_price * 1.002  # 2% default
    
    def _calculate_enhanced_take_profit(self, signal_type: SignalType, current_price: float,
                                      stop_loss: float, confluence: Dict) -> float:
        """Calculate enhanced take profit based on confluence quality"""
        base_risk = abs(current_price - stop_loss)
        
        # Enhanced RR based on confluence quality
        if confluence['avg_score'] >= 3.0:
            rr_multiplier = 3.5  # Very high quality
        elif confluence['avg_score'] >= 2.5:
            rr_multiplier = 3.0  # High quality
        elif confluence['avg_score'] >= 2.0:
            rr_multiplier = 2.5  # Good quality
        else:
            rr_multiplier = 2.0  # Minimum quality
        
        reward = base_risk * rr_multiplier
        
        if signal_type == SignalType.BUY:
            return current_price + reward
        else:
            return current_price - reward
    
    def _assess_analysis_quality(self, confluence: Dict) -> str:
        """Assess the overall quality of the analysis"""
        score = confluence['avg_score']
        factors = confluence['num_factors']
        
        if score >= 3.0 and factors >= 4:
            return "INSTITUTIONAL"
        elif score >= 2.5 and factors >= 3:
            return "PROFESSIONAL"
        elif score >= 2.0 and factors >= 3:
            return "STANDARD"
        else:
            return "BELOW_STANDARD"