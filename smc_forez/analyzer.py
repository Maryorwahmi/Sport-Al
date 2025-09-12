"""
Main SMC Forex Analyzer that coordinates all components
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from .config.settings import Settings, Timeframe
from .data_sources.mt5_source import MT5DataSource
from .market_structure.structure_analyzer import MarketStructureAnalyzer
from .smart_money.smc_analyzer import SmartMoneyAnalyzer
from .signals.signal_generator import SignalGenerator
from .utils.multi_timeframe import MultiTimeframeAnalyzer
from .backtesting.backtest_engine import BacktestEngine


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
        
        self.signal_generator = SignalGenerator(
            min_confluence_factors=2,
            min_rr_ratio=self.settings.trading.min_rr_ratio,
            enhanced_mode=self.settings.quality.enable_quality_analysis
        )
        
        # Initialize quality analyzer if enabled
        if self.settings.quality.enable_quality_analysis:
            from .signals.signal_quality_analyzer import SignalQualityAnalyzer
            quality_settings = {
                'min_institutional_score': self.settings.quality.min_institutional_score,
                'min_professional_score': self.settings.quality.min_professional_score,
                'min_execution_score': self.settings.quality.min_execution_score,
                'htf_weight': self.settings.quality.htf_weight,
                'mtf_weight': self.settings.quality.mtf_weight,
                'ltf_weight': self.settings.quality.ltf_weight,
                'trend_weight': self.settings.quality.trend_weight,
                'structure_weight': self.settings.quality.structure_weight,
                'orderblock_weight': self.settings.quality.orderblock_weight,
                'liquidity_weight': self.settings.quality.liquidity_weight,
                'fvg_weight': self.settings.quality.fvg_weight,
                'supply_demand_weight': self.settings.quality.supply_demand_weight,
                'min_rr_ratio': self.settings.quality.min_rr_ratio,
                'max_risk_percentage': self.settings.quality.max_risk_percentage,
                'allowed_sessions': self.settings.quality.allowed_sessions,
                'max_concurrent_trades': self.settings.quality.max_concurrent_trades,
                'duplicate_time_window': self.settings.quality.duplicate_time_window
            }
            self.quality_analyzer = SignalQualityAnalyzer(quality_settings)
        else:
            self.quality_analyzer = None
        
        self.multi_timeframe_analyzer = MultiTimeframeAnalyzer(
            timeframes=self.settings.timeframes,
            settings={
                'swing_length': self.settings.analysis.swing_length,
                'fvg_min_size': self.settings.analysis.fvg_min_size,
                'order_block_lookback': self.settings.analysis.order_block_lookback,
                'liquidity_threshold': self.settings.analysis.liquidity_threshold,
                'min_confluence_factors': 2,
                'min_rr_ratio': self.settings.trading.min_rr_ratio
            }
        )
        
        self.backtest_engine = BacktestEngine(
            initial_balance=self.settings.backtest.initial_balance,
            commission=self.settings.backtest.commission,
            risk_per_trade=self.settings.trading.risk_per_trade
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
                       count: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get market data for analysis
        
        Args:
            symbol: Currency pair symbol
            timeframe: Timeframe for data
            count: Number of bars to fetch
            
        Returns:
            DataFrame with OHLC data or None
        """
        return self.data_source.get_rates(symbol, timeframe, count)
    
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
            
            if not self.quality_analyzer:
                logger.warning("Quality analyzer not initialized. Using standard analysis.")
                return self.analyze_multi_timeframe(symbol, timeframes)
            
            timeframes = timeframes or self.settings.timeframes
            
            # Step 1: Perform multi-timeframe analysis
            timeframe_analyses = {}
            for tf in timeframes:
                single_analysis = self.analyze_single_timeframe(symbol, tf)
                if 'error' not in single_analysis:
                    timeframe_analyses[tf] = single_analysis
            
            if not timeframe_analyses:
                return {'error': 'No valid timeframe data available'}
            
            # Step 2: Get primary signal from lower timeframe
            primary_tf = min(timeframes, key=lambda tf: self._get_timeframe_minutes(tf))
            primary_signal = timeframe_analyses[primary_tf]['signal']
            
            # Step 3: Perform quality analysis
            quality_report = self.quality_analyzer.analyze_signal_quality(
                primary_signal, timeframe_analyses, symbol
            )
            
            # Step 4: Generate structured logging
            if self.settings.quality.enable_logging:
                self._log_signal_decision(quality_report, symbol)
            
            return {
                'symbol': symbol,
                'analysis_timestamp': pd.Timestamp.now(),
                'timeframes_analyzed': [tf.value for tf in timeframes],
                'primary_signal': primary_signal,
                'quality_report': quality_report,
                'timeframe_analyses': timeframe_analyses,
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
            logger.info(f"Scanning {len(symbols)} symbols for opportunities")
            
            opportunities = []
            timeframes = timeframes or self.settings.timeframes
            
            for symbol in symbols:
                try:
                    # Use institutional-grade analysis if quality analyzer is available
                    if use_quality_analysis and self.quality_analyzer:
                        analysis = self.analyze_institutional_grade_signal(symbol, timeframes)
                        
                        if 'error' not in analysis and analysis.get('institutional_grade', False):
                            quality_report = analysis.get('quality_report', {})
                            
                            opportunities.append({
                                'symbol': symbol,
                                'analysis_timestamp': analysis.get('analysis_timestamp'),
                                'quality_score': quality_report.get('total_quality_score', 0),
                                'quality_grade': quality_report.get('quality_grade', 'unknown'),
                                'signal_summary': quality_report.get('signal_summary', {}),
                                'should_execute': quality_report.get('should_execute', False),
                                'decision_reasoning': quality_report.get('decision_reasoning', []),
                                'analysis_type': 'institutional_grade'
                            })
                    else:
                        # Fallback to standard multi-timeframe analysis
                        analysis = self.analyze_multi_timeframe(symbol, timeframes)
                        
                        if 'error' not in analysis:
                            recommendation = analysis.get('recommendation', {})
                            
                            # Check if there's a valid trading opportunity
                            if (recommendation.get('confidence') in ['HIGH', 'MODERATE'] and
                                recommendation.get('action').value != 'wait'):
                                
                                opportunities.append({
                                    'symbol': symbol,
                                    'recommendation': recommendation,
                                    'analysis_timestamp': analysis.get('analysis_timestamp'),
                                    'trend_alignment': analysis.get('trend_alignment'),
                                    'signal_confluence': analysis.get('signal_confluence'),
                                    'analysis_type': 'standard'
                                })
                            
                except Exception as e:
                    logger.warning(f"Error analyzing {symbol}: {str(e)}")
                    continue
            
            # Sort opportunities by quality score (institutional) or confidence (standard)
            def sort_key(x):
                if x.get('analysis_type') == 'institutional_grade':
                    return (x.get('quality_score', 0), x.get('should_execute', False))
                else:
                    return (
                        x.get('recommendation', {}).get('strength_score', 0),
                        x.get('recommendation', {}).get('confidence') == 'HIGH'
                    )
            
            opportunities.sort(key=sort_key, reverse=True)
            
            logger.info(f"Found {len(opportunities)} trading opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning for opportunities: {str(e)}")
            return []
    
    def run_backtest(self, symbol: str, timeframe: Timeframe, 
                    start_date: str, end_date: str) -> Dict:
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
            
            # Filter data by date range
            data = data[start_date:end_date]
            if data.empty:
                return {'error': 'No data in specified date range'}
            
            # Generate signals for backtest
            signals = self._generate_backtest_signals(data, symbol, timeframe)
            
            # Run backtest
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
        Generate signals for backtesting
        
        Args:
            data: Historical OHLC data
            symbol: Currency pair symbol
            timeframe: Timeframe
            
        Returns:
            List of signals with timestamps
        """
        try:
            signals = []
            window_size = 200  # Analyze 200 bars at a time for efficiency
            
            for i in range(window_size, len(data)):
                # Get window of data for analysis
                window_data = data.iloc[i-window_size:i+1]
                
                # Perform analysis
                market_structure = self.structure_analyzer.get_market_structure_levels(window_data)
                smc_analysis = self.smc_analyzer.get_smart_money_analysis(window_data)
                
                # Generate signal
                current_price = window_data['Close'].iloc[-1]
                signal = self.signal_generator.generate_signal(
                    market_structure, smc_analysis, current_price
                )
                
                # Add timestamp and save valid signals
                if signal.get('valid', False):
                    signal['timestamp'] = data.index[i]
                    signals.append(signal)
            
            logger.info(f"Generated {len(signals)} valid signals for backtest")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating backtest signals: {str(e)}")
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
                
                summary += f"Recommendation: {rec.get('action', 'WAIT').value.upper()}\n"
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
                    summary += f"Signal: {signal.get('signal_type', 'WAIT').value.upper()}\n"
                    summary += f"Strength: {signal.get('signal_strength', 'WEAK').name}\n"
                    summary += f"Confluence Score: {signal.get('confluence_score', 0)}\n"
                    summary += f"Valid: {'✓' if signal.get('valid') else '✗'}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {str(e)}")
            return "Error generating summary"