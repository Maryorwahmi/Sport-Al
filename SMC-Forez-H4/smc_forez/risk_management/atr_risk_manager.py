
import pandas as pd
import pandas_ta as ta
from typing import Dict, Optional

class ATRRiskManager:
    """
    Manages risk using Average True Range (ATR) for dynamic stop loss
    and position size calculations.
    """

    def __init__(self, atr_length: int = 14, atr_multiplier: float = 2.5, default_risk_per_trade: float = 0.01):
        """
        Initializes the ATRRiskManager.

        Args:
            atr_length (int): The lookback period for calculating ATR.
            atr_multiplier (float): The multiplier to apply to the ATR value for stop loss placement.
            default_risk_per_trade (float): The default percentage of account to risk per trade (e.g., 0.01 for 1%).
        """
        self.atr_length = atr_length
        self.atr_multiplier = atr_multiplier
        self.default_risk_per_trade = default_risk_per_trade

    def calculate_atr(self, df: pd.DataFrame) -> Optional[float]:
        """
        Calculates the Average True Range (ATR) for the given data.

        Args:
            df (pd.DataFrame): DataFrame with OHLC data.

        Returns:
            Optional[float]: The latest ATR value, or None if calculation fails.
        """
        if df is None or len(df) < self.atr_length:
            return None
        try:
            atr_series = df.ta.atr(length=self.atr_length)
            if atr_series is None or atr_series.empty:
                return None
            return atr_series.iloc[-1]
        except Exception as e:
            # logger.error(f"Error calculating ATR: {e}")
            return None

    def calculate_atr_stop_loss(self, signal_type: str, entry_price: float, atr_value: float) -> float:
        """
        Calculates the stop loss based on the ATR value.

        Args:
            signal_type (str): 'buy' or 'sell'.
            entry_price (float): The trade entry price.
            atr_value (float): The current ATR value.

        Returns:
            float: The calculated stop loss price.
        """
        stop_distance = atr_value * self.atr_multiplier
        
        if signal_type.lower() == 'buy':
            return entry_price - stop_distance
        else: # sell
            return entry_price + stop_distance

    def calculate_position_size(self, account_balance: float, stop_loss_pips: float, risk_per_trade: Optional[float] = None) -> float:
        """
        Calculates the appropriate position size (lot size) for a trade.

        Args:
            account_balance (float): The current account balance.
            stop_loss_pips (float): The stop loss distance in pips.
            risk_per_trade (Optional[float]): The percentage of the account to risk. Uses default if None.

        Returns:
            float: The calculated lot size.
        """
        risk_amount = account_balance * (risk_per_trade or self.default_risk_per_trade)
        
        # Assuming a standard pip value of $10 for a 1.0 lot size on a standard account.
        # This needs to be adjusted based on the currency pair and account currency.
        # For simplicity, we'll use a generic calculation.
        pip_value_per_lot = 10.0 
        
        if stop_loss_pips <= 0:
            return 0.01 # Return a minimum lot size if SL is zero to avoid division errors

        lot_size = risk_amount / (stop_loss_pips * pip_value_per_lot)
        
        # Round to a valid lot size (usually 2 decimal places)
        return round(lot_size, 2)

    def enhance_entry_details_with_atr(self, entry_details: Dict, df: pd.DataFrame, signal_type: str) -> Dict:
        """
        Recalculates SL and TP using ATR and updates the entry_details dictionary.

        Args:
            entry_details (Dict): The original entry details from the signal generator.
            df (pd.DataFrame): The market data used for analysis.
            signal_type (str): The direction of the signal ('buy' or 'sell').

        Returns:
            Dict: The updated entry_details dictionary with ATR-based risk management.
        """
        atr_value = self.calculate_atr(df)
        if not atr_value:
            return entry_details # Return original if ATR calculation fails

        entry_price = entry_details['entry_price']
        
        # Recalculate Stop Loss using ATR
        original_sl = entry_details['stop_loss']
        atr_sl = self.calculate_atr_stop_loss(signal_type, entry_price, atr_value)

        # Use the more conservative (wider) stop loss between the original and ATR-based one
        if signal_type.lower() == 'buy':
            stop_loss = min(original_sl, atr_sl)
        else: # sell
            stop_loss = max(original_sl, atr_sl)

        # Recalculate Take Profit to maintain the original Risk:Reward ratio
        original_risk = abs(entry_price - original_sl)
        original_reward = abs(entry_details['take_profit'] - entry_price)
        
        if original_risk == 0:
            return entry_details # Avoid division by zero

        rr_ratio = original_reward / original_risk
        
        new_risk = abs(entry_price - stop_loss)
        new_reward = new_risk * rr_ratio

        if signal_type.lower() == 'buy':
            take_profit = entry_price + new_reward
        else: # sell
            take_profit = entry_price - new_reward

        # Update the dictionary
        entry_details['stop_loss'] = stop_loss
        entry_details['take_profit'] = take_profit
        entry_details['risk_pips'] = round(new_risk * 10000, 1)
        entry_details['reward_pips'] = round(new_reward * 10000, 1)
        entry_details['risk_management_type'] = 'ATR-Enhanced'
        entry_details['atr_value'] = atr_value

        return entry_details
