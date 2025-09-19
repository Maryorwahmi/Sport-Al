"""
Trading constants for AI-SMC engine
Institutional-grade trading parameters and thresholds
"""

from enum import Enum
from typing import Dict, Any

# Quality Grade Thresholds (12-point system)
class QualityGrade(Enum):
    """Signal quality classifications"""
    INSTITUTIONAL = "INSTITUTIONAL"  # 90%+ (10.8+/12 points)
    EXCELLENT = "EXCELLENT"          # 80%+ (9.6+/12 points) 
    GOOD = "GOOD"                    # 70%+ (8.4+/12 points)
    MODERATE = "MODERATE"            # 60%+ (7.2+/12 points)
    ACCEPTABLE = "ACCEPTABLE"        # 50%+ (6+/12 points)
    POOR = "POOR"                    # <50% (REJECTED)

QUALITY_THRESHOLDS = {
    QualityGrade.INSTITUTIONAL: 10.8,
    QualityGrade.EXCELLENT: 9.6,
    QualityGrade.GOOD: 8.4,
    QualityGrade.MODERATE: 7.2,
    QualityGrade.ACCEPTABLE: 6.0,
    QualityGrade.POOR: 0.0
}

# Trading Session Configuration
class TradingSession(Enum):
    """Trading session definitions"""
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OVERLAP = "OVERLAP"
    ASIAN = "ASIAN"
    
SESSION_CONFIG = {
    TradingSession.LONDON: {
        'start_hour': 8,
        'end_hour': 17,
        'timezone': 'GMT',
        'strength': 8
    },
    TradingSession.NEW_YORK: {
        'start_hour': 13,
        'end_hour': 22,
        'timezone': 'EST', 
        'strength': 7
    },
    TradingSession.OVERLAP: {
        'start_hour': 13,
        'end_hour': 17,
        'timezone': 'GMT',
        'strength': 10  # Optimal trading time
    }
}

# SMC Component Thresholds
SMC_THRESHOLDS = {
    'order_block_displacement_min': 20,  # Minimum 20 pips displacement
    'fvg_min_size_pips': 5,             # Minimum FVG size
    'liquidity_sweep_threshold': 0.1,    # Liquidity sweep detection
    'premium_discount_levels': {
        'discount_max': 0.382,           # 0-38.2% discount zone
        'equilibrium_min': 0.382,        # 38.2-61.8% equilibrium  
        'equilibrium_max': 0.618,
        'premium_min': 0.618             # 61.8-100% premium zone
    },
    'ote_zone': {
        'min': 0.618,                    # 61.8% minimum
        'max': 0.786                     # 78.6% maximum
    }
}

# Risk Management Constants  
RISK_CONSTANTS = {
    'max_portfolio_risk': 0.08,         # 8% maximum portfolio exposure
    'max_daily_loss': 0.03,             # 3% maximum daily loss
    'min_rr_ratio': 2.0,                # Minimum 2:1 risk/reward
    'correlation_limit': 0.7,           # Maximum correlation exposure
    'quality_multipliers': {
        QualityGrade.INSTITUTIONAL: 1.20,
        QualityGrade.EXCELLENT: 1.10,
        QualityGrade.GOOD: 1.00,
        QualityGrade.MODERATE: 0.80,
        QualityGrade.ACCEPTABLE: 0.50
    }
}

# Timeframe Weights for Multi-Timeframe Analysis
TIMEFRAME_WEIGHTS = {
    'H4': 0.50,  # Primary analysis - 50% weight
    'H1': 0.30,  # Confirmation - 30% weight  
    'M15': 0.20  # Entry refinement - 20% weight
}

# Default Symbol Configuration
DEFAULT_SYMBOLS = [
    'EURUSDm', 'GBPUSDm', 'USDJPYm', 'AUDUSDm', 'USDCADm',
    'USDCHFm', 'NZDUSDm', 'EURGBPm', 'EURJPY', 'GBPJPY'
]

# Performance Requirements
PERFORMANCE_TARGETS = {
    'analysis_speed_seconds': 5,        # <5 seconds per symbol
    'memory_limit_mb': 500,             # <500MB for 5 symbols
    'target_win_rate': 0.70,            # 70%+ win rate target
    'min_profit_factor': 1.5,           # Minimum profit factor
    'max_drawdown_percent': 15          # Maximum 15% drawdown
}

# 12-Point Quality Filter Weights
QUALITY_FILTER_WEIGHTS = {
    'market_bias_alignment': 2.0,       # CRITICAL - must match H4 bias
    'multi_timeframe_confluence': 2.0,  # 80%+ agreement
    'smc_component_confluence': 1.5,    # 4+ factors = 1.5pts
    'risk_reward_ratio': 1.5,           # 3:1+ = 1.5pts
    'session_timing_optimization': 1.0, # London/NY overlap preferred
    'premium_discount_position': 1.0,   # Optimal zone entry
    'market_structure_quality': 1.0,    # Structure strength
    'choch_mss_confirmation': 1.0,      # Recent structure shifts
    'ote_zone_validation': 1.0,         # 61.8-78.6% retracement
    'liquidity_considerations': 0.5,    # Sweep context
    'inducement_pattern_validation': 0.5, # Fake-out confirmation
    'volume_momentum_confirmation': 0.5  # Momentum alignment
}

# Signal Execution Thresholds
EXECUTION_THRESHOLDS = {
    'min_confluence_score': 3.0,        # Minimum confluence factors
    'min_quality_score': 0.7,           # 70% minimum quality
    'require_session_optimization': True,
    'enable_12_point_filter': True,
    'max_signals_per_session': 5,       # Limit signal quantity
    'cooldown_minutes': 30               # Minutes between similar signals
}