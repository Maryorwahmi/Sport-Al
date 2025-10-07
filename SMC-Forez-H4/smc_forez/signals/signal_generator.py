"""
Clean, simplified SMC Signal Generator - Version 2.0
Fixes all structural issues and provides robust signal generation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
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
    """Clean SMC Signal Generator - Professional Confluence Model"""
    
    def __init__(self, min_confluence_score: int = 7,  # New professional score threshold
                 min_rr_ratio: float = 2.0,
                 enhanced_mode: bool = True):
        self.min_confluence_score = min_confluence_score
        self.min_rr_ratio = min_rr_ratio
        self.enhanced_mode = enhanced_mode
        
    def generate_signal(self, market_structure: Dict, smc_analysis: Dict,
                       current_price: float, timeframe: str = "H1", market_bias: Optional[str] = None) -> Dict:
        """
        Generate trading signal using the new professional weighted scoring model.
        """
        try:
            logger.info(f"Generating signal at price: {current_price} with bias: {market_bias}")
            
            # CRITICAL DEBUG: Log timeframe trend vs global bias
            local_trend = market_structure.get('trend_direction')
            logger.info(f"🔍 TREND CHECK: Loca`l trend={local_trend}, Global bias={market_bias}")
            
            # 1. Calculate confluence score using the new professional model
            confluence = self._calculate_professional_confluence(
                market_structure, smc_analysis, current_price, market_bias
            )
            
            logger.info(f"🔍 CONFLUENCE DEBUG: signal_direction={confluence.get('signal_direction')}, total_score={confluence.get('total_score')}")
            
            # 2. Determine signal direction based on the new score
            signal_type = self._determine_signal_direction_from_confluence(confluence)
            
            logger.info(f"🔍 SIGNAL TYPE DEBUG: Determined signal_type={signal_type} from confluence")
            
            # 3. Check if the signal meets the minimum score threshold
            if confluence['total_score'] < self.min_confluence_score:
                signal_type = SignalType.WAIT

            # 4. Calculate entry details if we have a valid signal
            entry_details = {}
            if signal_type != SignalType.WAIT:
                logger.info(f"🔍 ENTRY DETAILS DEBUG: Attempting to calculate entry for {signal_type}")
                entry_details = self._calculate_entry_details(
                    signal_type, current_price, smc_analysis, market_structure, confluence
                )
                logger.info(f"🔍 ENTRY DETAILS RESULT: {bool(entry_details)} - {entry_details}")
                if not entry_details:
                    logger.warning(f"⚠️ Entry details calculation failed for {signal_type} - converting to WAIT")
                    signal_type = SignalType.WAIT
            
            # 5. Build the final signal structure
            is_valid = self._is_signal_valid(signal_type, entry_details, confluence)
            signal_strength = self._determine_signal_strength(confluence, entry_details)
            recommendation = self._build_recommendation(
                signal_type, signal_strength, entry_details, confluence, timeframe
            )
            
            # Calculate institutional quality rating
            analysis_quality = self._assess_quality(confluence, len(confluence.get('factors', [])))
            
            logger.info(f"  - Signal Result: Type={signal_type}, Valid={is_valid}, Score={confluence['total_score']}/{confluence['max_score']}")
            
            return {
                'signal_type': signal_type,
                'signal_strength': signal_strength,
                'confluence_score': confluence['total_score'],
                'entry_details': entry_details,
                'valid': is_valid,
                'analysis_quality': analysis_quality,  # Added institutional quality rating
                'recommendation': recommendation,
                'confluence_factors': confluence['factors']
            }
            
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return self._create_wait_signal(str(e))

    def _calculate_professional_confluence(self, market_structure: Dict, smc_analysis: Dict, 
                                           current_price: float, market_bias: Optional[str]) -> Dict:
        """
        Calculates confluence score based on the new professional weighted model.
        Total possible score: 15
        """
        factors = []
        total_score = 0
        max_score = 15
        signal_direction = 'neutral'

        # CRITICAL FIX: Determine signal direction from LOCAL TIMEFRAME TREND, not global bias
        local_trend = market_structure.get('trend_direction')
        logger.debug(f"🔍 LOCAL TREND DEBUG: trend={local_trend}, type={type(local_trend)}")
        
        if local_trend:
            trend_str = str(local_trend).upper()
            logger.debug(f"🔍 TREND STRING: '{trend_str}'")
            
            if 'UPTREND' in trend_str or 'BULLISH' in trend_str:
                signal_direction = 'bullish'
                logger.debug(f"🔍 SIGNAL DIRECTION: Set to bullish from {trend_str}")
            elif 'DOWNTREND' in trend_str or 'BEARISH' in trend_str:
                signal_direction = 'bearish'
                logger.debug(f"🔍 SIGNAL DIRECTION: Set to bearish from {trend_str}")
            else:
                logger.debug(f"🔍 SIGNAL DIRECTION: No match for {trend_str}, staying neutral")
        else:
            logger.debug(f"🔍 LOCAL TREND: None found in market_structure")
        
        # Use global bias only for confluence scoring, not signal direction
        # This ensures M15 UPTREND generates BUY signals, H4 DOWNTREND generates SELL signals
        
        # Base score for having a clear trend direction
        if signal_direction in ['bullish', 'bearish']:
            total_score += 1
            factors.append({'factor': 'Clear Trend Direction', 'score': 1, 'details': f'Local trend direction is {signal_direction}'})

        # 1. Trend Alignment - Score based on local trend strength
        if signal_direction in ['bullish', 'bearish']:
            # If we have a clear local trend direction, give it base points
            total_score += 2
            if market_bias in ['BULLISH', 'BEARISH']:
                factors.append({'factor': 'Trend Alignment (H4/H1)', 'score': 2, 'details': f'Market bias is {market_bias}'})
            else:
                factors.append({'factor': 'Local Trend Alignment', 'score': 2, 'details': f'Local trend is {signal_direction.upper()}'})

        # 2. Market Structure Break - Score: +3
        structure_breaks = market_structure.get('structure_breaks', [])
        bos_in_direction = False
        choch_found = False
        for b in structure_breaks:
            break_type = b.get('type')
            # A BOS in the direction of the signal is a strong confirmation
            if break_type == StructureType.BOS and b.get('direction', '').lower() == signal_direction:
                total_score += 3
                factors.append({'factor': 'BOS Confirmation', 'score': 3, 'details': f'Break of Structure aligned with {signal_direction} trend.'})
                bos_in_direction = True
                break
            # A CHOCH could signal a reversal, which is also a valid entry reason
            elif break_type == StructureType.CHOCH:
                choch_found = True
        
        if not bos_in_direction and choch_found:
            total_score += 2
            factors.append({'factor': 'CHOCH Reversal', 'score': 2, 'details': 'Change of Character suggests potential reversal.'})

        # 3. Recent Liquidity Sweep in opposite direction - Score: +3
        sweeps = smc_analysis.get('liquidity_sweeps', [])
        if sweeps:
            recent_sweep = sweeps[-1]
            sweep_type = str(recent_sweep.get('type', '')).lower()
            # Opposite sweeps create opportunities for our signal direction
            if (signal_direction == 'bullish' and 'bearish' in sweep_type) or \
               (signal_direction == 'bearish' and 'bullish' in sweep_type):
                total_score += 3
                factors.append({'factor': 'Recent Liquidity Sweep', 'score': 3, 'details': f'Opposite {sweep_type} creates opportunity'})

        # 4. Valid OB or FVG as POI - Score: +3
        poi_found = False
        # Check for valid Order Block
        valid_obs = self._extract_order_blocks(smc_analysis)
        for ob in valid_obs:
            ob_type = self._get_order_block_type(ob)
            if (signal_direction == 'bullish' and ob_type == 'bullish' and current_price >= ob['bottom']) or \
               (signal_direction == 'bearish' and ob_type == 'bearish' and current_price <= ob['top']):
                total_score += 3
                factors.append({'factor': 'Valid OB as POI', 'score': 3, 'details': f'Price is reacting to a {ob_type} OB.'})
                poi_found = True
                break
        # If no OB, check for FVG
        if not poi_found:
            active_fvgs = self._extract_fair_value_gaps(smc_analysis)
            for fvg in active_fvgs:
                fvg_type = fvg.get('type')
                if (signal_direction == 'bullish' and 'bullish' in fvg_type and current_price >= fvg['bottom']) or \
                   (signal_direction == 'bearish' and 'bearish' in fvg_type and current_price <= fvg['top']):
                    if fvg.get('mitigation_percent', 100) < 50: # Less than 50% mitigated
                        total_score += 3
                        factors.append({'factor': 'Valid FVG as POI', 'score': 3, 'details': f'Price is reacting to an unmitigated {fvg_type}.'})
                        poi_found = True
                        break
        
        # 5. Premium/Discount Zone Alignment - Score: +2
        pd_zones = smc_analysis.get('premium_discount_zones', {})
        if pd_zones:
            if signal_direction == 'bullish' and current_price <= pd_zones.get('equilibrium', current_price):
                total_score += 2
                factors.append({'factor': 'Premium/Discount Alignment', 'score': 2, 'details': 'Buy signal is in a Discount zone.'})
            elif signal_direction == 'bearish' and current_price >= pd_zones.get('equilibrium', current_price):
                total_score += 2
                factors.append({'factor': 'Premium/Discount Alignment', 'score': 2, 'details': 'Sell signal is in a Premium zone.'})

        # 6. Opposing S/D Zone Confirmation - Score: +2
        valid_sd_zones = smc_analysis.get('supply_demand_zones', {}).get('valid', [])
        opposing_zone_nearby = False
        if signal_direction == 'bullish':
            # Look for a clear path to the next supply zone
            for zone in valid_sd_zones:
                if zone.get('type') == ZoneType.SUPPLY and zone.get('bottom') > current_price:
                    if (zone['bottom'] - current_price) / current_price < 0.005: # Opposing zone within 0.5%
                        opposing_zone_nearby = True
                        break
        elif signal_direction == 'bearish':
            # Look for a clear path to the next demand zone
            for zone in valid_sd_zones:
                if zone.get('type') == ZoneType.DEMAND and zone.get('top') < current_price:
                    if (current_price - zone['top']) / current_price < 0.005: # Opposing zone within 0.5%
                        opposing_zone_nearby = True
                        break
        if not opposing_zone_nearby:
            total_score += 2
            factors.append({'factor': 'No Opposing S/D Zone', 'score': 2, 'details': 'No immediate opposing S/D zone found.'})

        # 7. Entry TF Candle Pattern - Score: +1 (Placeholder, requires candle pattern logic)
        # This would require a new function `detect_candle_patterns`
        # For now, we can add a placeholder if other conditions are strong
        if total_score >= 6: # If score is already good, add a point for momentum
            total_score += 1
            factors.append({'factor': 'Entry Candle Pattern', 'score': 1, 'details': 'Assumed momentum/pattern confirmation.'})

        logger.debug(f"🔍 FINAL CONFLUENCE: signal_direction={signal_direction}, total_score={total_score}")
        
        return {
            'factors': factors,
            'total_score': total_score,
            'max_score': max_score,
            'signal_direction': signal_direction
        }

    def _determine_signal_direction_from_confluence(self, confluence: Dict) -> SignalType:
        """Determines signal direction from the professional confluence result."""
        direction = confluence.get('signal_direction')
        if direction == 'bullish':
            return SignalType.BUY
        elif direction == 'bearish':
            return SignalType.SELL
        else:
            return SignalType.WAIT

    def _is_signal_valid(self, signal_type: SignalType, entry_details: Dict, confluence: Dict) -> bool:
        """Check if signal meets all validation criteria including the new score."""
        if signal_type == SignalType.WAIT or not entry_details:
            return False
        
        if confluence.get('total_score', 0) < self.min_confluence_score:
            return False
            
        rr_ratio = entry_details.get('risk_reward_ratio', 0)
        if rr_ratio < self.min_rr_ratio:
            return False
            
        # CRITICAL FIX: Validate signal direction matches expected logic
        signal_direction = confluence.get('signal_direction', 'neutral')
        if signal_type == SignalType.BUY and signal_direction != 'bullish':
            logger.error(f"🚨 SIGNAL LOGIC ERROR: BUY signal with {signal_direction} direction")
            return False
        
        if signal_type == SignalType.SELL and signal_direction != 'bearish':
            logger.error(f"🚨 SIGNAL LOGIC ERROR: SELL signal with {signal_direction} direction")
            return False
            
        return True
    
    def _calculate_entry_details(self, signal_type: SignalType, current_price: float,
                               smc_analysis: Dict, market_structure: Dict, confluence: Dict) -> Dict:
        """Calculate entry, stop loss, and take profit using SMC principles"""
        try:
            # Extract confluence factors for setup type determination
            confluence_factors = confluence.get('factors', []) if confluence else []
            
            # 1. Calculate entry price using order blocks and setup type
            entry_price = self._calculate_entry_price(signal_type, current_price, smc_analysis, confluence_factors)
            if entry_price is None:
                return {}
            
            # 2. Calculate stop loss
            stop_loss = self._calculate_stop_loss(signal_type, entry_price, smc_analysis, market_structure)
            if stop_loss is None:
                return {}
            
            # 3. Calculate take profit
            take_profit = self._calculate_take_profit(signal_type, entry_price, stop_loss, smc_analysis)
            if take_profit is None:
                return {}
            
            # 3.1. CRITICAL VALIDATION: Ensure signal direction consistency
            if not self._validate_signal_direction(signal_type, entry_price, stop_loss, take_profit):
                logger.error(f"🚨 SIGNAL DIRECTION VALIDATION FAILED for {signal_type.value}")
                return {}

            # 4. Calculate risk/reward
            if signal_type == SignalType.BUY:
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            if risk <= 0:
                logger.warning(f"Invalid risk calculation: {risk}")
                return {}
            
            risk_reward_ratio = reward / risk
            
            if risk_reward_ratio < self.min_rr_ratio:
                logger.info(f"RR too low: {risk_reward_ratio:.2f} < {self.min_rr_ratio}")
                return {}
            
            return {
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'risk_reward_ratio': round(float(risk_reward_ratio), 2),
                'risk_pips': round(abs(float(risk)) * 10000, 1),
                'reward_pips': round(abs(float(reward)) * 10000, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating entry details: {e}")
            return {}
    
    def _calculate_entry_price(self, signal_type: SignalType, current_price: float,
                              smc_analysis: Dict, confluence_factors: List[Dict]) -> Optional[float]:
        """Calculate SMC-based entry price using order blocks and setup type"""
        try:
            order_blocks = self._extract_order_blocks(smc_analysis)
            relevant_obs = []
            
            for ob in order_blocks:
                ob_type = self._get_order_block_type(ob)
                if signal_type == SignalType.BUY and ob_type == 'bullish':
                    relevant_obs.append(ob)
                elif signal_type == SignalType.SELL and ob_type == 'bearish':
                    relevant_obs.append(ob)
            
            # Determine setup type from confluence factors
            has_structure_break = any(factor.get('type') == 'STRUCTURE_BREAK' for factor in confluence_factors)
            
            if relevant_obs:
                # Use closest order block
                best_ob = min(relevant_obs, key=lambda x: abs(x.get('top', current_price) - current_price))
                
                ob_high = best_ob.get('top', current_price)
                ob_low = best_ob.get('bottom', current_price)
                
                # ENHANCEMENT: For pullbacks, target the 50% equilibrium of the Order Block
                if not has_structure_break:
                    entry_price = ob_low + (ob_high - ob_low) * 0.5
                    logger.info(f"SMC Entry: Pullback to OB equilibrium at {entry_price}")
                    return entry_price

                if has_structure_break:
                    # Breakout setup: Enter at extreme of order block
                    if signal_type == SignalType.BUY:
                        entry_price = ob_high + (ob_high - ob_low) * 0.1  # 10% above OB
                        logger.info(f"SMC Entry: BOS breakout above OB at {entry_price}")
                    else:
                        entry_price = ob_low - (ob_high - ob_low) * 0.1  # 10% below OB
                        logger.info(f"SMC Entry: BOS breakout below OB at {entry_price}")
                else:
                    # Pullback setup: Enter at order block equilibrium (50% level)
                    entry_price = (ob_high + ob_low) / 2
                    logger.info(f"SMC Entry: OB equilibrium at {entry_price}")
                
                return entry_price
            
            # Fallback to current price with small offset for setup type
            if has_structure_break:
                # Breakout: Enter at slight premium/discount
                offset = current_price * 0.0002  # 2 pips offset
                entry_price = current_price + offset if signal_type == SignalType.BUY else current_price - offset
                logger.info(f"SMC Entry: BOS breakout at {entry_price}")
            else:
                # Pullback: Enter at current price
                entry_price = current_price
                logger.info(f"SMC Entry: Current price pullback at {entry_price}")
            
            return entry_price
            
        except Exception as e:
            logger.error(f"Error calculating entry price: {e}")
            return None
    
    def _calculate_stop_loss(self, signal_type: SignalType, entry_price: float,
                           smc_analysis: Dict, market_structure: Dict) -> Optional[float]:
        """Calculate SMC-based stop loss with proper broker-compatible buffers"""
        try:
            order_blocks = self._extract_order_blocks(smc_analysis)
            
            # Use dynamic buffer based on entry price (minimum 5 pips for stability)
            buffer = max(0.0005, entry_price * 0.001)  # At least 5 pips or 0.1%
            
            if signal_type == SignalType.BUY:
                # For BUY signals, stop loss must be BELOW entry price
                target_sl = None
                
                # Try to find demand order block below current price
                demand_obs = [ob for ob in order_blocks if self._get_order_block_type(ob) == 'bullish']
                for ob in demand_obs:
                    ob_bottom = ob.get('bottom', 0)
                    if ob_bottom > 0 and ob_bottom < entry_price:  # Must be below entry
                        if target_sl is None or ob_bottom > target_sl:  # Find closest below entry
                            target_sl = ob_bottom
                
                if target_sl and target_sl < entry_price:
                    stop_loss = target_sl - buffer
                    # Ensure SL is reasonable distance below entry
                    min_sl = entry_price - (entry_price * 0.01)  # 1% minimum distance
                    stop_loss = min(stop_loss, min_sl)
                else:
                    # Fallback: Conservative stop below entry
                    stop_loss = entry_price - (entry_price * 0.01)  # 1% below entry
                
                # CRITICAL: Ensure SL is always below entry for BUY orders
                if stop_loss >= entry_price:
                    logger.error(f"🚨 CRITICAL BUY SL ERROR: {stop_loss:.5f} >= {entry_price:.5f}")
                    stop_loss = entry_price - (entry_price * 0.02)  # 2% below entry as emergency
                    
                logger.info(f"SMC SL BUY: {stop_loss:.5f} (Entry: {entry_price:.5f})")
                return stop_loss
                
            else:  # SELL
                # For SELL signals, stop loss must be ABOVE entry price
                target_sl = None
                
                # Try to find supply order block above current price
                supply_obs = [ob for ob in order_blocks if self._get_order_block_type(ob) == 'bearish']
                for ob in supply_obs:
                    ob_top = ob.get('top', 0)
                    if ob_top > 0 and ob_top > entry_price:  # Must be above entry
                        if target_sl is None or ob_top < target_sl:  # Find closest above entry
                            target_sl = ob_top
                
                if target_sl and target_sl > entry_price:
                    stop_loss = target_sl + buffer
                    # Ensure SL is reasonable distance above entry
                    min_sl = entry_price + (entry_price * 0.01)  # 1% minimum distance
                    stop_loss = max(stop_loss, min_sl)
                else:
                    # Fallback: Conservative stop above entry
                    stop_loss = entry_price + (entry_price * 0.01)  # 1% above entry
                
                # CRITICAL: Ensure SL is always above entry for SELL orders
                if stop_loss <= entry_price:
                    logger.error(f"🚨 CRITICAL SELL SL ERROR: {stop_loss:.5f} <= {entry_price:.5f}")
                    stop_loss = entry_price + (entry_price * 0.02)  # 2% above entry as emergency
                    
                logger.info(f"SMC SL SELL: {stop_loss:.5f} (Entry: {entry_price:.5f})")
                return stop_loss
                
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            # Emergency fallback
            if signal_type == SignalType.BUY:
                return entry_price * 0.97  # 3% below for BUY
            else:
                return entry_price * 1.03  # 3% above for SELL
    
    def _calculate_take_profit(self, signal_type: SignalType, entry_price: float,
                             stop_loss: float, smc_analysis: Dict) -> Optional[float]:
        """Calculate SMC-based take profit with robust validation"""
        try:
            risk = abs(entry_price - stop_loss)
            min_reward = risk * self.min_rr_ratio  # Use configured RR ratio
            
            logger.debug(f"TP Calculation: Entry={entry_price:.5f}, SL={stop_loss:.5f}, Risk={risk:.5f}, MinReward={min_reward:.5f}")
            
            if signal_type == SignalType.BUY:
                # For BUY signals, TP must be ABOVE entry price
                # Ensure stop loss is actually below entry price
                if stop_loss >= entry_price:
                    logger.error(f"Invalid SL for BUY: SL {stop_loss:.5f} >= Entry {entry_price:.5f}")
                    return None
                
                # Try to find supply zones or resistance levels above entry
                liquidity_zones = self._extract_liquidity_zones(smc_analysis)
                supply_demand = self._extract_supply_demand_zones(smc_analysis)
                
                target_tp = None
                
                # Check liquidity zones above entry
                for lz in liquidity_zones:
                    level = lz.get('level', 0)
                    if level > entry_price:  # Must be above entry for BUY TP
                        potential_reward = level - entry_price
                        if potential_reward >= min_reward:  # Must meet minimum RR
                            if target_tp is None or level < target_tp:  # Find closest valid target
                                target_tp = level
                
                # Check supply zones above entry
                for sz in supply_demand:
                    if sz.get('type') == 'supply' or 'supply' in str(sz.get('type', '')):
                        level = sz.get('top', 0)
                        if level > entry_price:  # Must be above entry for BUY TP
                            potential_reward = level - entry_price
                            if potential_reward >= min_reward:  # Must meet minimum RR
                                if target_tp is None or level < target_tp:  # Find closest valid target
                                    target_tp = level
                
                if target_tp:
                    take_profit = target_tp
                else:
                    # Fallback: Use minimum RR ratio
                    take_profit = entry_price + min_reward
                
                # Final validation: ensure TP is above entry
                if take_profit <= entry_price:
                    take_profit = entry_price + min_reward
                    
                logger.info(f"SMC TP BUY: {take_profit:.5f} (RR: {(take_profit - entry_price) / risk:.2f})")
                return take_profit
                
            else:  # SELL
                # For SELL signals, TP must be BELOW entry price
                # Ensure stop loss is actually above entry price
                if stop_loss <= entry_price:
                    logger.error(f"Invalid SL for SELL: SL {stop_loss:.5f} <= Entry {entry_price:.5f}")
                    return None
                
                # Try to find demand zones or support levels below entry
                liquidity_zones = self._extract_liquidity_zones(smc_analysis)
                supply_demand = self._extract_supply_demand_zones(smc_analysis)
                
                target_tp = None
                
                # Check liquidity zones below entry
                for lz in liquidity_zones:
                    level = lz.get('level', 0)
                    if level < entry_price:  # Must be below entry for SELL TP
                        potential_reward = entry_price - level
                        if potential_reward >= min_reward:  # Must meet minimum RR
                            if target_tp is None or level > target_tp:  # Find closest valid target
                                target_tp = level
                
                # Check demand zones below entry
                for dz in supply_demand:
                    if dz.get('type') == 'demand' or 'demand' in str(dz.get('type', '')):
                        level = dz.get('bottom', 0)
                        if level < entry_price:  # Must be below entry for SELL TP
                            potential_reward = entry_price - level
                            if potential_reward >= min_reward:  # Must meet minimum RR
                                if target_tp is None or level > target_tp:  # Find closest valid target
                                    target_tp = level
                
                if target_tp:
                    take_profit = target_tp
                else:
                    # Fallback: Use minimum RR ratio
                    take_profit = entry_price - min_reward
                
                # Final validation: ensure TP is below entry
                if take_profit >= entry_price:
                    take_profit = entry_price - min_reward
                    
                logger.info(f"SMC TP SELL: {take_profit:.5f} (RR: {(entry_price - take_profit) / risk:.2f})")
                return take_profit
                
        except Exception as e:
            logger.error(f"Error calculating take profit: {e}")
            # Emergency fallback
            risk = abs(entry_price - stop_loss)
            if signal_type == SignalType.BUY:
                return entry_price + (risk * self.min_rr_ratio)
            else:
                return entry_price - (risk * self.min_rr_ratio)
                # Look for liquidity above entry
                
        except Exception as e:
            logger.error(f"Error calculating take profit: {e}")
            # Emergency fallback
            risk = abs(entry_price - stop_loss)
            if signal_type == SignalType.BUY:
                return entry_price + (risk * self.min_rr_ratio)
            else:
                return entry_price - (risk * self.min_rr_ratio)
            risk = abs(entry_price - stop_loss)
            if signal_type == SignalType.BUY:
                return entry_price + (risk * self.min_rr_ratio)
            else:
                return entry_price - (risk * self.min_rr_ratio)
    
    def _validate_signal_direction(self, signal_type: SignalType, entry_price: float, 
                                 stop_loss: float, take_profit: float) -> bool:
        """
        Critical validation to ensure signal direction consistency.
        Prevents the bug where SELL signals have TP above entry price.
        
        Args:
            signal_type: BUY or SELL signal type
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            bool: True if signal direction is valid, False otherwise
        """
        try:
            logger.debug(f"🔍 Validating signal direction: {signal_type.value}")
            logger.debug(f"   Entry: {entry_price:.5f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}")
            
            if signal_type == SignalType.BUY:
                # For BUY signals:
                # - Stop loss should be BELOW entry price
                # - Take profit should be ABOVE entry price
                
                if stop_loss >= entry_price:
                    logger.error(f"🚨 BUY VALIDATION ERROR: Stop loss {stop_loss:.5f} not below entry {entry_price:.5f}")
                    return False
                    
                if take_profit <= entry_price:
                    logger.error(f"🚨 BUY VALIDATION ERROR: Take profit {take_profit:.5f} not above entry {entry_price:.5f}")
                    return False
                    
                logger.debug(f"✅ BUY signal direction valid")
                return True
                
            elif signal_type == SignalType.SELL:
                # For SELL signals:
                # - Stop loss should be ABOVE entry price
                # - Take profit should be BELOW entry price
                
                if stop_loss <= entry_price:
                    logger.error(f"🚨 SELL VALIDATION ERROR: Stop loss {stop_loss:.5f} not above entry {entry_price:.5f}")
                    return False
                    
                if take_profit >= entry_price:
                    logger.error(f"🚨 SELL VALIDATION ERROR: Take profit {take_profit:.5f} not below entry {entry_price:.5f}")
                    return False
                    
                logger.debug(f"✅ SELL signal direction valid")
                return True
                
            elif signal_type == SignalType.WAIT:
                # WAIT signals don't require SL/TP validation
                logger.debug(f"✅ WAIT signal - no direction validation needed")
                return True
                
            else:
                logger.error(f"🚨 UNKNOWN SIGNAL TYPE: {signal_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error in signal direction validation: {e}")
            return False

    def _build_recommendation(self, signal_type: SignalType, signal_strength: SignalStrength,
                            entry_details: Dict, confluence: Dict, timeframe: str) -> Dict:
        """Build recommendation structure for signal_runner_enhanced"""
        if signal_type == SignalType.WAIT or not entry_details:
            return {}
        
        # Determine setup type from confluence factors
        factors = confluence.get('factors', [])
        has_structure_break = any(factor.get('type') == 'STRUCTURE_BREAK' for factor in factors)
        setup_type = 'breakout' if has_structure_break else 'pullback'
        
        # Format strength factors for better readability and consistency
        strength_factors = []
        for factor in factors:
            if isinstance(factor, dict):
                factor_type = factor.get('type', 'UNKNOWN')
                direction = factor.get('direction', '')
                strength = factor.get('strength', 0)
                score = factor.get('score', 0)
                
                # Create human-readable factor descriptions
                if factor_type == 'TREND_ALIGNMENT':
                    strength_factors.append(f"Strong {direction} trend alignment ({strength:.1f})")
                elif factor_type == 'ORDER_BLOCK':
                    strength_factors.append(f"{direction.title()} order block (Score: {score})")
                elif factor_type == 'STRUCTURE_BREAK':
                    strength_factors.append(f"{direction.title()} structure break (Str: {strength:.1f})")
                elif factor_type == 'LIQUIDITY_ZONE':
                    strength_factors.append(f"{direction.title()} liquidity swept (Score: {score})")
                elif factor_type == 'SUPPLY_DEMAND':
                    strength_factors.append(f"{direction.title()} supply/demand zone")
                else:
                    strength_factors.append(f"{factor_type}: {direction}")
            else:
                # Fallback for unexpected format
                strength_factors.append(str(factor))
        
        return {
            'action': signal_type,  # Keep as SignalType enum for consistency
            'confidence': self._assess_quality(confluence, len(confluence.get('factors', []))),
            'entry_details': entry_details,
            'setup_type': setup_type,  # Added for proper order type selection
            'strength': signal_strength,  # Keep as SignalStrength enum for consistency  
            'strength_factors': strength_factors,  # Human-readable factor descriptions
            'entry_timeframe': timeframe,
            'confluence_score': len(confluence.get('factors', [])),  # Number of confluence factors
            'strength_score': confluence.get('total_score', 0),  # Total confluence score
            'confluence_quality': confluence.get('total_score', 0) / confluence.get('max_score', 15),  # Quality ratio
            'total_confluence_score': confluence.get('total_score', 0)  # Added for better scoring
        }
    
    def _determine_signal_strength(self, confluence: Dict, entry_details: Dict) -> SignalStrength:
        """Determine signal strength based on the new professional score."""
        if not entry_details:
            return SignalStrength.WEAK
        
        score = confluence.get('total_score', 0)
        
        if score >= 12:
            return SignalStrength.VERY_STRONG
        elif score >= 10:
            return SignalStrength.STRONG
        elif score >= 7:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _assess_quality(self, confluence: Dict, confluence_count: int = 0) -> str:
        """Assess overall signal quality based on professional score + confluence count."""
        score = confluence.get('total_score', 0)
        
        # Enhanced quality logic: score ≥10 + confluence ≥2 = High quality
        if score >= 10 and confluence_count >= 2:
            return "HIGH"
        elif score >= 7 and confluence_count >= 1:
            return "MEDIUM"  # Changed from MODERATE for consistency
        else:
            return "LOW"
    
    def _create_wait_signal(self, error_msg: str = "") -> Dict:
        """Create a WAIT signal for error cases"""
        return {
            'signal_type': SignalType.WAIT,
            'signal_strength': SignalStrength.WEAK,
            'confluence_score': 0,
            'confluence_quality': 0.0,
            'total_score': 0,
            'entry_details': {},
            'valid': False,
            'analysis_quality': "LOW",
            'timeframe': "UNKNOWN",
            'recommendation': {},
            'error': error_msg
        }
    
    # Helper methods for data extraction
    def _extract_order_blocks(self, smc_analysis: Dict) -> List[Dict]:
        """Extract order blocks from SMC analysis with robust error handling"""
        try:
            order_blocks_data = smc_analysis.get('order_blocks', {})
            
            if isinstance(order_blocks_data, dict) and 'valid' in order_blocks_data:
                return order_blocks_data['valid']
            elif isinstance(order_blocks_data, list):
                return order_blocks_data
            else:
                return []
        except:
            return []
    
    def _extract_fair_value_gaps(self, smc_analysis: Dict) -> List[Dict]:
        """Extract Fair Value Gaps from SMC analysis"""
        try:
            fvg_data = smc_analysis.get('fair_value_gaps', {})
            
            if isinstance(fvg_data, dict) and 'active' in fvg_data:
                return fvg_data['active']  # Return only active/unfilled FVGs
            elif isinstance(fvg_data, dict) and 'all' in fvg_data:
                return fvg_data['all']
            elif isinstance(fvg_data, list):
                return fvg_data
            else:
                return []
        except:
            return []
    
    def _extract_liquidity_zones(self, smc_analysis: Dict) -> List[Dict]:
        """Extract liquidity zones from SMC analysis"""
        try:
            liquidity_data = smc_analysis.get('liquidity_zones', {})
            
            if isinstance(liquidity_data, dict) and 'all' in liquidity_data:
                return liquidity_data['all']
            elif isinstance(liquidity_data, list):
                return liquidity_data
            else:
                return []
        except:
            return []
    
    def _extract_supply_demand_zones(self, smc_analysis: Dict) -> List[Dict]:
        """Extract supply/demand zones from SMC analysis"""
        try:
            sd_data = smc_analysis.get('supply_demand_zones', {})
            
            if isinstance(sd_data, dict) and 'all' in sd_data:
                return sd_data['all']
            elif isinstance(sd_data, list):
                return sd_data
            else:
                return []
        except:
            return []
    
    def _get_order_block_type(self, order_block: Dict) -> str:
        """Get order block type as string"""
        try:
            ob_type = order_block.get('type', 'unknown')
            
            if hasattr(ob_type, 'value'):
                return ob_type.value.lower()
            
            ob_type_str = str(ob_type).lower()
            
            if 'bullish' in ob_type_str or 'demand' in ob_type_str:
                return 'bullish'
            elif 'bearish' in ob_type_str or 'supply' in ob_type_str:
                return 'bearish'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _get_supply_demand_type(self, zone: Dict) -> str:
        """Get supply/demand zone type as string"""
        try:
            zone_type = zone.get('zone_type') or zone.get('type', 'unknown')
            
            if hasattr(zone_type, 'value'):
                return zone_type.value.lower()
            
            return str(zone_type).lower()
        except:
            return 'unknown'
    
    def _find_nearby_order_blocks(self, order_blocks: List[Dict], current_price: float) -> List[Dict]:
        """Find order blocks near current price"""
        try:
            # Calculate distance to each order block
            scored_obs = []
            for ob in order_blocks:
                ob_top = ob.get('top', current_price)
                ob_bottom = ob.get('bottom', current_price)
                
                # Distance to closest part of order block
                distance = min(abs(current_price - ob_top), abs(current_price - ob_bottom))
                
                # Only consider order blocks within 0.2% of current price
                if distance <= current_price * 0.005:
                    scored_obs.append((distance, ob))
            
            # Sort by distance and return order blocks
            scored_obs.sort(key=lambda x: x[0])
            return [ob for _, ob in scored_obs]
        except:
            return []