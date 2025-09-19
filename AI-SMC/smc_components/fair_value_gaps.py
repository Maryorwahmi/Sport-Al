"""
Advanced Fair Value Gap Analysis with 3-Candle Pattern Detection
Implements institutional-grade FVG identification with mitigation tracking
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime

class FVGType(Enum):
    """Fair Value Gap type classification"""
    BULLISH = "BULLISH"  # Gap up - buy opportunity
    BEARISH = "BEARISH"  # Gap down - sell opportunity

class FVGQuality(Enum):
    """Fair Value Gap quality rating"""
    INSTITUTIONAL = "INSTITUTIONAL"  # Large gap, strong momentum
    PROFESSIONAL = "PROFESSIONAL"   # Medium gap, good momentum
    RETAIL = "RETAIL"               # Small gap, weak momentum

class MitigationLevel(Enum):
    """FVG mitigation classification"""
    UNTESTED = "UNTESTED"           # 0% mitigation
    PARTIAL_25 = "PARTIAL_25"       # 0-25% mitigation
    PARTIAL_75 = "PARTIAL_75"       # 25-75% mitigation
    NEARLY_FILLED = "NEARLY_FILLED" # 75-100% mitigation
    FILLED = "FILLED"               # 100% filled - invalid

@dataclass
class FairValueGap:
    """Fair Value Gap data structure"""
    timestamp: datetime
    type: FVGType
    top: float
    bottom: float
    size_pips: float
    quality: FVGQuality
    mitigation_level: MitigationLevel = MitigationLevel.UNTESTED
    mitigation_percentage: float = 0.0
    filled: bool = False
    entry_zone_top: float = 0.0   # 25% from gap edge
    entry_zone_bottom: float = 0.0 # 75% from gap edge
    volume_profile: Optional[Dict] = None
    momentum_score: float = 0.0
    confluence_factors: List[str] = None

class FairValueGapAnalyzer:
    """
    Advanced Fair Value Gap Analysis Engine
    
    Implements institutional-grade FVG detection with:
    - 3-candle pattern validation
    - Mitigation tracking (0-25%, 25-75%, 75-100%)
    - Quality classification based on size and momentum
    - Entry zone optimization
    - Volume profile analysis
    """
    
    def __init__(self,
                 min_gap_size_pips: float = 5.0,
                 enable_volume_analysis: bool = True,
                 require_momentum_confirmation: bool = True,
                 max_gap_age_bars: int = 50):
        """
        Initialize Fair Value Gap Analyzer
        
        Args:
            min_gap_size_pips: Minimum gap size in pips
            enable_volume_analysis: Enable volume analysis
            require_momentum_confirmation: Require momentum for validation
            max_gap_age_bars: Maximum age in bars for active gaps
        """
        self.min_gap_size_pips = min_gap_size_pips
        self.enable_volume_analysis = enable_volume_analysis
        self.require_momentum_confirmation = require_momentum_confirmation
        self.max_gap_age_bars = max_gap_age_bars
        
    def detect_fair_value_gaps(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> List[FairValueGap]:
        """
        Detect Fair Value Gaps using 3-candle pattern
        
        Args:
            df: OHLC DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
            symbol: Symbol name for pip calculation
            
        Returns:
            List of detected Fair Value Gaps
        """
        if len(df) < 3:
            return []
        
        fvgs = []
        pip_size = self._get_pip_size(symbol)
        
        # Need at least 3 candles for FVG pattern
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]  # First candle
            candle2 = df.iloc[i-1]  # Middle candle (gap candle)
            candle3 = df.iloc[i]    # Third candle (continuation)
            
            # Check for bullish FVG
            bullish_fvg = self._detect_bullish_fvg(
                candle1, candle2, candle3, df.index[i-1], pip_size
            )
            if bullish_fvg:
                fvgs.append(bullish_fvg)
            
            # Check for bearish FVG
            bearish_fvg = self._detect_bearish_fvg(
                candle1, candle2, candle3, df.index[i-1], pip_size
            )
            if bearish_fvg:
                fvgs.append(bearish_fvg)
        
        # Post-process FVGs
        fvgs = self._calculate_mitigation_levels(fvgs, df)
        fvgs = self._classify_quality(fvgs)
        fvgs = self._calculate_entry_zones(fvgs)
        
        return fvgs
    
    def _detect_bullish_fvg(self, candle1: pd.Series, candle2: pd.Series, 
                           candle3: pd.Series, timestamp: datetime, 
                           pip_size: float) -> Optional[FairValueGap]:
        """
        Detect bullish Fair Value Gap pattern
        
        Pattern: candle1.high < candle3.low (gap between them)
        candle2 creates the gap with strong upward movement
        """
        
        # Check for gap: candle1 high < candle3 low
        if candle1['High'] >= candle3['Low']:
            return None
        
        gap_size = candle3['Low'] - candle1['High']
        gap_size_pips = gap_size / pip_size
        
        # Must meet minimum size requirement
        if gap_size_pips < self.min_gap_size_pips:
            return None
        
        # Validate momentum (candle2 should be strongly bullish)
        if self.require_momentum_confirmation:
            candle2_body = candle2['Close'] - candle2['Open']
            if candle2_body <= 0:  # Must be bullish candle
                return None
        
        # Calculate momentum score
        momentum_score = self._calculate_momentum_score([candle1, candle2, candle3])
        
        # Create FVG
        fvg = FairValueGap(
            timestamp=timestamp,
            type=FVGType.BULLISH,
            top=candle3['Low'],
            bottom=candle1['High'],
            size_pips=gap_size_pips,
            quality=FVGQuality.RETAIL,  # Will be classified later
            volume_profile=self._analyze_volume_profile([candle1, candle2, candle3]) if self.enable_volume_analysis else None,
            momentum_score=momentum_score,
            confluence_factors=[]
        )
        
        return fvg
    
    def _detect_bearish_fvg(self, candle1: pd.Series, candle2: pd.Series,
                           candle3: pd.Series, timestamp: datetime,
                           pip_size: float) -> Optional[FairValueGap]:
        """
        Detect bearish Fair Value Gap pattern
        
        Pattern: candle1.low > candle3.high (gap between them)
        candle2 creates the gap with strong downward movement
        """
        
        # Check for gap: candle1 low > candle3 high
        if candle1['Low'] <= candle3['High']:
            return None
        
        gap_size = candle1['Low'] - candle3['High']
        gap_size_pips = gap_size / pip_size
        
        # Must meet minimum size requirement
        if gap_size_pips < self.min_gap_size_pips:
            return None
        
        # Validate momentum (candle2 should be strongly bearish)
        if self.require_momentum_confirmation:
            candle2_body = candle2['Close'] - candle2['Open']
            if candle2_body >= 0:  # Must be bearish candle
                return None
        
        # Calculate momentum score
        momentum_score = self._calculate_momentum_score([candle1, candle2, candle3])
        
        # Create FVG
        fvg = FairValueGap(
            timestamp=timestamp,
            type=FVGType.BEARISH,
            top=candle1['Low'],
            bottom=candle3['High'],
            size_pips=gap_size_pips,
            quality=FVGQuality.RETAIL,  # Will be classified later
            volume_profile=self._analyze_volume_profile([candle1, candle2, candle3]) if self.enable_volume_analysis else None,
            momentum_score=momentum_score,
            confluence_factors=[]
        )
        
        return fvg
    
    def _calculate_mitigation_levels(self, fvgs: List[FairValueGap], 
                                   df: pd.DataFrame) -> List[FairValueGap]:
        """Calculate mitigation levels for all FVGs"""
        
        for fvg in fvgs:
            fvg_index = df.index.get_loc(fvg.timestamp)
            future_data = df.iloc[fvg_index+1:]
            
            if len(future_data) == 0:
                continue
            
            if fvg.type == FVGType.BULLISH:
                # Check price action back into the gap
                penetrations = future_data[future_data['Low'] <= fvg.top]['Low']
                if len(penetrations) > 0:
                    deepest_penetration = penetrations.min()
                    
                    if deepest_penetration <= fvg.bottom:
                        # Gap completely filled
                        fvg.mitigation_percentage = 100.0
                        fvg.mitigation_level = MitigationLevel.FILLED
                        fvg.filled = True
                    else:
                        # Partial mitigation
                        mitigated_distance = fvg.top - deepest_penetration
                        total_gap_size = fvg.top - fvg.bottom
                        fvg.mitigation_percentage = (mitigated_distance / total_gap_size) * 100.0
                        
                        # Classify mitigation level
                        if fvg.mitigation_percentage < 25:
                            fvg.mitigation_level = MitigationLevel.PARTIAL_25
                        elif fvg.mitigation_percentage < 75:
                            fvg.mitigation_level = MitigationLevel.PARTIAL_75
                        else:
                            fvg.mitigation_level = MitigationLevel.NEARLY_FILLED
            else:
                # Bearish FVG mitigation
                penetrations = future_data[future_data['High'] >= fvg.bottom]['High']
                if len(penetrations) > 0:
                    highest_penetration = penetrations.max()
                    
                    if highest_penetration >= fvg.top:
                        # Gap completely filled
                        fvg.mitigation_percentage = 100.0
                        fvg.mitigation_level = MitigationLevel.FILLED
                        fvg.filled = True
                    else:
                        # Partial mitigation
                        mitigated_distance = highest_penetration - fvg.bottom
                        total_gap_size = fvg.top - fvg.bottom
                        fvg.mitigation_percentage = (mitigated_distance / total_gap_size) * 100.0
                        
                        # Classify mitigation level
                        if fvg.mitigation_percentage < 25:
                            fvg.mitigation_level = MitigationLevel.PARTIAL_25
                        elif fvg.mitigation_percentage < 75:
                            fvg.mitigation_level = MitigationLevel.PARTIAL_75
                        else:
                            fvg.mitigation_level = MitigationLevel.NEARLY_FILLED
        
        return fvgs
    
    def _classify_quality(self, fvgs: List[FairValueGap]) -> List[FairValueGap]:
        """Classify FVG quality based on size and momentum"""
        
        for fvg in fvgs:
            # Quality classification based on size and momentum
            if fvg.size_pips >= 20 and fvg.momentum_score >= 0.8:
                fvg.quality = FVGQuality.INSTITUTIONAL
            elif fvg.size_pips >= 10 and fvg.momentum_score >= 0.6:
                fvg.quality = FVGQuality.PROFESSIONAL
            else:
                fvg.quality = FVGQuality.RETAIL
        
        return fvgs
    
    def _calculate_entry_zones(self, fvgs: List[FairValueGap]) -> List[FairValueGap]:
        """Calculate optimal entry zones within FVGs"""
        
        for fvg in fvgs:
            gap_size = fvg.top - fvg.bottom
            
            if fvg.type == FVGType.BULLISH:
                # Entry zone: 25-75% from top (closest to gap edge)
                fvg.entry_zone_top = fvg.top - (gap_size * 0.25)
                fvg.entry_zone_bottom = fvg.top - (gap_size * 0.75)
            else:
                # Entry zone: 25-75% from bottom (closest to gap edge)
                fvg.entry_zone_bottom = fvg.bottom + (gap_size * 0.25)
                fvg.entry_zone_top = fvg.bottom + (gap_size * 0.75)
        
        return fvgs
    
    def _calculate_momentum_score(self, candles: List[pd.Series]) -> float:
        """Calculate momentum score for FVG validation"""
        if len(candles) < 3:
            return 0.0
        
        candle1, candle2, candle3 = candles
        
        # Analyze momentum factors
        factors = []
        
        # Body size factor (larger bodies = stronger momentum)
        body2_size = abs(candle2['Close'] - candle2['Open'])
        range2_size = candle2['High'] - candle2['Low']
        if range2_size > 0:
            body_ratio = body2_size / range2_size
            factors.append(body_ratio)
        
        # Continuation factor (candle3 continues direction)
        direction2 = 1 if candle2['Close'] > candle2['Open'] else -1
        direction3 = 1 if candle3['Close'] > candle3['Open'] else -1
        continuation_factor = 1.0 if direction2 == direction3 else 0.5
        factors.append(continuation_factor)
        
        # Range expansion factor
        avg_range = np.mean([c['High'] - c['Low'] for c in candles])
        range2_factor = min(1.0, (candle2['High'] - candle2['Low']) / avg_range)
        factors.append(range2_factor)
        
        return np.mean(factors) if factors else 0.0
    
    def _analyze_volume_profile(self, candles: List[pd.Series]) -> Dict:
        """Analyze volume profile for FVG validation"""
        volume_data = []
        
        for candle in candles:
            if 'Volume' in candle and not pd.isna(candle['Volume']):
                volume_data.append(candle['Volume'])
        
        if not volume_data:
            return {'volume_confirmation': 'unknown', 'relative_volume': 'unknown'}
        
        avg_volume = np.mean(volume_data)
        middle_volume = volume_data[1] if len(volume_data) >= 2 else volume_data[0]
        
        # Volume analysis
        volume_confirmation = 'strong' if middle_volume > avg_volume * 1.5 else 'weak'
        relative_volume = 'high' if middle_volume > avg_volume else 'normal'
        
        return {
            'volume_confirmation': volume_confirmation,
            'relative_volume': relative_volume,
            'average_volume': avg_volume,
            'gap_volume': middle_volume
        }
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        jpy_pairs = ['JPY', 'jpy']
        if any(pair in symbol.upper() for pair in jpy_pairs):
            return 0.01
        else:
            return 0.0001
    
    def get_active_fvgs(self, fvgs: List[FairValueGap], current_price: float) -> List[FairValueGap]:
        """Get active (unfilled or partially filled) FVGs relevant to current price"""
        active_fvgs = []
        
        for fvg in fvgs:
            # Skip filled FVGs
            if fvg.filled:
                continue
            
            # Check relevance to current price
            price_tolerance = (fvg.top - fvg.bottom) * 2  # 2x gap size tolerance
            
            if fvg.type == FVGType.BULLISH:
                if fvg.bottom <= current_price <= fvg.top + price_tolerance:
                    active_fvgs.append(fvg)
            else:
                if fvg.top >= current_price >= fvg.bottom - price_tolerance:
                    active_fvgs.append(fvg)
        
        # Sort by quality and recency
        active_fvgs.sort(key=lambda x: (
            x.quality.value,
            x.size_pips,
            x.timestamp
        ), reverse=True)
        
        return active_fvgs[:10]  # Return top 10 most relevant
    
    def analyze_fvg_confluence(self, fvgs: List[FairValueGap], 
                              price_level: float, tolerance_pips: float = 5) -> Dict:
        """Analyze confluence of FVGs around a price level"""
        pip_size = 0.0001  # Assume standard pip size
        tolerance = tolerance_pips * pip_size
        
        nearby_fvgs = []
        for fvg in fvgs:
            if fvg.filled:
                continue
                
            # Check if price level is near or within FVG
            if (abs(fvg.top - price_level) <= tolerance or
                abs(fvg.bottom - price_level) <= tolerance or
                (fvg.bottom <= price_level <= fvg.top)):
                nearby_fvgs.append(fvg)
        
        if not nearby_fvgs:
            return {'confluence_score': 0, 'fvg_count': 0, 'dominant_type': None}
        
        bullish_count = sum(1 for fvg in nearby_fvgs if fvg.type == FVGType.BULLISH)
        bearish_count = sum(1 for fvg in nearby_fvgs if fvg.type == FVGType.BEARISH)
        
        # Calculate confluence score based on quality and quantity
        quality_weights = {
            FVGQuality.INSTITUTIONAL: 3.0,
            FVGQuality.PROFESSIONAL: 2.0,
            FVGQuality.RETAIL: 1.0
        }
        
        confluence_score = sum(quality_weights[fvg.quality] for fvg in nearby_fvgs)
        
        return {
            'confluence_score': confluence_score,
            'fvg_count': len(nearby_fvgs),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'dominant_type': FVGType.BULLISH if bullish_count > bearish_count else FVGType.BEARISH,
            'gaps': nearby_fvgs,
            'entry_opportunities': [
                fvg for fvg in nearby_fvgs 
                if fvg.mitigation_level in [MitigationLevel.UNTESTED, MitigationLevel.PARTIAL_25]
            ]
        }