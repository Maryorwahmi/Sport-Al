"""
Main Forex Analyzer Module
Coordinates all SMC and SMA components for comprehensive market analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta
import json

from .mt5_connector import MT5Connector, Timeframe
from .market_structure import MarketStructureAnalyzer, TrendDirection, StructureBreak
from .liquidity_zones import LiquidityZoneMapper, LiquidityZone, OrderBlock, FairValueGap
from .signal_generator import SignalGenerator, TradingSignal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Complete analysis result for a symbol/timeframe combination"""
    symbol: str
    timeframe: str
    timestamp: datetime
    current_price: float
    trend: TrendDirection
    swing_points: List
    structure_breaks: List[StructureBreak]
    order_blocks: List[OrderBlock]
    supply_demand_zones: List[LiquidityZone]
    fair_value_gaps: List[FairValueGap]
    trading_signals: List[TradingSignal]
    market_health: Dict
    analysis_summary: Dict


class ForexAnalyzer:
    """
    A-grade Forex Analyzer with Smart Money Concepts and Structural Market Analysis
    
    This class integrates all components to provide comprehensive forex market analysis
    including structure detection, liquidity mapping, and signal generation.
    """
    
    def __init__(self,
                 mt5_account: Optional[int] = None,
                 mt5_password: Optional[str] = None,
                 mt5_server: Optional[str] = None,
                 swing_strength: int = 3,
                 structure_confirmation: int = 2,
                 min_rr_ratio: float = 1.5,
                 min_confluence: int = 3):
        """
        Initialize the Forex Analyzer
        
        Args:
            mt5_account: MetaTrader 5 account number
            mt5_password: MetaTrader 5 password
            mt5_server: MetaTrader 5 server
            swing_strength: Strength for swing point detection
            structure_confirmation: Bars needed for structure confirmation
            min_rr_ratio: Minimum risk-reward ratio for signals
            min_confluence: Minimum confluence factors for signals
        """
        # Initialize MT5 connector
        self.mt5_connector = MT5Connector(mt5_account, mt5_password, mt5_server)
        
        # Initialize analysis components
        self.structure_analyzer = MarketStructureAnalyzer(swing_strength, structure_confirmation)
        self.liquidity_mapper = LiquidityZoneMapper()
        self.signal_generator = SignalGenerator(min_rr_ratio, min_confluence)
        
        # Analysis cache
        self.analysis_cache = {}
        self.last_update = {}
        
        # Default symbols to analyze
        self.default_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD']
        
        # Default timeframes for multi-timeframe analysis
        self.default_timeframes = [Timeframe.M15, Timeframe.H1, Timeframe.H4, Timeframe.D1]
        
        logger.info("Forex Analyzer initialized successfully")
    
    def connect_mt5(self) -> bool:
        """
        Connect to MetaTrader 5
        
        Returns:
            bool: True if connection successful
        """
        return self.mt5_connector.connect()
    
    def disconnect_mt5(self) -> None:
        """Disconnect from MetaTrader 5"""
        self.mt5_connector.disconnect()
    
    def analyze_symbol(self,
                      symbol: str,
                      timeframe: Timeframe,
                      bars: int = 1000,
                      cache_duration: int = 300) -> Optional[AnalysisResult]:
        """
        Perform complete analysis for a symbol on a specific timeframe
        
        Args:
            symbol: Currency pair symbol
            timeframe: Chart timeframe
            bars: Number of historical bars to analyze
            cache_duration: Cache duration in seconds
            
        Returns:
            AnalysisResult object or None if analysis failed
        """
        cache_key = f"{symbol}_{timeframe.name}"
        
        # Check cache
        if (cache_key in self.analysis_cache and 
            cache_key in self.last_update and
            (datetime.now() - self.last_update[cache_key]).seconds < cache_duration):
            logger.info(f"Returning cached analysis for {symbol} {timeframe.name}")
            return self.analysis_cache[cache_key]
        
        try:
            # Get historical data
            df = self.mt5_connector.get_historical_data(symbol, timeframe, bars)
            if df is None or len(df) < 50:
                logger.error(f"Insufficient data for {symbol} on {timeframe.name}")
                return None
            
            logger.info(f"Analyzing {symbol} on {timeframe.name} with {len(df)} bars")
            
            # Perform market structure analysis
            structure_analysis = self.structure_analyzer.analyze_structure(df)
            
            # Perform liquidity analysis
            liquidity_analysis = self.liquidity_mapper.analyze_liquidity(
                df, structure_analysis['swing_points']
            )
            
            # Generate trading signals
            trading_signals = self.signal_generator.generate_signals(
                df=df,
                trend=structure_analysis['current_trend'],
                structure_breaks=structure_analysis['structure_breaks'],
                order_blocks=liquidity_analysis['order_blocks'],
                supply_demand_zones=liquidity_analysis['supply_demand_zones'],
                fair_value_gaps=liquidity_analysis['fair_value_gaps'],
                symbol=symbol,
                timeframe=timeframe.name
            )
            
            # Calculate market health metrics
            market_health = self._calculate_market_health(
                df, structure_analysis, liquidity_analysis
            )
            
            # Create analysis summary
            analysis_summary = self._create_analysis_summary(
                structure_analysis, liquidity_analysis, trading_signals, market_health
            )
            
            # Create result object
            result = AnalysisResult(
                symbol=symbol,
                timeframe=timeframe.name,
                timestamp=datetime.now(),
                current_price=df['close'].iloc[-1],
                trend=structure_analysis['current_trend'],
                swing_points=structure_analysis['swing_points'],
                structure_breaks=structure_analysis['structure_breaks'],
                order_blocks=liquidity_analysis['order_blocks'],
                supply_demand_zones=liquidity_analysis['supply_demand_zones'],
                fair_value_gaps=liquidity_analysis['fair_value_gaps'],
                trading_signals=trading_signals,
                market_health=market_health,
                analysis_summary=analysis_summary
            )
            
            # Cache the result
            self.analysis_cache[cache_key] = result
            self.last_update[cache_key] = datetime.now()
            
            logger.info(f"Analysis completed for {symbol} {timeframe.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} on {timeframe.name}: {e}")
            return None
    
    def analyze_multiple_timeframes(self,
                                   symbol: str,
                                   timeframes: Optional[List[Timeframe]] = None,
                                   bars: int = 1000) -> Dict[str, AnalysisResult]:
        """
        Analyze a symbol across multiple timeframes
        
        Args:
            symbol: Currency pair symbol
            timeframes: List of timeframes to analyze
            bars: Number of bars per timeframe
            
        Returns:
            Dictionary mapping timeframe names to AnalysisResult objects
        """
        if timeframes is None:
            timeframes = self.default_timeframes
        
        results = {}
        
        for tf in timeframes:
            result = self.analyze_symbol(symbol, tf, bars)
            if result:
                results[tf.name] = result
            else:
                logger.warning(f"Failed to analyze {symbol} on {tf.name}")
        
        return results
    
    def scan_multiple_symbols(self,
                             symbols: Optional[List[str]] = None,
                             timeframe: Timeframe = Timeframe.H1,
                             bars: int = 500) -> Dict[str, AnalysisResult]:
        """
        Scan multiple symbols for trading opportunities
        
        Args:
            symbols: List of symbols to scan
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            Dictionary mapping symbols to AnalysisResult objects
        """
        if symbols is None:
            symbols = self.default_symbols
        
        results = {}
        
        for symbol in symbols:
            result = self.analyze_symbol(symbol, timeframe, bars)
            if result:
                results[symbol] = result
                logger.info(f"Scanned {symbol}: {len(result.trading_signals)} signals found")
            else:
                logger.warning(f"Failed to scan {symbol}")
        
        return results
    
    def get_live_signals(self,
                        symbols: Optional[List[str]] = None,
                        timeframes: Optional[List[Timeframe]] = None,
                        min_confidence: float = 0.6) -> List[TradingSignal]:
        """
        Get live trading signals across multiple symbols and timeframes
        
        Args:
            symbols: List of symbols to analyze
            timeframes: List of timeframes to analyze
            min_confidence: Minimum confidence level for signals
            
        Returns:
            List of high-confidence trading signals
        """
        if symbols is None:
            symbols = self.default_symbols
        if timeframes is None:
            timeframes = [Timeframe.H1, Timeframe.H4]
        
        all_signals = []
        
        for symbol in symbols:
            for timeframe in timeframes:
                result = self.analyze_symbol(symbol, timeframe)
                if result:
                    # Filter signals by confidence
                    high_confidence_signals = [
                        signal for signal in result.trading_signals
                        if signal.confidence >= min_confidence
                    ]
                    all_signals.extend(high_confidence_signals)
        
        # Sort by confidence
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return all_signals
    
    def _calculate_market_health(self,
                                df: pd.DataFrame,
                                structure_analysis: Dict,
                                liquidity_analysis: Dict) -> Dict:
        """
        Calculate market health metrics
        
        Args:
            df: Price data DataFrame
            structure_analysis: Market structure analysis results
            liquidity_analysis: Liquidity analysis results
            
        Returns:
            Dictionary with market health metrics
        """
        # Calculate volatility
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(len(returns))
        
        # Calculate trend strength
        trend_strength = 0.5  # Default neutral
        if structure_analysis['current_trend'] != TrendDirection.SIDEWAYS:
            recent_swings = structure_analysis['swing_points'][-10:] if structure_analysis['swing_points'] else []
            if len(recent_swings) >= 4:
                highs = [s for s in recent_swings if s.type == 'high']
                lows = [s for s in recent_swings if s.type == 'low']
                
                if len(highs) >= 2 and len(lows) >= 2:
                    if structure_analysis['current_trend'] == TrendDirection.BULLISH:
                        trend_strength = min(1.0, 0.5 + (highs[-1].price - highs[0].price) / highs[0].price * 10)
                    else:
                        trend_strength = min(1.0, 0.5 + (lows[0].price - lows[-1].price) / lows[0].price * 10)
        
        # Calculate liquidity health
        active_zones = len([z for z in liquidity_analysis['supply_demand_zones'] if z.is_active])
        unfilled_fvgs = len([f for f in liquidity_analysis['fair_value_gaps'] if not f.filled])
        liquidity_score = min(1.0, (active_zones + unfilled_fvgs) / 10)
        
        # Calculate structure clarity
        recent_breaks = len([b for b in structure_analysis['structure_breaks'][-5:]])
        structure_clarity = min(1.0, recent_breaks / 3)
        
        return {
            'volatility': volatility,
            'trend_strength': trend_strength,
            'liquidity_score': liquidity_score,
            'structure_clarity': structure_clarity,
            'overall_health': (trend_strength + liquidity_score + structure_clarity) / 3
        }
    
    def _create_analysis_summary(self,
                                structure_analysis: Dict,
                                liquidity_analysis: Dict,
                                trading_signals: List[TradingSignal],
                                market_health: Dict) -> Dict:
        """
        Create a summary of the analysis results
        
        Args:
            structure_analysis: Market structure analysis
            liquidity_analysis: Liquidity analysis
            trading_signals: Generated trading signals
            market_health: Market health metrics
            
        Returns:
            Analysis summary dictionary
        """
        return {
            'trend_direction': structure_analysis['current_trend'].value,
            'total_swings': len(structure_analysis['swing_points']),
            'recent_structure_breaks': len(structure_analysis['structure_breaks'][-5:]),
            'active_order_blocks': len(liquidity_analysis['order_blocks']),
            'active_zones': len([z for z in liquidity_analysis['supply_demand_zones'] if z.is_active]),
            'unfilled_fvgs': len([f for f in liquidity_analysis['fair_value_gaps'] if not f.filled]),
            'total_signals': len(trading_signals),
            'high_confidence_signals': len([s for s in trading_signals if s.confidence >= 0.7]),
            'avg_signal_confidence': np.mean([s.confidence for s in trading_signals]) if trading_signals else 0,
            'market_health_score': market_health['overall_health'],
            'recommendation': self._generate_recommendation(market_health, trading_signals)
        }
    
    def _generate_recommendation(self, market_health: Dict, signals: List[TradingSignal]) -> str:
        """
        Generate trading recommendation based on analysis
        
        Args:
            market_health: Market health metrics
            signals: Available trading signals
            
        Returns:
            Trading recommendation string
        """
        health_score = market_health['overall_health']
        high_conf_signals = len([s for s in signals if s.confidence >= 0.7])
        
        if health_score >= 0.7 and high_conf_signals >= 2:
            return "STRONG BUY/SELL OPPORTUNITIES"
        elif health_score >= 0.6 and high_conf_signals >= 1:
            return "MODERATE TRADING OPPORTUNITIES"
        elif health_score >= 0.4:
            return "WAIT FOR BETTER SETUPS"
        else:
            return "AVOID TRADING - UNCLEAR MARKET CONDITIONS"
    
    def export_analysis(self, result: AnalysisResult, format: str = 'json') -> str:
        """
        Export analysis result to different formats
        
        Args:
            result: AnalysisResult to export
            format: Export format ('json', 'summary')
            
        Returns:
            Formatted analysis string
        """
        if format == 'json':
            # Convert to JSON-serializable format
            export_data = {
                'symbol': result.symbol,
                'timeframe': result.timeframe,
                'timestamp': result.timestamp.isoformat(),
                'current_price': result.current_price,
                'trend': result.trend.value,
                'analysis_summary': result.analysis_summary,
                'market_health': result.market_health,
                'signals_count': len(result.trading_signals),
                'signals': [
                    {
                        'type': signal.signal_type.value,
                        'entry': signal.entry_price,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit,
                        'rr_ratio': signal.risk_reward_ratio,
                        'confidence': signal.confidence,
                        'confluence_factors': signal.confluence_factors
                    }
                    for signal in result.trading_signals
                ]
            }
            return json.dumps(export_data, indent=2)
        
        elif format == 'summary':
            summary = f"""
=== FOREX ANALYSIS SUMMARY ===
Symbol: {result.symbol}
Timeframe: {result.timeframe}
Analysis Time: {result.timestamp}
Current Price: {result.current_price:.5f}

MARKET STRUCTURE:
- Trend: {result.trend.value.upper()}
- Swing Points: {len(result.swing_points)}
- Structure Breaks: {len(result.structure_breaks)}

LIQUIDITY ANALYSIS:
- Order Blocks: {len(result.order_blocks)}
- Active Zones: {len([z for z in result.supply_demand_zones if z.is_active])}
- Unfilled FVGs: {len([f for f in result.fair_value_gaps if not f.filled])}

TRADING SIGNALS: {len(result.trading_signals)}
"""
            if result.trading_signals:
                summary += "\nTOP SIGNALS:\n"
                for i, signal in enumerate(result.trading_signals[:3], 1):
                    summary += f"{i}. {signal.signal_type.value.upper()}: {signal.entry_price:.5f} "
                    summary += f"(Confidence: {signal.confidence:.1%}, RR: {signal.risk_reward_ratio:.2f})\n"
            
            summary += f"\nMarket Health: {result.market_health['overall_health']:.1%}"
            summary += f"\nRecommendation: {result.analysis_summary['recommendation']}"
            
            return summary
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_market_overview(self) -> Dict:
        """
        Get overview of all monitored symbols
        
        Returns:
            Market overview dictionary
        """
        overview = {
            'timestamp': datetime.now(),
            'symbols_analyzed': 0,
            'total_signals': 0,
            'high_confidence_signals': 0,
            'market_conditions': {},
            'top_opportunities': []
        }
        
        all_signals = []
        
        for symbol in self.default_symbols:
            result = self.analyze_symbol(symbol, Timeframe.H1)
            if result:
                overview['symbols_analyzed'] += 1
                overview['total_signals'] += len(result.trading_signals)
                overview['high_confidence_signals'] += len([s for s in result.trading_signals if s.confidence >= 0.7])
                
                overview['market_conditions'][symbol] = {
                    'trend': result.trend.value,
                    'health': result.market_health['overall_health'],
                    'signals': len(result.trading_signals)
                }
                
                all_signals.extend(result.trading_signals)
        
        # Get top opportunities
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        overview['top_opportunities'] = [
            {
                'symbol': signal.symbol,
                'type': signal.signal_type.value,
                'confidence': signal.confidence,
                'entry': signal.entry_price,
                'rr_ratio': signal.risk_reward_ratio
            }
            for signal in all_signals[:5]
        ]
        
        return overview