"""
Advanced Settings Configuration for AI-SMC Engine
Pydantic-based configuration with environment variable support
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from .constants import DEFAULT_SYMBOLS, RISK_CONSTANTS, PERFORMANCE_TARGETS

class RiskLevel(Enum):
    """Risk level classifications"""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"  
    AGGRESSIVE = "AGGRESSIVE"

class TradingMode(Enum):
    """Trading mode options"""
    SIGNALS_ONLY = "SIGNALS_ONLY"
    PAPER_TRADING = "PAPER_TRADING"
    LIVE_TRADING = "LIVE_TRADING"

class MT5Settings(BaseModel):
    """MetaTrader 5 configuration settings"""
    
    # Auto-detect from system - no need for manual credentials
    auto_detect: bool = Field(True, description="Auto-detect MT5 configuration")
    terminal_path: Optional[str] = Field(None, description="MT5 terminal path override")
    timeout: int = Field(60, description="Connection timeout in seconds")
    
class AnalysisSettings(BaseModel):
    """Analysis configuration settings"""
    
    # Timeframe Configuration
    primary_timeframe: str = Field("H4", description="Primary analysis timeframe")
    confirmation_timeframes: List[str] = Field(["H1", "M15"], description="Confirmation timeframes")
    
    # SMC Parameters
    swing_length: int = Field(20, description="Swing point detection length")
    fvg_min_size: float = Field(5.0, description="Minimum FVG size in pips")
    order_block_lookback: int = Field(20, description="Order block detection lookback")
    liquidity_threshold: float = Field(0.1, description="Liquidity detection threshold")
    
    # Confluence Requirements
    min_confluence_score: float = Field(3.0, description="Minimum confluence factors")
    min_rr_ratio: float = Field(2.0, description="Minimum risk/reward ratio")
    
class TradingSettings(BaseModel):
    """Trading configuration settings"""
    
    # Symbol Configuration
    default_symbols: List[str] = Field(DEFAULT_SYMBOLS, description="Default trading symbols")
    
    # Risk Management
    risk_level: RiskLevel = Field(RiskLevel.CONSERVATIVE, description="Risk level")
    max_daily_loss: float = Field(0.03, description="Maximum daily loss percentage")
    max_portfolio_risk: float = Field(0.08, description="Maximum portfolio risk percentage")
    risk_per_trade: float = Field(0.02, description="Risk per trade percentage")
    
    # Trading Mode
    trading_mode: TradingMode = Field(TradingMode.SIGNALS_ONLY, description="Trading mode")
    
class QualitySettings(BaseModel):
    """Quality analysis configuration"""
    
    # Quality Filter
    enable_quality_analysis: bool = Field(True, description="Enable quality analysis")
    enable_12_point_filter: bool = Field(True, description="Enable 12-point filter")
    min_quality_score: float = Field(0.7, description="Minimum quality score (70%)")
    
    # Session Optimization
    require_session_optimization: bool = Field(True, description="Require session optimization")
    preferred_sessions: List[str] = Field(["overlap", "london", "new_york"], description="Preferred sessions")
    
class SessionSettings(BaseModel):
    """Session analysis configuration"""
    
    # Session Configuration
    enable_session_analysis: bool = Field(True, description="Enable session analysis")
    london_start: int = Field(8, description="London session start hour (GMT)")
    london_end: int = Field(17, description="London session end hour (GMT)")
    new_york_start: int = Field(13, description="NY session start hour (EST)")
    new_york_end: int = Field(22, description="NY session end hour (EST)")
    
class BacktestSettings(BaseModel):
    """Backtesting configuration"""
    
    # Backtest Parameters
    initial_balance: float = Field(10000.0, description="Initial balance for backtesting")
    commission: float = Field(0.0001, description="Commission per trade")
    spread: float = Field(0.0002, description="Spread cost")
    
    # Historical Data
    history_days: int = Field(180, description="Days of historical data")
    
class MonitoringSettings(BaseModel):
    """Monitoring and logging configuration"""
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_to_file: bool = Field(True, description="Enable file logging")
    log_directory: str = Field("logs", description="Log directory")
    
    # Performance Monitoring
    enable_performance_monitoring: bool = Field(True, description="Enable performance monitoring")
    metrics_interval: int = Field(60, description="Metrics collection interval (seconds)")
    
    # Alerts
    enable_alerts: bool = Field(True, description="Enable alert system")
    alert_email: Optional[str] = Field(None, description="Alert email address")
    
class APISettings(BaseModel):
    """API configuration settings"""
    
    # API Configuration
    enable_api: bool = Field(False, description="Enable REST API")
    api_host: str = Field("localhost", description="API host")
    api_port: int = Field(8080, description="API port")
    
    # WebSocket Configuration
    enable_websocket: bool = Field(False, description="Enable WebSocket")
    websocket_port: int = Field(8081, description="WebSocket port")
    
    # Security
    api_key: Optional[str] = Field(None, description="API key for authentication")
    
class Settings(BaseModel):
    """Main settings class combining all configuration sections"""
    
    # Core Settings
    mt5: MT5Settings = Field(default_factory=MT5Settings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    quality: QualitySettings = Field(default_factory=QualitySettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    backtest: BacktestSettings = Field(default_factory=BacktestSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    api: APISettings = Field(default_factory=APISettings)
    
    # Global Settings
    debug: bool = Field(False, description="Enable debug mode")
    environment: str = Field("development", description="Environment name")
    
    @field_validator('trading')
    def validate_trading_settings(cls, v):
        """Validate trading settings"""
        if v.max_daily_loss > 0.1:  # 10% maximum
            raise ValueError("Daily loss limit cannot exceed 10%")
        if v.max_portfolio_risk > 0.2:  # 20% maximum
            raise ValueError("Portfolio risk cannot exceed 20%")
        return v
    
    @field_validator('quality')
    def validate_quality_settings(cls, v):
        """Validate quality settings"""
        if v.min_quality_score < 0.3 or v.min_quality_score > 1.0:
            raise ValueError("Quality score must be between 30% and 100%")
        return v

# Factory function for easy configuration creation
def create_settings(
    risk_level: str = "conservative",
    trading_mode: str = "signals_only",
    enable_api: bool = False,
    **kwargs
) -> Settings:
    """
    Factory function to create settings with common configurations
    
    Args:
        risk_level: "conservative", "moderate", or "aggressive"
        trading_mode: "signals_only", "paper_trading", or "live_trading"
        enable_api: Enable REST API
        **kwargs: Additional overrides
        
    Returns:
        Configured Settings instance
    """
    # Set base configuration based on risk level
    risk_configs = {
        "conservative": {
            "trading__risk_per_trade": 0.01,
            "trading__max_daily_loss": 0.02,
            "quality__min_quality_score": 0.8
        },
        "moderate": {
            "trading__risk_per_trade": 0.02,
            "trading__max_daily_loss": 0.03,
            "quality__min_quality_score": 0.7
        },
        "aggressive": {
            "trading__risk_per_trade": 0.03,
            "trading__max_daily_loss": 0.05,
            "quality__min_quality_score": 0.6
        }
    }
    
    # Apply risk level configuration
    if risk_level.lower() in risk_configs:
        kwargs.update(risk_configs[risk_level.lower()])
    
    # Apply trading mode
    kwargs["trading__trading_mode"] = trading_mode.upper()
    
    # Apply API settings
    kwargs["api__enable_api"] = enable_api
    
    # Create settings with overrides
    return Settings(**kwargs)

# Predefined configurations for common use cases
CONSERVATIVE_CONFIG = create_settings("conservative", "signals_only")
MODERATE_CONFIG = create_settings("moderate", "paper_trading")
AGGRESSIVE_CONFIG = create_settings("aggressive", "live_trading", enable_api=True)