#!/usr/bin/env python3
"""
Enhanced Signal Quality Filter
Adds comprehensive quality filtering to ensure only premium signals are executed
"""

from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SignalQuality(Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    POOR = "POOR"

class EnhancedSignalQualityFilter:
    """
    Comprehensive signal quality filter with multiple validation layers
    """
    
    def __init__(self, 
                 min_confluence_score: float = 3.0,
                 min_strength_factors: int = 3,
                 min_rr_ratio: float = 2.5,
                 min_timeframe_agreement: float = 0.66,
                 min_trend_confidence: float = 0.7,
                 require_smc_confluence: bool = True):
        """
        Initialize quality filter with configurable parameters
        
        Args:
            min_confluence_score: Minimum confluence score required
            min_strength_factors: Minimum number of strength factors
            min_rr_ratio: Minimum risk-reward ratio
            min_timeframe_agreement: Minimum timeframe trend agreement (0.66 = 2/3)
            min_trend_confidence: Minimum trend confidence score
            require_smc_confluence: Whether SMC confluence is required
        """
        self.min_confluence_score = min_confluence_score
        self.min_strength_factors = min_strength_factors
        self.min_rr_ratio = min_rr_ratio
        self.min_timeframe_agreement = min_timeframe_agreement
        self.min_trend_confidence = min_trend_confidence
        self.require_smc_confluence = require_smc_confluence
        
    def evaluate_signal_quality(self, signal: Dict) -> tuple[SignalQuality, float, List[str]]:
        """
        Evaluate comprehensive signal quality
        
        Returns:
            (quality_level, quality_score, quality_issues)
        """
        issues = []
        quality_points = 0
        max_points = 10
        
        analysis = signal.get('analysis', {})
        symbol = signal.get('symbol', 'UNKNOWN')
        
        # == INDUSTRIAL GRADE UPGRADE: Market Bias Alignment Check (CRITICAL) ==
        # This is the new rule: the signal MUST align with the H4/H1 bias.
        market_bias = signal.get('market_bias')
        signal_type_str = str(signal.get('signal_type', ''))
        
        if market_bias == 'BULLISH' and 'buy' in signal_type_str.lower():
            quality_points += 2  # Strong alignment
        elif market_bias == 'BEARISH' and 'sell' in signal_type_str.lower():
            quality_points += 2  # Strong alignment
        elif market_bias in ['NEUTRAL', 'CONFLICT']:
            issues.append(f"Signal generated in a {market_bias} market bias.")
            # No points, but not an immediate failure, other factors might make it valid
        else:
            # Instead of immediate failure, allow degraded confidence for bias mismatches
            issues.append(f"CAUTION: Signal direction ({signal_type_str}) conflicts with market bias ({market_bias}).")
            quality_points *= 0.3  # Heavily penalize but don't reject outright
        
        # 1. Direction Validation (CRITICAL)
        direction_valid = self._validate_direction(signal)
        if direction_valid:
            quality_points += 2
        else:
            # Don't immediately reject for SL/TP issues - allow low confidence
            issues.append("Invalid SL/TP direction - Low confidence")
            quality_points *= 0.1  # Heavy penalty but not complete rejection
        
        # 2. Risk-Reward Ratio
        rr_ratio = signal.get('risk_reward_ratio', 0)
        if rr_ratio is not None and rr_ratio >= self.min_rr_ratio:
            quality_points += 1
        elif rr_ratio is not None and rr_ratio >= 2.0:
            quality_points += 0.5
        else:
            issues.append(f"Poor R:R ratio ({rr_ratio if rr_ratio is not None else 'N/A'}:1)")
        
        # 3. Confluence Analysis - Fix data extraction
        confluence_score = signal.get('confluence_score', 0)
        
        # If confluence_score is 0, try to extract from signal_confluence data structure
        if confluence_score == 0:
            signal_confluence_data = signal.get('signal_confluence', {})
            if isinstance(signal_confluence_data, dict):
                # Extract from signal_scores in the confluence data
                signal_scores = signal_confluence_data.get('signal_scores', {})
                if signal_scores:
                    # Get the total confluence score from buy/sell scores
                    buy_score = signal_scores.get('buy', 0)
                    sell_score = signal_scores.get('sell', 0)
                    confluence_score = max(buy_score, sell_score)  # Take the dominant signal score
        
        if confluence_score >= self.min_confluence_score:
            quality_points += 1.5
        elif confluence_score >= 2.0:
            quality_points += 1
        else:
            issues.append(f"Low confluence score ({confluence_score})")
        
        # 4. Strength Factors
        strength_factors = signal.get('strength_factors', [])  # Fix: Get strength factors directly from signal
        if len(strength_factors) >= self.min_strength_factors:
            quality_points += 1
        elif len(strength_factors) >= 2:
            quality_points += 0.5
        else:
            issues.append(f"Insufficient strength factors ({len(strength_factors)})")
        
        # 5. Trend Analysis - Fix data extraction from signal_confluence
        trend_aligned = signal.get('trend_aligned', False)
        signal_confluence = signal.get('signal_confluence', False)
        
        # If trend_aligned is False, try to extract from signal_confluence data structure
        if not trend_aligned:
            signal_confluence_data = signal.get('signal_confluence', {})
            if isinstance(signal_confluence_data, dict):
                # Check if we have confluence (3 TFs aligned)
                confluence_count = signal_confluence_data.get('confluence_count', 0)
                has_confluence = signal_confluence_data.get('has_confluence', False)
                if confluence_count >= 3 or has_confluence:
                    trend_aligned = True
                    signal_confluence = True
        
        if trend_aligned and signal_confluence:
            quality_points += 1.5
        elif trend_aligned or signal_confluence:
            quality_points += 1
        else:
            issues.append("No trend alignment or signal confluence")
        
        # 6. Multi-Timeframe Agreement - Extract from signal_confluence data structure
        confluence_count = 0
        signal_confluence_data = signal.get('signal_confluence', {})
        
        if isinstance(signal_confluence_data, dict):
            confluence_count = signal_confluence_data.get('confluence_count', 0)
        
        # Get recommendation data for later use
        recommendation = signal.get('analysis', {}).get('recommendation', {})
        
        # Fallback: try to get from recommendation data
        if confluence_count == 0:
            confluence_count = recommendation.get('confluence_count', 0)
        
        if confluence_count >= 3:
            quality_points += 1
        elif confluence_count >= 2:
            quality_points += 0.5
        else:
            issues.append(f"Insufficient timeframe agreement ({confluence_count}/3 TFs)")
        
        # 7. Market Structure Quality - Calculate from signal's recommendation data
        analysis_data = signal.get('analysis', {})
        recommendation = signal.get('recommendation', analysis_data.get('recommendation', {}))
        
        # Try multiple sources for confidence
        trend_confidence = (
            recommendation.get('confidence_score', 0) or  # First priority: confidence_score from recommendation
            analysis_data.get('trend_confidence', 0) or   # Second priority: analysis trend_confidence  
            signal.get('trend_confidence', 0)             # Third priority: signal level trend_confidence
        )
        
        # If still no confidence found, calculate from confluence and timeframe alignment
        if trend_confidence == 0:
            confluence_count = recommendation.get('confluence_count', 0)
            trend_aligned = recommendation.get('trend_aligned', False)
            
            # Calculate confidence based on confluence and alignment
            if confluence_count >= 3 and trend_aligned:
                trend_confidence = 0.9  # High confidence for perfect alignment
            elif confluence_count >= 2 and trend_aligned:
                trend_confidence = 0.8  # Good confidence
            elif trend_aligned:
                trend_confidence = 0.7  # Moderate confidence
            else:
                trend_confidence = 0.4  # Low confidence
        
        # Handle both percentage (0-100) and decimal (0-1) formats
        if trend_confidence > 1.0:
            trend_confidence = trend_confidence / 100.0
        
        if trend_confidence >= self.min_trend_confidence:
            quality_points += 1
        elif trend_confidence >= 0.5:
            quality_points += 0.5
        else:
            issues.append(f"Poor market structure quality (confidence: {trend_confidence:.1%})")
        
        # 8. SMC Component Quality - Get from signal's recommendation
        strength_factors = signal.get('strength_factors', [])
        # Count SMC components mentioned in strength factors
        smc_mentions = sum(1 for factor in strength_factors if any(
            keyword in factor.lower() for keyword in ['ob', 'order block', 'fvg', 'fair value', 'liquidity', 'structure']
        ))
        
        if smc_mentions >= 3:
            quality_points += 1
        elif smc_mentions >= 2:
            quality_points += 0.5
        else:
            issues.append(f"Low SMC component density ({smc_mentions} mentions)")
        
        # 9. Confidence Level - Get from signal data (check both fields)
        confidence = signal.get('confidence', signal.get('recommendation_confidence', 'LOW'))
        # Use the recommendation already defined above
        confidence_score = recommendation.get('confidence_score', 0)
        
        if confidence in ['HIGH', 'VERY_HIGH'] and confidence_score >= 0.8:
            quality_points += 0.5
        elif confidence in ['HIGH', 'MODERATE', 'MEDIUM']:  # FIXED: Accept MEDIUM as valid
            quality_points += 0.25
        else:
            issues.append(f"Low confidence ({confidence})")
        
        # Calculate final quality score with safety check
        final_score = quality_points / (max_points + 2) if (max_points + 2) > 0 else 0.0
        
        # Determine quality level - add None check for safety
        if final_score is not None and final_score >= 0.85:
            quality_level = SignalQuality.EXCELLENT
        elif final_score is not None and final_score >= 0.70:
            quality_level = SignalQuality.GOOD
        elif final_score is not None and final_score >= 0.50:
            quality_level = SignalQuality.MODERATE
        else:
            quality_level = SignalQuality.POOR
        
        return quality_level, final_score, issues
    
    def _validate_direction(self, signal: Dict) -> bool:
        """Validate SL/TP direction is correct with enhanced debugging"""
        signal_type_raw = signal.get('signal_type', '')
        
        # Handle both enum and string signal types
        if hasattr(signal_type_raw, 'value'):
            signal_type = signal_type_raw.value.lower()  # Convert enum to lowercase string
        elif isinstance(signal_type_raw, str):
            signal_type = signal_type_raw.lower()
        else:
            signal_type = str(signal_type_raw).lower()
            
        entry = signal.get('entry_price', 0)
        sl = signal.get('stop_loss', 0)
        tp = signal.get('take_profit', 0)
        
        # Round to 5 decimal places to avoid floating point precision issues
        entry_rounded = round(entry, 5) if entry else 0
        sl_rounded = round(sl, 5) if sl else 0
        tp_rounded = round(tp, 5) if tp else 0
        
        logger.debug(f"🔍 SL/TP Validation: {str(signal_type).upper()} - Entry:{entry_rounded}, SL:{sl_rounded}, TP:{tp_rounded}")
        
        if signal_type == 'buy':
            valid = sl_rounded < entry_rounded < tp_rounded
            if not valid:
                logger.warning(f"❌ BUY validation failed: SL({sl_rounded}) < Entry({entry_rounded}) < TP({tp_rounded}) = {sl_rounded < entry_rounded < tp_rounded}")
            return valid
        elif signal_type == 'sell':
            valid = tp_rounded < entry_rounded < sl_rounded
            if not valid:
                logger.warning(f"❌ SELL validation failed: TP({tp_rounded}) < Entry({entry_rounded}) < SL({sl_rounded}) = {tp_rounded < entry_rounded < sl_rounded}")
            return valid
        elif signal_type == 'wait':
            # WAIT signals are inherently valid but shouldn't be executed
            return True
        
        logger.warning(f"❌ Unknown signal type: {signal_type}")
        return False
    
    def should_execute_signal(self, signal: Dict) -> tuple[bool, str]:
        """
        Enhanced signal execution decision with nuanced outcomes
        
        Returns:
            (should_execute, reason)
        """
        quality_level, quality_score, issues = self.evaluate_signal_quality(signal)
        symbol = signal.get('symbol', 'UNKNOWN')
        signal_type = signal.get('signal_type', 'UNKNOWN')
        
        # Check for specific issue types to provide nuanced decisions
        has_bias_conflict = any("conflicts with market bias" in issue for issue in issues)
        has_sltp_issue = any("Invalid SL/TP direction" in issue for issue in issues)
        
        if quality_level == SignalQuality.EXCELLENT:
            return True, f"{symbol}: EXCELLENT quality ({quality_score:.1%}) - EXECUTE"
        
        elif quality_level == SignalQuality.GOOD:
            return True, f"{symbol}: GOOD quality ({quality_score:.1%}) - EXECUTE"
        
        elif quality_level == SignalQuality.MODERATE:
            # Additional checks for moderate signals
            rr_ratio = signal.get('risk_reward_ratio', 0)
            confidence = signal.get('recommendation_confidence', 'LOW')
            
            if rr_ratio is not None and rr_ratio >= 3.0 and confidence == 'HIGH':
                return True, f"{symbol}: MODERATE quality but high R:R and confidence - EXECUTE"
            elif has_bias_conflict:
                return False, f"{symbol}: WAIT - Bias mismatch during consolidation"
            else:
                return False, f"{symbol}: WAIT - Moderate quality with additional concerns"
        
        else:
            # Poor quality - provide specific feedback
            if has_bias_conflict and not has_sltp_issue:
                return False, f"{symbol}: WAIT - Signal conflicts with market bias"
            elif has_sltp_issue and not has_bias_conflict:
                return False, f"{symbol}: LOW_CONFIDENCE_{str(signal_type).upper()} - SL/TP validation failed"
            else:
                return False, f"{symbol}: REJECT - Multiple quality issues: {'; '.join(issues[:2])}"
    
    def filter_signals(self, signals: List[Dict]) -> tuple[List[Dict], List[str]]:
        """
        Filter list of signals and return only high-quality ones
        
        Returns:
            (approved_signals, rejection_reasons)
        """
        approved_signals = []
        rejection_reasons = []
        
        for signal in signals:
            should_execute, reason = self.should_execute_signal(signal)
            
            if should_execute:
                approved_signals.append(signal)
                logger.info(f"✅ APPROVED: {reason}")
            else:
                rejection_reasons.append(reason)
                logger.warning(f"❌ REJECTED: {reason}")
        
        return approved_signals, rejection_reasons

# Global instance with conservative settings for live trading
LIVE_TRADING_FILTER = EnhancedSignalQualityFilter(
    min_confluence_score=3.0,
    min_strength_factors=3,
    min_rr_ratio=2.5,
    min_timeframe_agreement=0.66,
    min_trend_confidence=0.7,
    require_smc_confluence=True
)