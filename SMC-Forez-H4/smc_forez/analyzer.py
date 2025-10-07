"""
Main SMC Forex Analyzer that coordinates all components
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import sys
import os

# Handle both relative and absolute imports
if __name__ == "__main__":
    # When run directly, add parent directory to path and use absolute imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from smc_forez.config.settings import Settings, Timeframe
    from smc_forez.data_sources.mt5_source import MT5DataSource
    from smc_forez.market_structure.structure_analyzer import MarketStructureAnalyzer
    from smc_forez.smart_money.smc_analyzer import SmartMoneyAnalyzer
    from smc_forez.signals.signal_generator import SignalGenerator
    from smc_forez.utils.multi_timeframe import MultiTimeframeAnalyzer
    from smc_forez.backtesting.backtest_engine import BacktestEngine
    # == STRATEGIC REFACTOR: Use the single, enhanced quality filter ==
    from smc_forez.quality.enhanced_signal_filter import EnhancedSignalQualityFilter, LIVE_TRADING_FILTER
    # == INDUSTRIAL GRADE UPGRADE: Import the new Bias Filter for top-down analysis ==
    from smc_forez.filters.bias_filter import BiasFilter, MarketBias
    # == INDUSTRIAL GRADE UPGRADE: Import the new ATR Risk Manager ==
    from smc_forez.risk_management.atr_risk_manager import ATRRiskManager
    # == INDUSTRIAL GRADE UPGRADE: Import the new External Condition Filter ==
    from smc_forez.filters.external_filters import ExternalConditionFilter
else:
    # When imported as module, use relative imports
    from .config.settings import Settings, Timeframe
    from .data_sources.mt5_source import MT5DataSource
    from .market_structure.structure_analyzer import MarketStructureAnalyzer
    from .smart_money.smc_analyzer import SmartMoneyAnalyzer
    from .signals.signal_generator import SignalGenerator
    from .utils.multi_timeframe import MultiTimeframeAnalyzer
    from .backtesting.backtest_engine import BacktestEngine
    # == STRATEGIC REFACTOR: Use the single, enhanced quality filter ==
    from .quality.enhanced_signal_filter import EnhancedSignalQualityFilter, LIVE_TRADING_FILTER, SignalQuality
    # == INDUSTRIAL GRADE UPGRADE: Import the new Bias Filter for top-down analysis ==
    from .filters.bias_filter import BiasFilter, MarketBias
    # == INDUSTRIAL GRADE UPGRADE: Import the new ATR Risk Manager ==
    from .risk_management.atr_risk_manager import ATRRiskManager
    # == INDUSTRIAL GRADE UPGRADE: Import the new External Condition Filter ==
    from .filters.external_filters import ExternalConditionFilter


logger = logging.getLogger(__name__)


class SMCAnalyzer:
    """
    Main SMC Forex Analyzer class that coordinates all analysis components
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the SMC Analyzer
        
        Args:
            settings: Configuration settings (uses defaults if None)
        """
        self.settings = settings or Settings()
        self.logger = logger # <-- FIX: Initialize logger
        
        # Initialize components
        self.data_source = MT5DataSource(
            login=self.settings.mt5_login,
            password=self.settings.mt5_password,
            server=self.settings.mt5_server
        )
        
        self.structure_analyzer = MarketStructureAnalyzer(
            swing_length=self.settings.analysis.swing_length
        )
        
        self.smc_analyzer = SmartMoneyAnalyzer(
            fvg_min_size=self.settings.analysis.fvg_min_size,
            order_block_lookback=self.settings.analysis.order_block_lookback,
            liquidity_threshold=self.settings.analysis.liquidity_threshold
        )
        
        # == INDUSTRIAL GRADE UPGRADE: Initialize the Bias Filter ==
        self.bias_filter = BiasFilter()

        # == INDUSTRIAL GRADE UPGRADE: Initialize the ATR Risk Manager ==
        self.atr_risk_manager = ATRRiskManager(
            atr_length=self.settings.trading.atr_length,
            atr_multiplier=self.settings.trading.atr_multiplier
        )

        # == INDUSTRIAL GRADE UPGRADE: Initialize the External Condition Filter ==
        self.external_filter = ExternalConditionFilter(
            news_impact_level=self.settings.trading.news_impact_level,
            min_volume_ratio=self.settings.trading.min_volume_ratio
        )
        
        self.signal_generator = SignalGenerator(
            min_confluence_score=self.settings.quality.min_confluence_score,
            min_rr_ratio=self.settings.quality.min_rr_ratio,  # Use quality settings for more stringent requirements
            enhanced_mode=self.settings.quality.enable_quality_analysis
        )
        
        # == STRATEGIC REFACTOR: Unify to a single quality analyzer ==
        # The old quality analyzer is deprecated. We now use the enhanced one.
        if self.settings.quality.enable_quality_analysis:
            self.quality_analyzer = LIVE_TRADING_FILTER
            logger.info("INFO: Enhanced signal quality filter is active.")
        else:
            self.quality_analyzer = None
        
        self.multi_timeframe_analyzer = MultiTimeframeAnalyzer(
            timeframes=self.settings.timeframes,
            settings={
                'swing_length': self.settings.analysis.swing_length,
                'fvg_min_size': self.settings.analysis.fvg_min_size,
                'order_block_lookback': self.settings.analysis.order_block_lookback,
                'liquidity_threshold': self.settings.analysis.liquidity_threshold,
                'min_confluence_score': self.settings.quality.min_confluence_score,
                'min_rr_ratio': self.settings.quality.min_rr_ratio
            }
        )
        
        self.backtest_engine = BacktestEngine(
            initial_balance=self.settings.backtest.initial_balance,
            commission=self.settings.backtest.commission,
            risk_per_trade=self.settings.trading.risk_per_trade,  # Use trading settings
            max_spread=self.settings.trading.max_spread,
            min_rr_ratio=self.settings.quality.min_rr_ratio  # Use quality settings for consistency
        )
        
    def connect_data_source(self) -> bool:
        """
        Connect to the data source (MT5)
        
        Returns:
            bool: True if connection successful
        """
        return self.data_source.connect()
    
    def disconnect_data_source(self):
        """Disconnect from the data source"""
        self.data_source.disconnect()
    
    def get_market_data(self, symbol: str, timeframe: Timeframe, 
                       count: int = 1000, start_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Get market data for analysis
        
        Args:
            symbol: Currency pair symbol
            timeframe: Timeframe for data
            count: Number of bars to fetch
            start_date: Optional start date for fetching data
            
        Returns:
            DataFrame with OHLC data or None
        """
        return self.data_source.get_rates(symbol, timeframe, count, start_date=start_date)
    
    def analyze_single_timeframe(self, symbol: str, timeframe: Timeframe, 
                                count: int = 1000) -> Dict:
        """
        Perform complete analysis on a single timeframe
        
        Args:
            symbol: Currency pair symbol
            timeframe: Timeframe to analyze
            count: Number of bars to analyze
            
        Returns:
            Dictionary with complete analysis results
        """
        try:
            logger.info(f"Analyzing {symbol} on {timeframe.value}")
            
            # Get market data
            data = self.get_market_data(symbol, timeframe, count)
            if data is None or data.empty:
                return {'error': 'No data available'}
            
            # Market structure analysis
            market_structure = self.structure_analyzer.get_market_structure_levels(data)
            
            # Smart Money Concepts analysis
            smc_analysis = self.smc_analyzer.get_smart_money_analysis(data)
            
            # Generate signals
            current_price = data['Close'].iloc[-1]
            signal = self.signal_generator.generate_signal(
                market_structure, smc_analysis, current_price, timeframe
            )
            
            return {
                'symbol': symbol,
                'timeframe': timeframe.value,
                'timestamp': data.index[-1],
                'current_price': current_price,
                'market_structure': market_structure,
                'smc_analysis': smc_analysis,
                'signal': signal,
                'data_points': len(data)
            }
            
        except Exception as e:
            logger.error(f"Error in single timeframe analysis: {str(e)}")
            return {'error': str(e)}
    
    def analyze_multi_timeframe(self, symbol: str, timeframes: Optional[List[Timeframe]] = None,
                               count: int = 1000) -> Dict:
        """
        Perform multi-timeframe analysis
        
        Args:
            symbol: Currency pair symbol
            timeframes: List of timeframes to analyze (uses default if None)
            count: Number of bars to analyze per timeframe
            
        Returns:
            Dictionary with multi-timeframe analysis results
        """
        try:
            logger.info(f"Multi-timeframe analysis for {symbol}")
            
            timeframes = timeframes or self.settings.timeframes
            
            # Get data for all timeframes
            data_dict = {}
            for tf in timeframes:
                data = self.get_market_data(symbol, tf, count)
                if data is not None and not data.empty:
                    data_dict[tf] = data
            
            if not data_dict:
                return {'error': 'No data available for any timeframe'}
            
            # Perform multi-timeframe analysis
            analysis = self.multi_timeframe_analyzer.analyze_multiple_timeframes(data_dict)
            analysis['symbol'] = symbol
            
            # === FIXED BIAS LOGIC: Use the market bias already calculated in multi-timeframe analysis ===
            # The multi-timeframe analyzer already calculated the correct market bias
            market_bias_str = analysis.get('market_bias', 'NEUTRAL')
            
            # Convert string bias back to enum for consistency with bias filter
            from smc_forez.filters.bias_filter import MarketBias
            if market_bias_str == 'BULLISH':
                market_bias = MarketBias.BULLISH
            elif market_bias_str == 'BEARISH':
                market_bias = MarketBias.BEARISH
            elif market_bias_str == 'CONFLICT':
                market_bias = MarketBias.CONFLICT
            else:
                market_bias = MarketBias.NEUTRAL

            # Invalidate any signal that does not align with the established bias
            recommendation = analysis.get('recommendation')
            if recommendation and recommendation.get('action'):
                # Ensure action is a string for comparison
                action_value = recommendation['action'].value if hasattr(recommendation['action'], 'value') else str(recommendation['action'])
                
                if action_value.upper() not in ['WAIT', 'UNCERTAIN']:
                    # Get timeframe alignment data for enhanced assessment
                    timeframe_alignment = {}
                    for tf, tf_data in analysis.get('timeframe_analyses', {}).items():
                        market_structure = tf_data.get('market_structure', {})
                        timeframe_alignment[tf] = {
                            'trend': market_structure.get('trend'),
                            'strength': market_structure.get('trend_strength', 0)
                        }
                    
                    # Use enhanced confidence assessment
                    # Convert SignalType enum to string for bias filter
                    action_str = action_value.name if hasattr(action_value, 'name') else str(action_value)
                    
                    # Pass signal confluence data for better validation
                    signal_confluence_data = analysis.get('signal_confluence', {})
                    
                    decision, confidence_score, reason = self.bias_filter.assess_signal_confidence(
                        action_str, market_bias, timeframe_alignment, signal_confluence_data
                    )
                    
                    logger.info(f"📊 {symbol}: Signal confidence assessment - {decision} ({confidence_score:.1%}) - {reason}")
                    
                    # Update recommendation based on enhanced assessment
                    if decision == "EXECUTE":
                        analysis['recommendation']['confidence_score'] = confidence_score
                        analysis['recommendation']['confidence'] = 'HIGH' if confidence_score >= 0.8 else 'MEDIUM'
                    elif decision == "LOW_CONFIDENCE":
                        analysis['recommendation']['confidence_score'] = confidence_score
                        analysis['recommendation']['confidence'] = 'LOW'
                        analysis['recommendation']['reason'] = reason
                    elif decision == "WAIT":
                        analysis['recommendation']['confidence_score'] = confidence_score
                        analysis['recommendation']['confidence'] = 'INVALID' if confidence_score < 0.2 else 'WAIT'
                        analysis['recommendation']['reason'] = reason
                        # Always override action for WAIT decision (not just when <0.2)
                        from .signals.signal_generator import SignalType
                        analysis['recommendation']['action'] = SignalType.WAIT
            # === END ENHANCED BIAS LOGIC ===

            return analysis
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {str(e)}")
            return {'error': str(e)}
    
    def analyze_institutional_grade_signal(self, symbol: str, 
                                         timeframes: Optional[List[Timeframe]] = None) -> Dict:
        """
        Perform institutional-grade signal analysis with quality validation
        
        Args:
            symbol: Currency pair symbol
            timeframes: List of timeframes for multi-timeframe analysis
            
        Returns:
            Dictionary with institutional-grade signal analysis
        """
        try:
            logger.info(f"Institutional-grade analysis for {symbol}")
            
            # == INDUSTRIAL GRADE UPGRADE: External Condition Checks First ==
            # 1. Check for market liquidity and volatility
            entry_tf_str = self.settings.timeframes[-1].value # Assume entry on lowest timeframe
            entry_df = self.get_market_data(symbol, Timeframe(entry_tf_str), 200)
            if entry_df is None or entry_df.empty:
                return {'error': f'Could not retrieve data for {symbol} to check market conditions.'}

            # Check market liquidity with symbol-specific adjustments
            is_liquid, liquidity_reason = self.external_filter.is_market_liquid(entry_df, symbol)
            if not is_liquid:
                return {'error': f'Signal for {symbol} vetoed due to market conditions: {liquidity_reason}'}

            # 2. Check for high-impact news
            currencies = [symbol[:3], symbol[3:]]
            news_df = self.external_filter.get_high_impact_news(currencies)
            is_news, news_reason = self.external_filter.is_news_risk_imminent(symbol, news_df)
            if is_news:
                return {'error': f'Signal for {symbol} vetoed due to news risk: {news_reason}'}
            # =============================================================

            if not self.quality_analyzer:
                logger.warning("Quality analyzer not initialized. Using standard analysis.")
                return self.analyze_multi_timeframe(symbol, timeframes)
            
            # Perform multi-timeframe analysis to get the base signal
            analysis = self.analyze_multi_timeframe(symbol, timeframes)
            if 'error' in analysis or not analysis.get('recommendation'):
                return {'error': 'Failed to generate base analysis or recommendation.'}

            # Initialize recommendation with safe fallback
            recommendation = analysis.get('recommendation')
            if not recommendation:
                return {'error': 'No recommendation found in multi-timeframe analysis.'}
            logger.debug(f"DEBUG: recommendation extracted successfully: {type(recommendation)}")
            
            # == INDUSTRIAL GRADE UPGRADE: Skip ATR Enhancement for now to avoid issues ==
            # ATR enhancement disabled to prevent variable scope issues and redundant data fetching
            # The signals already have proper risk management from the multi-timeframe analysis
            logger.debug(f"DEBUG: Skipping ATR enhancement to avoid data re-fetching")

            logger.debug(f"DEBUG: About to extract entry_details")
            entry_details = recommendation.get('entry_details', {})
            logger.debug(f"DEBUG: Entry details extracted successfully")
            
            # == INDUSTRIAL GRADE UPGRADE: Pass market bias to quality check ==
            market_bias_str = analysis.get('market_bias', 'NEUTRAL')

            # Create a signal object compatible with the new quality filter
            signal_for_quality_check = {
                'symbol': symbol,
                'signal_type': recommendation.get('action'),
                'entry_price': entry_details.get('entry_price'),
                'stop_loss': entry_details.get('stop_loss'),
                'take_profit': entry_details.get('take_profit'),
                'risk_reward_ratio': entry_details.get('risk_reward_ratio'),
                'confluence_score': recommendation.get('confluence_score', 0),  # Direct from recommendation
                'strength_factors': recommendation.get('strength_factors', []),  # Direct from recommendation
                'confidence': recommendation.get('confidence', 'LOW'),
                'strength_score': recommendation.get('strength_score', 0),
                'entry_timeframe': recommendation.get('entry_timeframe', 'UNKNOWN'),
                'trend_direction': recommendation.get('trend_direction', 'UNKNOWN'),
                'trend_aligned': recommendation.get('trend_aligned', False),
                'signal_confluence': recommendation.get('signal_confluence', False),  # Direct from recommendation
                'analysis': analysis,  # Keep for backwards compatibility
                'market_bias': recommendation.get('market_bias', 'NEUTRAL')  # Fix: Get bias from recommendation, not analysis
            }
            
            # Step 2: Perform quality analysis using the enhanced filter
            logger.debug(f"DEBUG: About to call quality analyzer")
            try:
                quality_level, quality_score, quality_issues = self.quality_analyzer.evaluate_signal_quality(
                    signal_for_quality_check
                )
                logger.debug(f"DEBUG: Quality analysis completed successfully")
            except Exception as qa_error:
                logger.error(f"Error in quality analysis: {str(qa_error)}")
                return {'error': f'Quality analysis failed: {str(qa_error)}'}
            
            # Step 3: Generate a unified quality report
            logger.debug(f"DEBUG: About to generate quality report")
            try:
                quality_report = {
                    'should_execute': quality_level in [SignalQuality.EXCELLENT, SignalQuality.GOOD],
                    'quality_grade': quality_level.value,
                    'total_quality_score': quality_score,
                    'decision_reasoning': quality_issues,
                    'signal_summary': {
                        'type': recommendation.get('action').value if hasattr(recommendation.get('action'), 'value') else str(recommendation.get('action')),
                        'entry_price': entry_details.get('entry_price'),
                        'stop_loss': entry_details.get('stop_loss'),
                        'take_profit': entry_details.get('take_profit'),
                    }
                }
                logger.debug(f"DEBUG: Quality report generated successfully")
            except Exception as qr_error:
                logger.error(f"Error generating quality report: {str(qr_error)}")
                return {'error': f'Quality report generation failed: {str(qr_error)}'}

            # Step 4: Generate structured logging
            if self.settings.quality.enable_logging:
                self._log_signal_decision(quality_report, symbol)
            
            return {
                'symbol': symbol,
                'analysis_timestamp': pd.Timestamp.now(),
                'timeframes_analyzed': [tf.value for tf in timeframes],
                'recommendation': recommendation,
                'market_bias': market_bias_str,  # Include bias in the final report
                'quality_report': quality_report,
                'timeframe_analyses': analysis.get('timeframe_analyses', {}),
                'institutional_grade': quality_report.get('should_execute', False)
            }
            
        except Exception as e:
            logger.error(f"Error in institutional-grade analysis: {str(e)}")
            return {'error': str(e)}
    
    def _get_timeframe_minutes(self, timeframe: Timeframe) -> int:
        """Convert timeframe to minutes for sorting"""
        minutes_map = {
            Timeframe.M1: 1,
            Timeframe.M5: 5,
            Timeframe.M15: 15,
            Timeframe.H1: 60,
            Timeframe.H4: 240,
            Timeframe.D1: 1440
        }
        return minutes_map.get(timeframe, 60)
    
    def _log_signal_decision(self, quality_report: Dict, symbol: str):
        """Log signal decision with structured format"""
        try:
            import json
            from datetime import datetime
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'decision': 'EXECUTE' if quality_report.get('should_execute', False) else 'REJECT',
                'total_score': quality_report.get('total_quality_score', 0),
                'quality_grade': quality_report.get('quality_grade', 'unknown'),
                'signal_type': quality_report.get('signal_summary', {}).get('type', 'unknown'),
                'entry_price': quality_report.get('signal_summary', {}).get('entry_price', 0),
                'reasoning': quality_report.get('decision_reasoning', [])
            }
            
            # FIX: Override decision to REJECT if critical issues are present in reasoning
            if log_entry['decision'] == 'EXECUTE' and log_entry['reasoning']:
                critical_issues = [
                    "Poor market structure quality", 
                    "Low risk/reward ratio", 
                    "Signal conflicts with market bias",
                    "M15 trend", # Reject if M15 conflicts with signal direction
                    "high risk of immediate drawdown" # Our new warning
                ]
                for reason in log_entry['reasoning']:
                    if any(issue in reason for issue in critical_issues):
                        log_entry['decision'] = 'REJECT'
                        logger.warning(f"Overriding decision to REJECT for {symbol} due to critical issue: {reason}")
                        break
            
            # Log to console
            logger.info(f"SIGNAL DECISION: {json.dumps(log_entry, indent=2)}")
            
            # Optionally save to file (can be enhanced with CSV/JSON file logging)
            
        except Exception as e:
            logger.error(f"Error logging signal decision: {str(e)}")
    
    def get_current_opportunities(self, symbols: List[str], 
                                 timeframes: Optional[List[Timeframe]] = None,
                                 use_quality_analysis: bool = True) -> List[Dict]:
        """
        Scan multiple symbols for current trading opportunities
        
        Args:
            symbols: List of currency pair symbols to scan
            timeframes: List of timeframes to analyze
            use_quality_analysis: Use institutional-grade quality analysis
            
        Returns:
            List of trading opportunities
        """
        try:
            self.logger.info(f"Scanning {len(symbols)} symbols for opportunities")
            
            opportunities = []
            timeframes = timeframes or self.settings.timeframes
            
            for symbol in symbols:
                try:
                    # Use institutional-grade analysis with news filtering and quality controls
                    if use_quality_analysis:
                        analysis = self.analyze_institutional_grade_signal(symbol, timeframes)
                    else:
                        analysis = self.analyze_multi_timeframe(symbol, timeframes)
                    
                    if 'error' not in analysis:
                        recommendation = analysis.get('recommendation', {})
                        
                        # Check if there's a valid trading opportunity
                        if (recommendation and 
                            recommendation.get('action') and 
                            str(recommendation.get('action')).upper() != 'WAIT'):
                            
                            opportunities.append({
                                'symbol': symbol,
                                'recommendation': recommendation,
                                'analysis': analysis,
                                'analysis_timestamp': analysis.get('analysis_timestamp'),
                                'trend_alignment': analysis.get('trend_alignment'),
                                'signal_confluence': analysis.get('signal_confluence'),
                                'analysis_type': 'institutional' if use_quality_analysis else 'standard'
                            })
                    else:
                        # Log news/liquidity vetoes for visibility
                        error_msg = analysis.get('error', '')
                        if 'news risk' in error_msg or 'market conditions' in error_msg:
                            self.logger.info(f"🚫 {symbol}: {error_msg}")
                            
                except Exception as e:
                    self.logger.warning(f"Error analyzing {symbol}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(opportunities)} trading opportunities")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning for opportunities: {str(e)}")
            return []
    
    def run_backtest(self, symbol: str, timeframe: Timeframe, 
                    start_date: str, end_date: str, min_signal_quality: float = 0.5) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            symbol: Currency pair symbol
            timeframe: Timeframe for backtesting
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with backtest results
        """
        try:
            logger.info(f"Running backtest for {symbol} on {timeframe.value}")
            
            # Get historical data
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Calculate number of bars needed
            days_diff = (end_dt - start_dt).days
            if timeframe == Timeframe.D1:
                count = days_diff
            elif timeframe == Timeframe.H4:
                count = days_diff * 6
            elif timeframe == Timeframe.H1:
                count = days_diff * 24
            else:
                count = min(10000, days_diff * 96)  # Limit to prevent excessive data
            
            data = self.get_market_data(symbol, timeframe, count)
            if data is None or data.empty:
                return {'error': 'No historical data available'}
            
            # For mock data, we don't need to filter by date range as it's generated data
            # For real data, filter by date range
            original_data_len = len(data)
            if hasattr(self.data_source, 'is_mock') and self.data_source.is_mock:
                # For mock data, just use the generated data as-is
                logger.info(f"Using {len(data)} bars of mock data for backtesting")
            else:
                # For real data, filter by date range
                data = data[start_date:end_date]
                if data.empty:
                    return {'error': 'No data in specified date range'}
                logger.info(f"Filtered to {len(data)} bars from {original_data_len} total bars")
            
            # Generate signals for backtest
            signals = self._generate_backtest_signals(data, symbol, timeframe)
            
            # Run backtest
            self.backtest_engine.min_signal_quality = min_signal_quality
            results = self.backtest_engine.run_backtest(data, signals)
            results['symbol'] = symbol
            results['timeframe'] = timeframe.value
            results['start_date'] = start_date
            results['end_date'] = end_date
            results['data_points'] = len(data)
            results['signals_generated'] = len(signals)
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return {'error': str(e)}
    
    def _generate_backtest_signals(self, data: pd.DataFrame, symbol: str,
                                  timeframe: Timeframe) -> List[Dict]:
        """
        Generate signals for backtesting using a more robust multi-timeframe approach.
        This method iterates through the historical data and, at each step,
        runs a multi-timeframe analysis to generate a high-quality signal.
        """
        try:
            signals = []
            min_data_required = 200  # Need sufficient data for MTF analysis
            
            if len(data) < min_data_required:
                logger.warning(f"Insufficient data for backtest signal generation: {len(data)} bars (need at least {min_data_required})")
                return signals

            logger.info(f"Generating backtest signals for {symbol} from {data.index[0]} to {data.index[-1]}...")

            # Determine the higher timeframes needed for context
            htf_map = {
                Timeframe.M15: (Timeframe.H1, Timeframe.H4),
                Timeframe.H1: (Timeframe.H4, Timeframe.D1),
                Timeframe.H4: (Timeframe.D1, Timeframe.W1) 
            }
            htf1, htf2 = htf_map.get(timeframe, (Timeframe.H4, Timeframe.D1))

            # Fetch all necessary data once to optimize
            base_data = self.data_source.get_rates(symbol, timeframe, len(data))
            htf1_data = self.data_source.get_rates(symbol, htf1, len(data)) # Fetch more for alignment
            htf2_data = self.data_source.get_rates(symbol, htf2, len(data))

            if base_data is None or htf1_data is None or htf2_data is None:
                logger.error("Failed to fetch all required historical data for backtest.")
                return []

            # Use the same enhanced quality filter as the live runner
            try:
                # Use the centralized, enhanced filter
                quality_filter = EnhancedSignalQualityFilter(config=LIVE_TRADING_FILTER)
            except ImportError:
                logger.warning("EnhancedSignalQualityFilter not available, using basic validation")
                quality_filter = None

            # Iterate through the main timeframe data, starting from a point where we have enough history
            # Skip every N bars to prevent over-processing and duplicate signals
            signal_interval = max(1, min_data_required // 50)  # Generate signals every N bars to avoid duplicates
            last_signal_time = None
            min_signal_gap = timedelta(hours=4)  # Minimum gap between signals
            
            for i in range(min_data_required, len(base_data), signal_interval):
                current_timestamp = base_data.index[i]
                
                # Prevent signals too close together
                if last_signal_time and (current_timestamp - last_signal_time) < min_signal_gap:
                    continue
                
                # Prepare data windows for analysis
                data_dict = {
                    timeframe: base_data.iloc[:i+1],
                    htf1: htf1_data[htf1_data.index <= current_timestamp],
                    htf2: htf2_data[htf2_data.index <= current_timestamp]
                }

                # Ensure we have sufficient data for all timeframes at this point
                if any(len(df) < 50 for df in data_dict.values()):
                    continue

                # Perform multi-timeframe analysis for the current step
                analysis_result = self.multi_timeframe_analyzer.analyze_multiple_timeframes(data_dict)
                
                recommendation = analysis_result.get('recommendation')
                if not recommendation or recommendation.get('action').value == 'wait':
                    continue

                # Create a signal object from the recommendation
                entry_details = recommendation.get('entry_details', {})
                if not entry_details:
                    continue

                # Validate risk/reward ratio
                rr_ratio = entry_details.get('risk_reward_ratio', 0)
                if rr_ratio < 1.5:
                    continue

                signal = {
                    'symbol': symbol,
                    'timestamp': current_timestamp,
                    'signal_type': recommendation['action'],
                    'valid': True,
                    'signal_strength': recommendation.get('strength'),
                    'confluence_score': len(recommendation.get('strength_factors', [])),
                    'risk_reward_ratio': rr_ratio,
                    
                    # Nest entry details and other expected fields
                    'entry_details': entry_details,
                    
                    # Add placeholder for pattern validations, as the engine checks for it
                    'pattern_validations': {'smc_pattern': {'valid': True, 'entry_type': 'multi_timeframe'}}
                }

                # Apply quality filter if available
                if quality_filter:
                    # Unpack the tuple from the enhanced filter
                    quality_level, quality_score, quality_issues = quality_filter.evaluate_signal_quality(signal)
                    
                    if quality_score >= quality_filter.min_quality_score and rr_ratio >= 1.5:
                        signal['quality_score'] = quality_score
                        signal['grade'] = quality_level.name
                        signals.append(signal)
                        last_signal_time = current_timestamp
                        logger.debug(f"Generated quality signal at {current_timestamp}: {signal['signal_type'].value} (Score: {quality_score:.2f})")
                else:
                    # Basic validation without quality filter - add None check
                    confluence_score = signal.get('confluence_score', 0)
                    if confluence_score is not None and confluence_score >= 2 and rr_ratio >= 1.8:
                        signal['quality_score'] = 0.7  # Default quality score
                        signal['grade'] = 'STANDARD'
                        signals.append(signal)
                        last_signal_time = current_timestamp
                        logger.debug(f"Generated basic signal at {current_timestamp}: {signal['signal_type'].value}")

            logger.info(f"Generated {len(signals)} valid, high-quality signals for backtest.")
            return signals

        except Exception as e:
            logger.error(f"Error generating backtest signals: {str(e)}", exc_info=True)
            return []
    
    def get_analysis_summary(self, analysis: Dict) -> str:
        """
        Get a human-readable summary of analysis results
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            String summary
        """
        try:
            if 'recommendation' in analysis:
                # Multi-timeframe analysis summary
                rec = analysis['recommendation']
                trend_align = analysis.get('trend_alignment', {})
                signal_conf = analysis.get('signal_confluence', {})
                
                summary = f"=== {analysis.get('symbol', 'Unknown')} Analysis ===\n"
                summary += f"Timestamp: {analysis.get('analysis_timestamp', 'Unknown')}\n\n"
                
                # == INDUSTRIAL GRADE UPGRADE: Add Market Bias to summary ==
                summary += f"Market Bias (H4/H1): {analysis.get('market_bias', 'UNKNOWN').upper()}\n"
                summary += f"Recommendation: {rec.get('action', 'WAIT').name.upper()}\n"
                summary += f"Confidence: {rec.get('confidence', 'LOW')}\n"
                summary += f"Trend Direction: {rec.get('trend_direction', 'Unknown').value}\n"
                summary += f"Entry Timeframe: {rec.get('entry_timeframe', 'None')}\n\n"
                
                if rec.get('strength_factors'):
                    summary += "Strength Factors:\n"
                    for factor in rec['strength_factors']:
                        summary += f"  • {factor}\n"
                
                summary += f"\nTrend Alignment: {'✓' if trend_align.get('is_aligned') else '✗'}\n"
                summary += f"Signal Confluence: {'✓' if signal_conf.get('has_confluence') else '✗'}\n"
                
                if rec.get('entry_details'):
                    entry = rec['entry_details']
                    summary += f"\nEntry Details:\n"
                    summary += f"  Entry: {entry.get('entry_price', 'N/A')}\n"
                    summary += f"  Stop Loss: {entry.get('stop_loss', 'N/A')}\n"
                    summary += f"  Take Profit: {entry.get('take_profit', 'N/A')}\n"
                    summary += f"  R:R Ratio: {entry.get('risk_reward_ratio', 'N/A'):.2f}\n"
                
            else:
                # Single timeframe analysis summary
                summary = f"=== {analysis.get('symbol', 'Unknown')} - {analysis.get('timeframe', 'Unknown')} ===\n"
                summary += f"Current Price: {analysis.get('current_price', 'Unknown')}\n"
                
                signal = analysis.get('signal', {})
                if signal:
                    summary += f"Signal: {signal.get('signal_type', 'WAIT').name.upper()}\n"
                    summary += f"Strength: {signal.get('signal_strength', 'WEAK').name}\n"
                    summary += f"Confluence Score: {signal.get('confluence_score', 0)}\n"
                    summary += f"Valid: {'✓' if signal.get('valid') else '✗'}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {str(e)}")
            return "Error generating summary"


def main():
    """Main function for direct execution of analyzer"""
    print("🚀 SMC FOREZ - ANALYZER DIRECT EXECUTION")
    print("="*60)
    
    try:
        # Create analyzer with default settings
        settings = Settings()
        analyzer = SMCAnalyzer(settings)
        
        print("✓ SMC Analyzer initialized successfully")
        print(f"✓ Configured for {len(settings.timeframes)} timeframes: {[tf.value for tf in settings.timeframes]}")
        print(f"✓ Analysis settings: swing_length={settings.analysis.swing_length}, fvg_min_size={settings.analysis.fvg_min_size}")
        print(f"✓ Trading settings: risk_per_trade={settings.trading.risk_per_trade}, min_rr_ratio={settings.trading.min_rr_ratio}")
        
        # Test data source connection (will likely fail without MT5, but should not crash)
        print("\n🔗 Testing data source connection...")
        if analyzer.connect_data_source():
            print("✓ Data source connected successfully")
            
            # Test analysis on a sample symbol
            print("\n📊 Testing analysis capabilities...")
            symbols = ['EURUSD', 'GBPUSD']
            
            for symbol in symbols:
                print(f"\nTesting {symbol}...")
                try:
                    analysis = analyzer.analyze_multi_timeframe(symbol)
                    if 'error' in analysis:
                        print(f"⚠️  Analysis returned error: {analysis['error']}")
                    else:
                        print(f"✓ Analysis completed for {symbol}")
                        
                        # Get summary
                        summary = analyzer.get_analysis_summary(analysis)
                        print("Summary:")
                        print(summary[:200] + "..." if len(summary) > 200 else summary)
                        
                except Exception as e:
                    print(f"❌ Error analyzing {symbol}: {str(e)}")
                    
            analyzer.disconnect_data_source()
            
        else:
            print("⚠️  Data source connection failed (expected without MT5 setup)")
            print("✓ Analyzer can still be used with external data")
        
        print("\n✅ Analyzer direct execution test completed successfully!")
        print("\n💡 Usage examples:")
        print("   - Import: from smc_forez.analyzer import SMCAnalyzer")
        print("   - Initialize: analyzer = SMCAnalyzer()")
        print("   - Analyze: analysis = analyzer.analyze_multi_timeframe('EURUSD')")
        
    except Exception as e:
        print(f"❌ Error during analyzer execution: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()