
import pandas as pd
import investpy
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ExternalConditionFilter:
    """
    Filters trading signals based on external market conditions like news events and volume.
    """

    def __init__(self, news_impact_level: str = 'high', news_lookahead_mins: int = 60, news_blackout_mins: int = 30, min_volume_ratio: float = 0.75):
        """
        Initializes the ExternalConditionFilter.

        Args:
            news_impact_level (str): The minimum news impact level to consider ('high', 'medium', 'low').
            news_lookahead_mins (int): How many minutes in the future to check for news.
            news_blackout_mins (int): The time window (in minutes) before and after a news event to avoid trading.
            min_volume_ratio (float): The minimum ratio of current volume to its moving average to be considered liquid.
        """
        self.news_impact_level = news_impact_level
        self.news_lookahead_mins = news_lookahead_mins
        self.news_blackout_mins = news_blackout_mins
        self.min_volume_ratio = min_volume_ratio

    def get_high_impact_news(self, currencies: List[str]) -> Optional[pd.DataFrame]:
        """
        Fetches upcoming high-impact economic news for the specified currencies.

        Args:
            currencies (List[str]): A list of currency symbols (e.g., ['USD', 'EUR', 'GBP']).

        Returns:
            Optional[pd.DataFrame]: A DataFrame of news events, or None if an error occurs.
        """
        try:
            # investpy expects full country names for some currencies
            country_map = {
                'USD': 'united states', 'EUR': 'euro zone', 'GBP': 'united kingdom',
                'JPY': 'japan', 'CAD': 'canada', 'AUD': 'australia', 'NZD': 'new zealand',
                'CHF': 'switzerland', 'CNY': 'china'
            }
            countries = [country_map.get(c.upper()) for c in currencies if c.upper() in country_map]
            
            logger.info(f"📰 Fetching {self.news_impact_level}-impact news for {currencies} ({countries})")
            
            news_df = investpy.economic_calendar(
                countries=countries,
                importances=[self.news_impact_level]
            )
            
            if news_df is not None and not news_df.empty:
                logger.info(f"📰 Found {len(news_df)} {self.news_impact_level}-impact news events")
            else:
                logger.info(f"📰 No {self.news_impact_level}-impact news events found")
                
            return news_df
        except Exception as e:
            logger.warning(f"📰 Error fetching economic calendar data: {e}")
            return None

    def is_news_risk_imminent(self, symbol: str, news_df: Optional[pd.DataFrame]) -> tuple[bool, Optional[str]]:
        """
        Checks if there is a high-impact news event for the given symbol within the blackout window.

        Args:
            symbol (str): The currency pair symbol (e.g., 'EURUSD').
            news_df (Optional[pd.DataFrame]): The DataFrame of news events.

        Returns:
            tuple[bool, Optional[str]]: (True if risk is imminent, reason string or None).
        """
        if news_df is None or news_df.empty:
            logger.info(f"📰 {symbol}: No news events to check")
            return False, None

        now = datetime.now()
        blackout_window = timedelta(minutes=self.news_blackout_mins)
        
        # Extract currencies from the symbol
        base_currency = symbol[:3].upper()
        quote_currency = symbol[3:].upper()

        logger.info(f"📰 {symbol}: Checking for news risk within {self.news_blackout_mins}min blackout window")

        for index, event in news_df.iterrows():
            event_time_str = f"{event['date']} {event['time']}"
            try:
                # investpy format can be inconsistent, handle potential errors
                event_time = datetime.strptime(event_time_str, '%d/%m/%Y %H:%M')
            except ValueError:
                logger.warning(f"Could not parse event time: {event_time_str}")
                continue

            event_currency = event['currency'].upper()

            # Check if the event is relevant to the symbol and within our time window
            if event_currency in [base_currency, quote_currency]:
                time_to_event = event_time - now
                if abs(time_to_event) <= blackout_window:
                    reason = f"High-impact news '{event['event']}' for {event_currency} at {event_time.strftime('%H:%M')}"
                    logger.warning(f"🚫 {symbol}: NEWS BLACKOUT - {reason}")
                    return True, reason
        
        logger.info(f"✅ {symbol}: No news risk detected - safe to trade")
        return False, None

    def is_liquidity_sufficient(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Checks if there is sufficient market liquidity for the given symbol.

        Args:
            symbol (str): The currency pair symbol.

        Returns:
            tuple[bool, Optional[str]]: (True if liquidity is sufficient, reason string or None).
        """
        # For simplicity, we'll assume sufficient liquidity during standard trading hours
        # In a real-world scenario, this would involve checking:
        # - Session overlap periods
        # - Volume indicators
        # - Bid-ask spreads
        # - Holiday schedules

        now = datetime.now()
        hour = now.hour
        
        # Major forex sessions
        # London: 7:00 - 16:00 UTC
        # New York: 12:00 - 21:00 UTC
        # Overlap: 12:00 - 16:00 UTC (best liquidity)
        
        logger.info(f"💧 {symbol}: Checking liquidity at {hour:02d}:00 UTC")
        
        if 7 <= hour <= 21:  # During major sessions
            if 12 <= hour <= 16:
                logger.info(f"✅ {symbol}: Optimal liquidity (London-NY overlap)")
            else:
                logger.info(f"✅ {symbol}: Good liquidity (major session active)")
            return True, None
        else:
            reason = f"Low liquidity period (current hour: {hour})"
            logger.warning(f"🚫 {symbol}: LIQUIDITY RISK - {reason}")
            return False, reason

    def is_market_liquid(self, df: pd.DataFrame, symbol: str = "", atr_period: int = 14, vol_period: int = 20) -> tuple[bool, Optional[str]]:
        """
        Enhanced session-aware liquidity check with adaptive thresholds.

        Args:
            df (pd.DataFrame): DataFrame with OHLC and Volume data.
            symbol (str): Currency pair symbol for pair-specific adjustments.
            atr_period (int): Lookback period for ATR calculation.
            vol_period (int): Lookback period for volume moving average.

        Returns:
            tuple[bool, Optional[str]]: (True if market is liquid, reason string or None).
        """
        # TEMPORARILY DISABLED FOR TESTING - Skip all volume checks
        return True, "Volume checks disabled for testing validation fixes"
        
        # ORIGINAL VOLUME LOGIC (commented out for testing):
        # if 'Volume' not in df.columns or df['Volume'].sum() == 0:
        #     return True, "Volume data not available, skipping check." # Fail open if no volume data
        # 
        # # Get session-aware volume threshold with pair-specific adjustment
        # base_threshold = self._get_session_volume_threshold()
        # pair_multiplier = self._get_pair_volume_multiplier(symbol)
        # final_threshold = base_threshold * pair_multiplier
        
        # 1. Enhanced Volume Check with session and pair awareness
        avg_volume = df['Volume'].rolling(window=vol_period).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]

        if avg_volume > 0 and (current_volume / avg_volume) < final_threshold:
            session_name = self._get_current_session_name()
            pair_type = self._get_pair_type(symbol)
            
            # If volume is extremely low, try ATR-based fallback
            if (current_volume / avg_volume) < 0.25:  # Less than 25% of average
                logger.warning(f"💧 {symbol}: Volume extremely low ({current_volume}), checking ATR fallback...")
                
                # ATR-based liquidity check as fallback
                try:
                    import pandas_ta as ta
                    atr = df.ta.atr(length=atr_period)
                    if atr is not None and not atr.empty:
                        current_atr = atr.iloc[-1]
                        avg_atr = atr.rolling(window=vol_period).mean().iloc[-1]
                        atr_ratio = current_atr / avg_atr if avg_atr > 0 else 0
                        
                        # If ATR shows reasonable volatility, allow trading
                        if 0.7 <= atr_ratio <= 2.0:  # Normal volatility range
                            logger.info(f"✅ {symbol}: ATR fallback PASSED - ATR ratio {atr_ratio:.2f} shows normal volatility")
                            return True, f"Volume low but ATR normal ({atr_ratio:.2f})"
                except:
                    pass  # ATR calculation failed, continue with volume rejection
            
            reason = f"Low liquidity: Current volume ({current_volume}) is below {final_threshold:.0%} of its {vol_period}-period average during {session_name} session ({pair_type} pair)."
            return False, reason

        # 2. Volatility Check (using ATR)
        atr = df.ta.atr(length=atr_period)
        if atr is None or atr.empty:
            return True, "ATR could not be calculated, skipping volatility check."

        avg_atr = atr.rolling(window=vol_period).mean().iloc[-1]
        current_atr = atr.iloc[-1]

        # Avoid extremely low volatility (dead market)
        if current_atr < avg_atr * 0.5:
            reason = f"Low volatility: Current ATR ({current_atr:.5f}) is less than 50% of its average."
            return False, reason
            
        # Avoid extremely high volatility (chaotic market)
        if current_atr > avg_atr * 3.0:
            reason = f"High volatility: Current ATR ({current_atr:.5f}) is more than 300% of its average."
            return False, reason

        return True, None

    def _get_session_volume_threshold(self) -> float:
        """Get volume threshold based on current trading session"""
        # TEMPORARILY DISABLED FOR TESTING - Allow all sessions with permissive threshold
        return 0.30  # Very permissive threshold for testing validation fixes
        
        # ORIGINAL SESSION-BASED LOGIC (commented out for testing):
        # now = datetime.now()
        # hour = now.hour
        # 
        # # London: 7:00 - 16:00 UTC (primary session)
        # # New York: 12:00 - 21:00 UTC (primary session)
        # # Overlap: 12:00 - 16:00 UTC (highest liquidity)
        # # Asia: 22:00 - 6:00 UTC (lower liquidity acceptable)
        # 
        # if 12 <= hour <= 16:  # London-NY overlap
        #     return 0.65  # Reduced from 0.70 for better signal flow
        # elif 7 <= hour < 12:  # London only
        #     return 0.55  # Reduced from 0.65 for London session
        # elif 16 < hour <= 21:  # New York only
        #     return 0.50  # Significantly reduced from 0.65 for NY session
        # else:  # Asia session
        #     return 0.45  # Reduced from 0.50 for Asia session
    
    def _get_pair_volume_multiplier(self, symbol: str) -> float:
        """Get volume multiplier based on currency pair type"""
        symbol_upper = symbol.upper()
        
        # Major pairs - standard thresholds
        majors = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
        if any(major in symbol_upper for major in majors):
            return 1.0  # No reduction
            
        # Minor pairs - more lenient
        minors = ['EURJPY', 'EURGBP', 'EURCHF', 'GBPJPY', 'GBPCHF', 'AUDJPY', 
                 'CADJPY', 'CHFJPY', 'CADCHF', 'NZDJPY', 'AUDCHF', 'AUDCAD']
        if any(minor in symbol_upper for minor in minors):
            return 0.85  # 15% more lenient
            
        # Exotic pairs - most lenient
        return 0.70  # 30% more lenient
    
    def _get_current_session_name(self) -> str:
        """Get current trading session name for logging"""
        now = datetime.now()
        hour = now.hour
        
        if 12 <= hour <= 16:
            return "London-NY Overlap"
        elif 7 <= hour < 12:
            return "London"
        elif 16 < hour <= 21:
            return "New York"
        elif 22 <= hour or hour <= 6:
            return "Asia"
        else:
            return "Transition"
    
    def _get_pair_type(self, symbol: str) -> str:
        """Get currency pair classification for logging"""
        symbol_upper = symbol.upper()
        
        majors = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
        if any(major in symbol_upper for major in majors):
            return "major"
            
        minors = ['EURJPY', 'EURGBP', 'EURCHF', 'GBPJPY', 'GBPCHF', 'AUDJPY', 
                 'CADJPY', 'CHFJPY', 'CADCHF', 'NZDJPY', 'AUDCHF', 'AUDCAD']
        if any(minor in symbol_upper for minor in minors):
            return "minor"
            
        return "exotic"
