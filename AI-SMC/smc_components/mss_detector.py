"""
Market Structure Shift (MSS) Detection Engine
Implements institutional-grade trend change identification with validation
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime

class MSSType(Enum):
    """Market Structure Shift type"""
    BULLISH_MSS = "BULLISH_MSS"   # Shift to bullish trend
    BEARISH_MSS = "BEARISH_MSS"   # Shift to bearish trend

class MSSStrength(Enum):
    """MSS strength classification"""
    MAJOR = "MAJOR"         # Strong trend shift with multiple confirmations
    INTERMEDIATE = "INTERMEDIATE"  # Moderate trend shift
    MINOR = "MINOR"         # Weak trend shift, needs more confirmation

@dataclass
class MSSSignal:
    """Market Structure Shift signal data structure"""
    timestamp: datetime
    type: MSSType
    break_level: float
    previous_trend: str
    new_trend: str
    strength: MSSStrength
    displacement_pips: float
    retest_count: int = 0
    volume_confirmation: bool = False
    momentum_score: float = 0.0
    confluence_factors: List[str] = None

class MSSDetector:
    """
    Advanced Market Structure Shift Detection Engine
    
    Implements institutional-grade MSS detection with:
    - Trend change identification  
    - Multi-swing validation
    - Retest analysis
    - Volume and momentum confirmation
    - Confluence tracking
    """
    
    def __init__(self,
                 swing_length: int = 15,
                 min_displacement_pips: float = 25.0,
                 trend_validation_swings: int = 3,
                 retest_tolerance_pips: float = 10.0):
        """
        Initialize MSS Detector
        
        Args:
            swing_length: Length for swing point detection
            min_displacement_pips: Minimum displacement for valid MSS
            trend_validation_swings: Number of swings needed for trend validation
            retest_tolerance_pips: Tolerance for retest validation
        """
        self.swing_length = swing_length
        self.min_displacement_pips = min_displacement_pips
        self.trend_validation_swings = trend_validation_swings
        self.retest_tolerance_pips = retest_tolerance_pips
        
    def detect_mss_signals(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> List[MSSSignal]:
        """
        Detect Market Structure Shift signals
        
        Args:
            df: OHLC DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            symbol: Symbol name for pip calculation
            
        Returns:
            List of detected MSS signals
        """
        if len(df) < self.swing_length * 5:
            return []
        
        mss_signals = []
        pip_size = self._get_pip_size(symbol)
        
        # Find swing points
        swing_highs = self._find_swing_highs(df)
        swing_lows = self._find_swing_lows(df)
        
        # Combine and sort swings
        all_swings = self._combine_swings(swing_highs, swing_lows)
        
        # Analyze trend changes
        for i in range(self.trend_validation_swings * 2, len(all_swings)):
            mss_signal = self._analyze_structure_shift(
                all_swings, i, df, pip_size
            )
            if mss_signal:
                mss_signals.append(mss_signal)
        
        # Post-process signals
        mss_signals = self._validate_retests(mss_signals, df, pip_size)
        mss_signals = self._add_volume_confirmation(mss_signals, df)
        mss_signals = self._calculate_momentum_scores(mss_signals, df)
        
        return mss_signals
    
    def _find_swing_highs(self, df: pd.DataFrame) -> List[Dict]:
        """Find swing high points"""
        swing_highs = []
        
        for i in range(self.swing_length, len(df) - self.swing_length):
            window_data = df.iloc[i-self.swing_length:i+self.swing_length+1]
            current_high = df.iloc[i]['High']
            
            if current_high == window_data['High'].max():
                swing_highs.append({
                    'timestamp': df.index[i],
                    'price': current_high,
                    'index': i,
                    'type': 'high'
                })
        
        return swing_highs
    
    def _find_swing_lows(self, df: pd.DataFrame) -> List[Dict]:
        """Find swing low points"""
        swing_lows = []
        
        for i in range(self.swing_length, len(df) - self.swing_length):
            window_data = df.iloc[i-self.swing_length:i+self.swing_length+1]
            current_low = df.iloc[i]['Low']
            
            if current_low == window_data['Low'].min():
                swing_lows.append({
                    'timestamp': df.index[i],
                    'price': current_low,
                    'index': i,
                    'type': 'low'
                })
        
        return swing_lows
    
    def _combine_swings(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> List[Dict]:
        """Combine and sort swing points chronologically"""
        all_swings = swing_highs + swing_lows
        all_swings.sort(key=lambda x: x['timestamp'])
        return all_swings
    
    def _analyze_structure_shift(self, all_swings: List[Dict], index: int,
                                df: pd.DataFrame, pip_size: float) -> Optional[MSSSignal]:
        """Analyze potential market structure shift at given swing index"""
        
        # Get recent swings for trend analysis
        recent_swings = all_swings[max(0, index - self.trend_validation_swings*2):index+1]
        
        if len(recent_swings) < self.trend_validation_swings * 2:
            return None
        
        # Determine previous trend
        prev_trend = self._determine_trend(recent_swings[:-1])
        
        # Check if current swing creates a structure shift
        current_swing = all_swings[index]
        shift_detected = False
        mss_type = None
        break_level = None
        
        if prev_trend == 'bearish' and current_swing['type'] == 'low':
            # Potential bullish MSS - need to break previous lower high
            prev_highs = [s for s in recent_swings if s['type'] == 'high']
            if prev_highs:
                prev_highs.sort(key=lambda x: x['timestamp'])
                potential_break_level = prev_highs[-1]['price']  # Most recent high
                
                # Check if price breaks above this level significantly
                future_high = self._get_future_extreme(df, current_swing['index'], 'high', 10)
                if future_high and (future_high - potential_break_level) / pip_size >= self.min_displacement_pips:
                    shift_detected = True
                    mss_type = MSSType.BULLISH_MSS
                    break_level = potential_break_level
        
        elif prev_trend == 'bullish' and current_swing['type'] == 'high':
            # Potential bearish MSS - need to break previous higher low
            prev_lows = [s for s in recent_swings if s['type'] == 'low']
            if prev_lows:
                prev_lows.sort(key=lambda x: x['timestamp'])
                potential_break_level = prev_lows[-1]['price']  # Most recent low
                
                # Check if price breaks below this level significantly
                future_low = self._get_future_extreme(df, current_swing['index'], 'low', 10)
                if future_low and (potential_break_level - future_low) / pip_size >= self.min_displacement_pips:
                    shift_detected = True
                    mss_type = MSSType.BEARISH_MSS
                    break_level = potential_break_level
        
        if not shift_detected:
            return None
        
        # Calculate displacement
        if mss_type == MSSType.BULLISH_MSS:
            displacement = (future_high - break_level) / pip_size
        else:
            displacement = (break_level - future_low) / pip_size
        
        # Determine new trend
        new_trend = 'bullish' if mss_type == MSSType.BULLISH_MSS else 'bearish'
        
        # Classify strength
        strength = self._classify_mss_strength(displacement, recent_swings)
        
        return MSSSignal(
            timestamp=current_swing['timestamp'],
            type=mss_type,
            break_level=break_level,
            previous_trend=prev_trend,
            new_trend=new_trend,
            strength=strength,
            displacement_pips=displacement,
            confluence_factors=[]
        )
    
    def _determine_trend(self, swings: List[Dict]) -> str:
        """Determine trend from swing sequence"""
        if len(swings) < 4:
            return 'ranging'
        
        highs = [s for s in swings if s['type'] == 'high']
        lows = [s for s in swings if s['type'] == 'low']
        
        if len(highs) < 2 or len(lows) < 2:
            return 'ranging'
        
        # Sort by time
        highs.sort(key=lambda x: x['timestamp'])
        lows.sort(key=lambda x: x['timestamp'])
        
        # Check for trend patterns
        recent_highs = highs[-2:]
        recent_lows = lows[-2:]
        
        higher_highs = recent_highs[1]['price'] > recent_highs[0]['price']
        higher_lows = recent_lows[1]['price'] > recent_lows[0]['price']
        
        lower_highs = recent_highs[1]['price'] < recent_highs[0]['price']
        lower_lows = recent_lows[1]['price'] < recent_lows[0]['price']
        
        if higher_highs and higher_lows:
            return 'bullish'
        elif lower_highs and lower_lows:
            return 'bearish'
        else:
            return 'ranging'
    
    def _get_future_extreme(self, df: pd.DataFrame, start_index: int,
                           extreme_type: str, lookforward: int) -> Optional[float]:
        """Get future high or low within lookforward bars"""
        end_index = min(start_index + lookforward + 1, len(df))
        future_data = df.iloc[start_index:end_index]
        
        if len(future_data) == 0:
            return None
        
        if extreme_type == 'high':
            return future_data['High'].max()
        else:
            return future_data['Low'].min()
    
    def _classify_mss_strength(self, displacement: float, recent_swings: List[Dict]) -> MSSStrength:
        """Classify MSS strength based on displacement and swing quality"""
        
        # Base classification on displacement
        if displacement >= 50:
            base_strength = MSSStrength.MAJOR
        elif displacement >= 35:
            base_strength = MSSStrength.INTERMEDIATE
        else:
            base_strength = MSSStrength.MINOR
        
        # Adjust based on swing quality (more swings = stronger confirmation)
        swing_count = len(recent_swings)
        if swing_count >= 8 and base_strength == MSSStrength.INTERMEDIATE:
            return MSSStrength.MAJOR
        elif swing_count >= 6 and base_strength == MSSStrength.MINOR:
            return MSSStrength.INTERMEDIATE
        
        return base_strength
    
    def _validate_retests(self, mss_signals: List[MSSSignal],
                         df: pd.DataFrame, pip_size: float) -> List[MSSSignal]:
        """Validate retests of MSS break levels"""
        
        for signal in mss_signals:
            signal_index = self._get_timestamp_index(df, signal.timestamp)
            if signal_index is None:
                continue
            
            # Look for retests in future data
            future_data = df.iloc[signal_index+1:]
            retest_tolerance = self.retest_tolerance_pips * pip_size
            
            retest_count = 0
            
            if signal.type == MSSType.BULLISH_MSS:
                # Look for retests of break level from above
                for _, candle in future_data.iterrows():
                    if (candle['Low'] <= signal.break_level + retest_tolerance and
                        candle['Close'] > signal.break_level):
                        retest_count += 1
            else:
                # Look for retests of break level from below
                for _, candle in future_data.iterrows():
                    if (candle['High'] >= signal.break_level - retest_tolerance and
                        candle['Close'] < signal.break_level):
                        retest_count += 1
            
            signal.retest_count = min(retest_count, 5)  # Cap at 5 retests
        
        return mss_signals
    
    def _add_volume_confirmation(self, mss_signals: List[MSSSignal],
                                df: pd.DataFrame) -> List[MSSSignal]:
        """Add volume confirmation analysis"""
        
        if 'Volume' not in df.columns:
            return mss_signals
        
        for signal in mss_signals:
            signal_index = self._get_timestamp_index(df, signal.timestamp)
            if signal_index is None:
                continue
            
            # Compare volume around MSS with historical average
            lookback_data = df.iloc[max(0, signal_index-20):signal_index]
            avg_volume = lookback_data['Volume'].mean()
            
            # Check volume in MSS period
            mss_period = df.iloc[signal_index:signal_index+3]
            mss_volume = mss_period['Volume'].mean()
            
            signal.volume_confirmation = mss_volume > avg_volume * 1.3
        
        return mss_signals
    
    def _calculate_momentum_scores(self, mss_signals: List[MSSSignal],
                                  df: pd.DataFrame) -> List[MSSSignal]:
        """Calculate momentum scores for MSS signals"""
        
        for signal in mss_signals:
            signal_index = self._get_timestamp_index(df, signal.timestamp)
            if signal_index is None:
                continue
            
            # Calculate momentum in subsequent bars
            momentum_period = df.iloc[signal_index:signal_index+5]
            if len(momentum_period) == 0:
                continue
            
            momentum_factors = []
            
            # Price momentum
            price_change = momentum_period.iloc[-1]['Close'] - momentum_period.iloc[0]['Close']
            if signal.type == MSSType.BULLISH_MSS:
                momentum_factors.append(1.0 if price_change > 0 else 0.3)
            else:
                momentum_factors.append(1.0 if price_change < 0 else 0.3)
            
            # Consecutive closes in direction
            consecutive_closes = 0
            for i in range(1, len(momentum_period)):
                prev_close = momentum_period.iloc[i-1]['Close']
                curr_close = momentum_period.iloc[i]['Close']
                
                if signal.type == MSSType.BULLISH_MSS and curr_close > prev_close:
                    consecutive_closes += 1
                elif signal.type == MSSType.BEARISH_MSS and curr_close < prev_close:
                    consecutive_closes += 1
                else:
                    break
            
            momentum_factors.append(min(1.0, consecutive_closes / 3))
            
            signal.momentum_score = np.mean(momentum_factors)
        
        return mss_signals
    
    def _get_timestamp_index(self, df: pd.DataFrame, timestamp: datetime) -> Optional[int]:
        """Get index for timestamp in DataFrame"""
        for i, ts in enumerate(df.index):
            if ts == timestamp:
                return i
        return None
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        jpy_pairs = ['JPY', 'jpy']
        if any(pair in symbol.upper() for pair in jpy_pairs):
            return 0.01
        else:
            return 0.0001
    
    def get_recent_mss_signals(self, mss_signals: List[MSSSignal],
                              lookback_bars: int = 100) -> List[MSSSignal]:
        """Get recent high-quality MSS signals"""
        if not mss_signals:
            return []
        
        # Sort by timestamp
        sorted_signals = sorted(mss_signals, key=lambda x: x.timestamp, reverse=True)
        
        # Filter for quality signals
        quality_signals = [
            signal for signal in sorted_signals
            if (signal.strength in [MSSStrength.MAJOR, MSSStrength.INTERMEDIATE] and
                signal.momentum_score >= 0.6)
        ]
        
        return quality_signals[:3]  # Return top 3 most recent quality signals
    
    def analyze_mss_confluence(self, mss_signals: List[MSSSignal]) -> Dict:
        """Analyze MSS confluence for trend bias"""
        recent_signals = self.get_recent_mss_signals(mss_signals)
        
        if not recent_signals:
            return {
                'trend_bias': 'neutral',
                'confluence_score': 0,
                'signal_count': 0,
                'dominant_trend': None
            }
        
        # Analyze trend bias
        bullish_count = sum(1 for s in recent_signals if s.type == MSSType.BULLISH_MSS)
        bearish_count = sum(1 for s in recent_signals if s.type == MSSType.BEARISH_MSS)
        
        if bullish_count > bearish_count:
            trend_bias = 'bullish'
            dominant_trend = 'bullish'
        elif bearish_count > bullish_count:
            trend_bias = 'bearish'
            dominant_trend = 'bearish'
        else:
            trend_bias = 'neutral'
            dominant_trend = None
        
        # Calculate confluence score
        strength_weights = {
            MSSStrength.MAJOR: 4.0,
            MSSStrength.INTERMEDIATE: 2.5,
            MSSStrength.MINOR: 1.0
        }
        
        confluence_score = sum(
            strength_weights[signal.strength] *
            (1 + signal.retest_count * 0.2) *
            (1.3 if signal.volume_confirmation else 1.0) *
            (1 + signal.momentum_score * 0.5)
            for signal in recent_signals
        )
        
        return {
            'trend_bias': trend_bias,
            'confluence_score': confluence_score,
            'signal_count': len(recent_signals),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'dominant_trend': dominant_trend,
            'strongest_signal': max(recent_signals, key=lambda x: x.displacement_pips) if recent_signals else None,
            'most_recent': recent_signals[0] if recent_signals else None,
            'avg_displacement': np.mean([s.displacement_pips for s in recent_signals]) if recent_signals else 0
        }