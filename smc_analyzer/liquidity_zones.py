"""
Liquidity Zones Module
Maps liquidity zones, order blocks, supply/demand areas, and Fair Value Gaps (FVGs)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ZoneType(Enum):
    """Types of liquidity zones"""
    ORDER_BLOCK = "order_block"
    SUPPLY_ZONE = "supply_zone"
    DEMAND_ZONE = "demand_zone"
    FVG = "fair_value_gap"
    LIQUIDITY_VOID = "liquidity_void"


class ZoneStrength(Enum):
    """Strength levels for zones"""
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class LiquidityZone:
    """Represents a liquidity zone"""
    zone_type: ZoneType
    top: float
    bottom: float
    start_time: pd.Timestamp
    end_time: Optional[pd.Timestamp]
    strength: ZoneStrength
    volume: Optional[float]
    touches: int
    is_active: bool
    origin_index: int


@dataclass
class OrderBlock:
    """Represents an order block"""
    high: float
    low: float
    time: pd.Timestamp
    is_bullish: bool
    strength: float
    volume: Optional[float]
    index: int


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap"""
    top: float
    bottom: float
    start_time: pd.Timestamp
    is_bullish: bool
    strength: float
    filled: bool
    index: int


class LiquidityZoneMapper:
    """
    Maps and analyzes liquidity zones, order blocks, and fair value gaps
    """
    
    def __init__(self, 
                 min_zone_size: float = 0.0001,
                 max_zone_age: int = 100,
                 volume_threshold: float = 1.5):
        """
        Initialize liquidity zone mapper
        
        Args:
            min_zone_size: Minimum size for a valid zone
            max_zone_age: Maximum age of zones to keep active (in bars)
            volume_threshold: Volume multiplier for significant zones
        """
        self.min_zone_size = min_zone_size
        self.max_zone_age = max_zone_age
        self.volume_threshold = volume_threshold
        
    def identify_order_blocks(self, df: pd.DataFrame, swing_points: List) -> List[OrderBlock]:
        """
        Identify order blocks based on price action
        
        Args:
            df: DataFrame with OHLC data
            swing_points: List of swing points from market structure analysis
            
        Returns:
            List of OrderBlock objects
        """
        order_blocks = []
        
        if len(df) < 10:
            return order_blocks
            
        for i, swing in enumerate(swing_points):
            # Look for order blocks around swing points
            if swing.type == 'high':  # Bearish order block
                # Find the last bullish candle before the swing high
                start_idx = max(0, swing.index - 10)
                for j in range(swing.index - 1, start_idx, -1):
                    if df['close'].iloc[j] > df['open'].iloc[j]:  # Bullish candle
                        # This could be an order block
                        strength = self._calculate_order_block_strength(df, j, swing.index)
                        if strength > 0.3:  # Minimum strength threshold
                            order_blocks.append(OrderBlock(
                                high=df['high'].iloc[j],
                                low=df['low'].iloc[j],
                                time=df.index[j],
                                is_bullish=False,  # Bearish order block
                                strength=strength,
                                volume=df['volume'].iloc[j] if 'volume' in df.columns else None,
                                index=j
                            ))
                        break
                        
            elif swing.type == 'low':  # Bullish order block
                # Find the last bearish candle before the swing low
                start_idx = max(0, swing.index - 10)
                for j in range(swing.index - 1, start_idx, -1):
                    if df['close'].iloc[j] < df['open'].iloc[j]:  # Bearish candle
                        # This could be an order block
                        strength = self._calculate_order_block_strength(df, j, swing.index)
                        if strength > 0.3:  # Minimum strength threshold
                            order_blocks.append(OrderBlock(
                                high=df['high'].iloc[j],
                                low=df['low'].iloc[j],
                                time=df.index[j],
                                is_bullish=True,  # Bullish order block
                                strength=strength,
                                volume=df['volume'].iloc[j] if 'volume' in df.columns else None,
                                index=j
                            ))
                        break
        
        return order_blocks
    
    def identify_supply_demand_zones(self, df: pd.DataFrame) -> List[LiquidityZone]:
        """
        Identify supply and demand zones
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of LiquidityZone objects representing supply/demand zones
        """
        zones = []
        
        # Look for strong rejection areas (supply/demand zones)
        for i in range(20, len(df) - 5):
            # Check for supply zone (resistance)
            high_area = df['high'].iloc[i-10:i+5]
            if self._is_significant_level(df, i, 'high'):
                zone_top = high_area.max()
                zone_bottom = high_area.quantile(0.8)
                
                if zone_top - zone_bottom >= self.min_zone_size:
                    strength = self._calculate_zone_strength(df, i, zone_top, zone_bottom, 'supply')
                    zones.append(LiquidityZone(
                        zone_type=ZoneType.SUPPLY_ZONE,
                        top=zone_top,
                        bottom=zone_bottom,
                        start_time=df.index[i],
                        end_time=None,
                        strength=strength,
                        volume=df['volume'].iloc[i] if 'volume' in df.columns else None,
                        touches=1,
                        is_active=True,
                        origin_index=i
                    ))
            
            # Check for demand zone (support)
            if self._is_significant_level(df, i, 'low'):
                low_area = df['low'].iloc[i-10:i+5]
                zone_bottom = low_area.min()
                zone_top = low_area.quantile(0.2)
                
                if zone_top - zone_bottom >= self.min_zone_size:
                    strength = self._calculate_zone_strength(df, i, zone_top, zone_bottom, 'demand')
                    zones.append(LiquidityZone(
                        zone_type=ZoneType.DEMAND_ZONE,
                        top=zone_top,
                        bottom=zone_bottom,
                        start_time=df.index[i],
                        end_time=None,
                        strength=strength,
                        volume=df['volume'].iloc[i] if 'volume' in df.columns else None,
                        touches=1,
                        is_active=True,
                        origin_index=i
                    ))
        
        return zones
    
    def identify_fair_value_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Identify Fair Value Gaps (FVGs) in price action
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of FairValueGap objects
        """
        fvgs = []
        
        for i in range(1, len(df) - 1):
            # Check for bullish FVG: gap between candle[i-1].high and candle[i+1].low
            prev_high = df['high'].iloc[i-1]
            next_low = df['low'].iloc[i+1]
            current_low = df['low'].iloc[i]
            current_high = df['high'].iloc[i]
            
            # Bullish FVG
            if prev_high < next_low and current_low > prev_high:
                gap_size = next_low - prev_high
                if gap_size >= self.min_zone_size:
                    strength = self._calculate_fvg_strength(df, i, gap_size)
                    fvgs.append(FairValueGap(
                        top=next_low,
                        bottom=prev_high,
                        start_time=df.index[i],
                        is_bullish=True,
                        strength=strength,
                        filled=False,
                        index=i
                    ))
            
            # Bearish FVG: gap between candle[i-1].low and candle[i+1].high
            prev_low = df['low'].iloc[i-1]
            next_high = df['high'].iloc[i+1]
            
            if prev_low > next_high and current_high < prev_low:
                gap_size = prev_low - next_high
                if gap_size >= self.min_zone_size:
                    strength = self._calculate_fvg_strength(df, i, gap_size)
                    fvgs.append(FairValueGap(
                        top=prev_low,
                        bottom=next_high,
                        start_time=df.index[i],
                        is_bullish=False,
                        strength=strength,
                        filled=False,
                        index=i
                    ))
        
        return fvgs
    
    def update_zone_status(self, zones: List[LiquidityZone], df: pd.DataFrame, current_index: int) -> List[LiquidityZone]:
        """
        Update the status of existing zones (touches, active status)
        
        Args:
            zones: List of existing zones
            df: Current DataFrame
            current_index: Current bar index
            
        Returns:
            Updated list of zones
        """
        updated_zones = []
        
        for zone in zones:
            # Check if zone is too old
            zone_age = current_index - zone.origin_index
            if zone_age > self.max_zone_age:
                zone.is_active = False
                continue
            
            # Check for touches
            touches = 0
            for i in range(zone.origin_index + 1, min(current_index + 1, len(df))):
                high = df['high'].iloc[i]
                low = df['low'].iloc[i]
                
                # Check if price touched the zone
                if zone.zone_type == ZoneType.SUPPLY_ZONE:
                    if high >= zone.bottom and low <= zone.top:
                        touches += 1
                elif zone.zone_type == ZoneType.DEMAND_ZONE:
                    if low <= zone.top and high >= zone.bottom:
                        touches += 1
            
            zone.touches = touches
            
            # Deactivate zone after too many touches
            if touches > 3:
                zone.is_active = False
            
            updated_zones.append(zone)
        
        return updated_zones
    
    def check_fvg_filled(self, fvgs: List[FairValueGap], df: pd.DataFrame, current_index: int) -> List[FairValueGap]:
        """
        Check if Fair Value Gaps have been filled
        
        Args:
            fvgs: List of FVGs to check
            df: Current DataFrame
            current_index: Current bar index
            
        Returns:
            Updated list of FVGs
        """
        for fvg in fvgs:
            if fvg.filled:
                continue
                
            # Check if FVG has been filled by subsequent price action
            for i in range(fvg.index + 1, min(current_index + 1, len(df))):
                high = df['high'].iloc[i]
                low = df['low'].iloc[i]
                
                if fvg.is_bullish:
                    # Bullish FVG filled when price returns to bottom
                    if low <= fvg.bottom:
                        fvg.filled = True
                        break
                else:
                    # Bearish FVG filled when price returns to top
                    if high >= fvg.top:
                        fvg.filled = True
                        break
        
        return fvgs
    
    def _calculate_order_block_strength(self, df: pd.DataFrame, block_index: int, swing_index: int) -> float:
        """Calculate order block strength"""
        # Volume factor
        volume_factor = 1.0
        if 'volume' in df.columns:
            current_vol = df['volume'].iloc[block_index]
            avg_vol = df['volume'].iloc[max(0, block_index-10):block_index].mean()
            volume_factor = min(current_vol / avg_vol, 3.0) if avg_vol > 0 else 1.0
        
        # Distance to swing factor
        distance = swing_index - block_index
        distance_factor = max(0.1, 1.0 - (distance / 20.0))
        
        # Candle size factor
        candle_size = abs(df['close'].iloc[block_index] - df['open'].iloc[block_index])
        avg_size = df['high'].iloc[max(0, block_index-10):block_index].subtract(
            df['low'].iloc[max(0, block_index-10):block_index]).mean()
        size_factor = min(candle_size / avg_size, 2.0) if avg_size > 0 else 1.0
        
        strength = (volume_factor * 0.4 + distance_factor * 0.3 + size_factor * 0.3) / 3.0
        return min(max(strength, 0.0), 1.0)
    
    def _calculate_zone_strength(self, df: pd.DataFrame, index: int, top: float, bottom: float, zone_type: str) -> ZoneStrength:
        """Calculate supply/demand zone strength"""
        # Volume analysis
        volume_score = 0
        if 'volume' in df.columns:
            zone_volume = df['volume'].iloc[index]
            avg_volume = df['volume'].iloc[max(0, index-20):index].mean()
            volume_score = min(zone_volume / avg_volume, 3.0) if avg_volume > 0 else 1.0
        
        # Price rejection strength
        zone_size = top - bottom
        avg_range = df['high'].iloc[max(0, index-10):index].subtract(
            df['low'].iloc[max(0, index-10):index]).mean()
        size_score = min(zone_size / avg_range, 2.0) if avg_range > 0 else 1.0
        
        # Time factor (fresher zones are stronger)
        time_score = 1.0  # Will be updated based on age
        
        total_score = (volume_score + size_score + time_score) / 3.0
        
        if total_score >= 2.5:
            return ZoneStrength.VERY_STRONG
        elif total_score >= 2.0:
            return ZoneStrength.STRONG
        elif total_score >= 1.5:
            return ZoneStrength.MEDIUM
        else:
            return ZoneStrength.WEAK
    
    def _calculate_fvg_strength(self, df: pd.DataFrame, index: int, gap_size: float) -> float:
        """Calculate Fair Value Gap strength"""
        # Gap size relative to average range
        avg_range = df['high'].iloc[max(0, index-10):index+1].subtract(
            df['low'].iloc[max(0, index-10):index+1]).mean()
        size_factor = min(gap_size / avg_range, 2.0) if avg_range > 0 else 1.0
        
        # Volume factor
        volume_factor = 1.0
        if 'volume' in df.columns:
            gap_volume = df['volume'].iloc[index]
            avg_volume = df['volume'].iloc[max(0, index-10):index].mean()
            volume_factor = min(gap_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
        
        strength = (size_factor + volume_factor) / 2.0
        return min(max(strength, 0.0), 1.0)
    
    def _is_significant_level(self, df: pd.DataFrame, index: int, level_type: str) -> bool:
        """Check if a price level is significant for zone formation"""
        if level_type == 'high':
            current = df['high'].iloc[index]
            nearby = df['high'].iloc[max(0, index-5):index+6]
            return current >= nearby.quantile(0.9)
        else:  # low
            current = df['low'].iloc[index]
            nearby = df['low'].iloc[max(0, index-5):index+6]
            return current <= nearby.quantile(0.1)
    
    def analyze_liquidity(self, df: pd.DataFrame, swing_points: List) -> Dict:
        """
        Perform complete liquidity analysis
        
        Args:
            df: DataFrame with OHLC data
            swing_points: List of swing points
            
        Returns:
            Dictionary containing all liquidity analysis results
        """
        order_blocks = self.identify_order_blocks(df, swing_points)
        supply_demand_zones = self.identify_supply_demand_zones(df)
        fair_value_gaps = self.identify_fair_value_gaps(df)
        
        # Update zone status for current market conditions
        current_index = len(df) - 1
        active_zones = self.update_zone_status(supply_demand_zones, df, current_index)
        updated_fvgs = self.check_fvg_filled(fair_value_gaps, df, current_index)
        
        return {
            'order_blocks': order_blocks,
            'supply_demand_zones': active_zones,
            'fair_value_gaps': updated_fvgs,
            'analysis_timestamp': pd.Timestamp.now(),
            'total_order_blocks': len(order_blocks),
            'active_zones': len([z for z in active_zones if z.is_active]),
            'unfilled_fvgs': len([f for f in updated_fvgs if not f.filled])
        }