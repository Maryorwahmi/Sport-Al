"""
Backtest Runner with Multiple Configuration Options
Supports: Quick Run (14 days), Standard Run (30 days), Long Run (60 days), Custom
"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.analyzer import SMCAnalyzer
from backtesting.backtest_engine import BacktestEngine

logger = logging.getLogger(__name__)


class RunType(Enum):
    """Backtest run types"""
    QUICK = "quick"           # 14 days, H1 timeframe
    STANDARD = "standard"     # 30 days, H1 timeframe
    LONG = "long"             # 60 days, H4 timeframe
    EXTENDED = "extended"     # 90 days, H4 timeframe
    CUSTOM = "custom"         # User-defined


@dataclass
class BacktestConfiguration:
    """Configuration for backtest runs"""
    name: str
    run_type: RunType
    symbol: str
    primary_timeframe: Timeframe
    multi_timeframes: List[Timeframe]
    days: int
    initial_balance: float = 10000.0
    risk_per_trade: float = 0.015
    min_rr_ratio: float = 2.0
    description: str = ""
    
    @classmethod
    def quick_run(cls, symbol: str = "EURUSD") -> 'BacktestConfiguration':
        """Create quick run configuration (14 days, fast testing)"""
        return cls(
            name="Quick Run",
            run_type=RunType.QUICK,
            symbol=symbol,
            primary_timeframe=Timeframe.H1,
            multi_timeframes=[Timeframe.H4, Timeframe.H1, Timeframe.M15],
            days=14,
            description="Fast 14-day test for quick validation"
        )
    
    @classmethod
    def standard_run(cls, symbol: str = "EURUSD") -> 'BacktestConfiguration':
        """Create standard run configuration (30 days, comprehensive)"""
        return cls(
            name="Standard Run",
            run_type=RunType.STANDARD,
            symbol=symbol,
            primary_timeframe=Timeframe.H1,
            multi_timeframes=[Timeframe.H4, Timeframe.H1, Timeframe.M15],
            days=30,
            description="Standard 30-day comprehensive test"
        )
    
    @classmethod
    def long_run(cls, symbol: str = "EURUSD") -> 'BacktestConfiguration':
        """Create long run configuration (60 days, thorough analysis)"""
        return cls(
            name="Long Run",
            run_type=RunType.LONG,
            symbol=symbol,
            primary_timeframe=Timeframe.H4,
            multi_timeframes=[Timeframe.D1, Timeframe.H4, Timeframe.H1],
            days=60,
            description="Thorough 60-day test with H4 focus"
        )
    
    @classmethod
    def extended_run(cls, symbol: str = "EURUSD") -> 'BacktestConfiguration':
        """Create extended run configuration (90 days, deep validation)"""
        return cls(
            name="Extended Run",
            run_type=RunType.EXTENDED,
            symbol=symbol,
            primary_timeframe=Timeframe.H4,
            multi_timeframes=[Timeframe.D1, Timeframe.H4, Timeframe.H1],
            days=90,
            description="Deep 90-day validation test"
        )
    
    @classmethod
    def custom_run(
        cls,
        symbol: str,
        timeframe: str,
        days: int,
        initial_balance: float = 10000.0
    ) -> 'BacktestConfiguration':
        """Create custom run configuration"""
        tf_enum = Timeframe(timeframe.upper())
        
        # Determine multi-timeframes based on primary timeframe
        if tf_enum == Timeframe.H1:
            multi_tfs = [Timeframe.H4, Timeframe.H1, Timeframe.M15]
        elif tf_enum == Timeframe.H4:
            multi_tfs = [Timeframe.D1, Timeframe.H4, Timeframe.H1]
        elif tf_enum == Timeframe.M15:
            multi_tfs = [Timeframe.H1, Timeframe.M15, Timeframe.M5]
        else:
            multi_tfs = [Timeframe.D1, Timeframe.H4]
        
        return cls(
            name="Custom Run",
            run_type=RunType.CUSTOM,
            symbol=symbol,
            primary_timeframe=tf_enum,
            multi_timeframes=multi_tfs,
            days=days,
            initial_balance=initial_balance,
            description=f"Custom {days}-day test on {timeframe}"
        )


class BacktestRunner:
    """
    Main backtest runner that orchestrates the entire backtesting process
    with multi-timeframe synchronous analysis
    """
    
    def __init__(self, config: BacktestConfiguration):
        """
        Initialize backtest runner
        
        Args:
            config: Backtest configuration
        """
        self.config = config
        self.settings = Settings()
        
        # Override settings with config
        self.settings.timeframes = config.multi_timeframes
        self.settings.trading.risk_per_trade = config.risk_per_trade
        
        # Initialize analyzer
        self.analyzer = SMCAnalyzer(self.settings)
        
        # Initialize backtest engine
        self.engine = BacktestEngine(
            initial_balance=config.initial_balance,
            risk_per_trade=config.risk_per_trade,
            min_signal_quality=0.70
        )
        
    def run(self) -> Dict:
        """
        Execute the backtest
        
        Returns:
            Dictionary with backtest results
        """
        try:
            print(f"\n{'='*80}")
            print(f"🚀 SMC FOREZ - {self.config.name.upper()}")
            print(f"{'='*80}")
            print(f"📊 Configuration:")
            print(f"   Symbol: {self.config.symbol}")
            print(f"   Primary Timeframe: {self.config.primary_timeframe.value}")
            print(f"   Multi-Timeframes: {[tf.value for tf in self.config.multi_timeframes]}")
            print(f"   Period: {self.config.days} days")
            print(f"   Initial Balance: ${self.config.initial_balance:,.2f}")
            print(f"   Risk per Trade: {self.config.risk_per_trade*100:.1f}%")
            print(f"   Description: {self.config.description}")
            print(f"{'='*80}\n")
            
            # Connect to data source
            data_connected = self.analyzer.connect_data_source()
            if not data_connected:
                print("⚠️  Using mock data (MT5 not available)")
            else:
                print("✓ Connected to data source\n")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config.days)
            
            print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print(f"\n⚡ Fetching multi-timeframe data...\n")
            
            # Fetch and cache data for all timeframes (multi-timeframe synchronous approach)
            timeframe_data = {}
            for tf in self.config.multi_timeframes:
                print(f"   Fetching {tf.value} data...")
                data = self.analyzer.get_market_data(
                    self.config.symbol,
                    tf,
                    count=2000  # Get enough data for analysis
                )
                
                if data is not None and not data.empty:
                    # Filter by date range
                    data = data[
                        (data.index >= start_date) & 
                        (data.index <= end_date)
                    ]
                    timeframe_data[tf.value] = data
                    self.engine.cache_timeframe_data(tf.value, data)
                    print(f"      ✓ Cached {len(data)} bars")
            
            if not timeframe_data:
                print("❌ No data available for backtesting")
                return {'error': 'No data available'}
            
            # Use primary timeframe data as the main iteration timeline
            primary_data = timeframe_data[self.config.primary_timeframe.value]
            
            print(f"\n⚡ Generating signals with real multi-timeframe analysis...\n")
            
            # Generate signals using multi-timeframe analysis
            signals = self._generate_multitimeframe_signals(
                timeframe_data,
                primary_data
            )
            
            print(f"   ✓ Generated {len(signals)} signals\n")
            
            # Run backtest
            print(f"⚡ Running backtest simulation...\n")
            
            results = self.engine.run_backtest(
                data=primary_data,
                signals=signals,
                symbol=self.config.symbol
            )
            
            # Add configuration to results
            results['config'] = {
                'name': self.config.name,
                'symbol': self.config.symbol,
                'timeframe': self.config.primary_timeframe.value,
                'multi_timeframes': [tf.value for tf in self.config.multi_timeframes],
                'days': self.config.days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
            # Disconnect from data source
            self.analyzer.disconnect_data_source()
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return {'error': str(e)}
    
    def _generate_multitimeframe_signals(
        self,
        timeframe_data: Dict[str, pd.DataFrame],
        primary_data: pd.DataFrame
    ) -> List[Dict]:
        """
        Generate signals using multi-timeframe synchronous analysis
        
        Args:
            timeframe_data: Dictionary of timeframe -> data
            primary_data: Primary timeframe data for iteration
            
        Returns:
            List of signals with timestamps
        """
        signals = []
        min_data_required = 100  # Minimum bars needed for analysis
        
        # Iterate through primary timeframe
        for i in range(min_data_required, len(primary_data)):
            try:
                current_timestamp = primary_data.index[i]
                current_price = primary_data.iloc[i]['Close']
                
                # Get aligned data for all timeframes up to current timestamp
                aligned_data = {}
                for tf_name, tf_data in timeframe_data.items():
                    mask = tf_data.index <= current_timestamp
                    aligned_data[Timeframe(tf_name)] = tf_data[mask].copy()
                
                # Skip if we don't have enough data
                if not all(len(data) >= min_data_required for data in aligned_data.values()):
                    continue
                
                # Perform multi-timeframe analysis
                analysis = self.analyzer.multi_timeframe_analyzer.analyze_multiple_timeframes(
                    aligned_data
                )
                
                # Extract signal
                recommendation = analysis.get('recommendation', {})
                if recommendation and recommendation.get('valid', False):
                    signal_data = {
                        'timestamp': current_timestamp,
                        'signal_type': recommendation.get('action'),
                        'entry_details': recommendation.get('entry_details', {}),
                        'valid': True,
                        'quality_score': recommendation.get('confidence_score', 0.75),
                        'confluence_score': recommendation.get('confluence_score', 0),
                        'timeframes': [tf.value for tf in self.config.multi_timeframes]
                    }
                    signals.append(signal_data)
                
            except Exception as e:
                logger.debug(f"Error generating signal at {current_timestamp}: {str(e)}")
                continue
        
        return signals
    
    def print_results(self, results: Dict):
        """
        Print formatted backtest results
        
        Args:
            results: Backtest results dictionary
        """
        if 'error' in results:
            print(f"\n❌ Error: {results['error']}\n")
            return
        
        metrics = results.get('metrics', {})
        
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST RESULTS")
        print(f"{'='*80}\n")
        
        # Account Summary
        print(f"💰 ACCOUNT SUMMARY:")
        print(f"   Initial Balance:    ${results['initial_balance']:,.2f}")
        print(f"   Final Balance:      ${results['final_balance']:,.2f}")
        net_pnl = results['final_balance'] - results['initial_balance']
        net_pnl_pct = (net_pnl / results['initial_balance'] * 100)
        print(f"   Net P&L:            ${net_pnl:,.2f} ({net_pnl_pct:+.2f}%)")
        print()
        
        # Trade Statistics
        print(f"📈 TRADE STATISTICS:")
        print(f"   Total Signals:      {results['total_signals']}")
        print(f"   Executed Trades:    {metrics['total_trades']}")
        print(f"   Winning Trades:     {metrics['winning_trades']}")
        print(f"   Losing Trades:      {metrics['losing_trades']}")
        print(f"   Breakeven Trades:   {metrics['breakeven_trades']}")
        print()
        
        # Performance Metrics
        print(f"🎯 PERFORMANCE METRICS:")
        print(f"   Win Rate:           {metrics['win_rate']:.2f}%")
        print(f"   Profit Factor:      {metrics['profit_factor']:.2f}")
        print(f"   Expected Payoff:    ${metrics['expected_payoff']:.2f} ({metrics['expected_payoff_pips']:.1f} pips)")
        print()
        
        # Risk Metrics
        print(f"⚠️  RISK METRICS:")
        print(f"   Max Drawdown:       ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_pct']:.2f}%)")
        print(f"   Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print(f"   Recovery Factor:    {metrics['recovery_factor']:.2f}")
        print()
        
        # Win/Loss Analysis
        print(f"📊 WIN/LOSS ANALYSIS:")
        print(f"   Average Win:        ${metrics['avg_win']:.2f} ({metrics['avg_win_pips']:.1f} pips)")
        print(f"   Average Loss:       ${metrics['avg_loss']:.2f} ({metrics['avg_loss_pips']:.1f} pips)")
        print(f"   Largest Win:        ${metrics['largest_win']:.2f}")
        print(f"   Largest Loss:       ${metrics['largest_loss']:.2f}")
        print(f"   Avg R:R Ratio:      {metrics['avg_rr_ratio']:.2f}")
        print()
        
        # Stress Test (Consecutive Losses)
        print(f"🔥 STRESS TEST:")
        print(f"   Max Consecutive Wins:    {metrics['max_consecutive_wins']}")
        print(f"   Max Consecutive Losses:  {metrics['max_consecutive_losses']}")
        print()
        
        # Trade Duration
        if metrics.get('avg_trade_duration'):
            print(f"⏱️  TRADE DURATION:")
            print(f"   Average Duration:        {metrics['avg_trade_duration']}")
            if metrics.get('avg_winning_duration'):
                print(f"   Avg Winning Duration:    {metrics['avg_winning_duration']}")
            if metrics.get('avg_losing_duration'):
                print(f"   Avg Losing Duration:     {metrics['avg_losing_duration']}")
            print()
        
        # Multi-Timeframe Robustness
        print(f"🎯 MULTI-TIMEFRAME ROBUSTNESS:")
        config = results.get('config', {})
        print(f"   Timeframes Used:    {', '.join(config.get('multi_timeframes', []))}")
        print(f"   Analysis Method:    Synchronous multi-timeframe with cached data")
        print(f"   Alignment:          All timeframes aligned to same timestamps")
        print()
        
        print(f"{'='*80}\n")
    
    def export_results(self, results: Dict, filename: Optional[str] = None):
        """
        Export results to JSON file
        
        Args:
            results: Backtest results
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_{self.config.symbol}_{self.config.primary_timeframe.value}_{timestamp}.json"
        
        output_path = Path(__file__).parent / filename
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📁 Results exported to: {output_path}\n")


def interactive_selection() -> BacktestConfiguration:
    """
    Interactive configuration selection
    
    Returns:
        Selected backtest configuration
    """
    print(f"\n{'='*80}")
    print(f"🚀 SMC FOREZ - BACKTEST CONFIGURATION")
    print(f"{'='*80}\n")
    
    print("Available configurations:")
    print("  1. Quick Run      - 14 days, H1 timeframe (fast validation)")
    print("  2. Standard Run   - 30 days, H1 timeframe (comprehensive)")
    print("  3. Long Run       - 60 days, H4 timeframe (thorough)")
    print("  4. Extended Run   - 90 days, H4 timeframe (deep validation)")
    print("  5. Custom Run     - User-defined parameters")
    print()
    
    choice = input("Select configuration (1-5) [default: 2]: ").strip() or "2"
    
    symbol = input("Enter symbol (default: EURUSD): ").strip().upper() or "EURUSD"
    
    if choice == "1":
        return BacktestConfiguration.quick_run(symbol)
    elif choice == "2":
        return BacktestConfiguration.standard_run(symbol)
    elif choice == "3":
        return BacktestConfiguration.long_run(symbol)
    elif choice == "4":
        return BacktestConfiguration.extended_run(symbol)
    elif choice == "5":
        timeframe = input("Enter timeframe (M15/H1/H4/D1) [default: H1]: ").strip().upper() or "H1"
        days = int(input("Enter days to backtest [default: 30]: ").strip() or "30")
        balance = float(input("Enter initial balance [default: 10000]: ").strip() or "10000")
        return BacktestConfiguration.custom_run(symbol, timeframe, days, balance)
    else:
        print("Invalid choice, using Standard Run")
        return BacktestConfiguration.standard_run(symbol)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Interactive selection
    config = interactive_selection()
    
    # Create runner and execute
    runner = BacktestRunner(config)
    results = runner.run()
    
    # Print results
    runner.print_results(results)
    
    # Export results
    runner.export_results(results)
