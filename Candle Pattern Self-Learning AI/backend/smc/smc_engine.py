"""
Smart Money Concepts (SMC) Detection Engine
Implements Order Blocks, Fair Value Gaps, BOS/CHOCH, Liquidity Sweeps
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OrderBlock:
    """Order Block data structure"""
    start_idx: int
    end_idx: int
    price_high: float
    price_low: float
    type: str  # 'bullish' or 'bearish'
    strength: float
    unmitigated: bool = True
    proximity_score: float = 0.0


@dataclass
class FairValueGap:
    """Fair Value Gap data structure"""
    idx: int
    gap_high: float
    gap_low: float
    size_pips: float
    type: str  # 'bullish' or 'bearish'
    mitigated: bool = False


@dataclass
class LiquiditySweep:
    """Liquidity Sweep data structure"""
    idx: int
    price: float
    type: str  # 'high' or 'low'
    swept_level: float
    reversal_confirmed: bool = False


class SMCEngine:
    """Smart Money Concepts Detection Engine"""
    
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.ob_lookback = self.settings.get('ob_lookback', 30)
        self.swing_length = self.settings.get('swing_length', 20)
        self.fvg_min_size_pips = self.settings.get('fvg_min_size_pips', 8.0)
    
    def detect_order_blocks(self, df: pd.DataFrame, lookback: int = None) -> List[OrderBlock]:
        """
        Detect Order Blocks (OB)
        OB = Last opposing candle before strong impulse move
        """
        if lookback is None:
            lookback = self.ob_lookback
        
        order_blocks = []
        
        # Calculate momentum for impulse detection
        df['momentum'] = df['Close'].diff(3)
        
        for i in range(lookback, len(df) - 5):
            # Look for strong bullish impulse
            if df['momentum'].iloc[i:i+3].mean() > 0:
                # Find last bearish candle before impulse
                for j in range(i-1, max(0, i-lookback), -1):
                    if df['Close'].iloc[j] < df['Open'].iloc[j]:  # Bearish candle
                        # Check if followed by strong bullish move
                        future_high = df['High'].iloc[j+1:j+5].max()
                        if future_high > df['High'].iloc[j]:
                            strength = (future_high - df['High'].iloc[j]) / df['High'].iloc[j]
                            
                            ob = OrderBlock(
                                start_idx=j,
                                end_idx=j,
                                price_high=df['High'].iloc[j],
                                price_low=df['Low'].iloc[j],
                                type='bullish',
                                strength=strength
                            )
                            order_blocks.append(ob)
                            break
            
            # Look for strong bearish impulse
            elif df['momentum'].iloc[i:i+3].mean() < 0:
                # Find last bullish candle before impulse
                for j in range(i-1, max(0, i-lookback), -1):
                    if df['Close'].iloc[j] > df['Open'].iloc[j]:  # Bullish candle
                        # Check if followed by strong bearish move
                        future_low = df['Low'].iloc[j+1:j+5].min()
                        if future_low < df['Low'].iloc[j]:
                            strength = (df['Low'].iloc[j] - future_low) / df['Low'].iloc[j]
                            
                            ob = OrderBlock(
                                start_idx=j,
                                end_idx=j,
                                price_high=df['High'].iloc[j],
                                price_low=df['Low'].iloc[j],
                                type='bearish',
                                strength=strength
                            )
                            order_blocks.append(ob)
                            break
        
        # Check mitigation
        current_price = df['Close'].iloc[-1]
        for ob in order_blocks:
            if ob.type == 'bullish':
                # Bullish OB is mitigated if price goes through it downward
                if current_price < ob.price_low:
                    ob.unmitigated = False
            else:
                # Bearish OB is mitigated if price goes through it upward
                if current_price > ob.price_high:
                    ob.unmitigated = False
            
            # Calculate proximity score
            ob_mid = (ob.price_high + ob.price_low) / 2
            distance = abs(current_price - ob_mid)
            ob_range = ob.price_high - ob.price_low
            if ob_range > 0:
                ob.proximity_score = 1 - min(distance / ob_range, 1.0)
        
        return order_blocks
    
    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (FVG)
        FVG = Gap between candles where no trading occurred
        """
        fvgs = []
        pip_size = 0.0001  # For forex pairs
        
        for i in range(2, len(df)):
            # Bullish FVG: Gap between candle[i-2] low and candle[i] high
            gap_low = df['Low'].iloc[i]
            gap_high = df['High'].iloc[i-2]
            
            if gap_low > gap_high:  # There's a gap
                gap_size_pips = (gap_low - gap_high) / pip_size
                
                if gap_size_pips >= self.fvg_min_size_pips:
                    # Check if gap was created by bullish move
                    if df['Close'].iloc[i-1] > df['Close'].iloc[i-2]:
                        fvg = FairValueGap(
                            idx=i,
                            gap_high=gap_low,
                            gap_low=gap_high,
                            size_pips=gap_size_pips,
                            type='bullish'
                        )
                        fvgs.append(fvg)
            
            # Bearish FVG: Gap between candle[i-2] high and candle[i] low
            gap_high = df['High'].iloc[i]
            gap_low = df['Low'].iloc[i-2]
            
            if gap_high < gap_low:  # There's a gap
                gap_size_pips = (gap_low - gap_high) / pip_size
                
                if gap_size_pips >= self.fvg_min_size_pips:
                    # Check if gap was created by bearish move
                    if df['Close'].iloc[i-1] < df['Close'].iloc[i-2]:
                        fvg = FairValueGap(
                            idx=i,
                            gap_high=gap_low,
                            gap_low=gap_high,
                            size_pips=gap_size_pips,
                            type='bearish'
                        )
                        fvgs.append(fvg)
        
        # Check mitigation
        for fvg in fvgs:
            for i in range(fvg.idx + 1, len(df)):
                if fvg.type == 'bullish':
                    # Mitigated if price enters the gap from above
                    if df['Low'].iloc[i] <= fvg.gap_high:
                        fvg.mitigated = True
                        break
                else:
                    # Mitigated if price enters the gap from below
                    if df['High'].iloc[i] >= fvg.gap_low:
                        fvg.mitigated = True
                        break
        
        return fvgs
    
    def detect_structure_breaks(self, df: pd.DataFrame) -> Dict[str, List]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHOCH)
        """
        # Find swing points
        swing_highs, swing_lows = self._find_swing_points(df, self.swing_length)
        
        bos_list = []
        choch_list = []
        
        # Analyze structure breaks
        for i in range(len(swing_highs) - 1):
            if i < len(swing_highs) - 1:
                current_high = swing_highs[i]
                next_high = swing_highs[i + 1]
                
                # Bullish BOS: Breaking previous swing high
                if next_high > current_high:
                    bos_list.append({
                        'idx': swing_highs.index[i + 1],
                        'type': 'bullish_bos',
                        'level': next_high
                    })
                # Bearish CHOCH: Failing to make higher high
                elif next_high < current_high:
                    choch_list.append({
                        'idx': swing_highs.index[i + 1],
                        'type': 'bearish_choch',
                        'level': next_high
                    })
        
        for i in range(len(swing_lows) - 1):
            if i < len(swing_lows) - 1:
                current_low = swing_lows[i]
                next_low = swing_lows[i + 1]
                
                # Bearish BOS: Breaking previous swing low
                if next_low < current_low:
                    bos_list.append({
                        'idx': swing_lows.index[i + 1],
                        'type': 'bearish_bos',
                        'level': next_low
                    })
                # Bullish CHOCH: Failing to make lower low
                elif next_low > current_low:
                    choch_list.append({
                        'idx': swing_lows.index[i + 1],
                        'type': 'bullish_choch',
                        'level': next_low
                    })
        
        return {
            'bos': bos_list,
            'choch': choch_list,
            'swing_highs': swing_highs.to_dict(),
            'swing_lows': swing_lows.to_dict()
        }
    
    def detect_liquidity_sweeps(self, df: pd.DataFrame) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps (stop hunts)
        """
        sweeps = []
        
        # Find swing points as liquidity levels
        swing_highs, swing_lows = self._find_swing_points(df, self.swing_length)
        
        # Check for sweeps of swing highs
        for swing_idx, swing_high in swing_highs.items():
            for i in range(swing_idx + 1, len(df)):
                # Check if high was swept (price went above then reversed)
                if df['High'].iloc[i] > swing_high:
                    # Check for reversal
                    if i < len(df) - 3:
                        reversal = df['Close'].iloc[i+1:i+4].min() < swing_high
                        
                        sweep = LiquiditySweep(
                            idx=i,
                            price=df['High'].iloc[i],
                            type='high',
                            swept_level=swing_high,
                            reversal_confirmed=reversal
                        )
                        sweeps.append(sweep)
                        break
        
        # Check for sweeps of swing lows
        for swing_idx, swing_low in swing_lows.items():
            for i in range(swing_idx + 1, len(df)):
                # Check if low was swept (price went below then reversed)
                if df['Low'].iloc[i] < swing_low:
                    # Check for reversal
                    if i < len(df) - 3:
                        reversal = df['Close'].iloc[i+1:i+4].max() > swing_low
                        
                        sweep = LiquiditySweep(
                            idx=i,
                            price=df['Low'].iloc[i],
                            type='low',
                            swept_level=swing_low,
                            reversal_confirmed=reversal
                        )
                        sweeps.append(sweep)
                        break
        
        return sweeps
    
    def _find_swing_points(self, df: pd.DataFrame, length: int) -> Tuple[pd.Series, pd.Series]:
        """Find swing high and swing low points"""
        swing_highs = pd.Series(dtype=float)
        swing_lows = pd.Series(dtype=float)
        
        for i in range(length, len(df) - length):
            # Swing high: highest point in window
            if df['High'].iloc[i] == df['High'].iloc[i-length:i+length+1].max():
                swing_highs[i] = df['High'].iloc[i]
            
            # Swing low: lowest point in window
            if df['Low'].iloc[i] == df['Low'].iloc[i-length:i+length+1].min():
                swing_lows[i] = df['Low'].iloc[i]
        
        return swing_highs, swing_lows
    
    def get_smc_analysis(self, df: pd.DataFrame) -> Dict:
        """Get comprehensive SMC analysis"""
        order_blocks = self.detect_order_blocks(df)
        fvgs = self.detect_fair_value_gaps(df)
        structure = self.detect_structure_breaks(df)
        sweeps = self.detect_liquidity_sweeps(df)
        
        # Filter for active/unmitigated elements
        active_obs = [ob for ob in order_blocks if ob.unmitigated]
        active_fvgs = [fvg for fvg in fvgs if not fvg.mitigated]
        confirmed_sweeps = [s for s in sweeps if s.reversal_confirmed]
        
        return {
            'order_blocks': {
                'all': order_blocks,
                'active': active_obs,
                'bullish': [ob for ob in active_obs if ob.type == 'bullish'],
                'bearish': [ob for ob in active_obs if ob.type == 'bearish']
            },
            'fair_value_gaps': {
                'all': fvgs,
                'active': active_fvgs,
                'bullish': [fvg for fvg in active_fvgs if fvg.type == 'bullish'],
                'bearish': [fvg for fvg in active_fvgs if fvg.type == 'bearish']
            },
            'structure': structure,
            'liquidity_sweeps': {
                'all': sweeps,
                'confirmed': confirmed_sweeps
            }
        }
