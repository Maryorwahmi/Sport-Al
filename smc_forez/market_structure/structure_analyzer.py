"""
Market structure analysis for detecting swing points, trends, and structural changes
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    CONSOLIDATION = "consolidation"


class StructureType(Enum):
    BOS = "break_of_structure"  # Break of Structure
    CHOCH = "change_of_character"  # Change of Character


class MarketStructureAnalyzer:
    """Analyzes market structure including swings, trends, and structural changes"""
    
    def __init__(self, swing_length: int = 10):
        """
        Initialize market structure analyzer
        
        Args:
            swing_length: Number of bars to look for swing highs/lows
        """
        self.swing_length = swing_length
        
    def find_swing_points(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Find swing highs and lows in the data
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with 'swing_highs' and 'swing_lows' Series
        """
        try:
            high_col = df['High']
            low_col = df['Low']
            
            # Find swing highs
            swing_highs = pd.Series(index=df.index, dtype=bool)
            swing_highs.iloc[:] = False
            
            # Find swing lows
            swing_lows = pd.Series(index=df.index, dtype=bool)
            swing_lows.iloc[:] = False
            
            for i in range(self.swing_length, len(df) - self.swing_length):
                # Check for swing high
                current_high = high_col.iloc[i]
                left_highs = high_col.iloc[i - self.swing_length:i]
                right_highs = high_col.iloc[i + 1:i + self.swing_length + 1]
                
                if (current_high > left_highs.max()) and (current_high > right_highs.max()):
                    swing_highs.iloc[i] = True
                
                # Check for swing low
                current_low = low_col.iloc[i]
                left_lows = low_col.iloc[i - self.swing_length:i]
                right_lows = low_col.iloc[i + 1:i + self.swing_length + 1]
                
                if (current_low < left_lows.min()) and (current_low < right_lows.min()):
                    swing_lows.iloc[i] = True
            
            logger.info(f"Found {swing_highs.sum()} swing highs and {swing_lows.sum()} swing lows")
            
            return {
                'swing_highs': swing_highs,
                'swing_lows': swing_lows
            }
            
        except Exception as e:
            logger.error(f"Error finding swing points: {str(e)}")
            return {'swing_highs': pd.Series(dtype=bool), 'swing_lows': pd.Series(dtype=bool)}
    
    def identify_trend_direction(self, df: pd.DataFrame, swing_points: Dict[str, pd.Series]) -> TrendDirection:
        """
        Identify the current trend direction based on swing points
        
        Args:
            df: DataFrame with OHLC data
            swing_points: Dictionary with swing highs and lows
            
        Returns:
            TrendDirection enum
        """
        try:
            swing_highs = swing_points['swing_highs']
            swing_lows = swing_points['swing_lows']
            
            # Get recent swing points (last 5 of each type)
            recent_highs_idx = df[swing_highs].tail(5).index
            recent_lows_idx = df[swing_lows].tail(5).index
            
            if len(recent_highs_idx) < 2 or len(recent_lows_idx) < 2:
                return TrendDirection.CONSOLIDATION
            
            # Check if highs are making higher highs
            recent_highs = df.loc[recent_highs_idx, 'High']
            higher_highs = recent_highs.iloc[-1] > recent_highs.iloc[-2]
            
            # Check if lows are making higher lows
            recent_lows = df.loc[recent_lows_idx, 'Low']
            higher_lows = recent_lows.iloc[-1] > recent_lows.iloc[-2]
            
            # Check if highs are making lower highs
            lower_highs = recent_highs.iloc[-1] < recent_highs.iloc[-2]
            
            # Check if lows are making lower lows
            lower_lows = recent_lows.iloc[-1] < recent_lows.iloc[-2]
            
            # Determine trend
            if higher_highs and higher_lows:
                return TrendDirection.UPTREND
            elif lower_highs and lower_lows:
                return TrendDirection.DOWNTREND
            else:
                return TrendDirection.CONSOLIDATION
                
        except Exception as e:
            logger.error(f"Error identifying trend direction: {str(e)}")
            return TrendDirection.CONSOLIDATION
    
    def detect_structure_breaks(self, df: pd.DataFrame, swing_points: Dict[str, pd.Series], 
                              confirmation_candles: int = 3) -> List[Dict]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHOCH)
        
        Args:
            df: DataFrame with OHLC data
            swing_points: Dictionary with swing highs and lows
            confirmation_candles: Number of candles for confirmation
            
        Returns:
            List of dictionaries with structure break information
        """
        try:
            structure_breaks = []
            swing_highs = swing_points['swing_highs']
            swing_lows = swing_points['swing_lows']
            
            # Get swing high and low points
            high_points = df[swing_highs][['High']].copy()
            low_points = df[swing_lows][['Low']].copy()
            
            # Detect BOS (Break of Structure)
            # BOS occurs when price breaks a significant high or low with momentum
            
            for i in range(len(df) - confirmation_candles):
                current_idx = df.index[i]
                current_high = df.iloc[i]['High']
                current_low = df.iloc[i]['Low']
                
                # Check for bullish BOS (break above previous swing high)
                if len(high_points) > 0:
                    prev_swing_high = high_points[high_points.index < current_idx]
                    if len(prev_swing_high) > 0:
                        last_swing_high = prev_swing_high.iloc[-1]['High']
                        
                        if current_high > last_swing_high:
                            # Confirm with next candles
                            confirmation_high = df.iloc[i:i + confirmation_candles]['High'].max()
                            if confirmation_high >= current_high:
                                structure_breaks.append({
                                    'timestamp': current_idx,
                                    'type': StructureType.BOS,
                                    'direction': 'bullish',
                                    'level': last_swing_high,
                                    'break_price': current_high
                                })
                
                # Check for bearish BOS (break below previous swing low)
                if len(low_points) > 0:
                    prev_swing_low = low_points[low_points.index < current_idx]
                    if len(prev_swing_low) > 0:
                        last_swing_low = prev_swing_low.iloc[-1]['Low']
                        
                        if current_low < last_swing_low:
                            # Confirm with next candles
                            confirmation_low = df.iloc[i:i + confirmation_candles]['Low'].min()
                            if confirmation_low <= current_low:
                                structure_breaks.append({
                                    'timestamp': current_idx,
                                    'type': StructureType.BOS,
                                    'direction': 'bearish',
                                    'level': last_swing_low,
                                    'break_price': current_low
                                })
            
            logger.info(f"Detected {len(structure_breaks)} structure breaks")
            return structure_breaks
            
        except Exception as e:
            logger.error(f"Error detecting structure breaks: {str(e)}")
            return []
    
    def get_market_structure_levels(self, df: pd.DataFrame) -> Dict:
        """
        Get comprehensive market structure analysis
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with complete market structure information
        """
        try:
            # Find swing points
            swing_points = self.find_swing_points(df)
            
            # Identify trend direction
            trend = self.identify_trend_direction(df, swing_points)
            
            # Detect structure breaks
            structure_breaks = self.detect_structure_breaks(df, swing_points)
            
            # Get key levels
            swing_highs_levels = df[swing_points['swing_highs']]['High'].tolist()
            swing_lows_levels = df[swing_points['swing_lows']]['Low'].tolist()
            
            return {
                'swing_points': swing_points,
                'trend_direction': trend,
                'structure_breaks': structure_breaks,
                'swing_high_levels': swing_highs_levels,
                'swing_low_levels': swing_lows_levels,
                'current_price': df['Close'].iloc[-1],
                'analysis_timestamp': df.index[-1]
            }
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {str(e)}")
            return {}