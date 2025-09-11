"""
Signal Generator Module
Generates limit entry signals based on trend, structure, and liquidity confluence
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .market_structure import TrendDirection, StructureBreak, StructureType
from .liquidity_zones import LiquidityZone, OrderBlock, FairValueGap, ZoneType

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class TradingSignal:
    """Represents a trading signal"""
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: List[float]
    risk_reward_ratio: float
    confidence: float
    timestamp: pd.Timestamp
    confluence_factors: List[str]
    timeframe: str
    symbol: str
    
    @property
    def risk_amount(self) -> float:
        """Calculate risk amount in pips/points"""
        return abs(self.entry_price - self.stop_loss)
    
    @property
    def reward_amount(self) -> float:
        """Calculate reward amount for first target"""
        if self.take_profit:
            return abs(self.take_profit[0] - self.entry_price)
        return 0.0


class SignalGenerator:
    """
    Generates trading signals based on Smart Money Concepts confluence
    """
    
    def __init__(self, 
                 min_rr_ratio: float = 1.5,
                 min_confluence: int = 3,
                 max_risk_percentage: float = 2.0):
        """
        Initialize signal generator
        
        Args:
            min_rr_ratio: Minimum risk-reward ratio for valid signals
            min_confluence: Minimum number of confluence factors required
            max_risk_percentage: Maximum risk as percentage of account
        """
        self.min_rr_ratio = min_rr_ratio
        self.min_confluence = min_confluence
        self.max_risk_percentage = max_risk_percentage
        
    def generate_signals(self,
                        df: pd.DataFrame,
                        trend: TrendDirection,
                        structure_breaks: List[StructureBreak],
                        order_blocks: List[OrderBlock],
                        supply_demand_zones: List[LiquidityZone],
                        fair_value_gaps: List[FairValueGap],
                        symbol: str,
                        timeframe: str) -> List[TradingSignal]:
        """
        Generate trading signals based on all analysis components
        
        Args:
            df: DataFrame with OHLC data
            trend: Current market trend
            structure_breaks: List of structure breaks
            order_blocks: List of order blocks
            supply_demand_zones: List of supply/demand zones
            fair_value_gaps: List of FVGs
            symbol: Currency pair symbol
            timeframe: Chart timeframe
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        current_price = df['close'].iloc[-1]
        
        # Generate bullish signals
        if trend in [TrendDirection.BULLISH, TrendDirection.SIDEWAYS]:
            bullish_signals = self._generate_bullish_signals(
                df, current_price, structure_breaks, order_blocks,
                supply_demand_zones, fair_value_gaps, symbol, timeframe
            )
            signals.extend(bullish_signals)
        
        # Generate bearish signals
        if trend in [TrendDirection.BEARISH, TrendDirection.SIDEWAYS]:
            bearish_signals = self._generate_bearish_signals(
                df, current_price, structure_breaks, order_blocks,
                supply_demand_zones, fair_value_gaps, symbol, timeframe
            )
            signals.extend(bearish_signals)
        
        # Filter signals by confluence and quality
        filtered_signals = self._filter_signals(signals)
        
        return filtered_signals
    
    def _generate_bullish_signals(self,
                                 df: pd.DataFrame,
                                 current_price: float,
                                 structure_breaks: List[StructureBreak],
                                 order_blocks: List[OrderBlock],
                                 supply_demand_zones: List[LiquidityZone],
                                 fair_value_gaps: List[FairValueGap],
                                 symbol: str,
                                 timeframe: str) -> List[TradingSignal]:
        """Generate bullish trading signals"""
        signals = []
        
        # Look for bullish order blocks below current price
        for ob in order_blocks:
            if ob.is_bullish and ob.high < current_price:
                confluence_factors = ["bullish_order_block"]
                
                # Check for additional confluence
                confluence_score = self._calculate_confluence(
                    ob.low, ob.high, structure_breaks, supply_demand_zones, 
                    fair_value_gaps, "bullish"
                )
                
                confluence_factors.extend(confluence_score['factors'])
                
                if len(confluence_factors) >= self.min_confluence:
                    # Calculate entry, stop loss, and take profit
                    entry_price = ob.high  # Buy limit at top of order block
                    stop_loss = ob.low - (ob.high - ob.low) * 0.1  # Below order block
                    
                    # Calculate take profits based on nearby resistance levels
                    take_profits = self._calculate_take_profits(
                        entry_price, "bullish", supply_demand_zones, fair_value_gaps
                    )
                    
                    if take_profits:
                        rr_ratio = abs(take_profits[0] - entry_price) / abs(entry_price - stop_loss)
                        
                        if rr_ratio >= self.min_rr_ratio:
                            confidence = min(confluence_score['score'] * ob.strength, 1.0)
                            
                            signals.append(TradingSignal(
                                signal_type=SignalType.BUY_LIMIT,
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                take_profit=take_profits,
                                risk_reward_ratio=rr_ratio,
                                confidence=confidence,
                                timestamp=pd.Timestamp.now(),
                                confluence_factors=confluence_factors,
                                timeframe=timeframe,
                                symbol=symbol
                            ))
        
        # Look for bullish demand zones
        for zone in supply_demand_zones:
            if (zone.zone_type == ZoneType.DEMAND_ZONE and 
                zone.is_active and 
                zone.bottom < current_price < zone.top * 1.1):
                
                confluence_factors = ["demand_zone"]
                
                confluence_score = self._calculate_confluence(
                    zone.bottom, zone.top, structure_breaks, supply_demand_zones,
                    fair_value_gaps, "bullish"
                )
                
                confluence_factors.extend(confluence_score['factors'])
                
                if len(confluence_factors) >= self.min_confluence:
                    entry_price = zone.top
                    stop_loss = zone.bottom - (zone.top - zone.bottom) * 0.2
                    
                    take_profits = self._calculate_take_profits(
                        entry_price, "bullish", supply_demand_zones, fair_value_gaps
                    )
                    
                    if take_profits:
                        rr_ratio = abs(take_profits[0] - entry_price) / abs(entry_price - stop_loss)
                        
                        if rr_ratio >= self.min_rr_ratio:
                            confidence = confluence_score['score'] * 0.8
                            
                            signals.append(TradingSignal(
                                signal_type=SignalType.BUY_LIMIT,
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                take_profit=take_profits,
                                risk_reward_ratio=rr_ratio,
                                confidence=confidence,
                                timestamp=pd.Timestamp.now(),
                                confluence_factors=confluence_factors,
                                timeframe=timeframe,
                                symbol=symbol
                            ))
        
        # Look for bullish FVG opportunities
        for fvg in fair_value_gaps:
            if (fvg.is_bullish and 
                not fvg.filled and 
                fvg.bottom < current_price < fvg.top * 1.05):
                
                confluence_factors = ["bullish_fvg"]
                
                confluence_score = self._calculate_confluence(
                    fvg.bottom, fvg.top, structure_breaks, supply_demand_zones,
                    fair_value_gaps, "bullish"
                )
                
                confluence_factors.extend(confluence_score['factors'])
                
                if len(confluence_factors) >= self.min_confluence:
                    entry_price = fvg.top
                    stop_loss = fvg.bottom - (fvg.top - fvg.bottom) * 0.1
                    
                    take_profits = self._calculate_take_profits(
                        entry_price, "bullish", supply_demand_zones, fair_value_gaps
                    )
                    
                    if take_profits:
                        rr_ratio = abs(take_profits[0] - entry_price) / abs(entry_price - stop_loss)
                        
                        if rr_ratio >= self.min_rr_ratio:
                            confidence = confluence_score['score'] * fvg.strength
                            
                            signals.append(TradingSignal(
                                signal_type=SignalType.BUY_LIMIT,
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                take_profit=take_profits,
                                risk_reward_ratio=rr_ratio,
                                confidence=confidence,
                                timestamp=pd.Timestamp.now(),
                                confluence_factors=confluence_factors,
                                timeframe=timeframe,
                                symbol=symbol
                            ))
        
        return signals
    
    def _generate_bearish_signals(self,
                                 df: pd.DataFrame,
                                 current_price: float,
                                 structure_breaks: List[StructureBreak],
                                 order_blocks: List[OrderBlock],
                                 supply_demand_zones: List[LiquidityZone],
                                 fair_value_gaps: List[FairValueGap],
                                 symbol: str,
                                 timeframe: str) -> List[TradingSignal]:
        """Generate bearish trading signals"""
        signals = []
        
        # Look for bearish order blocks above current price
        for ob in order_blocks:
            if not ob.is_bullish and ob.low > current_price:
                confluence_factors = ["bearish_order_block"]
                
                confluence_score = self._calculate_confluence(
                    ob.low, ob.high, structure_breaks, supply_demand_zones,
                    fair_value_gaps, "bearish"
                )
                
                confluence_factors.extend(confluence_score['factors'])
                
                if len(confluence_factors) >= self.min_confluence:
                    entry_price = ob.low  # Sell limit at bottom of order block
                    stop_loss = ob.high + (ob.high - ob.low) * 0.1  # Above order block
                    
                    take_profits = self._calculate_take_profits(
                        entry_price, "bearish", supply_demand_zones, fair_value_gaps
                    )
                    
                    if take_profits:
                        rr_ratio = abs(entry_price - take_profits[0]) / abs(stop_loss - entry_price)
                        
                        if rr_ratio >= self.min_rr_ratio:
                            confidence = min(confluence_score['score'] * ob.strength, 1.0)
                            
                            signals.append(TradingSignal(
                                signal_type=SignalType.SELL_LIMIT,
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                take_profit=take_profits,
                                risk_reward_ratio=rr_ratio,
                                confidence=confidence,
                                timestamp=pd.Timestamp.now(),
                                confluence_factors=confluence_factors,
                                timeframe=timeframe,
                                symbol=symbol
                            ))
        
        # Look for bearish supply zones
        for zone in supply_demand_zones:
            if (zone.zone_type == ZoneType.SUPPLY_ZONE and 
                zone.is_active and 
                zone.bottom * 0.9 < current_price < zone.top):
                
                confluence_factors = ["supply_zone"]
                
                confluence_score = self._calculate_confluence(
                    zone.bottom, zone.top, structure_breaks, supply_demand_zones,
                    fair_value_gaps, "bearish"
                )
                
                confluence_factors.extend(confluence_score['factors'])
                
                if len(confluence_factors) >= self.min_confluence:
                    entry_price = zone.bottom
                    stop_loss = zone.top + (zone.top - zone.bottom) * 0.2
                    
                    take_profits = self._calculate_take_profits(
                        entry_price, "bearish", supply_demand_zones, fair_value_gaps
                    )
                    
                    if take_profits:
                        rr_ratio = abs(entry_price - take_profits[0]) / abs(stop_loss - entry_price)
                        
                        if rr_ratio >= self.min_rr_ratio:
                            confidence = confluence_score['score'] * 0.8
                            
                            signals.append(TradingSignal(
                                signal_type=SignalType.SELL_LIMIT,
                                entry_price=entry_price,
                                stop_loss=stop_loss,
                                take_profit=take_profits,
                                risk_reward_ratio=rr_ratio,
                                confidence=confidence,
                                timestamp=pd.Timestamp.now(),
                                confluence_factors=confluence_factors,
                                timeframe=timeframe,
                                symbol=symbol
                            ))
        
        return signals
    
    def _calculate_confluence(self,
                            zone_bottom: float,
                            zone_top: float,
                            structure_breaks: List[StructureBreak],
                            supply_demand_zones: List[LiquidityZone],
                            fair_value_gaps: List[FairValueGap],
                            direction: str) -> Dict:
        """
        Calculate confluence score for a given zone
        
        Args:
            zone_bottom: Bottom of the zone
            zone_top: Top of the zone
            structure_breaks: List of structure breaks
            supply_demand_zones: List of supply/demand zones
            fair_value_gaps: List of FVGs
            direction: "bullish" or "bearish"
            
        Returns:
            Dictionary with confluence score and factors
        """
        factors = []
        score = 0.0
        
        # Check for structure breaks in the area
        for sb in structure_breaks[-5:]:  # Recent structure breaks
            if zone_bottom <= sb.price <= zone_top:
                if direction == "bullish" and sb.type == StructureType.CHOCH:
                    factors.append("bullish_choch")
                    score += 0.3
                elif direction == "bearish" and sb.type == StructureType.CHOCH:
                    factors.append("bearish_choch")
                    score += 0.3
                elif sb.type == StructureType.BOS:
                    factors.append("bos_confluence")
                    score += 0.2
        
        # Check for overlapping zones
        overlapping_zones = 0
        for zone in supply_demand_zones:
            if not zone.is_active:
                continue
                
            # Check if zones overlap
            if (zone.bottom <= zone_top and zone.top >= zone_bottom):
                overlapping_zones += 1
                if direction == "bullish" and zone.zone_type == ZoneType.DEMAND_ZONE:
                    factors.append("demand_zone_confluence")
                    score += 0.25
                elif direction == "bearish" and zone.zone_type == ZoneType.SUPPLY_ZONE:
                    factors.append("supply_zone_confluence")
                    score += 0.25
        
        # Check for FVG confluence
        for fvg in fair_value_gaps:
            if fvg.filled:
                continue
                
            if (fvg.bottom <= zone_top and fvg.top >= zone_bottom):
                if direction == "bullish" and fvg.is_bullish:
                    factors.append("bullish_fvg_confluence")
                    score += 0.2
                elif direction == "bearish" and not fvg.is_bullish:
                    factors.append("bearish_fvg_confluence")
                    score += 0.2
        
        # Add Fibonacci level confluence (simplified)
        zone_mid = (zone_top + zone_bottom) / 2
        # In a real implementation, you would calculate Fibonacci retracements
        # from recent swing highs/lows and check for confluence
        
        return {
            'score': min(score, 1.0),
            'factors': factors
        }
    
    def _calculate_take_profits(self,
                               entry_price: float,
                               direction: str,
                               supply_demand_zones: List[LiquidityZone],
                               fair_value_gaps: List[FairValueGap]) -> List[float]:
        """
        Calculate take profit levels based on nearby zones and levels
        
        Args:
            entry_price: Entry price for the trade
            direction: "bullish" or "bearish"
            supply_demand_zones: List of supply/demand zones
            fair_value_gaps: List of FVGs
            
        Returns:
            List of take profit levels
        """
        take_profits = []
        
        if direction == "bullish":
            # Look for supply zones above entry for take profits
            potential_targets = []
            
            for zone in supply_demand_zones:
                if (zone.zone_type == ZoneType.SUPPLY_ZONE and 
                    zone.is_active and 
                    zone.bottom > entry_price):
                    potential_targets.append(zone.bottom)
            
            # Look for bearish FVGs above entry
            for fvg in fair_value_gaps:
                if not fvg.is_bullish and not fvg.filled and fvg.bottom > entry_price:
                    potential_targets.append(fvg.bottom)
            
            # Sort targets by proximity
            potential_targets.sort()
            
            # Select first 2-3 targets
            for i, target in enumerate(potential_targets[:3]):
                if target > entry_price * 1.005:  # Minimum 0.5% profit
                    take_profits.append(target)
            
        else:  # bearish
            # Look for demand zones below entry for take profits
            potential_targets = []
            
            for zone in supply_demand_zones:
                if (zone.zone_type == ZoneType.DEMAND_ZONE and 
                    zone.is_active and 
                    zone.top < entry_price):
                    potential_targets.append(zone.top)
            
            # Look for bullish FVGs below entry
            for fvg in fair_value_gaps:
                if fvg.is_bullish and not fvg.filled and fvg.top < entry_price:
                    potential_targets.append(fvg.top)
            
            # Sort targets by proximity (descending for bearish)
            potential_targets.sort(reverse=True)
            
            # Select first 2-3 targets
            for i, target in enumerate(potential_targets[:3]):
                if target < entry_price * 0.995:  # Minimum 0.5% profit
                    take_profits.append(target)
        
        # If no specific targets found, use risk-based targets
        if not take_profits:
            if direction == "bullish":
                take_profits = [
                    entry_price * 1.01,  # 1% profit
                    entry_price * 1.02,  # 2% profit
                    entry_price * 1.03   # 3% profit
                ]
            else:
                take_profits = [
                    entry_price * 0.99,  # 1% profit
                    entry_price * 0.98,  # 2% profit
                    entry_price * 0.97   # 3% profit
                ]
        
        return take_profits
    
    def _filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filter signals based on quality and confluence requirements
        
        Args:
            signals: List of trading signals
            
        Returns:
            Filtered list of high-quality signals
        """
        filtered_signals = []
        
        for signal in signals:
            # Check minimum confluence requirement
            if len(signal.confluence_factors) < self.min_confluence:
                continue
            
            # Check minimum risk-reward ratio
            if signal.risk_reward_ratio < self.min_rr_ratio:
                continue
            
            # Check minimum confidence level
            if signal.confidence < 0.4:  # 40% minimum confidence
                continue
            
            # Check for reasonable risk amount
            if signal.risk_amount == 0:
                continue
            
            filtered_signals.append(signal)
        
        # Sort by confidence (highest first)
        filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return filtered_signals
    
    def format_signal_output(self, signal: TradingSignal) -> str:
        """
        Format trading signal for output display
        
        Args:
            signal: TradingSignal object
            
        Returns:
            Formatted string representation
        """
        signal_direction = "BUY" if "BUY" in signal.signal_type.value.upper() else "SELL"
        
        output = f"""
=== {signal_direction} SIGNAL ===
Symbol: {signal.symbol}
Timeframe: {signal.timeframe}
Signal Type: {signal.signal_type.value.upper()}
Entry Price: {signal.entry_price:.5f}
Stop Loss: {signal.stop_loss:.5f}
Take Profits: {', '.join([f'{tp:.5f}' for tp in signal.take_profit])}
Risk/Reward: {signal.risk_reward_ratio:.2f}
Confidence: {signal.confidence:.2%}
Risk Amount: {signal.risk_amount:.5f} points
Confluence Factors: {', '.join(signal.confluence_factors)}
Timestamp: {signal.timestamp}
"""
        return output