
from enum import Enum
from typing import Dict, Optional

from ..market_structure.structure_analyzer import TrendDirection

class MarketBias(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    CONFLICT = "CONFLICT"

class BiasFilter:
    """
    Determines the overall market bias based on a strict top-down analysis
    from higher timeframes (H4, H1) to a lower timeframe (M15).
    """

    def __init__(self, htf_timeframe='H4', mtf_timeframe='H1', ltf_timeframe='M15'):
        """
        Initializes the BiasFilter.

        Args:
            htf_timeframe (str): The highest timeframe for establishing bias.
            mtf_timeframe (str): The medium timeframe for confirming bias.
            ltf_timeframe (str): The lower timeframe for execution.
        """
        self.htf_timeframe = htf_timeframe
        self.mtf_timeframe = mtf_timeframe
        self.ltf_timeframe = ltf_timeframe

    def get_market_bias(self, timeframe_analyses: Dict) -> MarketBias:
        """
        Determines the definitive market bias based on the "H4 -> H1 -> M15" rule.

        Args:
            timeframe_analyses (Dict): A dictionary containing the analysis for each timeframe.
                                       Example: {'H4': {'trend': TrendDirection.UPTREND}, 'H1': ...}

        Returns:
            MarketBias: The definitive market bias (BULLISH, BEARISH, NEUTRAL, or CONFLICT).
        """
        htf_trend = self._get_trend_from_analysis(timeframe_analyses, self.htf_timeframe)
        mtf_trend = self._get_trend_from_analysis(timeframe_analyses, self.mtf_timeframe)

        # Rule 1: H4 defines the primary bias.
        if htf_trend == TrendDirection.UPTREND:
            # Rule 2: H1 must align with H4 for a confirmed bullish bias.
            if mtf_trend == TrendDirection.UPTREND:
                return MarketBias.BULLISH
            # If H1 is sideways, the bias is neutral but leaning bullish.
            elif mtf_trend == TrendDirection.CONSOLIDATION:
                return MarketBias.NEUTRAL
            # If H1 conflicts with H4, the market is in conflict.
            else:
                return MarketBias.CONFLICT

        elif htf_trend == TrendDirection.DOWNTREND:
            # Rule 2: H1 must align with H4 for a confirmed bearish bias.
            if mtf_trend == TrendDirection.DOWNTREND:
                return MarketBias.BEARISH
            # If H1 is sideways, the bias is neutral but leaning bearish.
            elif mtf_trend == TrendDirection.CONSOLIDATION:
                return MarketBias.NEUTRAL
            # If H1 conflicts with H4, the market is in conflict.
            else:
                return MarketBias.CONFLICT

        # If H4 is sideways or uncertain, the overall bias is neutral.
        else:
            return MarketBias.NEUTRAL

    def _get_trend_from_analysis(self, timeframe_analyses: Dict, timeframe: str) -> Optional[TrendDirection]:
        """Safely extracts the trend from the analysis dictionary."""
        analysis = timeframe_analyses.get(timeframe, {})
        if not analysis:
            return None
        
        # Handle both direct trend object and nested market structure
        trend = analysis.get('trend')
        if not trend and 'market_structure' in analysis:
            trend = analysis['market_structure'].get('trend')
            
        # Convert string to enum if necessary
        if isinstance(trend, str):
            try:
                return TrendDirection[trend.upper()]
            except KeyError:
                return TrendDirection.CONSOLIDATION  # Default to consolidation instead of UNCERTAIN
        
        return trend

    def can_execute_trade(self, signal_direction: str, market_bias: MarketBias) -> bool:
        """
        Checks if a trade signal is valid based on the established market bias.
        M15 execution must align with the H4/H1 bias.

        Args:
            signal_direction (str): The direction of the trade signal ('BUY' or 'SELL').
            market_bias (MarketBias): The established market bias.

        Returns:
            bool: True if the trade is aligned with the bias, False otherwise.
        """
        if market_bias == MarketBias.BULLISH and signal_direction.upper() == 'BUY':
            return True
        if market_bias == MarketBias.BEARISH and signal_direction.upper() == 'SELL':
            return True
        
        # No trades are allowed in NEUTRAL or CONFLICT states.
        return False

    def assess_signal_confidence(self, signal_direction: str, market_bias: MarketBias, 
                                timeframe_alignment: dict, signal_confluence_data: dict = None) -> tuple[str, float, str]:
        """
        Enhanced assessment providing confidence scoring instead of binary approval.
        
        Args:
            signal_direction: 'BUY' or 'SELL'
            market_bias: Current market bias
            timeframe_alignment: Dict with timeframe trend info
            signal_confluence_data: Pre-calculated signal confluence data (NEW)
            
        Returns:
            tuple: (decision, confidence_score, reason)
        """
        signal_dir = signal_direction.upper()
        
        # Perfect alignment
        if market_bias == MarketBias.BULLISH and signal_dir == 'BUY':
            return "EXECUTE", 1.0, "Perfect bullish alignment"
        if market_bias == MarketBias.BEARISH and signal_dir == 'SELL':
            return "EXECUTE", 1.0, "Perfect bearish alignment"
        
        # Use pre-calculated signal confluence data if available (PRIORITY FIX)
        if signal_confluence_data:
            confluence_count = signal_confluence_data.get('confluence_count', 0)
            signal_scores = signal_confluence_data.get('signal_scores', {})
            total_confluence = sum(signal_scores.values()) if signal_scores else 0
            
            # Strong confluence detected from multi-timeframe signal generation
            if confluence_count >= 3 and total_confluence >= 30:  # 3 TFs with strong signals
                return "EXECUTE", 0.9, f"Strong multi-timeframe confluence ({confluence_count} TFs, total score: {total_confluence})"
            elif confluence_count >= 2 and total_confluence >= 20:  # 2 TFs with good signals
                return "EXECUTE", 0.7, f"Good multi-timeframe confluence ({confluence_count} TFs, total score: {total_confluence})"
            elif confluence_count >= 1:
                return "LOW_CONFIDENCE", 0.4, f"Weak confluence ({confluence_count} TFs aligned)"
            else:
                return "WAIT", 0.2, "No significant timeframe confluence"
        
        # Fallback to original trend-based validation if no signal confluence data
        # Consolidation scenarios - check timeframe agreement
        if market_bias == MarketBias.NEUTRAL:
            aligned_tfs = sum(1 for tf_data in timeframe_alignment.values() 
                            if self._is_trend_supporting_signal(tf_data.get('trend'), signal_dir))
            total_tfs = len(timeframe_alignment)
            
            if aligned_tfs >= (total_tfs * 2/3):  # At least 2/3 timeframes agree
                return "EXECUTE", 0.7, f"Consolidation with {aligned_tfs}/{total_tfs} TFs supporting {signal_dir}"
            elif aligned_tfs >= (total_tfs / 2):  # At least half agree
                return "LOW_CONFIDENCE", 0.4, f"Weak consolidation signal ({aligned_tfs}/{total_tfs} TFs agree)"
            else:
                return "WAIT", 0.2, f"Insufficient timeframe agreement ({aligned_tfs}/{total_tfs} TFs)"
        
        # Bias mismatch scenarios
        if market_bias == MarketBias.BULLISH and signal_dir == 'SELL':
            return "WAIT", 0.1, "SELL signal conflicts with BULLISH bias"
        if market_bias == MarketBias.BEARISH and signal_dir == 'BUY':
            return "WAIT", 0.1, "BUY signal conflicts with BEARISH bias"
        
        # Conflict states
        return "WAIT", 0.0, "Market bias in conflict state"
    
    def _is_trend_supporting_signal(self, trend, signal_direction: str) -> bool:
        """Check if timeframe trend supports signal direction"""
        if not trend:
            return False
        
        trend_str = str(trend).upper()
        signal_dir = signal_direction.upper()
        
        if 'UPTREND' in trend_str and signal_dir == 'BUY':
            return True
        if 'DOWNTREND' in trend_str and signal_dir == 'SELL':
            return True
        
        return False
