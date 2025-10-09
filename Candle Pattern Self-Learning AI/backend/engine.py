"""
Main Trading Engine - Coordinates all components
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

try:
    # Try absolute imports first
    from config.settings import Settings, Timeframe
    from data.data_manager import DataManager
    from models.features import extract_candle_features, create_pattern_windows, calculate_technical_indicators
    from models.pattern_recognition import PatternRecognitionEngine
    from models.signal_generator import SignalGenerator, TradingSignal
    from smc.smc_engine import SMCEngine
    from risk.risk_manager import RiskManager
    from backtesting.backtest_engine import BacktestEngine
except ImportError:
    # Fall back to relative imports
    from .config.settings import Settings, Timeframe
    from .data.data_manager import DataManager
    from .models.features import extract_candle_features, create_pattern_windows, calculate_technical_indicators
    from .models.pattern_recognition import PatternRecognitionEngine
    from .models.signal_generator import SignalGenerator, TradingSignal
    from .smc.smc_engine import SMCEngine
    from .risk.risk_manager import RiskManager
    from .backtesting.backtest_engine import BacktestEngine


class TradingEngine:
    """Main trading engine coordinating all components"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        
        # Initialize components
        self.data_manager = DataManager(self.settings.data.data_path)
        self.pattern_engine = PatternRecognitionEngine(self.settings.ml.model_path)
        self.smc_engine = SMCEngine(self.settings.smc.__dict__)
        self.signal_generator = SignalGenerator(self.settings.confluence.__dict__)
        self.risk_manager = RiskManager(self.settings.risk.__dict__)
        self.backtest_engine = BacktestEngine(self.settings.backtest.__dict__)
        
        print("Trading Engine initialized")
    
    def train_pattern_model(self, symbol: str = "EURUSD", timeframe: str = "H1", n_bars: int = 5000):
        """Train the pattern recognition model"""
        print(f"Training pattern model on {symbol} {timeframe}...")
        
        # Fetch data
        df = self.data_manager.fetch_ohlcv(symbol, timeframe, n_bars=n_bars)
        
        # Extract features
        df_feat = extract_candle_features(df)
        
        # Create pattern windows
        windows = create_pattern_windows(df_feat, window_size=self.settings.ml.window_size)
        
        if len(windows) == 0:
            print("Error: Not enough data for training")
            return None
        
        # Create outcomes (next candle direction)
        outcomes = []
        for i in range(len(windows)):
            idx = i + self.settings.ml.window_size
            if idx < len(df):
                next_close = df['Close'].iloc[idx]
                current_close = df['Close'].iloc[idx - 1]
                if next_close > current_close * 1.0005:  # Up > 0.05%
                    outcomes.append(1)
                elif next_close < current_close * 0.9995:  # Down > 0.05%
                    outcomes.append(-1)
                else:
                    outcomes.append(0)
            else:
                outcomes.append(0)
        
        outcomes = np.array(outcomes[:len(windows)])
        
        # Train
        results = self.pattern_engine.train(
            windows, outcomes, 
            n_clusters=self.settings.ml.n_clusters,
            method='kmeans'
        )
        
        # Save model
        self.pattern_engine.save_model()
        
        print("Pattern model training complete")
        return results
    
    def analyze_symbol(self, symbol: str, timeframes: List[str] = None) -> Dict:
        """
        Analyze symbol across multiple timeframes
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes (default: H4, H1, M15)
            
        Returns:
            Multi-timeframe analysis
        """
        if timeframes is None:
            timeframes = ['H4', 'H1', 'M15']
        
        print(f"Analyzing {symbol} on timeframes: {timeframes}")
        
        mtf_data = {}
        
        for tf in timeframes:
            # Fetch data
            df = self.data_manager.get_or_fetch_data(symbol, tf, n_bars=1000)
            
            # Extract features
            df_feat = extract_candle_features(df)
            df_feat = calculate_technical_indicators(df_feat)
            
            # SMC analysis
            smc_analysis = self.smc_engine.get_smc_analysis(df)
            
            # Store analysis
            mtf_data[tf] = {
                'data': df,
                'features': df_feat.iloc[-1].to_dict(),
                'smc': smc_analysis,
                'structure': smc_analysis['structure']
            }
        
        return mtf_data
    
    def generate_signal(self, symbol: str, timeframes: List[str] = None) -> TradingSignal:
        """
        Generate trading signal for symbol
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes
            
        Returns:
            TradingSignal
        """
        # Multi-timeframe analysis
        mtf_data = self.analyze_symbol(symbol, timeframes)
        
        # Get current price
        df_m15 = mtf_data['M15']['data']
        current_price = df_m15['Close'].iloc[-1]
        
        # Pattern prediction
        if self.pattern_engine.is_trained:
            # Create window for M15
            df_feat = extract_candle_features(df_m15)
            windows = create_pattern_windows(df_feat, window_size=self.settings.ml.window_size)
            if len(windows) > 0:
                pattern_pred = self.pattern_engine.predict(windows[-1])
            else:
                pattern_pred = {'prediction': 0, 'confidence': 0.0}
        else:
            pattern_pred = {'prediction': 0, 'confidence': 0.0}
        
        # Generate signal
        signal = self.signal_generator.generate_signal(
            symbol, mtf_data, pattern_pred, current_price
        )
        
        return signal
    
    def scan_opportunities(self, symbols: List[str] = None) -> List[TradingSignal]:
        """
        Scan multiple symbols for trading opportunities
        
        Args:
            symbols: List of symbols to scan
            
        Returns:
            List of signals with action != 'IGNORE'
        """
        if symbols is None:
            symbols = self.settings.data.symbols
        
        print(f"Scanning {len(symbols)} symbols for opportunities...")
        
        opportunities = []
        for symbol in symbols:
            try:
                signal = self.generate_signal(symbol)
                if signal.action != 'IGNORE':
                    opportunities.append(signal)
                    print(f"  ✓ {symbol}: {signal.action} @ {signal.entry_price:.5f} "
                          f"(Confluence: {signal.confluence_score:.2%})")
            except Exception as e:
                print(f"  ✗ {symbol}: Error - {str(e)}")
        
        return opportunities
    
    def run_backtest(self, symbol: str, timeframe: str = "H1", 
                     n_bars: int = 1000) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for backtest
            n_bars: Number of bars to test
            
        Returns:
            Backtest results
        """
        print(f"Running backtest on {symbol} {timeframe}...")
        
        # Fetch data
        df = self.data_manager.fetch_ohlcv(symbol, timeframe, n_bars=n_bars)
        
        # Generate signals for each bar
        signals = []
        window_size = self.settings.ml.window_size
        
        for i in range(window_size + 100, len(df) - 50, 10):  # Every 10 bars
            # Create subset data
            df_subset = df.iloc[:i+1].copy()
            
            try:
                # Simulate multi-timeframe analysis with subset
                df_feat = extract_candle_features(df_subset)
                df_feat = calculate_technical_indicators(df_feat)
                
                smc_analysis = self.smc_engine.get_smc_analysis(df_subset)
                
                current_price = df_subset['Close'].iloc[-1]
                
                # Pattern prediction
                if self.pattern_engine.is_trained:
                    windows = create_pattern_windows(df_feat, window_size=window_size)
                    if len(windows) > 0:
                        pattern_pred = self.pattern_engine.predict(windows[-1])
                    else:
                        continue
                else:
                    continue
                
                # Create minimal mtf_data
                mtf_data = {
                    'H4': {'features': df_feat.iloc[-1].to_dict(), 'smc': smc_analysis, 'structure': smc_analysis['structure']},
                    'H1': {'features': df_feat.iloc[-1].to_dict(), 'smc': smc_analysis, 'structure': smc_analysis['structure']},
                    'M15': {'features': df_feat.iloc[-1].to_dict(), 'smc': smc_analysis, 'structure': smc_analysis['structure']}
                }
                
                signal = self.signal_generator.generate_signal(
                    symbol, mtf_data, pattern_pred, current_price
                )
                
                if signal.action in ['BUY', 'SELL']:
                    signals.append(signal.to_dict())
                
            except Exception as e:
                continue
        
        print(f"Generated {len(signals)} signals for backtest")
        
        # Run backtest
        results = self.backtest_engine.run_backtest(signals, df)
        
        # Print summary
        metrics = results['metrics']
        print(f"\nBacktest Results:")
        print(f"  Total Trades: {metrics.get('total_trades', 0)}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.1%}")
        print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"  Total Return: {metrics.get('total_return', 0):.1%}")
        print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            'pattern_engine_trained': self.pattern_engine.is_trained,
            'pattern_stats': self.pattern_engine.get_pattern_statistics() if self.pattern_engine.is_trained else {},
            'settings': {
                'window_size': self.settings.ml.window_size,
                'n_clusters': self.settings.ml.n_clusters,
                'min_rr_ratio': self.settings.risk.min_rr_ratio,
                'risk_per_trade': self.settings.risk.risk_per_trade
            }
        }
