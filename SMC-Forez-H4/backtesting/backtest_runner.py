#!/usr/bin/env python3
"""
SMC-Forez-H4 Comprehensive Backtest Runner
Interactive command-line interface for running backtests with multiple configurations
"""
import sys
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

# Add parent directory to path to import smc_forez
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Timeframe, create_default_settings


class BacktestRunner:
    """Interactive backtest runner with predefined configurations"""
    
    CONFIGURATIONS = {
        '1': {
            'name': 'Quick Test (14 days)',
            'days': 14,
            'description': 'Fast 14-day backtest for quick validation'
        },
        '2': {
            'name': 'Standard Test (30 days)',
            'days': 30,
            'description': 'Standard 30-day backtest for general validation'
        },
        '3': {
            'name': 'Long Test (60 days)',
            'days': 60,
            'description': 'Comprehensive 60-day backtest for thorough analysis'
        },
        '4': {
            'name': 'Extended Test (90 days)',
            'days': 90,
            'description': 'Extended 90-day backtest for complete validation'
        },
        '5': {
            'name': 'Custom',
            'days': None,
            'description': 'Custom date range configuration'
        }
    }
    
    TIMEFRAMES = {
        '1': {'tf': Timeframe.M15, 'name': 'M15 (15 Minutes)'},
        '2': {'tf': Timeframe.H1, 'name': 'H1 (1 Hour)'},
        '3': {'tf': Timeframe.H4, 'name': 'H4 (4 Hours)'},
        '4': {'tf': Timeframe.D1, 'name': 'D1 (Daily)'}
    }
    
    SYMBOLS = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 
        'USDCAD', 'NZDUSD', 'USDCHF'
    ]
    
    def __init__(self):
        """Initialize backtest runner"""
        self.results_dir = Path(__file__).parent / 'results'
        self.results_dir.mkdir(exist_ok=True)
        
    def display_banner(self):
        """Display welcome banner"""
        print("=" * 70)
        print("  SMC-Forez-H4 Comprehensive Backtest System")
        print("  Multi-Timeframe Smart Money Concepts Backtesting")
        print("=" * 70)
        print()
    
    def select_configuration(self):
        """Interactive configuration selection"""
        print("📊 Select Backtest Configuration:")
        print("-" * 50)
        for key, config in self.CONFIGURATIONS.items():
            print(f"  [{key}] {config['name']}")
            print(f"      {config['description']}")
        print()
        
        choice = input("Enter your choice (1-5): ").strip()
        if choice not in self.CONFIGURATIONS:
            print("❌ Invalid choice. Using Standard Test (30 days)")
            choice = '2'
        
        return choice
    
    def select_symbol(self):
        """Interactive symbol selection"""
        print("\n💱 Select Currency Pair:")
        print("-" * 50)
        for i, symbol in enumerate(self.SYMBOLS, 1):
            print(f"  [{i}] {symbol}")
        print(f"  [{len(self.SYMBOLS) + 1}] Custom Symbol")
        print()
        
        choice = input(f"Enter your choice (1-{len(self.SYMBOLS) + 1}): ").strip()
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(self.SYMBOLS):
                return self.SYMBOLS[choice_idx]
            elif choice_idx == len(self.SYMBOLS):
                return input("Enter custom symbol: ").strip().upper()
        except ValueError:
            pass
        
        print("❌ Invalid choice. Using EURUSD")
        return 'EURUSD'
    
    def select_timeframe(self):
        """Interactive timeframe selection"""
        print("\n⏱️  Select Timeframe:")
        print("-" * 50)
        for key, tf_info in self.TIMEFRAMES.items():
            print(f"  [{key}] {tf_info['name']}")
        print()
        
        choice = input("Enter your choice (1-4): ").strip()
        if choice not in self.TIMEFRAMES:
            print("❌ Invalid choice. Using H1")
            choice = '2'
        
        return self.TIMEFRAMES[choice]['tf']
    
    def get_custom_dates(self):
        """Get custom date range from user"""
        print("\n📅 Custom Date Range:")
        print("-" * 50)
        print("Enter dates in YYYY-MM-DD format")
        
        while True:
            start_str = input("Start date (e.g., 2024-01-01): ").strip()
            end_str = input("End date (e.g., 2024-12-31): ").strip()
            
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                
                if start_date >= end_date:
                    print("❌ Start date must be before end date. Try again.")
                    continue
                
                return start_date, end_date
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD. Try again.")
    
    def get_signal_quality_threshold(self):
        """Get minimum signal quality threshold"""
        print("\n🎯 Signal Quality Threshold:")
        print("-" * 50)
        print("Enter minimum signal quality (0.0 - 1.0)")
        print("  0.50 = Standard quality")
        print("  0.70 = Professional quality (Recommended)")
        print("  0.85 = Institutional quality")
        print()
        
        while True:
            quality_str = input("Enter threshold (default 0.70): ").strip()
            if not quality_str:
                return 0.70
            
            try:
                quality = float(quality_str)
                if 0.0 <= quality <= 1.0:
                    return quality
                print("❌ Value must be between 0.0 and 1.0. Try again.")
            except ValueError:
                print("❌ Invalid number. Try again.")
    
    def run_backtest(self, symbol, timeframe, start_date, end_date, min_quality):
        """Execute the backtest"""
        print("\n🚀 Running Backtest...")
        print("=" * 70)
        print(f"Symbol:     {symbol}")
        print(f"Timeframe:  {timeframe.value}")
        print(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
        print(f"End Date:   {end_date.strftime('%Y-%m-%d')}")
        print(f"Min Quality: {min_quality:.2f}")
        print("=" * 70)
        print()
        
        # Create analyzer
        settings, _ = create_default_settings()
        analyzer = SMCAnalyzer(settings)
        
        # Run backtest
        try:
            results = analyzer.run_backtest(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                min_signal_quality=min_quality
            )
            
            if 'error' in results:
                print(f"❌ Error running backtest: {results['error']}")
                return None
            
            return results
        except Exception as e:
            print(f"❌ Backtest failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def display_results(self, results):
        """Display backtest results"""
        if not results or 'error' in results:
            return
        
        print("\n" + "=" * 70)
        print("  BACKTEST RESULTS")
        print("=" * 70)
        
        metrics = results.get('performance_metrics')
        if metrics:
            print(f"\n💰 Financial Performance:")
            print(f"   Total Return:        {results.get('total_return', 0):.2f}%")
            print(f"   Final Balance:       ${results.get('final_balance', 0):.2f}")
            print(f"   Max Drawdown:        {metrics.max_drawdown_pct:.2f}%")
            
            print(f"\n📊 Trade Statistics:")
            print(f"   Total Trades:        {metrics.total_trades}")
            print(f"   Winning Trades:      {metrics.winning_trades}")
            print(f"   Losing Trades:       {metrics.losing_trades}")
            print(f"   Win Rate:            {metrics.win_rate * 100:.1f}%")
            
            print(f"\n⚡ Performance Metrics:")
            print(f"   Profit Factor:       {metrics.profit_factor:.2f}")
            print(f"   Sharpe Ratio:        {metrics.sharpe_ratio:.2f}")
            print(f"   Recovery Factor:     {metrics.recovery_factor:.2f}")
            
            print(f"\n💎 Trade Quality:")
            print(f"   Average Win:         ${metrics.avg_win:.2f} ({metrics.avg_win_pips:.1f} pips)")
            print(f"   Average Loss:        ${metrics.avg_loss:.2f} ({metrics.avg_loss_pips:.1f} pips)")
            print(f"   Largest Win:         ${metrics.largest_win:.2f}")
            print(f"   Largest Loss:        ${metrics.largest_loss:.2f}")
            
            print(f"\n🔄 Consistency:")
            print(f"   Max Consecutive Wins:   {metrics.consecutive_wins}")
            print(f"   Max Consecutive Losses: {metrics.consecutive_losses}")
        
        print(f"\n📈 Data Summary:")
        print(f"   Data Points:         {results.get('data_points', 0)}")
        print(f"   Signals Generated:   {results.get('signals_generated', 0)}")
        
        print("\n" + "=" * 70)
    
    def save_results(self, results, symbol, timeframe, start_date, end_date):
        """Save results to JSON file"""
        if not results or 'error' in results:
            return None
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_{symbol}_{timeframe.value}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        # Add metadata
        results['metadata'] = {
            'symbol': symbol,
            'timeframe': timeframe.value,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat()
        }
        
        # Convert metrics to dict for JSON serialization
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            results['performance_metrics'] = {
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'win_rate': metrics.win_rate,
                'total_pnl': metrics.total_pnl,
                'total_pnl_pips': metrics.total_pnl_pips,
                'max_drawdown': metrics.max_drawdown,
                'max_drawdown_pct': metrics.max_drawdown_pct,
                'avg_win': metrics.avg_win,
                'avg_loss': metrics.avg_loss,
                'avg_win_pips': metrics.avg_win_pips,
                'avg_loss_pips': metrics.avg_loss_pips,
                'profit_factor': metrics.profit_factor,
                'sharpe_ratio': metrics.sharpe_ratio,
                'recovery_factor': metrics.recovery_factor,
                'largest_win': metrics.largest_win,
                'largest_loss': metrics.largest_loss,
                'consecutive_wins': metrics.consecutive_wins,
                'consecutive_losses': metrics.consecutive_losses
            }
        
        # Save to file
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n✅ Results saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"\n❌ Error saving results: {str(e)}")
            return None
    
    def run(self):
        """Main runner method"""
        self.display_banner()
        
        # Get configuration
        config_choice = self.select_configuration()
        config = self.CONFIGURATIONS[config_choice]
        
        # Get symbol and timeframe
        symbol = self.select_symbol()
        timeframe = self.select_timeframe()
        
        # Get date range
        if config['days']:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=config['days'])
        else:
            start_date, end_date = self.get_custom_dates()
        
        # Get quality threshold
        min_quality = self.get_signal_quality_threshold()
        
        # Run backtest
        results = self.run_backtest(symbol, timeframe, start_date, end_date, min_quality)
        
        # Display and save results
        if results:
            self.display_results(results)
            self.save_results(results, symbol, timeframe, start_date, end_date)
        
        print("\n✨ Backtest completed!")
        print()


def main():
    """Entry point"""
    try:
        runner = BacktestRunner()
        runner.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
