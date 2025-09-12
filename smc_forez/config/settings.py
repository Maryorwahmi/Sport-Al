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
class QualitySettings:
    """Signal quality analysis configuration"""
    # Quality score thresholds - ENHANCED for 70%+ standard
    min_institutional_score: float = 90.0  # 90-100 institutional grade
    min_professional_score: float = 75.0   # 75-89 professional grade  
    min_execution_score: float = 70.0      # 70+ minimum for execution (ENHANCED)
    
    # Multi-timeframe weights
    htf_weight: float = 0.45    # Higher timeframe weight (45% - INCREASED)
    mtf_weight: float = 0.35    # Mid timeframe weight (35%)
    ltf_weight: float = 0.20    # Lower timeframe weight (20% - DECREASED)
    
    # Confluence factor weights (0-100 scale) - ENHANCED requirements
    trend_weight: float = 30.0        # Trend alignment weight (INCREASED)
    structure_weight: float = 25.0    # Structure break weight (INCREASED)
    orderblock_weight: float = 20.0   # Order block weight (INCREASED)
    liquidity_weight: float = 15.0    # Liquidity zone weight (DECREASED)
    fvg_weight: float = 5.0           # Fair value gap weight (DECREASED)
    supply_demand_weight: float = 5.0  # Supply/demand zone weight (DECREASED)
    
    # Risk management thresholds - ENHANCED
    min_rr_ratio: float = 2.5         # Minimum risk:reward ratio (INCREASED)
    max_risk_percentage: float = 0.015 # Maximum 1.5% risk per trade (DECREASED)
    min_confluence_factors: int = 3    # Minimum confluence factors required (NEW)
    
    # Execution filters - ENHANCED
    allowed_sessions: List[str] = field(default_factory=lambda: ['london', 'newyork', 'overlap'])
    max_concurrent_trades: int = 3     # Reduced for quality (DECREASED)
    duplicate_time_window: int = 6     # Hours to check for duplicates (INCREASED)
    
    # Pattern and structure requirements - NEW
    require_pattern_confirmation: bool = True
    require_structure_break: bool = True
    require_momentum_alignment: bool = True
    min_pattern_strength: float = 0.75  # 75% pattern strength minimum
    
    # Enable/disable quality analysis
    enable_quality_analysis: bool = True
    enable_logging: bool = True


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
    quality: QualitySettings = field(default_factory=QualitySettings)
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