"""
MetaTrader 5 data source integration
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
from ..config.settings import Timeframe


logger = logging.getLogger(__name__)


class MT5DataSource:
    """MetaTrader 5 data source for fetching forex data"""
    
    def __init__(self, login: Optional[int] = None, password: Optional[str] = None, 
                 server: Optional[str] = None):
        """
        Initialize MT5 connection
        
        Args:
            login: MT5 account login
            password: MT5 account password
            server: MT5 server
        """
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        
    def connect(self) -> bool:
        """
        Connect to MetaTrader 5
        
        Returns:
            bool: True if connection successful
        """
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
                
            if self.login and self.password and self.server:
                if not mt5.login(self.login, self.password, self.server):
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
                    
            self.connected = True
            logger.info("MT5 connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 connection closed")
    
    def _timeframe_to_mt5(self, timeframe: Timeframe) -> int:
        """Convert Timeframe enum to MT5 timeframe constant"""
        timeframe_map = {
            Timeframe.M1: mt5.TIMEFRAME_M1,
            Timeframe.M5: mt5.TIMEFRAME_M5,
            Timeframe.M15: mt5.TIMEFRAME_M15,
            Timeframe.H1: mt5.TIMEFRAME_H1,
            Timeframe.H4: mt5.TIMEFRAME_H4,
            Timeframe.D1: mt5.TIMEFRAME_D1,
        }
        return timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
    
    def get_rates(self, symbol: str, timeframe: Timeframe, count: int = 1000,
                  start_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Get historical rates data
        
        Args:
            symbol: Currency pair symbol (e.g., 'EURUSD')
            timeframe: Timeframe for data
            count: Number of bars to fetch
            start_date: Start date for data (if None, gets latest data)
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.connected:
            logger.error("MT5 not connected")
            return None
            
        try:
            mt5_timeframe = self._timeframe_to_mt5(timeframe)
            
            if start_date:
                rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_date, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
                
            if rates is None or len(rates) == 0:
                logger.error(f"No data received for {symbol} {timeframe.value}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns to standard format
            df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'tick_volume': 'Volume'
            }, inplace=True)
            
            # Drop spread column if exists
            if 'spread' in df.columns:
                df.drop('spread', axis=1, inplace=True)
                
            logger.info(f"Fetched {len(df)} bars for {symbol} {timeframe.value}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching rates: {str(e)}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Dictionary with symbol info or None if error
        """
        if not self.connected:
            logger.error("MT5 not connected")
            return None
            
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                logger.error(f"Symbol {symbol} not found")
                return None
                
            return {
                'symbol': info.name,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'bid': info.bid,
                'ask': info.ask,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info: {str(e)}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Get current bid/ask prices
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Dictionary with bid/ask prices or None if error
        """
        if not self.connected:
            logger.error("MT5 not connected")
            return None
            
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"No tick data for {symbol}")
                return None
                
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': (tick.ask - tick.bid) * 10000,  # In pips for major pairs
                'time': datetime.fromtimestamp(tick.time)
            }
            
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            return None