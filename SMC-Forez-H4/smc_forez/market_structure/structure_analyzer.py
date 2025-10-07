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
    
    def __init__(self, swing_length: int = 20):
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
            
            if len(recent_highs_idx) < 3 or len(recent_lows_idx) < 3:
                return TrendDirection.CONSOLIDATION
            
            # More robust trend detection using sequence analysis
            recent_highs = df.loc[recent_highs_idx, 'High']
            recent_lows = df.loc[recent_lows_idx, 'Low']

            # Check for uptrend: 2 of last 3 highs are higher, and 2 of last 3 lows are higher
            is_higher_highs = (recent_highs.iloc[-1] > recent_highs.iloc[-2]) + \
                              (recent_highs.iloc[-2] > recent_highs.iloc[-3])
            is_higher_lows = (recent_lows.iloc[-1] > recent_lows.iloc[-2]) + \
                             (recent_lows.iloc[-2] > recent_lows.iloc[-3])

            if is_higher_highs >= 1 and is_higher_lows >= 1:
                logger.info("Trend detected: UPTREND (Higher Highs and Higher Lows sequence)")
                return TrendDirection.UPTREND

            # Check for downtrend: 2 of last 3 highs are lower, and 2 of last 3 lows are lower
            is_lower_highs = (recent_highs.iloc[-1] < recent_highs.iloc[-2]) + \
                             (recent_highs.iloc[-2] < recent_highs.iloc[-3])
            is_lower_lows = (recent_lows.iloc[-1] < recent_lows.iloc[-2]) + \
                            (recent_lows.iloc[-2] < recent_lows.iloc[-3])

            if is_lower_highs >= 1 and is_lower_lows >= 1:
                logger.info("Trend detected: DOWNTREND (Lower Highs and Lower Lows sequence)")
                return TrendDirection.DOWNTREND
            
            logger.info("Trend detected: CONSOLIDATION (No clear HH/HL or LH/LL sequence)")
            return TrendDirection.CONSOLIDATION
                
        except Exception as e:
            logger.error(f"Error identifying trend: {str(e)}")
            return TrendDirection.CONSOLIDATION
    
    def detect_structure_breaks(self, df: pd.DataFrame, swing_points: Dict[str, pd.Series], 
                              confirmation_candles: int = 2) -> List[Dict]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHOCH)
        Enhanced version with stronger confirmation requirements
        
        Args:
            df: DataFrame with OHLC data
            swing_points: Dictionary with swing highs and lows
            confirmation_candles: Number of candles for confirmation (increased default)
            
        Returns:
            List of dictionaries with structure break information
        """
        try:
            structure_breaks = []
            swing_highs = swing_points['swing_highs']
            swing_lows = swing_points['swing_lows']
            
            # Get swing high and low points
            high_points = df[swing_highs]['High']
            low_points = df[swing_lows]['Low']
            
            if high_points.empty or low_points.empty:
                return []

            # Use more recent swing points for relevance
            recent_high_points = high_points.tail(20)  # Last 20 swing highs
            recent_low_points = low_points.tail(20)   # Last 20 swing lows

            for i in range(confirmation_candles, len(df)):
                current_candle = df.iloc[i]
                current_high = current_candle['High']
                current_low = current_candle['Low']
                current_close = current_candle['Close']
                current_idx = df.index[i]

                # Find the most recent swing high/low before the current candle
                relevant_highs = recent_high_points[recent_high_points.index < current_idx]
                relevant_lows = recent_low_points[recent_low_points.index < current_idx]
                
                if relevant_highs.empty or relevant_lows.empty:
                    continue

                last_swing_high = relevant_highs.iloc[-1]
                last_swing_low = relevant_lows.iloc[-1]

                # Enhanced Bullish BOS detection with multiple confirmations
                if current_high > last_swing_high:
                    # Require close above the swing high for stronger confirmation
                    if current_close > last_swing_high:
                        # Check for momentum confirmation in previous candles
                        momentum_confirmed = True
                        if i >= confirmation_candles:
                            for j in range(1, confirmation_candles + 1):
                                prev_candle = df.iloc[i - j]
                                if prev_candle['Close'] <= prev_candle['Open']:  # Bearish candle
                                    momentum_confirmed = False
                                    break
                        
                        # Calculate strength based on how far above the swing high
                        strength = min((current_high - last_swing_high) / last_swing_high * 100, 1.0)
                        
                        # Volume confirmation if available
                        volume_confirmed = True
                        if 'Volume' in df.columns and df['Volume'].iloc[i] > 0:
                            avg_volume = df['Volume'].iloc[max(0, i-20):i].mean()
                            if avg_volume > 0 and df['Volume'].iloc[i] < avg_volume * 1.2:
                                volume_confirmed = False
                        
                        if momentum_confirmed and strength > 0.1:  # Minimum 10 pips break
                            structure_breaks.append({
                                'timestamp': current_idx,
                                'type': StructureType.BOS,
                                'direction': 'bullish',
                                'level': last_swing_high,
                                'break_price': current_high,
                                'close_price': current_close,
                                'strength': strength,
                                'momentum_confirmed': momentum_confirmed,
                                'volume_confirmed': volume_confirmed,
                                'quality': 'high' if momentum_confirmed and volume_confirmed and strength > 0.3 else 'medium'
                            })

                # Enhanced Bearish BOS detection with multiple confirmations
                if current_low < last_swing_low:
                    # Require close below the swing low for stronger confirmation
                    if current_close < last_swing_low:
                        # Check for momentum confirmation in previous candles
                        momentum_confirmed = True
                        if i >= confirmation_candles:
                            for j in range(1, confirmation_candles + 1):
                                prev_candle = df.iloc[i - j]
                                if prev_candle['Close'] >= prev_candle['Open']:  # Bullish candle
                                    momentum_confirmed = False
                                    break
                        
                        # Calculate strength based on how far below the swing low
                        strength = min((last_swing_low - current_low) / last_swing_low * 100, 1.0)
                        
                        # Volume confirmation if available
                        volume_confirmed = True
                        if 'Volume' in df.columns and df['Volume'].iloc[i] > 0:
                            avg_volume = df['Volume'].iloc[max(0, i-20):i].mean()
                            if avg_volume > 0 and df['Volume'].iloc[i] < avg_volume * 1.2:
                                volume_confirmed = False
                        
                        if momentum_confirmed and strength > 0.1:  # Minimum 10 pips break
                            structure_breaks.append({
                                'timestamp': current_idx,
                                'type': StructureType.BOS,
                                'direction': 'bearish',
                                'level': last_swing_low,
                                'break_price': current_low,
                                'close_price': current_close,
                                'strength': strength,
                                'momentum_confirmed': momentum_confirmed,
                                'volume_confirmed': volume_confirmed,
                                'quality': 'high' if momentum_confirmed and volume_confirmed and strength > 0.3 else 'medium'
                            })
            
            # Filter for high-quality structure breaks only
            quality_breaks = [sb for sb in structure_breaks if sb.get('quality') == 'high' and sb.get('strength', 0) > 0.2]
            
            logger.info(f"Detected {len(quality_breaks)}/{len(structure_breaks)} high-quality structure breaks")
            return quality_breaks
            
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
            
            # Calculate trend strength based on swing progression
            trend_strength = 0.7  # Default strength for detected trends
            
            if trend in [TrendDirection.UPTREND, TrendDirection.DOWNTREND]:
                # Enhanced trend strength calculation based on swing quality
                if len(swing_highs_levels) >= 3 and len(swing_lows_levels) >= 3:
                    # Calculate progression strength
                    recent_highs = swing_highs_levels[-3:]
                    recent_lows = swing_lows_levels[-3:]
                    
                    if trend == TrendDirection.UPTREND:
                        # Check consistency of higher highs and higher lows
                        hh_strength = (recent_highs[-1] > recent_highs[-2]) and (recent_highs[-2] > recent_highs[-3])
                        hl_strength = (recent_lows[-1] > recent_lows[-2]) and (recent_lows[-2] > recent_lows[-3])
                        trend_strength = 0.8 if (hh_strength and hl_strength) else 0.6
                    else:  # DOWNTREND
                        # Check consistency of lower highs and lower lows
                        lh_strength = (recent_highs[-1] < recent_highs[-2]) and (recent_highs[-2] < recent_highs[-3])
                        ll_strength = (recent_lows[-1] < recent_lows[-2]) and (recent_lows[-2] < recent_lows[-3])
                        trend_strength = 0.8 if (lh_strength and ll_strength) else 0.6
            
            return {
                'swing_points': swing_points,
                'trend_direction': trend,  # Fixed: renamed from 'trend' to 'trend_direction'
                'trend_strength': trend_strength,  # Added: missing trend_strength field
                'structure_breaks': structure_breaks,
                'swing_high_levels': swing_highs_levels,
                'swing_low_levels': swing_lows_levels,
                'current_price': df['Close'].iloc[-1],
                'analysis_timestamp': df.index[-1]
            }
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {str(e)}")
            return {}