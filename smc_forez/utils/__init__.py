"""
Utility modules for SMC Forez
"""

from .multi_timeframe import MultiTimeframeAnalyzer

# Optional imports with graceful fallback
try:
    from .logger import SMCLogger, get_logger, cleanup_logger
    from .risk_manager import RiskManager, create_risk_manager, RiskLevel
    LOGGING_AVAILABLE = True
    RISK_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    RISK_AVAILABLE = False

try:
    from .visualizer import SMCChartPlotter, create_chart
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Export based on what's available
__all__ = ['MultiTimeframeAnalyzer']

if LOGGING_AVAILABLE:
    __all__.extend(['SMCLogger', 'get_logger', 'cleanup_logger'])

if RISK_AVAILABLE:
    __all__.extend(['RiskManager', 'create_risk_manager', 'RiskLevel'])

if VISUALIZATION_AVAILABLE:
    __all__.extend(['SMCChartPlotter', 'create_chart'])