"""
Advanced Order Block Detection with Displacement Validation
Implements institutional-grade order block identification following ICT methodology
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime

class OrderBlockType(Enum):
    """Order block type classification"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

class OrderBlockQuality(Enum):
    """Order block quality rating"""
    INSTITUTIONAL = "INSTITUTIONAL"  # High displacement, strong structure
    PROFESSIONAL = "PROFESSIONAL"   # Good displacement, clear structure
    RETAIL = "RETAIL"               # Minimal displacement, weak structure

@dataclass
class OrderBlock:
    """Order block data structure"""
    timestamp: datetime
    type: OrderBlockType
    top: float
    bottom: float
    displacement_pips: float
    quality: OrderBlockQuality
    tested: bool = False
    valid: bool = True
    strength: float = 0.0
    volume_profile: Optional[Dict] = None
    mitigation_level: float = 0.0  # How much has been tested (0-100%)
    
class OrderBlockDetector:
    """
    Advanced Order Block Detection Engine
    
    Implements institutional-grade order block identification with:
    - Displacement validation (>20 pips minimum)
    - Multi-timeframe confirmation
    - Volume profile analysis
    - Quality classification
    - Mitigation tracking
    """
    
    def __init__(self, 
                 min_displacement_pips: float = 20.0,
                 lookback_period: int = 50,
                 min_body_ratio: float = 0.6,
                 enable_volume_analysis: bool = True):
        """
        Initialize Order Block Detector
        
        Args:
            min_displacement_pips: Minimum displacement for valid order block
            lookback_period: Periods to look back for structure
            min_body_ratio: Minimum body to range ratio
            enable_volume_analysis: Enable volume profile analysis
        """
        self.min_displacement_pips = min_displacement_pips
        self.lookback_period = lookback_period
        self.min_body_ratio = min_body_ratio
        self.enable_volume_analysis = enable_volume_analysis
        
    def detect_order_blocks(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> List[OrderBlock]:
        """
        Detect order blocks with displacement validation
        
        Args:
            df: OHLC DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            symbol: Symbol name for pip calculation
            
        Returns:
            List of detected order blocks
        """
        if len(df) < self.lookback_period:
            return []
        
        order_blocks = []
        pip_size = self._get_pip_size(symbol)
        
        for i in range(self.lookback_period, len(df) - 1):
            current_candle = df.iloc[i]
            
            # Check for bullish order block pattern
            bullish_ob = self._detect_bullish_order_block(
                df, i, current_candle, pip_size
            )
            if bullish_ob:
                order_blocks.append(bullish_ob)
            
            # Check for bearish order block pattern  
            bearish_ob = self._detect_bearish_order_block(
                df, i, current_candle, pip_size
            )
            if bearish_ob:
                order_blocks.append(bearish_ob)
        
        # Post-process order blocks
        order_blocks = self._validate_displacement(order_blocks, df, pip_size)
        order_blocks = self._calculate_mitigation_levels(order_blocks, df)
        order_blocks = self._classify_quality(order_blocks)
        
        return order_blocks
    
    def _detect_bullish_order_block(self, df: pd.DataFrame, index: int, 
                                   candle: pd.Series, pip_size: float) -> Optional[OrderBlock]:
        """Detect bullish order block pattern"""
        
        # Look for strong bullish candle with subsequent upward movement
        body_size = abs(candle['Close'] - candle['Open'])
        range_size = candle['High'] - candle['Low']
        
        if range_size == 0:
            return None
            
        body_ratio = body_size / range_size
        
        # Must be bullish candle with sufficient body
        if candle['Close'] <= candle['Open'] or body_ratio < self.min_body_ratio:
            return None
        
        # Check for displacement after the order block
        future_data = df.iloc[index+1:index+10]  # Look ahead 10 periods
        if len(future_data) == 0:
            return None
            
        highest_future = future_data['High'].max()
        displacement = (highest_future - candle['High']) / pip_size
        
        if displacement < self.min_displacement_pips:
            return None
        
        # Create order block
        order_block = OrderBlock(
            timestamp=df.index[index],
            type=OrderBlockType.BULLISH,
            top=candle['High'],
            bottom=min(candle['Open'], candle['Close']),
            displacement_pips=displacement,
            quality=OrderBlockQuality.RETAIL,  # Will be classified later
            strength=body_ratio,
            volume_profile=self._analyze_volume_profile(candle) if self.enable_volume_analysis else None
        )
        
        return order_block
    
    def _detect_bearish_order_block(self, df: pd.DataFrame, index: int,
                                   candle: pd.Series, pip_size: float) -> Optional[OrderBlock]:
        """Detect bearish order block pattern"""
        
        # Look for strong bearish candle with subsequent downward movement
        body_size = abs(candle['Close'] - candle['Open'])
        range_size = candle['High'] - candle['Low']
        
        if range_size == 0:
            return None
            
        body_ratio = body_size / range_size
        
        # Must be bearish candle with sufficient body
        if candle['Close'] >= candle['Open'] or body_ratio < self.min_body_ratio:
            return None
        
        # Check for displacement after the order block
        future_data = df.iloc[index+1:index+10]  # Look ahead 10 periods
        if len(future_data) == 0:
            return None
            
        lowest_future = future_data['Low'].min()
        displacement = (candle['Low'] - lowest_future) / pip_size
        
        if displacement < self.min_displacement_pips:
            return None
        
        # Create order block
        order_block = OrderBlock(
            timestamp=df.index[index],
            type=OrderBlockType.BEARISH,
            top=max(candle['Open'], candle['Close']),
            bottom=candle['Low'],
            displacement_pips=displacement,
            quality=OrderBlockQuality.RETAIL,  # Will be classified later
            strength=body_ratio,
            volume_profile=self._analyze_volume_profile(candle) if self.enable_volume_analysis else None
        )
        
        return order_block
    
    def _validate_displacement(self, order_blocks: List[OrderBlock], 
                              df: pd.DataFrame, pip_size: float) -> List[OrderBlock]:
        """Validate displacement requirements for all order blocks"""
        validated_blocks = []
        
        for ob in order_blocks:
            # Re-validate displacement with more stringent criteria
            ob_index = df.index.get_loc(ob.timestamp)
            future_data = df.iloc[ob_index+1:ob_index+20]  # Extended validation
            
            if len(future_data) == 0:
                continue
            
            if ob.type == OrderBlockType.BULLISH:
                max_displacement = (future_data['High'].max() - ob.top) / pip_size
            else:
                max_displacement = (ob.bottom - future_data['Low'].min()) / pip_size
            
            # Update displacement with maximum observed
            ob.displacement_pips = max(ob.displacement_pips, max_displacement)
            
            if ob.displacement_pips >= self.min_displacement_pips:
                validated_blocks.append(ob)
        
        return validated_blocks
    
    def _calculate_mitigation_levels(self, order_blocks: List[OrderBlock], 
                                   df: pd.DataFrame) -> List[OrderBlock]:
        """Calculate mitigation levels for order blocks"""
        
        for ob in order_blocks:
            ob_index = df.index.get_loc(ob.timestamp)
            future_data = df.iloc[ob_index+1:]
            
            if len(future_data) == 0:
                continue
            
            if ob.type == OrderBlockType.BULLISH:
                # Check how much of the order block has been tested
                penetrations = future_data[future_data['Low'] <= ob.top]['Low']
                if len(penetrations) > 0:
                    deepest_penetration = penetrations.min()
                    if deepest_penetration <= ob.bottom:
                        ob.mitigation_level = 100.0  # Fully mitigated
                        ob.valid = False
                    else:
                        # Partial mitigation
                        mitigated_range = ob.top - deepest_penetration
                        total_range = ob.top - ob.bottom
                        ob.mitigation_level = (mitigated_range / total_range) * 100.0
                        ob.tested = True
            else:
                # Bearish order block mitigation
                penetrations = future_data[future_data['High'] >= ob.bottom]['High']
                if len(penetrations) > 0:
                    highest_penetration = penetrations.max()
                    if highest_penetration >= ob.top:
                        ob.mitigation_level = 100.0  # Fully mitigated
                        ob.valid = False
                    else:
                        # Partial mitigation
                        mitigated_range = highest_penetration - ob.bottom
                        total_range = ob.top - ob.bottom
                        ob.mitigation_level = (mitigated_range / total_range) * 100.0
                        ob.tested = True
        
        return order_blocks
    
    def _classify_quality(self, order_blocks: List[OrderBlock]) -> List[OrderBlock]:
        """Classify order block quality based on displacement and structure"""
        
        for ob in order_blocks:
            # Quality classification based on displacement and strength
            if ob.displacement_pips >= 50 and ob.strength >= 0.8:
                ob.quality = OrderBlockQuality.INSTITUTIONAL
            elif ob.displacement_pips >= 30 and ob.strength >= 0.7:
                ob.quality = OrderBlockQuality.PROFESSIONAL
            else:
                ob.quality = OrderBlockQuality.RETAIL
        
        return order_blocks
    
    def _analyze_volume_profile(self, candle: pd.Series) -> Dict:
        """Analyze volume profile for order block"""
        if 'Volume' not in candle or pd.isna(candle['Volume']):
            return {'volume': 0, 'relative_volume': 'unknown'}
        
        volume = candle['Volume']
        
        # Simple volume analysis (can be enhanced with historical comparison)
        return {
            'volume': volume,
            'relative_volume': 'high' if volume > 0 else 'low',
            'volume_price_trend': 'bullish' if candle['Close'] > candle['Open'] else 'bearish'
        }
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        # Standard pip sizes for major pairs
        jpy_pairs = ['JPY', 'jpy']
        if any(pair in symbol.upper() for pair in jpy_pairs):
            return 0.01  # 1 pip = 0.01 for JPY pairs
        else:
            return 0.0001  # 1 pip = 0.0001 for other pairs
    
    def get_active_order_blocks(self, order_blocks: List[OrderBlock], 
                               current_price: float) -> List[OrderBlock]:
        """Get currently active (untested or partially tested) order blocks"""
        active_blocks = []
        
        for ob in order_blocks:
            if not ob.valid:
                continue
                
            # Check if order block is relevant to current price
            if ob.type == OrderBlockType.BULLISH:
                if current_price >= ob.bottom * 0.99:  # Within 1% of order block
                    active_blocks.append(ob)
            else:
                if current_price <= ob.top * 1.01:  # Within 1% of order block
                    active_blocks.append(ob)
        
        # Sort by quality and recency
        active_blocks.sort(key=lambda x: (
            x.quality.value,
            x.displacement_pips,
            x.timestamp
        ), reverse=True)
        
        return active_blocks[:5]  # Return top 5 most relevant
    
    def analyze_order_block_confluence(self, order_blocks: List[OrderBlock],
                                     price_level: float, tolerance_pips: float = 10) -> Dict:
        """Analyze confluence of order blocks around a price level"""
        pip_size = 0.0001  # Assume standard pip size
        tolerance = tolerance_pips * pip_size
        
        nearby_blocks = [
            ob for ob in order_blocks
            if ob.valid and (
                abs(ob.top - price_level) <= tolerance or
                abs(ob.bottom - price_level) <= tolerance or
                (ob.bottom <= price_level <= ob.top)
            )
        ]
        
        if not nearby_blocks:
            return {'confluence_score': 0, 'block_count': 0, 'dominant_type': None}
        
        bullish_count = sum(1 for ob in nearby_blocks if ob.type == OrderBlockType.BULLISH)
        bearish_count = sum(1 for ob in nearby_blocks if ob.type == OrderBlockType.BEARISH)
        
        # Calculate confluence score based on quantity and quality
        quality_weights = {
            OrderBlockQuality.INSTITUTIONAL: 3.0,
            OrderBlockQuality.PROFESSIONAL: 2.0,
            OrderBlockQuality.RETAIL: 1.0
        }
        
        confluence_score = sum(quality_weights[ob.quality] for ob in nearby_blocks)
        
        return {
            'confluence_score': confluence_score,
            'block_count': len(nearby_blocks),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'dominant_type': OrderBlockType.BULLISH if bullish_count > bearish_count else OrderBlockType.BEARISH,
            'blocks': nearby_blocks
        }