"""
MT5 Connector Module
Handles connection to MetaTrader 5 and data retrieval across multiple timeframes
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    # MT5 not available, use mock values
    MT5_AVAILABLE = False
    
    # Create mock MT5 module for development/testing
    class MockMT5:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 16385
        TIMEFRAME_H4 = 16388
        TIMEFRAME_D1 = 16408
        
        @staticmethod
        def initialize():
            return False
        
        @staticmethod
        def login(*args):
            return False
        
        @staticmethod
        def shutdown():
            pass
        
        @staticmethod
        def last_error():
            return "MT5 not available"
        
        @staticmethod
        def copy_rates_from(*args):
            return None
        
        @staticmethod
        def copy_rates_from_pos(*args):
            return None
        
        @staticmethod
        def symbol_info_tick(*args):
            return None
        
        @staticmethod
        def symbol_info(*args):
            return None
    
    mt5 = MockMT5()

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Timeframe(Enum):
    """MT5 timeframe enum"""
    M1 = mt5.TIMEFRAME_M1
    M5 = mt5.TIMEFRAME_M5
    M15 = mt5.TIMEFRAME_M15
    M30 = mt5.TIMEFRAME_M30
    H1 = mt5.TIMEFRAME_H1
    H4 = mt5.TIMEFRAME_H4
    D1 = mt5.TIMEFRAME_D1


@dataclass
class CandleData:
    """Represents OHLCV candle data"""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str


class MT5Connector:
    """
    MetaTrader 5 connector for retrieving live and historical forex data
    """
    
    def __init__(self, account: Optional[int] = None, password: Optional[str] = None, server: Optional[str] = None):
        """
        Initialize MT5 connection
        
        Args:
            account: MT5 account number
            password: MT5 account password  
            server: MT5 server name
        """
        self.account = account
        self.password = password
        self.server = server
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to MT5
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not MT5_AVAILABLE:
                logger.warning("MetaTrader5 not available - running in demo mode")
                return False
                
            if not mt5.initialize():
                logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
                return False
                
            if self.account and self.password and self.server:
                if not mt5.login(self.account, self.password, self.server):
                    logger.error(f"Failed to login to MT5: {mt5.last_error()}")
                    return False
                    
            self.is_connected = True
            logger.info("Successfully connected to MT5")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MT5"""
        mt5.shutdown()
        self.is_connected = False
        logger.info("Disconnected from MT5")
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int = 1000,
        start_time: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve historical candlestick data
        
        Args:
            symbol: Currency pair symbol (e.g., 'EURUSD')
            timeframe: Chart timeframe
            count: Number of bars to retrieve
            start_time: Start time for data retrieval
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.is_connected:
            logger.error("Not connected to MT5")
            return None
            
        try:
            if start_time:
                rates = mt5.copy_rates_from(symbol, timeframe.value, start_time, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, timeframe.value, 0, count)
                
            if rates is None or len(rates) == 0:
                logger.error(f"No data retrieved for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving historical data: {e}")
            return None
    
    def get_live_data(self, symbol: str) -> Optional[Dict]:
        """
        Get current market data for a symbol
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Dictionary with current market data or None if error
        """
        if not self.is_connected:
            logger.error("Not connected to MT5")
            return None
            
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"No tick data for {symbol}")
                return None
                
            return {
                'symbol': symbol,
                'time': datetime.fromtimestamp(tick.time),
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume
            }
            
        except Exception as e:
            logger.error(f"Error retrieving live data: {e}")
            return None
    
    def get_multi_timeframe_data(
        self,
        symbol: str,
        timeframes: List[Timeframe],
        count: int = 1000
    ) -> Dict[str, pd.DataFrame]:
        """
        Retrieve data for multiple timeframes
        
        Args:
            symbol: Currency pair symbol
            timeframes: List of timeframes to retrieve
            count: Number of bars per timeframe
            
        Returns:
            Dictionary mapping timeframe names to DataFrames
        """
        data = {}
        
        for tf in timeframes:
            df = self.get_historical_data(symbol, tf, count)
            if df is not None:
                data[tf.name] = df
            else:
                logger.warning(f"Failed to retrieve data for {symbol} on {tf.name}")
                
        return data
    
    def is_market_open(self, symbol: str) -> bool:
        """
        Check if market is open for the given symbol
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            bool: True if market is open, False otherwise
        """
        if not self.is_connected:
            return False
            
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return False
                
            return symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
            
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Dictionary with symbol information or None if error
        """
        if not self.is_connected:
            return None
            
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
                
            return {
                'symbol': symbol,
                'digits': info.digits,
                'point': info.point,
                'spread': info.spread,
                'trade_mode': info.trade_mode,
                'min_lot': info.volume_min,
                'max_lot': info.volume_max,
                'lot_step': info.volume_step
            }
            
        except Exception as e:
            logger.error(f"Error retrieving symbol info: {e}")
            return None