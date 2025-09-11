"""
Configuration settings for SMC Forez analyzer
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Timeframe(Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


@dataclass
class TradingSettings:
    """Trading configuration settings"""
    default_symbol: str = "EURUSD"
    risk_per_trade: float = 0.01  # 1% risk
    max_spread: float = 2.0  # 2 pips
    min_rr_ratio: float = 1.5  # Risk/Reward ratio
    

@dataclass
class AnalysisSettings:
    """Analysis configuration settings"""
    swing_length: int = 10
    liquidity_threshold: float = 0.1
    fvg_min_size: float = 5.0  # Minimum FVG size in pips
    order_block_lookback: int = 20
    bos_confirmation_candles: int = 3
    

@dataclass
class BacktestSettings:
    """Backtesting configuration settings"""
    initial_balance: float = 10000.0
    commission: float = 0.00007  # 0.7 pips
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"


@dataclass
class Settings:
    """Main configuration class"""
    trading: TradingSettings = field(default_factory=TradingSettings)
    analysis: AnalysisSettings = field(default_factory=AnalysisSettings)
    backtest: BacktestSettings = field(default_factory=BacktestSettings)
    
    # MT5 connection settings
    mt5_login: Optional[int] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    
    # Supported timeframes for analysis
    timeframes: List[Timeframe] = field(default_factory=lambda: [
        Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1
    ])
    
    # Major forex symbols for backtesting (7+ symbols)
    major_symbols: List[str] = field(default_factory=lambda: [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"
    ])
    
    # Extended symbol list for signal generation (28+ symbols)
    all_symbols: List[str] = field(default_factory=lambda: [
        # Major pairs
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
        # Minor pairs
        "EURJPY", "EURGBP", "EURCHF", "EURAUD", "EURCAD", "EURNZD",
        "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
        "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
        "NZDJPY", "NZDCHF", "NZDCAD",
        "CADJPY", "CADCHF", "CHFJPY"
    ])