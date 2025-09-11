"""
Signal generation system that combines market structure and Smart Money Concepts
to identify high-probability trading opportunities
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from enum import Enum
import logging
from ..market_structure.structure_analyzer import TrendDirection, StructureType
from ..smart_money.smc_analyzer import ZoneType, OrderBlockType


logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    WAIT = "wait"


class SignalStrength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


class ConfluenceFactor(Enum):
    TREND_ALIGNMENT = "trend_alignment"
    STRUCTURE_BREAK = "structure_break"
    ORDER_BLOCK = "order_block"
    LIQUIDITY_ZONE = "liquidity_zone"
    FAIR_VALUE_GAP = "fair_value_gap"
    SUPPLY_DEMAND = "supply_demand"


class SignalGenerator:
    """Generates trading signals based on confluence of multiple factors"""
    
    def __init__(self, min_confluence_factors: int = 2, min_rr_ratio: float = 1.5):
        """
        Initialize signal generator
        
        Args:
            min_confluence_factors: Minimum number of confluence factors required
            min_rr_ratio: Minimum risk/reward ratio for signals
        """
        self.min_confluence_factors = min_confluence_factors
        self.min_rr_ratio = min_rr_ratio
        
    def calculate_confluence_score(self, market_structure: Dict, smc_analysis: Dict,
                                  current_price: float) -> Dict:
        """
        Calculate confluence score based on multiple factors
        
        Args:
            market_structure: Market structure analysis results
            smc_analysis: Smart Money Concepts analysis results
            current_price: Current market price
            
        Returns:
            Dictionary with confluence factors and scores
        """
        confluence_factors = []
        total_score = 0
        
        try:
            # Factor 1: Trend Alignment
            trend = market_structure.get('trend_direction', TrendDirection.CONSOLIDATION)
            if trend == TrendDirection.UPTREND:
                confluence_factors.append({
                    'factor': ConfluenceFactor.TREND_ALIGNMENT,
                    'direction': 'bullish',
                    'score': 2
                })
                total_score += 2
            elif trend == TrendDirection.DOWNTREND:
                confluence_factors.append({
                    'factor': ConfluenceFactor.TREND_ALIGNMENT,
                    'direction': 'bearish',
                    'score': 2
                })
                total_score += 2
            
            # Factor 2: Recent Structure Breaks
            structure_breaks = market_structure.get('structure_breaks', [])
            recent_breaks = [sb for sb in structure_breaks if sb.get('timestamp')]
            if recent_breaks:
                latest_break = recent_breaks[-1]
                confluence_factors.append({
                    'factor': ConfluenceFactor.STRUCTURE_BREAK,
                    'direction': latest_break.get('direction', 'neutral'),
                    'score': 3
                })
                total_score += 3
            
            # Factor 3: Nearby Order Blocks
            order_blocks = smc_analysis.get('order_blocks', {}).get('valid', [])
            nearby_obs = []
            for ob in order_blocks:
                ob_top = ob.get('top', 0)
                ob_bottom = ob.get('bottom', 0)
                
                # Check if current price is near the order block
                distance_to_ob = min(abs(current_price - ob_top), abs(current_price - ob_bottom))
                if distance_to_ob <= current_price * 0.001:  # Within 0.1%
                    nearby_obs.append(ob)
            
            if nearby_obs:
                for ob in nearby_obs:
                    direction = 'bullish' if ob['type'] == OrderBlockType.BULLISH else 'bearish'
                    confluence_factors.append({
                        'factor': ConfluenceFactor.ORDER_BLOCK,
                        'direction': direction,
                        'score': 2,
                        'level': ob.get('top', 0) if direction == 'bearish' else ob.get('bottom', 0)
                    })
                    total_score += 2
            
            # Factor 4: Unswept Liquidity
            liquidity_zones = smc_analysis.get('liquidity_zones', {}).get('unswept', [])
            nearby_liquidity = []
            for lz in liquidity_zones:
                distance_to_lz = abs(current_price - lz.get('level', 0))
                if distance_to_lz <= current_price * 0.002:  # Within 0.2%
                    nearby_liquidity.append(lz)
            
            if nearby_liquidity:
                for lz in nearby_liquidity:
                    direction = 'bearish' if lz['type'] == ZoneType.LIQUIDITY_HIGH else 'bullish'
                    confluence_factors.append({
                        'factor': ConfluenceFactor.LIQUIDITY_ZONE,
                        'direction': direction,
                        'score': 1,
                        'level': lz.get('level', 0)
                    })
                    total_score += 1
            
            # Factor 5: Active Fair Value Gaps
            active_fvgs = smc_analysis.get('fair_value_gaps', {}).get('active', [])
            nearby_fvgs = []
            for fvg in active_fvgs:
                fvg_top = fvg.get('top', 0)
                fvg_bottom = fvg.get('bottom', 0)
                
                # Check if current price is approaching the FVG
                if fvg_bottom <= current_price <= fvg_top:
                    nearby_fvgs.append(fvg)
            
            if nearby_fvgs:
                for fvg in nearby_fvgs:
                    direction = 'bullish' if 'bullish' in fvg.get('type', '') else 'bearish'
                    confluence_factors.append({
                        'factor': ConfluenceFactor.FAIR_VALUE_GAP,
                        'direction': direction,
                        'score': 2
                    })
                    total_score += 2
            
            # Factor 6: Supply/Demand Zones
            sd_zones = smc_analysis.get('supply_demand_zones', {}).get('valid', [])
            nearby_sd_zones = []
            for zone in sd_zones:
                zone_top = zone.get('top', 0)
                zone_bottom = zone.get('bottom', 0)
                
                # Check if current price is in or near the zone
                if zone_bottom <= current_price <= zone_top:
                    nearby_sd_zones.append(zone)
            
            if nearby_sd_zones:
                for zone in nearby_sd_zones:
                    direction = 'bullish' if zone['type'] == ZoneType.DEMAND else 'bearish'
                    confluence_factors.append({
                        'factor': ConfluenceFactor.SUPPLY_DEMAND,
                        'direction': direction,
                        'score': 2
                    })
                    total_score += 2
            
            return {
                'confluence_factors': confluence_factors,
                'total_score': total_score,
                'factor_count': len(confluence_factors)
            }
            
        except Exception as e:
            logger.error(f"Error calculating confluence score: {str(e)}")
            return {'confluence_factors': [], 'total_score': 0, 'factor_count': 0}
    
    def generate_signal(self, market_structure: Dict, smc_analysis: Dict,
                       current_price: float) -> Dict:
        """
        Generate trading signal based on confluence analysis
        
        Args:
            market_structure: Market structure analysis results
            smc_analysis: Smart Money Concepts analysis results
            current_price: Current market price
            
        Returns:
            Dictionary with signal information
        """
        try:
            # Calculate confluence
            confluence = self.calculate_confluence_score(market_structure, smc_analysis, current_price)
            
            # Determine signal direction based on confluence factors
            bullish_score = sum(cf['score'] for cf in confluence['confluence_factors'] 
                              if cf.get('direction') == 'bullish')
            bearish_score = sum(cf['score'] for cf in confluence['confluence_factors'] 
                               if cf.get('direction') == 'bearish')
            
            # Determine signal type
            signal_type = SignalType.WAIT
            signal_strength = SignalStrength.WEAK
            
            if confluence['factor_count'] >= self.min_confluence_factors:
                if bullish_score > bearish_score and bullish_score >= 3:
                    signal_type = SignalType.BUY
                elif bearish_score > bullish_score and bearish_score >= 3:
                    signal_type = SignalType.SELL
                
                # Determine signal strength
                max_score = max(bullish_score, bearish_score)
                if max_score >= 6:
                    signal_strength = SignalStrength.VERY_STRONG
                elif max_score >= 4:
                    signal_strength = SignalStrength.STRONG
                elif max_score >= 2:
                    signal_strength = SignalStrength.MODERATE
            
            # Calculate entry, stop loss, and take profit levels
            entry_levels = self._calculate_entry_levels(signal_type, confluence, current_price)
            
            signal = {
                'timestamp': pd.Timestamp.now(),
                'signal_type': signal_type,
                'signal_strength': signal_strength,
                'current_price': current_price,
                'confluence_score': confluence['total_score'],
                'confluence_factors': confluence['confluence_factors'],
                'entry_price': entry_levels.get('entry', current_price),
                'stop_loss': entry_levels.get('stop_loss'),
                'take_profit': entry_levels.get('take_profit'),
                'risk_reward_ratio': entry_levels.get('rr_ratio'),
                'valid': entry_levels.get('rr_ratio', 0) >= self.min_rr_ratio
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return {
                'signal_type': SignalType.WAIT,
                'signal_strength': SignalStrength.WEAK,
                'valid': False
            }
    
    def _calculate_entry_levels(self, signal_type: SignalType, confluence: Dict,
                               current_price: float) -> Dict:
        """
        Calculate entry, stop loss, and take profit levels
        
        Args:
            signal_type: Type of signal (BUY/SELL)
            confluence: Confluence analysis results
            current_price: Current market price
            
        Returns:
            Dictionary with entry levels
        """
        try:
            if signal_type == SignalType.WAIT:
                return {}
            
            # Find relevant levels from confluence factors
            support_levels = []
            resistance_levels = []
            
            for cf in confluence['confluence_factors']:
                if 'level' in cf:
                    level = cf['level']
                    if cf.get('direction') == 'bullish':
                        support_levels.append(level)
                    else:
                        resistance_levels.append(level)
            
            # Calculate levels based on signal type
            if signal_type == SignalType.BUY:
                # Entry at current price or slightly above
                entry_price = current_price
                
                # Stop loss below nearest support or 0.5% below entry
                if support_levels:
                    stop_loss = min(support_levels) - (current_price * 0.001)  # 10 pips buffer
                else:
                    stop_loss = current_price * 0.995  # 0.5% below
                
                # Take profit at nearest resistance or based on R:R ratio
                risk = entry_price - stop_loss
                if resistance_levels:
                    take_profit = min(resistance_levels)
                    # Ensure minimum R:R ratio
                    min_tp = entry_price + (risk * self.min_rr_ratio)
                    take_profit = max(take_profit, min_tp)
                else:
                    take_profit = entry_price + (risk * 2.0)  # 2:1 R:R ratio
                
            else:  # SELL signal
                # Entry at current price or slightly below
                entry_price = current_price
                
                # Stop loss above nearest resistance or 0.5% above entry
                if resistance_levels:
                    stop_loss = max(resistance_levels) + (current_price * 0.001)  # 10 pips buffer
                else:
                    stop_loss = current_price * 1.005  # 0.5% above
                
                # Take profit at nearest support or based on R:R ratio
                risk = stop_loss - entry_price
                if support_levels:
                    take_profit = max(support_levels)
                    # Ensure minimum R:R ratio
                    min_tp = entry_price - (risk * self.min_rr_ratio)
                    take_profit = min(take_profit, min_tp)
                else:
                    take_profit = entry_price - (risk * 2.0)  # 2:1 R:R ratio
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            return {
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rr_ratio': rr_ratio
            }
            
        except Exception as e:
            logger.error(f"Error calculating entry levels: {str(e)}")
            return {}
    
    def get_signal_summary(self, signal: Dict) -> str:
        """
        Get a human-readable signal summary
        
        Args:
            signal: Signal dictionary
            
        Returns:
            String summary of the signal
        """
        if signal.get('signal_type') == SignalType.WAIT:
            return "WAIT - No high-probability setup detected"
        
        signal_type = signal.get('signal_type', SignalType.WAIT).value.upper()
        strength = signal.get('signal_strength', SignalStrength.WEAK).name
        confluence_score = signal.get('confluence_score', 0)
        rr_ratio = signal.get('risk_reward_ratio', 0)
        
        factors = signal.get('confluence_factors', [])
        factor_names = [cf['factor'].value for cf in factors]
        
        summary = f"{signal_type} Signal - {strength} Strength\n"
        summary += f"Confluence Score: {confluence_score}\n"
        summary += f"Risk/Reward Ratio: {rr_ratio:.2f}\n"
        summary += f"Entry: {signal.get('entry_price', 0):.5f}\n"
        summary += f"Stop Loss: {signal.get('stop_loss', 0):.5f}\n"
        summary += f"Take Profit: {signal.get('take_profit', 0):.5f}\n"
        summary += f"Confluence Factors: {', '.join(factor_names)}"
        
        return summary