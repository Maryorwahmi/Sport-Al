"""
Market Structure Analysis Module
Detects swing highs/lows, Break of Structure (BOS), and Change of Character (CHOCH)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Market trend direction"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"


class StructureType(Enum):
    """Market structure types"""
    BOS = "break_of_structure"
    CHOCH = "change_of_character"
    SWING_HIGH = "swing_high"
    SWING_LOW = "swing_low"


@dataclass
class SwingPoint:
    """Represents a swing high or low point"""
    index: int
    price: float
    time: pd.Timestamp
    type: str  # 'high' or 'low'
    strength: int  # Number of bars on each side confirming the swing


@dataclass
class StructureBreak:
    """Represents a structure break (BOS or CHOCH)"""
    index: int
    price: float
    time: pd.Timestamp
    type: StructureType
    previous_trend: TrendDirection
    new_trend: TrendDirection
    strength: float


class MarketStructureAnalyzer:
    """
    Analyzes market structure to identify swing points, BOS, and CHOCH
    """
    
    def __init__(self, swing_strength: int = 3, structure_confirmation: int = 2):
        """
        Initialize market structure analyzer
        
        Args:
            swing_strength: Number of bars on each side to confirm swing point
            structure_confirmation: Number of bars to confirm structure break
        """
        self.swing_strength = swing_strength
        self.structure_confirmation = structure_confirmation
        
    def identify_swing_points(self, df: pd.DataFrame) -> List[SwingPoint]:
        """
        Identify swing highs and lows in price data
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of SwingPoint objects
        """
        swing_points = []
        
        if len(df) < (self.swing_strength * 2 + 1):
            return swing_points
            
        highs = df['high'].values
        lows = df['low'].values
        
        # Find swing highs
        for i in range(self.swing_strength, len(highs) - self.swing_strength):
            is_swing_high = True
            current_high = highs[i]
            
            # Check left side
            for j in range(i - self.swing_strength, i):
                if highs[j] >= current_high:
                    is_swing_high = False
                    break
                    
            # Check right side
            if is_swing_high:
                for j in range(i + 1, i + self.swing_strength + 1):
                    if highs[j] >= current_high:
                        is_swing_high = False
                        break
                        
            if is_swing_high:
                swing_points.append(SwingPoint(
                    index=i,
                    price=current_high,
                    time=df.index[i],
                    type='high',
                    strength=self.swing_strength
                ))
        
        # Find swing lows
        for i in range(self.swing_strength, len(lows) - self.swing_strength):
            is_swing_low = True
            current_low = lows[i]
            
            # Check left side
            for j in range(i - self.swing_strength, i):
                if lows[j] <= current_low:
                    is_swing_low = False
                    break
                    
            # Check right side
            if is_swing_low:
                for j in range(i + 1, i + self.swing_strength + 1):
                    if lows[j] <= current_low:
                        is_swing_low = False
                        break
                        
            if is_swing_low:
                swing_points.append(SwingPoint(
                    index=i,
                    price=current_low,
                    time=df.index[i],
                    type='low',
                    strength=self.swing_strength
                ))
        
        # Sort by index
        swing_points.sort(key=lambda x: x.index)
        return swing_points
    
    def determine_trend(self, swing_points: List[SwingPoint], lookback: int = 5) -> TrendDirection:
        """
        Determine current market trend based on swing points
        
        Args:
            swing_points: List of swing points
            lookback: Number of recent swings to analyze
            
        Returns:
            Current trend direction
        """
        if len(swing_points) < 4:
            return TrendDirection.SIDEWAYS
            
        recent_swings = swing_points[-lookback:] if len(swing_points) >= lookback else swing_points
        
        highs = [sp for sp in recent_swings if sp.type == 'high']
        lows = [sp for sp in recent_swings if sp.type == 'low']
        
        if len(highs) < 2 or len(lows) < 2:
            return TrendDirection.SIDEWAYS
        
        # Check for higher highs and higher lows (bullish trend)
        higher_highs = all(highs[i].price > highs[i-1].price for i in range(1, len(highs)))
        higher_lows = all(lows[i].price > lows[i-1].price for i in range(1, len(lows)))
        
        if higher_highs and higher_lows:
            return TrendDirection.BULLISH
        
        # Check for lower highs and lower lows (bearish trend)
        lower_highs = all(highs[i].price < highs[i-1].price for i in range(1, len(highs)))
        lower_lows = all(lows[i].price < lows[i-1].price for i in range(1, len(lows)))
        
        if lower_highs and lower_lows:
            return TrendDirection.BEARISH
            
        return TrendDirection.SIDEWAYS
    
    def detect_bos_choch(self, df: pd.DataFrame, swing_points: List[SwingPoint]) -> List[StructureBreak]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHOCH)
        
        Args:
            df: DataFrame with OHLC data
            swing_points: List of identified swing points
            
        Returns:
            List of structure breaks
        """
        structure_breaks = []
        
        if len(swing_points) < 3:
            return structure_breaks
            
        current_trend = TrendDirection.SIDEWAYS
        last_significant_high = None
        last_significant_low = None
        
        for i, swing in enumerate(swing_points):
            if swing.type == 'high':
                last_significant_high = swing
            else:
                last_significant_low = swing
                
            # Need at least 3 swing points to determine structure
            if i < 2:
                continue
                
            previous_trend = current_trend
            current_trend = self.determine_trend(swing_points[:i+1])
            
            # Detect structure breaks
            if previous_trend != TrendDirection.SIDEWAYS and current_trend != previous_trend:
                # This is a potential CHOCH
                structure_breaks.append(StructureBreak(
                    index=swing.index,
                    price=swing.price,
                    time=swing.time,
                    type=StructureType.CHOCH,
                    previous_trend=previous_trend,
                    new_trend=current_trend,
                    strength=self._calculate_break_strength(df, swing.index)
                ))
            
            elif current_trend != TrendDirection.SIDEWAYS:
                # Check for BOS in continuation of trend
                if current_trend == TrendDirection.BULLISH and last_significant_high:
                    # Look for break above previous high
                    recent_highs = df['high'].iloc[swing.index:swing.index + self.structure_confirmation]
                    if any(recent_highs > last_significant_high.price):
                        structure_breaks.append(StructureBreak(
                            index=swing.index,
                            price=last_significant_high.price,
                            time=swing.time,
                            type=StructureType.BOS,
                            previous_trend=current_trend,
                            new_trend=current_trend,
                            strength=self._calculate_break_strength(df, swing.index)
                        ))
                
                elif current_trend == TrendDirection.BEARISH and last_significant_low:
                    # Look for break below previous low
                    recent_lows = df['low'].iloc[swing.index:swing.index + self.structure_confirmation]
                    if any(recent_lows < last_significant_low.price):
                        structure_breaks.append(StructureBreak(
                            index=swing.index,
                            price=last_significant_low.price,
                            time=swing.time,
                            type=StructureType.BOS,
                            previous_trend=current_trend,
                            new_trend=current_trend,
                            strength=self._calculate_break_strength(df, swing.index)
                        ))
        
        return structure_breaks
    
    def _calculate_break_strength(self, df: pd.DataFrame, index: int) -> float:
        """
        Calculate the strength of a structure break
        
        Args:
            df: DataFrame with OHLC data
            index: Index of the break
            
        Returns:
            Strength score between 0 and 1
        """
        if index < 10 or index >= len(df) - 5:
            return 0.5
            
        # Calculate volume spike (if volume data available)
        volume_strength = 0.0
        if 'volume' in df.columns:
            current_vol = df['volume'].iloc[index]
            avg_vol = df['volume'].iloc[index-10:index].mean()
            volume_strength = min(current_vol / avg_vol / 2, 1.0) if avg_vol > 0 else 0.5
        
        # Calculate price movement strength
        price_range = abs(df['close'].iloc[index] - df['open'].iloc[index])
        avg_range = df['high'].iloc[index-10:index].subtract(df['low'].iloc[index-10:index]).mean()
        price_strength = min(price_range / avg_range, 1.0) if avg_range > 0 else 0.5
        
        # Calculate follow-through strength
        followthrough_strength = 0.5
        if index < len(df) - 5:
            future_closes = df['close'].iloc[index+1:index+6]
            current_close = df['close'].iloc[index]
            
            if len(future_closes) > 0:
                if current_close > df['open'].iloc[index]:  # Bullish break
                    followthrough = sum(1 for close in future_closes if close > current_close) / len(future_closes)
                else:  # Bearish break
                    followthrough = sum(1 for close in future_closes if close < current_close) / len(future_closes)
                followthrough_strength = followthrough
        
        # Combine all factors
        return (volume_strength * 0.3 + price_strength * 0.4 + followthrough_strength * 0.3)
    
    def analyze_structure(self, df: pd.DataFrame) -> Dict:
        """
        Perform complete market structure analysis
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary containing all structure analysis results
        """
        swing_points = self.identify_swing_points(df)
        current_trend = self.determine_trend(swing_points)
        structure_breaks = self.detect_bos_choch(df, swing_points)
        
        return {
            'swing_points': swing_points,
            'current_trend': current_trend,
            'structure_breaks': structure_breaks,
            'analysis_timestamp': pd.Timestamp.now(),
            'total_swings': len(swing_points),
            'total_structure_breaks': len(structure_breaks)
        }