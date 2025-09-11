#!/usr/bin/env python3
"""
Enhanced Multi-Symbol Backtest Runner for SMC Forez
Supports multiple symbols with 30+ days of historical data and comprehensive result saving
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional
from pathlib import Path

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.backtesting import BacktestEngine, Trade, PerformanceMetrics
from smc_forez.signals.signal_generator import SignalType
from smc_forez.config.settings import Settings, Timeframe

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiSymbolBacktester:
    """Enhanced backtester that handles multiple symbols with comprehensive reporting"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.results_dir = Path("backtest_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def create_historical_data(self, symbol: str, days: int = 30, timeframe: str = "H1") -> pd.DataFrame:
        """
        Create realistic historical data for backtesting
        
        Args:
            symbol: Currency pair symbol
            days: Number of days of historical data
            timeframe: Timeframe for data generation
            
        Returns:
            DataFrame with OHLC data
        """
        logger.info(f"Creating {days} days of {timeframe} data for {symbol}")
        
        # Calculate number of bars based on timeframe
        if timeframe == "H1":
            bars_per_day = 24
        elif timeframe == "H4":
            bars_per_day = 6
        elif timeframe == "D1":
            bars_per_day = 1
        elif timeframe == "M15":
            bars_per_day = 96
        else:
            bars_per_day = 24  # Default to H1
            
        num_bars = days * bars_per_day
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        if timeframe == "H1":
            dates = pd.date_range(start=start_date, end=end_date, freq='H')[:num_bars]
        elif timeframe == "H4":
            dates = pd.date_range(start=start_date, end=end_date, freq='4H')[:num_bars]
        elif timeframe == "D1":
            dates = pd.date_range(start=start_date, end=end_date, freq='D')[:num_bars]
        elif timeframe == "M15":
            dates = pd.date_range(start=start_date, end=end_date, freq='15T')[:num_bars]
        else:
            dates = pd.date_range(start=start_date, end=end_date, freq='H')[:num_bars]
        
        # Set base price for different symbols
        base_prices = {
            "EURUSD": 1.1000, "GBPUSD": 1.2500, "USDJPY": 110.00, "USDCHF": 0.9200,
            "AUDUSD": 0.7500, "USDCAD": 1.2500, "NZDUSD": 0.6800, "EURJPY": 121.00,
            "EURGBP": 0.8800, "EURCHF": 1.0100, "EURAUD": 1.4700, "EURCAD": 1.3800,
            "EURNZD": 1.6200, "GBPJPY": 137.50, "GBPCHF": 1.1500, "GBPAUD": 1.6700,
            "GBPCAD": 1.5600, "GBPNZD": 1.8400, "AUDJPY": 82.50, "AUDCHF": 0.6900,
            "AUDCAD": 0.9400, "AUDNZD": 1.0700, "NZDJPY": 77.00, "NZDCHF": 0.6400,
            "NZDCAD": 0.8700, "CADJPY": 87.50, "CADCHF": 0.7400, "CHFJPY": 118.50
        }
        
        base_price = base_prices.get(symbol, 1.1000)
        
        # Generate realistic price movements
        np.random.seed(hash(symbol) % 2**32)  # Different seed for each symbol
        
        # Create price changes with trending and ranging behavior
        price_changes = np.random.normal(0, 0.0003, len(dates))  # Base volatility
        
        # Add trending behavior (some symbols trend more than others)
        trend_strength = np.random.uniform(-0.002, 0.002)
        trend = np.linspace(-trend_strength, trend_strength, len(dates))
        price_changes += trend
        
        # Add some volatility clustering
        volatility = np.random.uniform(0.8, 1.2, len(dates))
        price_changes *= volatility
        
        # Calculate prices
        prices = [base_price]
        for change in price_changes[1:]:
            new_price = prices[-1] + change
            # Keep within realistic bounds for each symbol
            if "JPY" in symbol:
                new_price = max(50.0, min(200.0, new_price))
            else:
                new_price = max(0.3000, min(2.0000, new_price))
            prices.append(new_price)
        
        # Create OHLC data
        data = []
        for i, price in enumerate(prices):
            # Create realistic OHLC bars
            spread = np.random.uniform(0.0001, 0.0005)  # Variable spread
            
            open_price = price + np.random.uniform(-spread, spread)
            close_price = price + np.random.uniform(-spread, spread)
            
            high_price = max(open_price, close_price) + np.random.uniform(0, spread * 2)
            low_price = min(open_price, close_price) - np.random.uniform(0, spread * 2)
            
            # Round to appropriate decimal places
            if "JPY" in symbol:
                decimals = 3
            else:
                decimals = 5
                
            data.append({
                'Open': round(open_price, decimals),
                'High': round(high_price, decimals), 
                'Low': round(low_price, decimals),
                'Close': round(close_price, decimals),
                'Volume': np.random.randint(100, 1000)
            })
        
        df = pd.DataFrame(data, index=dates)
        logger.info(f"✓ Created {len(df)} bars of historical data for {symbol}")
        return df
    
    def create_enhanced_signals(self, data: pd.DataFrame, symbol: str, num_signals: int = 10) -> List[Dict]:
        """
        Create enhanced trading signals with better quality filtering
        
        Args:
            data: Historical OHLC data
            symbol: Currency pair symbol
            num_signals: Number of signals to generate
            
        Returns:
            List of enhanced signals
        """
        logger.info(f"Creating {num_signals} enhanced signals for {symbol}")
        
        signals = []
        data_len = len(data)
        
        # Use different signal densities for different market conditions
        signal_positions = np.random.choice(
            range(100, data_len - 50), size=num_signals, replace=False
        )
        signal_positions.sort()
        
        for i, pos in enumerate(signal_positions):
            # Analyze local market conditions around this position
            window = data.iloc[max(0, pos-50):pos+1]
            
            current_price = data.iloc[pos]['Close']
            
            # Calculate technical indicators for signal quality
            sma_20 = window['Close'].rolling(20).mean().iloc[-1]
            sma_50 = window['Close'].rolling(50).mean().iloc[-1] if len(window) >= 50 else sma_20
            
            price_above_sma20 = current_price > sma_20
            sma_trend = sma_20 > sma_50
            
            # Calculate volatility
            returns = window['Close'].pct_change().dropna()
            volatility = returns.std()
            
            # Determine signal type based on technical analysis
            if price_above_sma20 and sma_trend:
                signal_type = SignalType.BUY
                confidence = 0.75 + np.random.uniform(0, 0.25)
            elif not price_above_sma20 and not sma_trend:
                signal_type = SignalType.SELL
                confidence = 0.75 + np.random.uniform(0, 0.25)
            else:
                # Mixed signals - lower confidence
                signal_type = np.random.choice([SignalType.BUY, SignalType.SELL])
                confidence = 0.5 + np.random.uniform(0, 0.3)
            
            # Only include high-quality signals (confidence > 0.7)
            if confidence < 0.7:
                continue
                
            # Calculate entry levels based on signal type
            if signal_type == SignalType.BUY:
                entry_price = current_price
                if "JPY" in symbol:
                    stop_loss = entry_price - np.random.uniform(0.2, 0.5)  # 20-50 pips
                    take_profit = entry_price + np.random.uniform(0.4, 1.0)  # 40-100 pips
                else:
                    stop_loss = entry_price - np.random.uniform(0.0020, 0.0050)  # 20-50 pips
                    take_profit = entry_price + np.random.uniform(0.0040, 0.0100)  # 40-100 pips
            else:  # SELL
                entry_price = current_price
                if "JPY" in symbol:
                    stop_loss = entry_price + np.random.uniform(0.2, 0.5)  # 20-50 pips
                    take_profit = entry_price - np.random.uniform(0.4, 1.0)  # 40-100 pips
                else:
                    stop_loss = entry_price + np.random.uniform(0.0020, 0.0050)  # 20-50 pips
                    take_profit = entry_price - np.random.uniform(0.0040, 0.0100)  # 40-100 pips
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Only include signals with good R:R ratio
            if rr_ratio < self.settings.trading.min_rr_ratio:
                continue
            
            signal = {
                'timestamp': data.index[pos],
                'symbol': symbol,
                'signal_type': signal_type,  # Keep as enum for compatibility
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': confidence,
                'risk_reward_ratio': rr_ratio,
                'volatility': volatility,
                'technical_score': confidence * rr_ratio,  # Combined quality score
                'valid': True
            }
            
            signals.append(signal)
        
        # Sort by quality score and return best signals
        signals.sort(key=lambda x: x['technical_score'], reverse=True)
        
        logger.info(f"✓ Created {len(signals)} high-quality signals for {symbol}")
        return signals[:num_signals]  # Return only requested number of best signals
    
    def run_multi_symbol_backtest(self, symbols: Optional[List[str]] = None, 
                                 days: int = 30, timeframe: str = "H1") -> Dict:
        """
        Run backtest across multiple symbols
        
        Args:
            symbols: List of symbols to backtest (defaults to major pairs)
            days: Days of historical data
            timeframe: Timeframe for backtesting
            
        Returns:
            Comprehensive backtest results
        """
        if symbols is None:
            symbols = self.settings.major_symbols
            
        logger.info(f"Starting multi-symbol backtest for {len(symbols)} symbols")
        logger.info(f"Symbols: {', '.join(symbols)}")
        
        all_results = {}
        summary_stats = {
            'total_symbols': len(symbols),
            'total_trades': 0,
            'total_return': 0.0,
            'winning_symbols': 0,
            'best_symbol': None,
            'worst_symbol': None,
            'best_return': float('-inf'),
            'worst_return': float('inf')
        }
        
        for symbol in symbols:
            logger.info(f"\n{'='*60}")
            logger.info(f"BACKTESTING {symbol}")
            logger.info(f"{'='*60}")
            
            try:
                # Create historical data
                data = self.create_historical_data(symbol, days, timeframe)
                
                # Generate enhanced signals
                signals = self.create_enhanced_signals(data, symbol, num_signals=15)
                
                if not signals:
                    logger.warning(f"No valid signals generated for {symbol}")
                    continue
                
                # Initialize backtest engine for this symbol
                engine = BacktestEngine(
                    initial_balance=self.settings.backtest.initial_balance,
                    commission=self.settings.backtest.commission,
                    max_spread=self.settings.trading.max_spread
                )
                
                # Run backtest
                results = engine.run_backtest(data, signals)
                
                if 'error' in results:
                    logger.error(f"Backtest failed for {symbol}: {results['error']}")
                    continue
                
                # Store results
                all_results[symbol] = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'days': days,
                    'data_points': len(data),
                    'signals_generated': len(signals),
                    'backtest_results': results,
                    'signal_details': signals
                }
                
                # Update summary statistics
                total_return = results.get('total_return', 0)
                summary_stats['total_trades'] += len(results.get('trades', []))
                summary_stats['total_return'] += total_return
                
                if total_return > 0:
                    summary_stats['winning_symbols'] += 1
                
                if total_return > summary_stats['best_return']:
                    summary_stats['best_return'] = total_return
                    summary_stats['best_symbol'] = symbol
                    
                if total_return < summary_stats['worst_return']:
                    summary_stats['worst_return'] = total_return
                    summary_stats['worst_symbol'] = symbol
                
                logger.info(f"✓ {symbol} backtest completed - Return: {total_return:.2f}%")
                
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {str(e)}")
                continue
        
        # Calculate average return
        if len(all_results) > 0:
            summary_stats['average_return'] = summary_stats['total_return'] / len(all_results)
        else:
            summary_stats['average_return'] = 0.0
        
        # Prepare final results
        final_results = {
            'backtest_config': {
                'symbols': symbols,
                'timeframe': timeframe,
                'days': days,
                'timestamp': datetime.now().isoformat(),
                'settings': {
                    'initial_balance': self.settings.backtest.initial_balance,
                    'commission': self.settings.backtest.commission,
                    'risk_per_trade': self.settings.trading.risk_per_trade,
                    'min_rr_ratio': self.settings.trading.min_rr_ratio
                }
            },
            'summary': summary_stats,
            'symbol_results': all_results
        }
        
        return final_results
    
    def save_results(self, results: Dict, filename: Optional[str] = None) -> str:
        """
        Save backtest results to JSON file
        
        Args:
            results: Backtest results dictionary
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            symbols_str = f"{len(results['backtest_config']['symbols'])}symbols"
            timeframe = results['backtest_config']['timeframe']
            filename = f"multi_backtest_{symbols_str}_{timeframe}_{timestamp}.json"
        
        filepath = self.results_dir / filename
        
        # Convert any non-serializable objects to strings
        serializable_results = self._make_serializable(results)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"✓ Results saved to: {filepath}")
        return str(filepath)
    
    def _make_serializable(self, obj):
        """Convert object to JSON serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Handle enum objects
            return obj.value
        else:
            return obj
    
    def print_summary(self, results: Dict):
        """Print a comprehensive summary of backtest results"""
        print(f"\n{'='*80}")
        print("MULTI-SYMBOL BACKTEST SUMMARY")
        print(f"{'='*80}")
        
        config = results['backtest_config']
        summary = results['summary']
        
        print(f"📊 Configuration:")
        print(f"   Symbols Tested: {config['symbols']}")
        print(f"   Timeframe: {config['timeframe']}")
        print(f"   Historical Days: {config['days']}")
        print(f"   Test Date: {config['timestamp'][:19]}")
        
        print(f"\n📈 Overall Performance:")
        print(f"   Total Symbols: {summary['total_symbols']}")
        print(f"   Successful Tests: {len(results['symbol_results'])}")
        print(f"   Total Trades: {summary['total_trades']}")
        print(f"   Winning Symbols: {summary['winning_symbols']}")
        print(f"   Average Return: {summary.get('average_return', 0):.2f}%")
        
        if summary['best_symbol']:
            print(f"   Best Performer: {summary['best_symbol']} ({summary['best_return']:.2f}%)")
        if summary['worst_symbol']:
            print(f"   Worst Performer: {summary['worst_symbol']} ({summary['worst_return']:.2f}%)")
        
        print(f"\n📋 Individual Symbol Results:")
        print(f"{'Symbol':<8} {'Return':<10} {'Trades':<8} {'Win Rate':<10} {'Profit Factor':<12}")
        print("-" * 60)
        
        for symbol, result in results['symbol_results'].items():
            backtest = result['backtest_results']
            metrics = backtest.get('performance_metrics', {})
            
            return_pct = backtest.get('total_return', 0)
            trade_count = len(backtest.get('trades', []))
            win_rate = getattr(metrics, 'win_rate', 0) * 100 if hasattr(metrics, 'win_rate') else 0
            profit_factor = getattr(metrics, 'profit_factor', 0) if hasattr(metrics, 'profit_factor') else 0
            
            print(f"{symbol:<8} {return_pct:>9.2f}% {trade_count:>7} {win_rate:>9.1f}% {profit_factor:>11.2f}")


def main():
    """Main function to run multi-symbol backtest"""
    print("🚀 SMC FOREZ - ENHANCED MULTI-SYMBOL BACKTEST RUNNER")
    print("="*80)
    
    # Initialize settings
    settings = Settings()
    
    # Create backtester
    backtester = MultiSymbolBacktester(settings)
    
    # Configuration
    config = {
        'symbols': settings.major_symbols,  # Use major symbols for backtesting
        'days': 45,  # 45 days of historical data
        'timeframe': 'H1',
    }
    
    print(f"📋 CONFIGURATION")
    print("-" * 40)
    print(f"   Symbols: {', '.join(config['symbols'])}")
    print(f"   Timeframe: {config['timeframe']}")
    print(f"   Historical Days: {config['days']}")
    print(f"   Initial Balance: ${settings.backtest.initial_balance:,.2f}")
    print(f"   Risk per Trade: {settings.trading.risk_per_trade * 100}%")
    print(f"   Min R:R Ratio: {settings.trading.min_rr_ratio}")
    print()
    
    # Run multi-symbol backtest
    print("⚡ RUNNING MULTI-SYMBOL BACKTEST")
    print("-" * 40)
    
    results = backtester.run_multi_symbol_backtest(
        symbols=config['symbols'],
        days=config['days'],
        timeframe=config['timeframe']
    )
    
    # Save results
    results_file = backtester.save_results(results)
    
    # Print summary
    backtester.print_summary(results)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Multi-symbol backtest completed successfully!")
    print("\n💡 NEXT STEPS:")
    print("   - Review individual symbol performance")
    print("   - Analyze signal quality and R:R ratios")
    print("   - Consider adjusting parameters for best performers")
    print("   - Run live signal generation with top symbols")


if __name__ == "__main__":
    main()