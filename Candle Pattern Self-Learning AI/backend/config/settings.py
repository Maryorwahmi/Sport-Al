"""
Configuration settings for Candle Pattern Self-Learning AI
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class Timeframe(Enum):
    """Trading timeframes"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


@dataclass
class DataSettings:
    """Data ingestion settings"""
    symbols: List[str] = None
    timeframes: List[Timeframe] = None
    retention_years: int = 5
    data_path: str = "data/ohlcv"
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        if self.timeframes is None:
            self.timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]


@dataclass
class MLSettings:
    """Machine Learning settings"""
    model_type: str = "lstm"  # lstm, cnn, transformer, ensemble
    window_size: int = 20
    train_test_split: float = 0.8
    validation_split: float = 0.1
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    dropout_rate: float = 0.2
    model_path: str = "models/saved_models"
    
    # Pattern recognition
    n_clusters: int = 50
    min_pattern_confidence: float = 0.6
    use_dtw: bool = True


@dataclass
class SMCSettings:
    """Smart Money Concepts settings"""
    # Order Blocks
    ob_lookback: int = 30
    ob_min_proximity: float = 0.6
    ob_max_proximity: float = 0.8
    
    # Fair Value Gaps
    fvg_min_size_pips: float = 8.0
    fvg_track_mitigation: bool = True
    
    # Liquidity
    liquidity_threshold: float = 0.15
    sweep_confirmation_pips: float = 5.0
    
    # Structure
    swing_length: int = 20
    bos_confirmation_bars: int = 2


@dataclass
class ConfluenceSettings:
    """Confluence scoring weights"""
    h4_bias_weight: float = 0.20
    h1_structure_weight: float = 0.20
    m15_poi_weight: float = 0.20
    ob_proximity_weight: float = 0.15
    fvg_presence_weight: float = 0.08
    liquidity_sweep_weight: float = 0.07
    momentum_weight: float = 0.05
    session_weight: float = 0.05
    
    # Thresholds
    execute_threshold: float = 0.75
    watch_threshold: float = 0.50
    ignore_threshold: float = 0.50


@dataclass
class RiskSettings:
    """Risk management settings"""
    risk_per_trade: float = 0.01  # 1%
    max_portfolio_risk: float = 0.05  # 5%
    max_position_size: float = 0.1  # 10% of account
    max_concurrent_trades: int = 3
    max_daily_loss: float = 0.03  # 3%
    min_rr_ratio: float = 2.0
    max_rr_ratio: float = 5.0
    
    # Position sizing
    use_atr_stops: bool = True
    atr_multiplier: float = 2.0
    
    # Drawdown controls
    max_drawdown: float = 0.10  # 10%
    emergency_stop: bool = True


@dataclass
class BacktestSettings:
    """Backtesting settings"""
    initial_balance: float = 10000.0
    commission_pips: float = 0.8
    slippage_pips: float = 0.5
    spread_pips: float = 1.0
    
    # Walk-forward
    train_window_days: int = 365
    test_window_days: int = 90
    step_days: int = 30


@dataclass
class Settings:
    """Main settings container"""
    data: DataSettings = None
    ml: MLSettings = None
    smc: SMCSettings = None
    confluence: ConfluenceSettings = None
    risk: RiskSettings = None
    backtest: BacktestSettings = None
    
    # MT5 connection (optional)
    mt5_login: Optional[int] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = DataSettings()
        if self.ml is None:
            self.ml = MLSettings()
        if self.smc is None:
            self.smc = SMCSettings()
        if self.confluence is None:
            self.confluence = ConfluenceSettings()
        if self.risk is None:
            self.risk = RiskSettings()
        if self.backtest is None:
            self.backtest = BacktestSettings()


def load_settings() -> Settings:
    """Load settings from environment or config file"""
    return Settings()
