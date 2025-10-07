"""
MetaTrader 5 data source integration
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
from ..config.settings import Timeframe

# Try to import MetaTrader5 - graceful fallback if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    MT5_AVAILABLE = False
    mt5 = None  # Ensure mt5 is None if import fails

# Define MockMT5 class outside of the initial try-except block
# so it's always available for fallback.
class MockMT5:
    """A mock class to simulate MetaTrader5 API for testing purposes."""
    # Timeframe constants
    TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15 = 1, 5, 15
    TIMEFRAME_H1, TIMEFRAME_H4, TIMEFRAME_D1, TIMEFRAME_W1 = 16385, 16388, 16408, 32769
    
    def __init__(self):
        self._initialized = False
        logging.info("Initialized MockMT5")

    def initialize(self, *args, **kwargs):
        self._initialized = True
        logging.info("MockMT5: Initialized")
        return True

    def login(self, *args, **kwargs):
        if not self._initialized: return False
        logging.info("MockMT5: Logged in")
        return True

    def shutdown(self):
        self._initialized = False
        logging.info("MockMT5: Shutdown")

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        logging.debug(f"MockMT5: Generating {count} bars for {symbol}")
        end_date = datetime.now()
        # Adjust frequency based on timeframe for more realistic data
        freq_map = {
            self.TIMEFRAME_M15: '15T', self.TIMEFRAME_H1: 'H',
            self.TIMEFRAME_H4: '4H', self.TIMEFRAME_D1: 'D',
            self.TIMEFRAME_W1: 'W'
        }
        freq = freq_map.get(timeframe, 'H')
        
        dates = pd.date_range(end=end_date, periods=count, freq=freq)
        
        base_price = 1.0850 if 'EURUSD' in symbol else 1.2500
        volatility = 0.001
        
        returns = np.random.normal(loc=0, scale=volatility, size=count)
        prices = base_price * (1 + returns).cumprod()
        
        data = []
        for i, price in enumerate(prices):
            open_price = prices[i-1] if i > 0 else price
            high_price = max(open_price, price) + abs(np.random.normal(0, volatility/2))
            low_price = min(open_price, price) - abs(np.random.normal(0, volatility/2))
            
            data.append({
                'time': int(dates[i].timestamp()),
                'open': open_price, 'high': high_price, 'low': low_price, 'close': price,
                'tick_volume': np.random.randint(100, 1000), 'spread': 2, 'real_volume': 0
            })
        
        dtype = [('time', '<i8'), ('open', '<f8'), ('high', '<f8'), ('low', '<f8'), 
                 ('close', '<f8'), ('tick_volume', '<i8'), ('spread', '<i4'), ('real_volume', '<i8')]
        return np.array([tuple(d.values()) for d in data], dtype=dtype)

    def copy_rates_from(self, symbol, timeframe, start_date, count):
        return self.copy_rates_from_pos(symbol, timeframe, 0, count)

    def symbol_info(self, symbol):
        return type('SymbolInfo', (object,), {'spread': 2, 'point': 0.00001, 'name': symbol, 'digits': 5, 'bid': 1.0850, 'ask': 1.0852, 'volume_min': 0.01, 'volume_max': 100})()

    def symbol_info_tick(self, symbol):
        return type('Tick', (object,), {'bid': 1.0850, 'ask': 1.0852, 'time': int(datetime.now().timestamp())})()


# If the real MT5 failed to import, create an instance of the mock.
if not MT5_AVAILABLE:
    mt5 = MockMT5()


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
        self.is_mock = not MT5_AVAILABLE  # Track if we're using mock data
        
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 not available - using mock data for testing")
        
    def is_connected(self) -> bool:
        """Check if the data source is connected."""
        return self.connected

    def connect(self) -> bool:
        """
        Connect to MetaTrader 5, with fallback to mock data if connection fails.
        
        Returns:
            bool: True if connection successful or fallback to mock is successful
        """
        try:
            if not MT5_AVAILABLE:
                logger.warning("MT5 library not found. Switching to mock data mode.")
                self.is_mock = True
                self.connected = True
                return True

            if not mt5.initialize():
                logger.warning("MT5 initialization failed. Switching to mock data mode.")
                self.is_mock = True
                self.connected = True
                # Ensure we are using the mock mt5 object now
                globals()['mt5'] = MockMT5()
                return True
            
            # Check if MT5 is already connected/logged in
            account_info = mt5.account_info()
            if account_info is not None:
                logger.info(f"Using existing MT5 connection - Account: {account_info.login}")
                self.connected = True
                self.is_mock = False
                return True
                
            # If not connected, try to login with credentials (if provided)
            if self.login and self.password and self.server:
                if not mt5.login(self.login, self.password, self.server):
                    logger.error(f"MT5 login failed. Switching to mock data mode.")
                    self.is_mock = True
                    self.connected = True
                    globals()['mt5'] = MockMT5()
                    return True
            else:
                logger.warning("No existing MT5 connection found and no credentials provided. Using mock data.")
                self.is_mock = True
                self.connected = True
                globals()['mt5'] = MockMT5()
                return True
                    
            self.connected = True
            self.is_mock = False
            logger.info("MT5 connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {str(e)}. Switching to mock data mode.")
            self.is_mock = True
            self.connected = True
            globals()['mt5'] = MockMT5()
            return True
    
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