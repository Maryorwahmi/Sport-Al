"""
Change of Character (CHoCH) Detection Engine
Implements institutional-grade market structure break detection with confirmation
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime

class MarketStructure(Enum):
    """Market structure classification"""
    BULLISH = "BULLISH"     # Higher highs and higher lows
    BEARISH = "BEARISH"     # Lower highs and lower lows
    RANGING = "RANGING"     # No clear trend

class CHoCHType(Enum):
    """Change of Character type"""
    BULLISH_CHOCH = "BULLISH_CHOCH"   # Break from bearish to bullish
    BEARISH_CHOCH = "BEARISH_CHOCH"   # Break from bullish to bearish

class CHoCHStrength(Enum):
    """CHoCH strength classification"""
    STRONG = "STRONG"         # Clear break with displacement
    MODERATE = "MODERATE"     # Confirmed break, moderate displacement
    WEAK = "WEAK"            # Minimal break, needs more confirmation

@dataclass
class CHoCHSignal:
    """Change of Character signal data structure"""
    timestamp: datetime
    type: CHoCHType
    break_level: float
    previous_structure: MarketStructure
    new_structure: MarketStructure
    strength: CHoCHStrength
    displacement_pips: float
    confirmation_count: int = 0
    volume_confirmation: bool = False
    follow_through: bool = False
    confluence_factors: List[str] = None

class CHoCHDetector:
    """
    Advanced Change of Character Detection Engine
    
    Implements institutional-grade CHoCH detection with:
    - Market structure break identification
    - Displacement validation
    - Confirmation requirements
    - Volume analysis
    - Follow-through tracking
    """
    
    def __init__(self,
                 swing_length: int = 10,
                 min_displacement_pips: float = 15.0,
                 confirmation_bars: int = 3,
                 volume_threshold_multiplier: float = 1.2):
        """
        Initialize CHoCH Detector
        
        Args:
            swing_length: Length for swing point detection
            min_displacement_pips: Minimum displacement for valid CHoCH
            confirmation_bars: Bars needed for confirmation
            volume_threshold_multiplier: Volume multiplier for confirmation
        """
        self.swing_length = swing_length
        self.min_displacement_pips = min_displacement_pips
        self.confirmation_bars = confirmation_bars
        self.volume_threshold_multiplier = volume_threshold_multiplier
        
    def detect_choch_signals(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> List[CHoCHSignal]:
        """
        Detect Change of Character signals
        
        Args:
            df: OHLC DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            symbol: Symbol name for pip calculation
            
        Returns:
            List of detected CHoCH signals
        """
        if len(df) < self.swing_length * 3:
            return []
        
        choch_signals = []
        pip_size = self._get_pip_size(symbol)
        
        # Find swing points
        swing_highs = self._find_swing_highs(df)
        swing_lows = self._find_swing_lows(df)
        
        # Analyze market structure
        structure_history = self._analyze_market_structure(swing_highs, swing_lows, df)
        
        # Detect structure breaks
        for i in range(len(structure_history) - 1):
            current_structure = structure_history[i]
            next_structure = structure_history[i + 1]
            
            if current_structure['structure'] != next_structure['structure']:
                choch_signal = self._validate_choch(
                    current_structure, next_structure, df, pip_size
                )
                if choch_signal:
                    choch_signals.append(choch_signal)
        
        # Post-process signals
        choch_signals = self._add_confirmations(choch_signals, df)
        choch_signals = self._analyze_follow_through(choch_signals, df, pip_size)
        
        return choch_signals
    
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
                    'index': i
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
                    'index': i
                })
        
        return swing_lows
    
    def _analyze_market_structure(self, swing_highs: List[Dict], 
                                 swing_lows: List[Dict], df: pd.DataFrame) -> List[Dict]:
        """Analyze market structure evolution"""
        structure_history = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return structure_history
        
        # Combine and sort swing points by time
        all_swings = []
        for swing in swing_highs:
            swing['type'] = 'high'
            all_swings.append(swing)
        for swing in swing_lows:
            swing['type'] = 'low'
            all_swings.append(swing)
        
        all_swings.sort(key=lambda x: x['timestamp'])
        
        # Analyze structure at each swing point
        for i in range(4, len(all_swings)):  # Need at least 4 swings for structure
            recent_swings = all_swings[i-4:i+1]
            structure = self._determine_structure(recent_swings)
            
            structure_history.append({
                'timestamp': all_swings[i]['timestamp'],
                'structure': structure,
                'swing_point': all_swings[i],
                'recent_swings': recent_swings
            })
        
        return structure_history
    
    def _determine_structure(self, swings: List[Dict]) -> MarketStructure:
        """Determine market structure from swing points"""
        highs = [s for s in swings if s['type'] == 'high']
        lows = [s for s in swings if s['type'] == 'low']
        
        if len(highs) < 2 or len(lows) < 2:
            return MarketStructure.RANGING
        
        # Sort by time
        highs.sort(key=lambda x: x['timestamp'])
        lows.sort(key=lambda x: x['timestamp'])
        
        # Check for higher highs and higher lows (bullish structure)
        recent_highs = highs[-2:]
        recent_lows = lows[-2:]
        
        higher_highs = recent_highs[1]['price'] > recent_highs[0]['price']
        higher_lows = recent_lows[1]['price'] > recent_lows[0]['price']
        
        lower_highs = recent_highs[1]['price'] < recent_highs[0]['price']
        lower_lows = recent_lows[1]['price'] < recent_lows[0]['price']
        
        if higher_highs and higher_lows:
            return MarketStructure.BULLISH
        elif lower_highs and lower_lows:
            return MarketStructure.BEARISH
        else:
            return MarketStructure.RANGING
    
    def _validate_choch(self, current_structure: Dict, next_structure: Dict,
                       df: pd.DataFrame, pip_size: float) -> Optional[CHoCHSignal]:
        """Validate potential CHoCH signal"""
        
        prev_struct = current_structure['structure']
        new_struct = next_structure['structure']
        
        # Only interested in clear structure changes
        if prev_struct == MarketStructure.RANGING or new_struct == MarketStructure.RANGING:
            return None
        
        # Determine CHoCH type
        if prev_struct == MarketStructure.BEARISH and new_struct == MarketStructure.BULLISH:
            choch_type = CHoCHType.BULLISH_CHOCH
        elif prev_struct == MarketStructure.BULLISH and new_struct == MarketStructure.BEARISH:
            choch_type = CHoCHType.BEARISH_CHOCH
        else:
            return None
        
        # Find the break level (significant swing point that was broken)
        break_level = self._find_break_level(current_structure, next_structure, choch_type)
        if break_level is None:
            return None
        
        # Calculate displacement
        break_timestamp = next_structure['timestamp']
        break_index = None
        for i, timestamp in enumerate(df.index):
            if timestamp == break_timestamp:
                break_index = i
                break
        
        if break_index is None:
            return None
        
        displacement = self._calculate_displacement(
            df, break_index, break_level, choch_type, pip_size
        )
        
        if displacement < self.min_displacement_pips:
            return None
        
        # Classify strength
        strength = self._classify_choch_strength(displacement)
        
        return CHoCHSignal(
            timestamp=break_timestamp,
            type=choch_type,
            break_level=break_level,
            previous_structure=prev_struct,
            new_structure=new_struct,
            strength=strength,
            displacement_pips=displacement,
            confluence_factors=[]
        )
    
    def _find_break_level(self, current_structure: Dict, next_structure: Dict,
                         choch_type: CHoCHType) -> Optional[float]:
        """Find the level that was broken to create CHoCH"""
        
        current_swings = current_structure['recent_swings']
        
        if choch_type == CHoCHType.BULLISH_CHOCH:
            # Find the most recent significant high that needs to be broken
            highs = [s for s in current_swings if s['type'] == 'high']
            if highs:
                highs.sort(key=lambda x: x['timestamp'])
                return highs[-1]['price']  # Most recent high
        else:
            # Find the most recent significant low that needs to be broken
            lows = [s for s in current_swings if s['type'] == 'low']
            if lows:
                lows.sort(key=lambda x: x['timestamp'])
                return lows[-1]['price']  # Most recent low
        
        return None
    
    def _calculate_displacement(self, df: pd.DataFrame, break_index: int,
                              break_level: float, choch_type: CHoCHType,
                              pip_size: float) -> float:
        """Calculate displacement after structure break"""
        
        # Look at displacement in the next few bars
        end_index = min(break_index + 5, len(df))
        future_data = df.iloc[break_index:end_index]
        
        if choch_type == CHoCHType.BULLISH_CHOCH:
            max_price = future_data['High'].max()
            displacement = (max_price - break_level) / pip_size
        else:
            min_price = future_data['Low'].min()
            displacement = (break_level - min_price) / pip_size
        
        return max(0, displacement)
    
    def _classify_choch_strength(self, displacement: float) -> CHoCHStrength:
        """Classify CHoCH strength based on displacement"""
        if displacement >= 30:
            return CHoCHStrength.STRONG
        elif displacement >= 20:
            return CHoCHStrength.MODERATE
        else:
            return CHoCHStrength.WEAK
    
    def _add_confirmations(self, choch_signals: List[CHoCHSignal],
                          df: pd.DataFrame) -> List[CHoCHSignal]:
        """Add confirmation analysis to CHoCH signals"""
        
        for signal in choch_signals:
            signal_index = None
            for i, timestamp in enumerate(df.index):
                if timestamp == signal.timestamp:
                    signal_index = i
                    break
            
            if signal_index is None:
                continue
            
            # Look for confirmation in subsequent bars
            end_index = min(signal_index + self.confirmation_bars + 1, len(df))
            confirmation_data = df.iloc[signal_index+1:end_index]
            
            confirmation_count = 0
            
            if signal.type == CHoCHType.BULLISH_CHOCH:
                # Count bullish confirmation bars
                for _, candle in confirmation_data.iterrows():
                    if candle['Close'] > candle['Open'] and candle['Close'] > signal.break_level:
                        confirmation_count += 1
            else:
                # Count bearish confirmation bars
                for _, candle in confirmation_data.iterrows():
                    if candle['Close'] < candle['Open'] and candle['Close'] < signal.break_level:
                        confirmation_count += 1
            
            signal.confirmation_count = confirmation_count
            
            # Volume confirmation
            if 'Volume' in df.columns:
                signal.volume_confirmation = self._check_volume_confirmation(
                    df, signal_index, confirmation_data
                )
        
        return choch_signals
    
    def _check_volume_confirmation(self, df: pd.DataFrame, signal_index: int,
                                  confirmation_data: pd.DataFrame) -> bool:
        """Check for volume confirmation of CHoCH"""
        if 'Volume' not in df.columns:
            return False
        
        # Compare volume during break with average volume
        lookback_data = df.iloc[max(0, signal_index-10):signal_index]
        avg_volume = lookback_data['Volume'].mean()
        
        break_volume = df.iloc[signal_index]['Volume']
        confirmation_volume = confirmation_data['Volume'].mean()
        
        return (break_volume > avg_volume * self.volume_threshold_multiplier or
                confirmation_volume > avg_volume * self.volume_threshold_multiplier)
    
    def _analyze_follow_through(self, choch_signals: List[CHoCHSignal],
                               df: pd.DataFrame, pip_size: float) -> List[CHoCHSignal]:
        """Analyze follow-through after CHoCH signals"""
        
        for signal in choch_signals:
            signal_index = None
            for i, timestamp in enumerate(df.index):
                if timestamp == signal.timestamp:
                    signal_index = i
                    break
            
            if signal_index is None:
                continue
            
            # Look for follow-through in next 10 bars
            end_index = min(signal_index + 11, len(df))
            follow_data = df.iloc[signal_index+1:end_index]
            
            if len(follow_data) == 0:
                continue
            
            if signal.type == CHoCHType.BULLISH_CHOCH:
                # Check if price continues higher
                max_follow = follow_data['High'].max()
                follow_displacement = (max_follow - signal.break_level) / pip_size
                signal.follow_through = follow_displacement > signal.displacement_pips * 0.5
            else:
                # Check if price continues lower
                min_follow = follow_data['Low'].min()
                follow_displacement = (signal.break_level - min_follow) / pip_size
                signal.follow_through = follow_displacement > signal.displacement_pips * 0.5
        
        return choch_signals
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        jpy_pairs = ['JPY', 'jpy']
        if any(pair in symbol.upper() for pair in jpy_pairs):
            return 0.01
        else:
            return 0.0001
    
    def get_recent_choch_signals(self, choch_signals: List[CHoCHSignal],
                                lookback_bars: int = 50) -> List[CHoCHSignal]:
        """Get recent CHoCH signals within lookback period"""
        if not choch_signals:
            return []
        
        # Sort by timestamp
        sorted_signals = sorted(choch_signals, key=lambda x: x.timestamp, reverse=True)
        
        # Filter for strong and moderate signals with good confirmation
        quality_signals = [
            signal for signal in sorted_signals
            if (signal.strength in [CHoCHStrength.STRONG, CHoCHStrength.MODERATE] and
                signal.confirmation_count >= 2)
        ]
        
        return quality_signals[:5]  # Return top 5 most recent quality signals
    
    def analyze_choch_confluence(self, choch_signals: List[CHoCHSignal],
                                current_price: float) -> Dict:
        """Analyze CHoCH confluence for current market conditions"""
        recent_signals = self.get_recent_choch_signals(choch_signals)
        
        if not recent_signals:
            return {
                'bias': 'neutral',
                'confluence_score': 0,
                'recent_choch_count': 0,
                'dominant_structure': None
            }
        
        # Analyze bias from recent CHoCH signals
        bullish_count = sum(1 for s in recent_signals if s.type == CHoCHType.BULLISH_CHOCH)
        bearish_count = sum(1 for s in recent_signals if s.type == CHoCHType.BEARISH_CHOCH)
        
        if bullish_count > bearish_count:
            bias = 'bullish'
            dominant_structure = MarketStructure.BULLISH
        elif bearish_count > bullish_count:
            bias = 'bearish'
            dominant_structure = MarketStructure.BEARISH
        else:
            bias = 'neutral'
            dominant_structure = None
        
        # Calculate confluence score based on signal quality
        strength_weights = {
            CHoCHStrength.STRONG: 3.0,
            CHoCHStrength.MODERATE: 2.0,
            CHoCHStrength.WEAK: 1.0
        }
        
        confluence_score = sum(
            strength_weights[signal.strength] * 
            (1 + signal.confirmation_count * 0.2) *
            (1.2 if signal.volume_confirmation else 1.0) *
            (1.3 if signal.follow_through else 1.0)
            for signal in recent_signals
        )
        
        return {
            'bias': bias,
            'confluence_score': confluence_score,
            'recent_choch_count': len(recent_signals),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'dominant_structure': dominant_structure,
            'strongest_signal': max(recent_signals, key=lambda x: x.displacement_pips) if recent_signals else None,
            'most_recent': recent_signals[0] if recent_signals else None
        }