"""
SMC Forez - Professional Forex Analyzer using Smart Money Concepts
"""

__version__ = "1.0.0"
__author__ = "SMC Forez Team"

# Import settings first (no external dependencies)
from .config.settings import Settings

# Conditional import of main analyzer (requires external dependencies)
try:
    from .analyzer import SMCAnalyzer
    __all__ = ["SMCAnalyzer", "Settings"]
except ImportError:
    # If external dependencies are not available, only export Settings
    __all__ = ["Settings"]
    SMCAnalyzer = None