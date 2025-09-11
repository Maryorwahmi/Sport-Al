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
    
    def __init__(self, fvg_min_size: float = 5.0, order_block_lookback: int = 20,
                 liquidity_threshold: float = 0.1):
        """
        Initialize Smart Money analyzer
        
        Args:
            fvg_min_size: Minimum Fair Value Gap size in pips
            order_block_lookback: Number of bars to look back for order blocks
            liquidity_threshold: Threshold for liquidity detection
        """
        self.fvg_min_size = fvg_min_size
        self.order_block_lookback = order_block_lookback
        self.liquidity_threshold = liquidity_threshold
        
    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Fair Value Gaps (FVGs) - areas where price moves rapidly leaving gaps
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of dictionaries with FVG information
        """
        try:
            fvgs = []
            
            for i in range(2, len(df)):
                # Check for bullish FVG
                # Occurs when current candle's low is above previous candle's high
                current_low = df.iloc[i]['Low']
                prev_high = df.iloc[i-1]['High']
                prev2_high = df.iloc[i-2]['High']
                
                # Bullish FVG: gap between previous high and current low
                if current_low > prev_high:
                    gap_size = (current_low - prev_high) * 10000  # Convert to pips
                    if gap_size >= self.fvg_min_size:
                        fvgs.append({
                            'timestamp': df.index[i],
                            'type': 'bullish_fvg',
                            'top': current_low,
                            'bottom': prev_high,
                            'size_pips': gap_size,
                            'filled': False
                        })
                
                # Check for bearish FVG
                # Occurs when current candle's high is below previous candle's low
                current_high = df.iloc[i]['High']
                prev_low = df.iloc[i-1]['Low']
                
                # Bearish FVG: gap between previous low and current high
                if current_high < prev_low:
                    gap_size = (prev_low - current_high) * 10000  # Convert to pips
                    if gap_size >= self.fvg_min_size:
                        fvgs.append({
                            'timestamp': df.index[i],
                            'type': 'bearish_fvg',
                            'top': prev_low,
                            'bottom': current_high,
                            'size_pips': gap_size,
                            'filled': False
                        })
            
            # Check which FVGs have been filled
            for fvg in fvgs:
                fvg_idx = df.index.get_loc(fvg['timestamp'])
                future_data = df.iloc[fvg_idx+1:]
                
                if fvg['type'] == 'bullish_fvg':
                    # FVG is filled when price goes back into the gap
                    if (future_data['Low'] <= fvg['top']).any():
                        fvg['filled'] = True
                else:  # bearish_fvg
                    # FVG is filled when price goes back into the gap
                    if (future_data['High'] >= fvg['bottom']).any():
                        fvg['filled'] = True
            
            logger.info(f"Detected {len(fvgs)} Fair Value Gaps")
            return fvgs
            
        except Exception as e:
            logger.error(f"Error detecting FVGs: {str(e)}")
            return []
    
    def detect_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect Order Blocks - areas where institutions place large orders
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            List of dictionaries with Order Block information
        """
        try:
            order_blocks = []
            
            for i in range(self.order_block_lookback, len(df) - 1):
                current_candle = df.iloc[i]
                next_candle = df.iloc[i + 1]
                
                # Look for strong moves that create order blocks
                current_body = abs(current_candle['Close'] - current_candle['Open'])
                current_range = current_candle['High'] - current_candle['Low']
                
                # Strong bullish candle followed by continuation
                if (current_candle['Close'] > current_candle['Open'] and
                    current_body > current_range * 0.7 and  # Strong body
                    next_candle['Close'] > current_candle['Close']):  # Continuation
                    
                    # The order block is around the opening price area
                    order_blocks.append({
                        'timestamp': df.index[i],
                        'type': OrderBlockType.BULLISH,
                        'top': max(current_candle['Open'], current_candle['Close']),
                        'bottom': current_candle['Low'],
                        'strength': current_body / current_range,
                        'tested': False,
                        'valid': True
                    })
                
                # Strong bearish candle followed by continuation
                elif (current_candle['Close'] < current_candle['Open'] and
                      current_body > current_range * 0.7 and  # Strong body
                      next_candle['Close'] < current_candle['Close']):  # Continuation
                    
                    # The order block is around the opening price area
                    order_blocks.append({
                        'timestamp': df.index[i],
                        'type': OrderBlockType.BEARISH,
                        'top': current_candle['High'],
                        'bottom': min(current_candle['Open'], current_candle['Close']),
                        'strength': current_body / current_range,
                        'tested': False,
                        'valid': True
                    })
            
            # Check which order blocks have been tested
            for ob in order_blocks:
                ob_idx = df.index.get_loc(ob['timestamp'])
                future_data = df.iloc[ob_idx+1:]
                
                if ob['type'] == OrderBlockType.BULLISH:
                    # Test if price came back to the order block
                    if (future_data['Low'] <= ob['top']).any():
                        ob['tested'] = True
                        # Check if it held (didn't break below)
                        if (future_data['Low'] < ob['bottom']).any():
                            ob['valid'] = False
                else:  # BEARISH
                    # Test if price came back to the order block
                    if (future_data['High'] >= ob['bottom']).any():
                        ob['tested'] = True
                        # Check if it held (didn't break above)
                        if (future_data['High'] > ob['top']).any():
                            ob['valid'] = False
            
            logger.info(f"Detected {len(order_blocks)} Order Blocks")
            return order_blocks
            
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
            
            # Look for equal highs and lows where liquidity might be resting
            for i in range(20, len(df) - 10):
                current_high = df.iloc[i]['High']
                current_low = df.iloc[i]['Low']
                
                # Look for equal highs in nearby candles
                window_start = max(0, i - 10)
                window_end = min(len(df), i + 10)
                window_highs = df.iloc[window_start:window_end]['High']
                window_lows = df.iloc[window_start:window_end]['Low']
                
                # Check for multiple touches at similar levels (liquidity)
                high_touches = sum(abs(h - current_high) <= current_high * self.liquidity_threshold 
                                 for h in window_highs)
                low_touches = sum(abs(l - current_low) <= current_low * self.liquidity_threshold 
                                for l in window_lows)
                
                # If multiple touches, it's likely a liquidity zone
                if high_touches >= 3:
                    liquidity_zones.append({
                        'timestamp': df.index[i],
                        'type': ZoneType.LIQUIDITY_HIGH,
                        'level': current_high,
                        'touches': high_touches,
                        'strength': high_touches / 10,  # Normalize strength
                        'swept': False
                    })
                
                if low_touches >= 3:
                    liquidity_zones.append({
                        'timestamp': df.index[i],
                        'type': ZoneType.LIQUIDITY_LOW,
                        'level': current_low,
                        'touches': low_touches,
                        'strength': low_touches / 10,  # Normalize strength
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
            
            logger.info(f"Detected {len(liquidity_zones)} liquidity zones")
            return liquidity_zones
            
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
                
                if consolidation_range <= avg_range * 2:  # Tight consolidation
                    # Check for strong move out of consolidation
                    move_size = abs(move_data['Close'].iloc[-1] - df.iloc[i]['Open'])
                    
                    if move_size > avg_range * 3:  # Strong move
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
                    
                    # For demand zones, check if price held above bottom
                    if zone['type'] == ZoneType.DEMAND:
                        if (future_data['Low'] < zone['bottom']).any():
                            zone['valid'] = False
                    # For supply zones, check if price held below top
                    else:
                        if (future_data['High'] > zone['top']).any():
                            zone['valid'] = False
            
            logger.info(f"Detected {len(zones)} supply/demand zones")
            return zones
            
        except Exception as e:
            logger.error(f"Error detecting supply/demand zones: {str(e)}")
            return []
    
    def get_smart_money_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Get comprehensive Smart Money Concepts analysis
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dictionary with complete SMC analysis
        """
        try:
            # Detect all SMC elements
            fvgs = self.detect_fair_value_gaps(df)
            order_blocks = self.detect_order_blocks(df)
            liquidity_zones = self.detect_liquidity_zones(df)
            supply_demand_zones = self.detect_supply_demand_zones(df)
            
            # Filter for active/valid zones
            active_fvgs = [fvg for fvg in fvgs if not fvg['filled']]
            valid_order_blocks = [ob for ob in order_blocks if ob['valid']]
            unswept_liquidity = [lz for lz in liquidity_zones if not lz['swept']]
            valid_sd_zones = [zone for zone in supply_demand_zones if zone['valid']]
            
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
                'analysis_timestamp': df.index[-1],
                'current_price': df['Close'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error in Smart Money analysis: {str(e)}")
            return {}