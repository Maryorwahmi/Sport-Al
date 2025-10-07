import configparser
import os
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class Timeframe(Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"

@dataclass
class TradingSettings:
    """Trading configuration settings, loaded from config.ini"""
    symbols: List[str]
    timeframes: List[Timeframe]
    risk_per_trade: float
    max_spread: float
    atr_length: int
    atr_multiplier: float
    news_impact_level: str
    min_volume_ratio: float

@dataclass
class AnalysisSettings:
    """Analysis configuration settings, loaded from config.ini"""
    swing_length: int
    fvg_min_size: float
    order_block_lookback: int
    liquidity_threshold: float
    swing_point_lookback: int

@dataclass
class QualitySettings:
    """Signal quality analysis configuration, loaded from config.ini"""
    min_confluence_score: int
    min_rr_ratio: float
    enable_quality_analysis: bool
    enable_logging: bool

@dataclass
class BacktestSettings:
    """Backtesting configuration settings, loaded from config.ini"""
    initial_balance: float
    commission: float
    start_date: str
    end_date: str

@dataclass
class Settings:
    """Main configuration class, loads all settings from config.ini"""
    mt5_login: int
    mt5_password: str
    mt5_server: str
    trading: TradingSettings
    analysis: AnalysisSettings
    quality: QualitySettings
    backtest: BacktestSettings
    timeframes: List[Timeframe] # Keep a direct reference for convenience

    def __init__(self, config_file: str = 'config.ini'):
        config = configparser.ConfigParser()
        
        # Ensure the config file path is correct, assuming it's in the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, config_file)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
            
        config.read(config_path)

        # MT5 Settings - Handle "auto" mode for existing connections
        login_str = config.get('mt5', 'login')
        if login_str.lower() == 'auto':
            self.mt5_login = None  # Signal to use existing connection
        else:
            try:
                self.mt5_login = int(login_str) if login_str.strip() else None
            except ValueError:
                self.mt5_login = None
                
        password_str = config.get('mt5', 'password')
        self.mt5_password = None if password_str.lower() == 'auto' else password_str
        
        server_str = config.get('mt5', 'server')
        self.mt5_server = None if server_str.lower() == 'auto' else server_str

        # Trading Settings
        symbols_str = config.get('trading', 'symbols')
        timeframes_str = config.get('trading', 'timeframes')
        
        self.trading = TradingSettings(
            symbols=[s.strip() for s in symbols_str.split(',')],
            timeframes=[Timeframe(tf.strip()) for tf in timeframes_str.split(',')],
            risk_per_trade=config.getfloat('trading', 'risk_per_trade'),
            max_spread=config.getfloat('trading', 'max_spread'),
            atr_length=config.getint('trading', 'atr_length'),
            atr_multiplier=config.getfloat('trading', 'atr_multiplier'),
            news_impact_level=config.get('trading', 'news_impact_level'),
            min_volume_ratio=config.getfloat('trading', 'min_volume_ratio')
        )
        self.timeframes = self.trading.timeframes # Direct access

        # Analysis Settings
        self.analysis = AnalysisSettings(
            swing_length=config.getint('analysis', 'swing_length'),
            fvg_min_size=config.getfloat('analysis', 'fvg_min_size'),
            order_block_lookback=config.getint('analysis', 'order_block_lookback'),
            liquidity_threshold=config.getfloat('analysis', 'liquidity_threshold'),
            swing_point_lookback=config.getint('analysis', 'swing_point_lookback')
        )

        # Quality Settings
        self.quality = QualitySettings(
            min_confluence_score=config.getint('quality', 'min_confluence_score'),
            min_rr_ratio=config.getfloat('quality', 'min_rr_ratio'),
            enable_quality_analysis=config.getboolean('quality', 'enable_quality_analysis'),
            enable_logging=config.getboolean('quality', 'enable_logging')
        )

        # Backtest Settings
        self.backtest = BacktestSettings(
            initial_balance=config.getfloat('backtest', 'initial_balance'),
            commission=config.getfloat('backtest', 'commission'),
            start_date=config.get('backtest', 'start_date'),
            end_date=config.get('backtest', 'end_date')
        )

    
    