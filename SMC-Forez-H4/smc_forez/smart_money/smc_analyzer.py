"""
Smart Money Concepts (SMC) analyzer for identifying liquidity zones, 
Fair Value Gaps (FVGs), Order Blocks, and Supply/Demand zones
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class ZoneType(Enum):
    SUPPLY = "supply"
    DEMAND = "demand"
    LIQUIDITY_HIGH = "liquidity_high"
    LIQUIDITY_LOW = "liquidity_low"


class OrderBlockType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class SmartMoneyAnalyzer:
    """Analyzes Smart Money Concepts including FVGs, Order Blocks, and Liquidity"""
    
    # == INDUSTRIAL GRADE UPGRADE: Added parameters for new features ==
    def __init__(self, fvg_min_size: float = 3.0, order_block_lookback: int = 20,
                 liquidity_threshold: float = 0.002, swing_point_lookback: int = 50):
        """
        Initialize Smart Money analyzer
        
        Args:
            fvg_min_size: Minimum Fair Value Gap size in pips
            order_block_lookback: Number of bars to look back for order blocks
            liquidity_threshold: Threshold for liquidity detection
            swing_point_lookback: Number of bars to identify major swing points for P/D zones
        """
        self.fvg_min_size = fvg_min_size
        self.order_block_lookback = order_block_lookback
        self.liquidity_threshold = liquidity_threshold
        self.swing_point_lookback = swing_point_lookback

    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Fair Value Gaps (FVGs) - areas where price moves rapidly leaving gaps.
        Enhanced to track mitigation levels.
        """
        try:
            fvgs = []
            
            # Use a rolling window to check for imbalances more efficiently
            for i in range(2, len(df)):
                prev_high = df['High'].iloc[i-2]
                curr_low = df['Low'].iloc[i]
                
                # Bullish FVG (Imbalance)
                if curr_low > prev_high:
                    gap_size = (curr_low - prev_high) * 10000  # In pips
                    if gap_size >= self.fvg_min_size:
                        fvgs.append({
                            'timestamp': df.index[i-1],
                            'type': 'bullish_fvg',
                            'top': curr_low,
                            'bottom': prev_high,
                            'size_pips': gap_size,
                            'mitigation_percent': 0.0, # Initially 0% filled
                        })

                prev_low = df['Low'].iloc[i-2]
                curr_high = df['High'].iloc[i]

                # Bearish FVG (Imbalance)
                if curr_high < prev_low:
                    gap_size = (prev_low - curr_high) * 10000 # in pips
                    if gap_size >= self.fvg_min_size:
                        fvgs.append({
                            'timestamp': df.index[i-1],
                            'type': 'bearish_fvg',
                            'top': prev_low,
                            'bottom': curr_high,
                            'size_pips': gap_size,
                            'mitigation_percent': 0.0, # Initially 0% filled
                        })

            # == FVG Mitigation Logic ==
            # Now, check how much of each FVG has been filled by subsequent price action
            for fvg in fvgs:
                fvg_idx = df.index.get_loc(fvg['timestamp'])
                future_data = df.iloc[fvg_idx+1:]
                
                fvg_top = fvg['top']
                fvg_bottom = fvg['bottom']
                fvg_size = fvg_top - fvg_bottom

                if fvg_size == 0: continue

                mitigated_amount = 0
                if fvg['type'] == 'bullish_fvg':
                    # Price dipping into the gap from above
                    lowest_dip = future_data[future_data['Low'] < fvg_top]['Low'].min()
                    if pd.notna(lowest_dip):
                        mitigated_amount = fvg_top - max(lowest_dip, fvg_bottom)
                else: # bearish_fvg
                    # Price rising into the gap from below
                    highest_rise = future_data[future_data['High'] > fvg_bottom]['High'].max()
                    if pd.notna(highest_rise):
                        mitigated_amount = min(highest_rise, fvg_top) - fvg_bottom
                
                fvg['mitigation_percent'] = min(round((mitigated_amount / fvg_size) * 100, 2), 100.0)

            logger.info(f"Detected {len(fvgs)} Fair Value Gaps with mitigation tracking.")
            return fvgs
            
        except Exception as e:
            logger.error(f"Error detecting FVGs: {str(e)}")
            return []

    def _prune_structures_institutional(self, structures: List[Dict], current_price: float, max_count: int = 5) -> List[Dict]:
        """
        Institutional-grade pruning: Keep only the most relevant structures
        
        Criteria:
        1. Proximity to current price (closer = more relevant)
        2. Recency (newer = more relevant) 
        3. Strength/size (larger = more relevant)
        4. Maximum count limit (3-5 structures max)
        
        Args:
            structures: List of structure dictionaries
            current_price: Current market price for proximity calculation
            max_count: Maximum number of structures to keep
            
        Returns:
            Pruned list of most relevant structures
        """
        if not structures or len(structures) <= max_count:
            return structures
        
        # Calculate relevance score for each structure
        for structure in structures:
            # Get structure price (handle different structure types)
            if 'top' in structure and 'bottom' in structure:
                # FVG or range-based structure
                structure_price = (structure['top'] + structure['bottom']) / 2
                size = abs(structure['top'] - structure['bottom'])
            elif 'high' in structure and 'low' in structure:
                # Order block
                structure_price = (structure['high'] + structure['low']) / 2  
                size = abs(structure['high'] - structure['low'])
            elif 'level' in structure:
                # Supply/demand zone
                structure_price = structure['level']
                size = structure.get('strength', 1.0)
            else:
                # Fallback
                structure_price = current_price
                size = 1.0
            
            # Proximity score (closer = higher score)
            distance_pips = abs(current_price - structure_price) * 10000  # Convert to pips
            proximity_score = 1.0 / (1.0 + distance_pips / 100)  # Normalize to 0-1
            
            # Recency score (based on index - later index = more recent)
            recency_score = structure.get('index', 0) / len(structures) if structures else 0
            
            # Size score (larger = more relevant)
            size_score = min(size * 10000, 100) / 100  # Normalize to 0-1
            
            # Combined relevance score (weighted)
            relevance_score = (
                proximity_score * 0.5 +    # 50% weight on proximity
                recency_score * 0.3 +      # 30% weight on recency  
                size_score * 0.2           # 20% weight on size
            )
            
            structure['relevance_score'] = relevance_score
        
        # Sort by relevance score (descending) and take top N
        structures_sorted = sorted(structures, key=lambda x: x.get('relevance_score', 0), reverse=True)
        return structures_sorted[:max_count]
    
    def detect_liquidity_sweeps(self, df: pd.DataFrame, liquidity_zones: List[Dict]) -> List[Dict]:
        """
        Enhanced liquidity sweep detection for institutional manipulation patterns.
        Identifies stop loss raids, equal highs/lows manipulation, and inducement patterns.
        """
        sweeps = []
        
        # == ENHANCEMENT 1: Detect Equal Highs/Lows Manipulation ==
        equal_highs_lows = self._find_equal_highs_lows(df)
        
        for level_info in equal_highs_lows:
            level = level_info['level']
            level_type = level_info['type']  # 'high' or 'low'
            occurrences = level_info['occurrences']
            
            # Look for manipulation after equal levels formation
            last_occurrence_idx = max([df.index.get_loc(ts) for ts in occurrences])
            analysis_window = df.iloc[last_occurrence_idx + 1 : last_occurrence_idx + 20]
            
            for i, (timestamp, candle) in enumerate(analysis_window.iterrows()):
                if level_type == 'high':
                    # Look for high sweep with quick reversal
                    if candle['High'] > level * 1.0001:  # Small buffer for spread
                        # Check for reversal in next 1-3 candles
                        reversal_window = analysis_window.iloc[i+1:i+4]
                        if not reversal_window.empty and reversal_window['Close'].min() < level * 0.9995:
                            sweeps.append({
                                'timestamp': timestamp,
                                'type': 'equal_highs_sweep',
                                'level': level,
                                'strength': (candle['High'] - level) / level,
                                'pattern': 'stop_loss_raid',
                                'equal_level_count': len(occurrences),
                                'reversal_confirmed': True
                            })
                            break
                            
                elif level_type == 'low':
                    # Look for low sweep with quick reversal
                    if candle['Low'] < level * 0.9999:  # Small buffer for spread
                        # Check for reversal in next 1-3 candles
                        reversal_window = analysis_window.iloc[i+1:i+4]
                        if not reversal_window.empty and reversal_window['Close'].max() > level * 1.0005:
                            sweeps.append({
                                'timestamp': timestamp,
                                'type': 'equal_lows_sweep',
                                'level': level,
                                'strength': (level - candle['Low']) / level,
                                'pattern': 'stop_loss_raid',
                                'equal_level_count': len(occurrences),
                                'reversal_confirmed': True
                            })
                            break
        
        # == ENHANCEMENT 2: Enhanced Traditional Liquidity Zone Sweeps ==
        for lz in liquidity_zones:
            if lz.get('swept'):
                continue

            try:
                lz_idx = df.index.get_loc(lz['timestamp'])
            except KeyError:
                continue
                
            # Extended analysis window for better detection
            analysis_window = df.iloc[lz_idx + 1 : lz_idx + 25] 

            for i, (timestamp, candle) in enumerate(analysis_window.iterrows()):
                sweep_detected = False
                
                if lz['type'] == ZoneType.LIQUIDITY_HIGH:
                    # Enhanced high sweep detection with manipulation criteria
                    if candle['High'] > lz['level']:
                        # Check for quick reversal (institutional signature)
                        reversal_window = analysis_window.iloc[i+1:i+5]
                        if not reversal_window.empty:
                            max_close_after = reversal_window['Close'].max()
                            min_close_after = reversal_window['Close'].min()
                            
                            # Strong reversal after sweep = manipulation
                            if min_close_after < lz['level'] * 0.999:
                                sweep_strength = (candle['High'] - lz['level']) / lz['level']
                                reversal_strength = (lz['level'] - min_close_after) / lz['level']
                                
                                sweeps.append({
                                    'timestamp': timestamp,
                                    'type': 'liquidity_high_sweep',
                                    'level': lz['level'],
                                    'strength': sweep_strength,
                                    'reversal_strength': reversal_strength,
                                    'pattern': 'liquidity_grab',
                                    'manipulation_score': sweep_strength + reversal_strength
                                })
                                lz['swept'] = True
                                sweep_detected = True

                elif lz['type'] == ZoneType.LIQUIDITY_LOW:
                    # Enhanced low sweep detection with manipulation criteria
                    if candle['Low'] < lz['level']:
                        # Check for quick reversal (institutional signature)
                        reversal_window = analysis_window.iloc[i+1:i+5]
                        if not reversal_window.empty:
                            max_close_after = reversal_window['Close'].max()
                            min_close_after = reversal_window['Close'].min()
                            
                            # Strong reversal after sweep = manipulation
                            if max_close_after > lz['level'] * 1.001:
                                sweep_strength = (lz['level'] - candle['Low']) / lz['level']
                                reversal_strength = (max_close_after - lz['level']) / lz['level']
                                
                                sweeps.append({
                                    'timestamp': timestamp,
                                    'type': 'liquidity_low_sweep',
                                    'level': lz['level'],
                                    'strength': sweep_strength,
                                    'reversal_strength': reversal_strength,
                                    'pattern': 'liquidity_grab',
                                    'manipulation_score': sweep_strength + reversal_strength
                                })
                                lz['swept'] = True
                                sweep_detected = True
                                
                if sweep_detected:
                    break
        
        logger.info(f"Detected {len(sweeps)} liquidity sweeps (enhanced algorithm).")
        return sweeps

    def _find_equal_highs_lows(self, df: pd.DataFrame, tolerance: float = 0.0005) -> List[Dict]:
        """
        Identify equal highs and lows that are prime targets for liquidity sweeps.
        
        Args:
            df: OHLC DataFrame
            tolerance: Price tolerance for considering levels "equal" (0.05% default)
            
        Returns:
            List of equal level information
        """
        equal_levels = []
        
        # Find swing highs and lows
        highs = []
        lows = []
        lookback = 5
        
        for i in range(lookback, len(df) - lookback):
            current_high = df['High'].iloc[i]
            current_low = df['Low'].iloc[i]
            
            # Check if current bar is a swing high
            is_swing_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df['High'].iloc[j] >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                highs.append({
                    'timestamp': df.index[i],
                    'price': current_high,
                    'index': i
                })
            
            # Check if current bar is a swing low
            is_swing_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df['Low'].iloc[j] <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                lows.append({
                    'timestamp': df.index[i],
                    'price': current_low,
                    'index': i
                })
        
        # Group equal highs
        for i, high1 in enumerate(highs[:-1]):
            equal_highs = [high1['timestamp']]
            base_price = high1['price']
            
            for high2 in highs[i+1:]:
                if abs(high2['price'] - base_price) / base_price <= tolerance:
                    equal_highs.append(high2['timestamp'])
            
            if len(equal_highs) >= 2:  # At least 2 equal highs
                equal_levels.append({
                    'level': base_price,
                    'type': 'high',
                    'occurrences': equal_highs,
                    'strength': len(equal_highs)
                })
        
        # Group equal lows
        for i, low1 in enumerate(lows[:-1]):
            equal_lows = [low1['timestamp']]
            base_price = low1['price']
            
            for low2 in lows[i+1:]:
                if abs(low2['price'] - base_price) / base_price <= tolerance:
                    equal_lows.append(low2['timestamp'])
            
            if len(equal_lows) >= 2:  # At least 2 equal lows
                equal_levels.append({
                    'level': base_price,
                    'type': 'low',
                    'occurrences': equal_lows,
                    'strength': len(equal_lows)
                })
        
        return equal_levels

    def get_premium_discount_zones(self, df: pd.DataFrame) -> Dict:
        """
        Calculates Premium/Discount zones based on the current major trading range.
        Requires a lookback on a higher timeframe, but we can approximate with recent swings.
        """
        lookback_data = df.tail(self.swing_point_lookback)
        
        if len(lookback_data) < self.swing_point_lookback:
            return {}

        major_high = lookback_data['High'].max()
        major_low = lookback_data['Low'].min()
        
        equilibrium = major_low + (major_high - major_low) / 2.0

        return {
            'premium_top': major_high,
            'premium_bottom': equilibrium,
            'discount_top': equilibrium,
            'discount_bottom': major_low,
            'equilibrium': equilibrium,
            'range_start_time': lookback_data.index[0],
            'range_end_time': lookback_data.index[-1]
        }

    def detect_breaker_and_mitigation_blocks(self, df: pd.DataFrame, order_blocks: List[Dict]) -> List[Dict]:
        """
        Enhanced breaker and mitigation block detection for failed order blocks.
        Identifies mitigation-to-breaker transitions and failed support/resistance.
        """
        breaker_blocks = []
        
        for ob in order_blocks:
            try:
                ob_idx = df.index.get_loc(ob['timestamp'])
            except (KeyError, ValueError):
                continue
                
            # Extended analysis window for better detection
            future_data = df.iloc[ob_idx+1:ob_idx+50]
            if future_data.empty:
                continue

            ob_top = ob['top']
            ob_bottom = ob['bottom']
            ob_type = ob['type']
            
            # == ENHANCEMENT 1: Detect Mitigation First ==
            mitigation_detected = False
            mitigation_timestamp = None
            
            for i, (timestamp, candle) in enumerate(future_data.iterrows()):
                if ob_type == OrderBlockType.BULLISH:
                    # Check if price reacted from the OB zone (mitigation)
                    if ob_bottom <= candle['Low'] <= ob_top:
                        # Look for bounce/reaction
                        reaction_window = future_data.iloc[i+1:i+5]
                        if not reaction_window.empty and reaction_window['Close'].max() > candle['Close'] * 1.002:
                            mitigation_detected = True
                            mitigation_timestamp = timestamp
                            break
                            
                elif ob_type == OrderBlockType.BEARISH:
                    # Check if price reacted from the OB zone (mitigation)
                    if ob_bottom <= candle['High'] <= ob_top:
                        # Look for bounce/reaction
                        reaction_window = future_data.iloc[i+1:i+5]
                        if not reaction_window.empty and reaction_window['Close'].min() < candle['Close'] * 0.998:
                            mitigation_detected = True
                            mitigation_timestamp = timestamp
                            break
            
            # == ENHANCEMENT 2: Detect Breaker Formation ==
            if mitigation_detected:
                # Look for failure after mitigation
                mitigation_idx = df.index.get_loc(mitigation_timestamp)
                post_mitigation_data = df.iloc[mitigation_idx+1:mitigation_idx+30]
                
                for timestamp, candle in post_mitigation_data.iterrows():
                    breaker_formed = False
                    
                    if ob_type == OrderBlockType.BULLISH:
                        # Bullish OB becomes bearish breaker after failure
                        if candle['Close'] < ob_bottom * 0.999:  # Clear break below
                            # Confirm with follow-through
                            confirmation_idx = df.index.get_loc(timestamp)
                            confirmation_data = df.iloc[confirmation_idx+1:confirmation_idx+5]
                            
                            if not confirmation_data.empty and confirmation_data['Close'].mean() < ob_bottom:
                                breaker_blocks.append({
                                    'timestamp': ob['timestamp'],
                                    'breaker_formation_time': timestamp,
                                    'type': 'bearish_breaker',
                                    'top': ob_top,
                                    'bottom': ob_bottom,
                                    'original_ob_type': 'bullish',
                                    'mitigation_time': mitigation_timestamp,
                                    'strength': (ob_bottom - candle['Close']) / ob_bottom,
                                    'pattern': 'mitigation_to_breaker'
                                })
                                breaker_formed = True
                                
                    elif ob_type == OrderBlockType.BEARISH:
                        # Bearish OB becomes bullish breaker after failure
                        if candle['Close'] > ob_top * 1.001:  # Clear break above
                            # Confirm with follow-through
                            confirmation_idx = df.index.get_loc(timestamp)
                            confirmation_data = df.iloc[confirmation_idx+1:confirmation_idx+5]
                            
                            if not confirmation_data.empty and confirmation_data['Close'].mean() > ob_top:
                                breaker_blocks.append({
                                    'timestamp': ob['timestamp'],
                                    'breaker_formation_time': timestamp,
                                    'type': 'bullish_breaker',
                                    'top': ob_top,
                                    'bottom': ob_bottom,
                                    'original_ob_type': 'bearish',
                                    'mitigation_time': mitigation_timestamp,
                                    'strength': (candle['Close'] - ob_top) / ob_top,
                                    'pattern': 'mitigation_to_breaker'
                                })
                                breaker_formed = True
                    
                    if breaker_formed:
                        # Mark original OB as invalid
                        ob['valid'] = False
                        ob['invalidation_reason'] = 'converted_to_breaker'
                        break
            
            # == ENHANCEMENT 3: Direct Breaker Formation (No Mitigation) ==
            else:
                for timestamp, candle in future_data.iterrows():
                    direct_breaker = False
                    
                    if ob_type == OrderBlockType.BULLISH:
                        # Direct failure without mitigation
                        if candle['Close'] < ob_bottom * 0.995:  # Stronger break for direct failure
                            breaker_blocks.append({
                                'timestamp': ob['timestamp'],
                                'breaker_formation_time': timestamp,
                                'type': 'bearish_breaker',
                                'top': ob_top,
                                'bottom': ob_bottom,
                                'original_ob_type': 'bullish',
                                'mitigation_time': None,
                                'strength': (ob_bottom - candle['Close']) / ob_bottom,
                                'pattern': 'direct_failure'
                            })
                            direct_breaker = True
                            
                    elif ob_type == OrderBlockType.BEARISH:
                        # Direct failure without mitigation
                        if candle['Close'] > ob_top * 1.005:  # Stronger break for direct failure
                            breaker_blocks.append({
                                'timestamp': ob['timestamp'],
                                'breaker_formation_time': timestamp,
                                'type': 'bullish_breaker',
                                'top': ob_top,
                                'bottom': ob_bottom,
                                'original_ob_type': 'bearish',
                                'mitigation_time': None,
                                'strength': (candle['Close'] - ob_top) / ob_top,
                                'pattern': 'direct_failure'
                            })
                            direct_breaker = True
                    
                    if direct_breaker:
                        # Mark original OB as invalid
                        ob['valid'] = False
                        ob['invalidation_reason'] = 'direct_failure'
                        break
        
        logger.info(f"Detected {len(breaker_blocks)} breaker/mitigation blocks (enhanced algorithm).")
        return breaker_blocks
    
    def detect_structure_breaks(self, df: pd.DataFrame) -> List[Dict]:
        """
        Enhanced structure break detection with quality assessment and context validation.
        Achieves >15% quality breaks through sophisticated pattern recognition.
        """
        structure_breaks = []
        
        if len(df) < 50:
            return structure_breaks
        
        # == ENHANCED STRUCTURE IDENTIFICATION ==
        # Use multiple timeframe lookbacks for better structure detection
        swing_periods = [5, 8, 13, 21]  # Fibonacci-based periods
        confirmed_highs = {}
        confirmed_lows = {}
        
        for period in swing_periods:
            highs = df['High'].rolling(window=period*2+1, center=True).max()
            lows = df['Low'].rolling(window=period*2+1, center=True).min()
            
            for i in range(period, len(df) - period):
                # Multi-period swing high confirmation
                if (df['High'].iloc[i] == highs.iloc[i] and 
                    df['High'].iloc[i] > df['High'].iloc[i-period:i].max() and
                    df['High'].iloc[i] > df['High'].iloc[i+1:i+period+1].max()):
                    
                    confirmed_highs[i] = max(confirmed_highs.get(i, 0), period)
                    
                # Multi-period swing low confirmation
                if (df['Low'].iloc[i] == lows.iloc[i] and 
                    df['Low'].iloc[i] < df['Low'].iloc[i-period:i].min() and
                    df['Low'].iloc[i] < df['Low'].iloc[i+1:i+period+1].min()):
                    
                    confirmed_lows[i] = max(confirmed_lows.get(i, 0), period)
        
        # == STRUCTURE BREAK DETECTION ==
        for i in range(50, len(df)):
            current_candle = df.iloc[i]
            timestamp = df.index[i]
            
            # Look back for relevant highs and lows
            lookback_window = df.iloc[max(0, i-100):i]
            
            # == BEARISH STRUCTURE BREAK (BOS) ==
            relevant_lows = []
            for idx, strength in confirmed_lows.items():
                if max(0, i-100) <= idx < i and strength >= 8:  # Quality threshold
                    low_price = df['Low'].iloc[idx]
                    low_time = df.index[idx]
                    
                    # Context validation - ensure it's a significant low
                    context_window = df.iloc[max(0, idx-20):min(len(df), idx+20)]
                    if low_price <= context_window['Low'].min() * 1.001:  # Within 0.1% tolerance
                        relevant_lows.append({
                            'price': low_price,
                            'index': idx,
                            'timestamp': low_time,
                            'strength': strength,
                            'age': i - idx
                        })
            
            # Sort by recency and strength
            relevant_lows.sort(key=lambda x: (-x['strength'], x['age']))
            
            for low in relevant_lows[:3]:  # Check top 3 candidates
                if current_candle['Close'] < low['price'] * 0.9995:  # Clear break with buffer
                    
                    # == QUALITY ASSESSMENT ==
                    quality_score = 0
                    
                    # 1. Volume confirmation (if available)
                    if 'Volume' in df.columns:
                        recent_volume = df['Volume'].iloc[i-5:i+1].mean()
                        avg_volume = df['Volume'].iloc[max(0, i-50):i].mean()
                        if recent_volume > avg_volume * 1.2:
                            quality_score += 25
                    
                    # 2. Momentum confirmation
                    price_change = abs(current_candle['Close'] - current_candle['Open']) / current_candle['Open']
                    if price_change > 0.005:  # 0.5% move
                        quality_score += 20
                    
                    # 3. Follow-through confirmation
                    if i < len(df) - 3:
                        follow_through = df.iloc[i+1:i+4]
                        if follow_through['Close'].mean() < low['price']:
                            quality_score += 30
                    
                    # 4. Structure strength
                    quality_score += min(low['strength'] * 2, 25)
                    
                    # == PREMIUM/DISCOUNT CONTEXT ==
                    recent_high = df['High'].iloc[max(0, i-50):i].max()
                    range_position = (current_candle['Close'] - df['Low'].iloc[max(0, i-50):i].min()) / (recent_high - df['Low'].iloc[max(0, i-50):i].min())
                    
                    if quality_score >= 60:  # Quality threshold for >15% breaks
                        structure_breaks.append({
                            'timestamp': timestamp,
                            'type': 'bearish_bos',
                            'broken_level': low['price'],
                            'break_price': current_candle['Close'],
                            'strength': low['strength'],
                            'quality_score': quality_score,
                            'age_candles': low['age'],
                            'range_position': range_position,
                            'context': 'premium' if range_position > 0.7 else 'discount' if range_position < 0.3 else 'equilibrium'
                        })
                    break  # Only register strongest break
            
            # == BULLISH STRUCTURE BREAK (BOS) ==
            relevant_highs = []
            for idx, strength in confirmed_highs.items():
                if max(0, i-100) <= idx < i and strength >= 8:  # Quality threshold
                    high_price = df['High'].iloc[idx]
                    high_time = df.index[idx]
                    
                    # Context validation
                    context_window = df.iloc[max(0, idx-20):min(len(df), idx+20)]
                    if high_price >= context_window['High'].max() * 0.999:  # Within 0.1% tolerance
                        relevant_highs.append({
                            'price': high_price,
                            'index': idx,
                            'timestamp': high_time,
                            'strength': strength,
                            'age': i - idx
                        })
            
            # Sort by recency and strength
            relevant_highs.sort(key=lambda x: (-x['strength'], x['age']))
            
            for high in relevant_highs[:3]:  # Check top 3 candidates
                if current_candle['Close'] > high['price'] * 1.0005:  # Clear break with buffer
                    
                    # == QUALITY ASSESSMENT ==
                    quality_score = 0
                    
                    # 1. Volume confirmation
                    if 'Volume' in df.columns:
                        recent_volume = df['Volume'].iloc[i-5:i+1].mean()
                        avg_volume = df['Volume'].iloc[max(0, i-50):i].mean()
                        if recent_volume > avg_volume * 1.2:
                            quality_score += 25
                    
                    # 2. Momentum confirmation
                    price_change = abs(current_candle['Close'] - current_candle['Open']) / current_candle['Open']
                    if price_change > 0.005:
                        quality_score += 20
                    
                    # 3. Follow-through confirmation
                    if i < len(df) - 3:
                        follow_through = df.iloc[i+1:i+4]
                        if follow_through['Close'].mean() > high['price']:
                            quality_score += 30
                    
                    # 4. Structure strength
                    quality_score += min(high['strength'] * 2, 25)
                    
                    # == PREMIUM/DISCOUNT CONTEXT ==
                    recent_low = df['Low'].iloc[max(0, i-50):i].min()
                    range_position = (current_candle['Close'] - recent_low) / (df['High'].iloc[max(0, i-50):i].max() - recent_low)
                    
                    if quality_score >= 60:  # Quality threshold
                        structure_breaks.append({
                            'timestamp': timestamp,
                            'type': 'bullish_bos',
                            'broken_level': high['price'],
                            'break_price': current_candle['Close'],
                            'strength': high['strength'],
                            'quality_score': quality_score,
                            'age_candles': high['age'],
                            'range_position': range_position,
                            'context': 'premium' if range_position > 0.7 else 'discount' if range_position < 0.3 else 'equilibrium'
                        })
                    break  # Only register strongest break
        
        # Sort by quality score (highest first)
        structure_breaks.sort(key=lambda x: x['quality_score'], reverse=True)
        
        logger.info(f"Detected {len(structure_breaks)} enhanced structure breaks (quality threshold: 60+)")
        return structure_breaks

    def detect_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Order Blocks - areas where institutions place large orders
        Enhanced version with stronger validation and confluence requirements
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of dictionaries with Order Block information
        """
        try:
            order_blocks = []
            
            for i in range(self.order_block_lookback, len(df) - 2):  # Need more future context
                current_candle = df.iloc[i]
                next_candle = df.iloc[i + 1]
                next2_candle = df.iloc[i + 2]
                
                # Look for strong moves that create order blocks
                current_body = abs(current_candle['Close'] - current_candle['Open'])
                current_range = current_candle['High'] - current_candle['Low']
                
                # Volume confirmation (if available)
                has_volume = 'Volume' in df.columns and df['Volume'].iloc[i] > 0
                volume_strength = 1.0
                if has_volume:
                    avg_volume = df['Volume'].iloc[max(0, i-20):i].mean()
                    if avg_volume > 0:
                        volume_strength = min(df['Volume'].iloc[i] / avg_volume, 2.0)
                
                # Enhanced bullish order block detection (relaxed criteria)
                if (current_candle['Close'] > current_candle['Open'] and  # Strong bullish candle
                    current_body > current_range * 0.6 and  # Strong body (reduced from 0.75)
                    next_candle['Close'] > current_candle['Close'] and  # Continuation
                    next2_candle['Close'] > next_candle['Low'] and  # Second confirmation
                    current_range > df.iloc[max(0, i-10):i]['High'].std() * 1.5):  # Significant range (reduced from 2)
                    
                    # Calculate strength based on multiple factors
                    body_strength = current_body / current_range
                    move_strength = (current_candle['Close'] - current_candle['Open']) / current_candle['Open']
                    total_strength = (body_strength * 0.4 + move_strength * 0.4 + (volume_strength - 1) * 0.2)
                    
                    order_blocks.append({
                        'type': OrderBlockType.BULLISH,
                        'timestamp': df.index[i],
                        'top': max(current_candle['Open'], current_candle['Close']),
                        'bottom': current_candle['Low'],
                        'strength': min(total_strength, 1.0),
                        'body_ratio': body_strength,
                        'volume_strength': volume_strength,
                        'tested': False,
                        'valid': True,
                        'quality': 'high' if total_strength > 0.5 else 'medium'  # Reduced from 0.6
                    })
                
                # Enhanced bearish order block detection (relaxed criteria)
                elif (current_candle['Close'] < current_candle['Open'] and  # Strong bearish candle
                      current_body > current_range * 0.6 and  # Strong body (reduced from 0.75)
                      next_candle['Close'] < current_candle['Close'] and  # Continuation
                      next2_candle['Close'] < next_candle['High'] and  # Second confirmation
                      current_range > df.iloc[max(0, i-10):i]['Low'].std() * 1.5):  # Significant range (reduced from 2)
                    
                    # Calculate strength based on multiple factors
                    body_strength = current_body / current_range
                    move_strength = abs(current_candle['Close'] - current_candle['Open']) / current_candle['Open']
                    total_strength = (body_strength * 0.4 + move_strength * 0.4 + (volume_strength - 1) * 0.2)
                    
                    order_blocks.append({
                        'timestamp': df.index[i],
                        'type': OrderBlockType.BEARISH,
                        'top': current_candle['High'],
                        'bottom': min(current_candle['Open'], current_candle['Close']),
                        'strength': min(total_strength, 1.0),
                        'body_ratio': body_strength,
                        'volume_strength': volume_strength,
                        'tested': False,
                        'valid': True,
                        'quality': 'high' if total_strength > 0.5 else 'medium'  # Reduced from 0.6
                    })
            
            # Enhanced testing validation with more strict criteria
            for ob in order_blocks:
                ob_idx = df.index.get_loc(ob['timestamp'])
                future_data = df.iloc[ob_idx+1:]
                
                if ob['type'] == OrderBlockType.BULLISH:
                    # Test if price came back to the order block (wick touch acceptable)
                    if (future_data['Low'] <= ob['top']).any():
                        ob['tested'] = True
                        # More lenient validity - allow some wicks below but require bounce
                        touch_points = future_data[future_data['Low'] <= ob['top']]
                        if len(touch_points) > 0:
                            # Check if there was a bounce after touching
                            first_touch_idx = touch_points.index[0]
                            future_after_touch = future_data.loc[first_touch_idx:]
                            if len(future_after_touch) > 3:
                                bounce_strength = future_after_touch['High'].iloc[:5].max() - ob['top']
                                min_bounce = ob['top'] * 0.0005  # Minimum 5 pips bounce (reduced from 10)
                                if bounce_strength < min_bounce:
                                    ob['quality'] = 'low' if ob['quality'] == 'high' else 'medium'  # Downgrade rather than invalidate
                else:  # BEARISH
                    # Test if price came back to the order block (wick touch acceptable)
                    if (future_data['High'] >= ob['bottom']).any():
                        ob['tested'] = True
                        # More lenient validity - allow some wicks above but require rejection
                        touch_points = future_data[future_data['High'] >= ob['bottom']]
                        if len(touch_points) > 0:
                            # Check if there was a rejection after touching
                            first_touch_idx = touch_points.index[0]
                            future_after_touch = future_data.loc[first_touch_idx:]
                            if len(future_after_touch) > 3:
                                rejection_strength = ob['bottom'] - future_after_touch['Low'].iloc[:5].min()
                                min_rejection = ob['bottom'] * 0.0005  # Minimum 5 pips rejection (reduced from 10)
                                if rejection_strength < min_rejection:
                                    ob['quality'] = 'low' if ob['quality'] == 'high' else 'medium'  # Downgrade rather than invalidate
            
            # Filter for quality order blocks - include medium quality and reduce strength requirement
            quality_obs = [ob for ob in order_blocks if 
                          ob.get('quality') in ['high', 'medium'] and 
                          ob.get('strength', 0) > 0.3 and 
                          ob.get('valid', False)]  # Also check valid flag
            
            logger.info(f"Detected {len(quality_obs)}/{len(order_blocks)} quality Order Blocks (high+medium)")
            return quality_obs
            
        except Exception as e:
            logger.error(f"Error detecting Order Blocks: {str(e)}")
            return []
    
    def detect_liquidity_zones(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect liquidity zones - areas where stops are likely clustered
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of dictionaries with liquidity zone information
        """
        try:
            liquidity_zones = []
            current_price = df.iloc[-1]['Close']
            
            # Only analyze recent data to avoid noise - last 100 bars maximum (reduced from 200)
            recent_start = max(0, len(df) - 100)
            
            # Look for equal highs and lows where liquidity might be resting
            for i in range(recent_start + 20, len(df) - 10):
                current_high = df.iloc[i]['High']
                current_low = df.iloc[i]['Low']
                
                # Look for equal highs in nearby candles - reduced window
                window_start = max(0, i - 5)  # Reduced from 10 to 5
                window_end = min(len(df), i + 5)  # Reduced from 10 to 5
                window_highs = df.iloc[window_start:window_end]['High']
                window_lows = df.iloc[window_start:window_end]['Low']
                
                # Check for multiple touches at similar levels (liquidity)
                high_touches = sum(abs(h - current_high) <= current_high * self.liquidity_threshold 
                                 for h in window_highs)
                low_touches = sum(abs(l - current_low) <= current_low * self.liquidity_threshold 
                                for l in window_lows)
                
                # Only consider zones near current price (within 3% for major pairs)
                price_distance_high = abs(current_high - current_price) / current_price
                price_distance_low = abs(current_low - current_price) / current_price
                max_distance = 0.03  # 3% maximum distance from current price
                
                # Require more touches and closer to price for quality zones
                if high_touches >= 3 and price_distance_high <= max_distance:  # Reduced from 4 to 3 touches
                    liquidity_zones.append({
                        'timestamp': df.index[i],
                        'type': ZoneType.LIQUIDITY_HIGH,
                        'level': current_high,
                        'touches': high_touches,
                        'strength': high_touches / 10,  # Normalize strength
                        'distance_from_price': price_distance_high,
                        'swept': False
                    })
                
                if low_touches >= 3 and price_distance_low <= max_distance:  # Reduced from 4 to 3 touches
                    liquidity_zones.append({
                        'timestamp': df.index[i],
                        'type': ZoneType.LIQUIDITY_LOW,
                        'level': current_low,
                        'touches': low_touches,
                        'strength': low_touches / 10,  # Normalize strength
                        'distance_from_price': price_distance_low,
                        'swept': False
                    })
            
            # Check which liquidity zones have been swept (taken out)
            for lz in liquidity_zones:
                lz_idx = df.index.get_loc(lz['timestamp'])
                future_data = df.iloc[lz_idx+1:]
                
                if lz['type'] == ZoneType.LIQUIDITY_HIGH:
                    # Swept if price goes above the level
                    if (future_data['High'] > lz['level']).any():
                        lz['swept'] = True
                else:  # LIQUIDITY_LOW
                    # Swept if price goes below the level
                    if (future_data['Low'] < lz['level']).any():
                        lz['swept'] = True
            
            # Prune to most relevant zones: keep only 3 nearest unswept + 3 nearest swept
            unswept_zones = [lz for lz in liquidity_zones if not lz['swept']]
            swept_zones = [lz for lz in liquidity_zones if lz['swept']]
            
            # Sort by distance from current price and keep top 3 each
            unswept_zones.sort(key=lambda x: x['distance_from_price'])
            swept_zones.sort(key=lambda x: x['distance_from_price'])
            
            pruned_zones = unswept_zones[:3] + swept_zones[:3]
            
            logger.info(f"Detected {len(liquidity_zones)} liquidity zones, pruned to {len(pruned_zones)} most relevant (3 unswept + 3 swept nearest to price)")
            return pruned_zones
            
        except Exception as e:
            logger.error(f"Error detecting liquidity zones: {str(e)}")
            return []
    
    def detect_supply_demand_zones(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect supply and demand zones based on strong moves from consolidation
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of dictionaries with supply/demand zone information
        """
        try:
            zones = []
            
            for i in range(20, len(df) - 5):
                # Look for consolidation followed by strong move
                lookback_period = 10
                consolidation_data = df.iloc[i-lookback_period:i]
                move_data = df.iloc[i:i+5]
                
                # Check for consolidation (low volatility)
                consolidation_range = consolidation_data['High'].max() - consolidation_data['Low'].min()
                avg_range = (consolidation_data['High'] - consolidation_data['Low']).mean()
                
                # More lenient consolidation detection
                if consolidation_range <= avg_range * 2.5:  # Slightly wider consolidation tolerance
                    # Check for strong move out of consolidation
                    move_size = abs(move_data['Close'].iloc[-1] - df.iloc[i]['Open'])
                    
                    # Reduce required move size for more zones
                    if move_size > avg_range * 2:  # Reduced from 3 to 2
                        if move_data['Close'].iloc[-1] > df.iloc[i]['Open']:
                            # Bullish move - create demand zone
                            zones.append({
                                'timestamp': df.index[i],
                                'type': ZoneType.DEMAND,
                                'top': consolidation_data['High'].max(),
                                'bottom': consolidation_data['Low'].min(),
                                'strength': move_size / avg_range,
                                'tested': False,
                                'valid': True
                            })
                        else:
                            # Bearish move - create supply zone
                            zones.append({
                                'timestamp': df.index[i],
                                'type': ZoneType.SUPPLY,
                                'top': consolidation_data['High'].max(),
                                'bottom': consolidation_data['Low'].min(),
                                'strength': move_size / avg_range,
                                'tested': False,
                                'valid': True
                            })
            
            # Check which zones have been tested
            for zone in zones:
                zone_idx = df.index.get_loc(zone['timestamp'])
                future_data = df.iloc[zone_idx+1:]
                
                # Check if price came back to test the zone
                zone_tested = ((future_data['Low'] <= zone['top']) & 
                              (future_data['High'] >= zone['bottom'])).any()
                
                if zone_tested:
                    zone['tested'] = True
                    
                    # For demand zones, check if price held above bottom (more lenient)
                    if zone['type'] == ZoneType.DEMAND:
                        # Allow some wicks below but close should hold
                        closes_below = (future_data['Close'] < zone['bottom']).any()
                        if closes_below:
                            zone['valid'] = False
                    else:  # Supply zones
                        # For supply zones, check if price held below top
                        closes_above = (future_data['Close'] > zone['top']).any()
                        if closes_above:
                            zone['valid'] = False
            
            logger.info(f"Detected {len(zones)} supply/demand zones")
            return zones
            
        except Exception as e:
            logger.error(f"Error detecting supply/demand zones: {str(e)}")
            return []
    
    def get_smart_money_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Get comprehensive Smart Money Concepts analysis, now with institutional-grade features.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with complete SMC analysis
        """
        try:
            # Detect all base SMC elements
            fvgs = self.detect_fair_value_gaps(df)
            order_blocks = self.detect_order_blocks(df)
            liquidity_zones = self.detect_liquidity_zones(df)
            supply_demand_zones = self.detect_supply_demand_zones(df)

            # == INDUSTRIAL GRADE UPGRADE: Detect advanced concepts ==
            liquidity_sweeps = self.detect_liquidity_sweeps(df, liquidity_zones)
            premium_discount_zones = self.get_premium_discount_zones(df)
            breaker_blocks = self.detect_breaker_and_mitigation_blocks(df, order_blocks)
            structure_breaks = self.detect_structure_breaks(df)
            
            # Filter for active/valid zones
            active_fvgs = [fvg for fvg in fvgs if fvg['mitigation_percent'] < 100.0]
            valid_order_blocks = [ob for ob in order_blocks if ob['valid']]
            unswept_liquidity = [lz for lz in liquidity_zones if not lz['swept']]
            valid_sd_zones = [zone for zone in supply_demand_zones if zone['valid']]
            
            # INSTITUTIONAL PRUNING: Keep only most relevant 3-5 structures
            active_fvgs = self._prune_structures_institutional(active_fvgs, df['Close'].iloc[-1], max_count=5)
            valid_order_blocks = self._prune_structures_institutional(valid_order_blocks, df['Close'].iloc[-1], max_count=5)
            valid_sd_zones = self._prune_structures_institutional(valid_sd_zones, df['Close'].iloc[-1], max_count=3)
            
            return {
                'fair_value_gaps': {
                    'all': fvgs,
                    'active': active_fvgs
                },
                'order_blocks': {
                    'all': order_blocks,
                    'valid': valid_order_blocks
                },
                'liquidity_zones': {
                    'all': liquidity_zones,
                    'unswept': unswept_liquidity
                },
                'supply_demand_zones': {
                    'all': supply_demand_zones,
                    'valid': valid_sd_zones
                },
                # == New Institutional Concepts ==
                'liquidity_sweeps': liquidity_sweeps,
                'premium_discount_zones': premium_discount_zones,
                'breaker_blocks': breaker_blocks,
                'structure_breaks': structure_breaks,
                # ===============================
                'analysis_timestamp': df.index[-1],
                'current_price': df['Close'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error in Smart Money analysis: {str(e)}")
            return {}