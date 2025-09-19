"""
Advanced Liquidity Zone Mapping with Equal Highs/Lows Detection
Implements institutional-grade liquidity identification and sweep analysis
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime

class LiquidityType(Enum):
    """Liquidity zone type classification"""
    BUY_SIDE = "BUY_SIDE"    # Above resistance levels (sell stops)
    SELL_SIDE = "SELL_SIDE"   # Below support levels (buy stops)

class LiquidityStrength(Enum):
    """Liquidity zone strength classification"""
    MAJOR = "MAJOR"           # Multiple touches, high volume
    INTERMEDIATE = "INTERMEDIATE"  # Several touches, medium volume
    MINOR = "MINOR"           # Few touches, low volume

@dataclass
class LiquidityZone:
    """Liquidity zone data structure"""
    timestamp: datetime
    type: LiquidityType
    price_level: float
    strength: LiquidityStrength
    touch_count: int
    swept: bool = False
    sweep_timestamp: Optional[datetime] = None
    volume_accumulation: float = 0.0
    sweep_displacement: float = 0.0  # Pips displaced after sweep
    confluence_factors: List[str] = None
    equal_levels: List[float] = None  # Equal highs/lows

class LiquidityZoneMapper:
    """
    Advanced Liquidity Zone Mapping Engine
    
    Implements institutional-grade liquidity detection with:
    - Equal highs/lows identification
    - Liquidity sweep detection and analysis
    - Volume accumulation tracking
    - Confluence with other SMC factors
    - Displacement measurement after sweeps
    """
    
    def __init__(self,
                 equal_level_tolerance_pips: float = 3.0,
                 min_touch_count: int = 2,
                 sweep_threshold_pips: float = 2.0,
                 volume_threshold_multiplier: float = 1.5):
        """
        Initialize Liquidity Zone Mapper
        
        Args:
            equal_level_tolerance_pips: Tolerance for equal levels in pips
            min_touch_count: Minimum touches to consider valid liquidity
            sweep_threshold_pips: Minimum displacement to confirm sweep
            volume_threshold_multiplier: Volume multiplier for strength classification
        """
        self.equal_level_tolerance_pips = equal_level_tolerance_pips
        self.min_touch_count = min_touch_count
        self.sweep_threshold_pips = sweep_threshold_pips
        self.volume_threshold_multiplier = volume_threshold_multiplier
        
    def detect_liquidity_zones(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> List[LiquidityZone]:
        """
        Detect liquidity zones through equal highs/lows analysis
        
        Args:
            df: OHLC DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            symbol: Symbol name for pip calculation
            
        Returns:
            List of detected liquidity zones
        """
        if len(df) < 10:
            return []
        
        liquidity_zones = []
        pip_size = self._get_pip_size(symbol)
        
        # Detect equal highs (buy-side liquidity)
        equal_highs = self._find_equal_levels(df['High'], pip_size, 'high')
        for level_data in equal_highs:
            lz = self._create_liquidity_zone(
                level_data, LiquidityType.BUY_SIDE, df, pip_size
            )
            if lz:
                liquidity_zones.append(lz)
        
        # Detect equal lows (sell-side liquidity)
        equal_lows = self._find_equal_levels(df['Low'], pip_size, 'low')
        for level_data in equal_lows:
            lz = self._create_liquidity_zone(
                level_data, LiquidityType.SELL_SIDE, df, pip_size
            )
            if lz:
                liquidity_zones.append(lz)
        
        # Analyze sweeps for all zones
        liquidity_zones = self._analyze_sweeps(liquidity_zones, df, pip_size)
        
        return liquidity_zones
    
    def _find_equal_levels(self, price_series: pd.Series, pip_size: float, 
                          level_type: str) -> List[Dict]:
        """Find equal price levels (highs or lows)"""
        equal_levels = []
        tolerance = self.equal_level_tolerance_pips * pip_size
        
        # Find local extremes
        if level_type == 'high':
            extremes = self._find_local_maxima(price_series, window=5)
        else:
            extremes = self._find_local_minima(price_series, window=5)
        
        if len(extremes) < 2:
            return equal_levels
        
        # Group equal levels
        level_groups = []
        for i, (idx1, price1) in enumerate(extremes):
            group = [(idx1, price1)]
            
            for j, (idx2, price2) in enumerate(extremes[i+1:], i+1):
                if abs(price1 - price2) <= tolerance:
                    group.append((idx2, price2))
            
            if len(group) >= self.min_touch_count:
                # Check if this group is unique (not already added)
                is_unique = True
                for existing_group in level_groups:
                    if any(idx in [x[0] for x in existing_group] for idx, _ in group):
                        is_unique = False
                        break
                
                if is_unique:
                    level_groups.append(group)
        
        # Convert groups to level data
        for group in level_groups:
            avg_price = np.mean([price for _, price in group])
            timestamps = [price_series.index[idx] for idx, _ in group]
            
            equal_levels.append({
                'price_level': avg_price,
                'touch_count': len(group),
                'timestamps': timestamps,
                'indices': [idx for idx, _ in group],
                'equal_prices': [price for _, price in group]
            })
        
        return equal_levels
    
    def _find_local_maxima(self, series: pd.Series, window: int = 5) -> List[Tuple[int, float]]:
        """Find local maximum points"""
        maxima = []
        for i in range(window, len(series) - window):
            window_data = series.iloc[i-window:i+window+1]
            if series.iloc[i] == window_data.max():
                maxima.append((i, series.iloc[i]))
        return maxima
    
    def _find_local_minima(self, series: pd.Series, window: int = 5) -> List[Tuple[int, float]]:
        """Find local minimum points"""
        minima = []
        for i in range(window, len(series) - window):
            window_data = series.iloc[i-window:i+window+1]
            if series.iloc[i] == window_data.min():
                minima.append((i, series.iloc[i]))
        return minima
    
    def _create_liquidity_zone(self, level_data: Dict, lz_type: LiquidityType,
                              df: pd.DataFrame, pip_size: float) -> Optional[LiquidityZone]:
        """Create liquidity zone from level data"""
        
        if level_data['touch_count'] < self.min_touch_count:
            return None
        
        # Calculate volume accumulation
        volume_accumulation = 0.0
        if 'Volume' in df.columns:
            for idx in level_data['indices']:
                if not pd.isna(df.iloc[idx]['Volume']):
                    volume_accumulation += df.iloc[idx]['Volume']
        
        # Determine strength based on touches and volume
        strength = self._classify_strength(
            level_data['touch_count'], volume_accumulation
        )
        
        # Use the most recent timestamp
        most_recent_timestamp = max(level_data['timestamps'])
        
        return LiquidityZone(
            timestamp=most_recent_timestamp,
            type=lz_type,
            price_level=level_data['price_level'],
            strength=strength,
            touch_count=level_data['touch_count'],
            volume_accumulation=volume_accumulation,
            confluence_factors=[],
            equal_levels=level_data['equal_prices']
        )
    
    def _classify_strength(self, touch_count: int, volume: float) -> LiquidityStrength:
        """Classify liquidity zone strength"""
        
        # Base classification on touch count
        if touch_count >= 4:
            base_strength = LiquidityStrength.MAJOR
        elif touch_count >= 3:
            base_strength = LiquidityStrength.INTERMEDIATE
        else:
            base_strength = LiquidityStrength.MINOR
        
        # Volume can upgrade strength
        if volume > 0:  # Simple volume check (can be enhanced with historical comparison)
            if base_strength == LiquidityStrength.MINOR and volume > 1000:
                return LiquidityStrength.INTERMEDIATE
            elif base_strength == LiquidityStrength.INTERMEDIATE and volume > 5000:
                return LiquidityStrength.MAJOR
        
        return base_strength
    
    def _analyze_sweeps(self, liquidity_zones: List[LiquidityZone],
                       df: pd.DataFrame, pip_size: float) -> List[LiquidityZone]:
        """Analyze liquidity sweeps for all zones"""
        
        for lz in liquidity_zones:
            # Find the index of the most recent touch
            lz_index = None
            for i, timestamp in enumerate(df.index):
                if timestamp == lz.timestamp:
                    lz_index = i
                    break
            
            if lz_index is None:
                continue
            
            # Look for sweeps after the liquidity zone formation
            future_data = df.iloc[lz_index+1:]
            if len(future_data) == 0:
                continue
            
            sweep_threshold = self.sweep_threshold_pips * pip_size
            
            if lz.type == LiquidityType.BUY_SIDE:
                # Look for price breaking above the liquidity level
                sweep_candles = future_data[future_data['High'] > lz.price_level + sweep_threshold]
                if len(sweep_candles) > 0:
                    first_sweep = sweep_candles.index[0]
                    lz.swept = True
                    lz.sweep_timestamp = first_sweep
                    
                    # Calculate displacement after sweep
                    sweep_candle = future_data.loc[first_sweep]
                    displacement = (sweep_candle['High'] - lz.price_level) / pip_size
                    lz.sweep_displacement = displacement
                    
            else:  # SELL_SIDE liquidity
                # Look for price breaking below the liquidity level
                sweep_candles = future_data[future_data['Low'] < lz.price_level - sweep_threshold]
                if len(sweep_candles) > 0:
                    first_sweep = sweep_candles.index[0]
                    lz.swept = True
                    lz.sweep_timestamp = first_sweep
                    
                    # Calculate displacement after sweep
                    sweep_candle = future_data.loc[first_sweep]
                    displacement = (lz.price_level - sweep_candle['Low']) / pip_size
                    lz.sweep_displacement = displacement
        
        return liquidity_zones
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        jpy_pairs = ['JPY', 'jpy']
        if any(pair in symbol.upper() for pair in jpy_pairs):
            return 0.01
        else:
            return 0.0001
    
    def get_active_liquidity_zones(self, liquidity_zones: List[LiquidityZone],
                                  current_price: float) -> List[LiquidityZone]:
        """Get active (unswept) liquidity zones relevant to current price"""
        active_zones = []
        
        for lz in liquidity_zones:
            if lz.swept:
                continue
            
            # Check relevance to current price (within reasonable distance)
            price_distance = abs(lz.price_level - current_price)
            max_distance = current_price * 0.02  # 2% of current price
            
            if price_distance <= max_distance:
                active_zones.append(lz)
        
        # Sort by strength and proximity
        active_zones.sort(key=lambda x: (
            x.strength.value,
            x.touch_count,
            abs(x.price_level - current_price)
        ), reverse=True)
        
        return active_zones[:8]  # Return top 8 most relevant
    
    def analyze_liquidity_sweeps(self, liquidity_zones: List[LiquidityZone],
                                current_price: float) -> Dict:
        """Analyze recent liquidity sweeps for bias indication"""
        recent_sweeps = [lz for lz in liquidity_zones if lz.swept and lz.sweep_timestamp]
        
        if not recent_sweeps:
            return {
                'recent_sweep_count': 0,
                'sweep_bias': 'neutral',
                'avg_displacement': 0.0,
                'strongest_sweep': None
            }
        
        # Sort by recency
        recent_sweeps.sort(key=lambda x: x.sweep_timestamp, reverse=True)
        
        # Analyze sweep bias (last 5 sweeps)
        last_5_sweeps = recent_sweeps[:5]
        buy_side_sweeps = sum(1 for lz in last_5_sweeps if lz.type == LiquidityType.BUY_SIDE)
        sell_side_sweeps = sum(1 for lz in last_5_sweeps if lz.type == LiquidityType.SELL_SIDE)
        
        if buy_side_sweeps > sell_side_sweeps:
            sweep_bias = 'bearish'  # Sweeping buy stops suggests bearish move
        elif sell_side_sweeps > buy_side_sweeps:
            sweep_bias = 'bullish'  # Sweeping sell stops suggests bullish move
        else:
            sweep_bias = 'neutral'
        
        # Calculate average displacement
        avg_displacement = np.mean([lz.sweep_displacement for lz in recent_sweeps])
        
        # Find strongest sweep
        strongest_sweep = max(recent_sweeps, key=lambda x: x.sweep_displacement)
        
        return {
            'recent_sweep_count': len(recent_sweeps),
            'sweep_bias': sweep_bias,
            'avg_displacement': avg_displacement,
            'strongest_sweep': strongest_sweep,
            'last_5_sweeps': last_5_sweeps,
            'buy_side_sweeps': buy_side_sweeps,
            'sell_side_sweeps': sell_side_sweeps
        }
    
    def find_liquidity_confluence(self, liquidity_zones: List[LiquidityZone],
                                 price_level: float, tolerance_pips: float = 5) -> Dict:
        """Find confluence of liquidity zones around a price level"""
        pip_size = 0.0001  # Assume standard pip size
        tolerance = tolerance_pips * pip_size
        
        nearby_zones = [
            lz for lz in liquidity_zones
            if not lz.swept and abs(lz.price_level - price_level) <= tolerance
        ]
        
        if not nearby_zones:
            return {'confluence_score': 0, 'zone_count': 0, 'dominant_type': None}
        
        buy_side_count = sum(1 for lz in nearby_zones if lz.type == LiquidityType.BUY_SIDE)
        sell_side_count = sum(1 for lz in nearby_zones if lz.type == LiquidityType.SELL_SIDE)
        
        # Calculate confluence score based on strength and quantity
        strength_weights = {
            LiquidityStrength.MAJOR: 3.0,
            LiquidityStrength.INTERMEDIATE: 2.0,
            LiquidityStrength.MINOR: 1.0
        }
        
        confluence_score = sum(strength_weights[lz.strength] for lz in nearby_zones)
        
        return {
            'confluence_score': confluence_score,
            'zone_count': len(nearby_zones),
            'buy_side_count': buy_side_count,
            'sell_side_count': sell_side_count,
            'dominant_type': LiquidityType.BUY_SIDE if buy_side_count > sell_side_count else LiquidityType.SELL_SIDE,
            'zones': nearby_zones,
            'total_touch_count': sum(lz.touch_count for lz in nearby_zones),
            'avg_volume': np.mean([lz.volume_accumulation for lz in nearby_zones]) if nearby_zones else 0
        }