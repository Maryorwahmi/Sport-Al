"""
AI-SMC: Advanced Institutional-Grade SMC Forex Analyzer Engine

A comprehensive Smart Money Concepts (SMC) trading system implementing ICT methodology
with multi-timeframe analysis, 12-point quality filtering, and institutional-grade
risk management for professional forex trading.

Author: AI-SMC Development Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "AI-SMC Development Team"

# Core imports for easy access
try:
    from analyzer import SMCAnalyzer
    from config.settings import Settings
    from signals.signal_generator import SignalGenerator
    from risk_management.risk_manager import RiskManager
except ImportError:
    # Fallback for package imports
    SMCAnalyzer = None
    Settings = None
    SignalGenerator = None
    RiskManager = None

__all__ = [
    'SMCAnalyzer',
    'Settings', 
    'SignalGenerator',
    'RiskManager'
]