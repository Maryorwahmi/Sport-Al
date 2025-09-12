"""
Backtesting engine for evaluating SMC Forex strategies on historical data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from ..signals.signal_generator import SignalType


logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: datetime
    exit_time: Optional[datetime]
    signal_type: SignalType
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    size: float
    pnl: Optional[float] = None
    pnl_pips: Optional[float] = None
    commission: float = 0.0
    status: str = "open"  # open, closed, stopped_out, target_hit
    exit_reason: str = ""


@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pips: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_win_pips: float = 0.0
    avg_loss_pips: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    recovery_factor: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    avg_trade_duration: Optional[timedelta] = None


class BacktestEngine:
    """Enhanced backtesting engine aligned with live SMC signal generation"""
    
    def __init__(self, initial_balance: float = 10000.0, commission: float = 0.00007,
                 risk_per_trade: float = 0.015, max_spread: float = 2.0, 
                 min_signal_quality: float = 0.70):
        """
        Initialize enhanced backtesting engine
        
        Args:
            initial_balance: Starting account balance
            commission: Commission per trade (in decimal, e.g., 0.00007 = 0.7 pips)
            risk_per_trade: Risk per trade as percentage of balance (ENHANCED to 1.5%)
            max_spread: Maximum spread to accept trades (in pips)
            min_signal_quality: Minimum signal quality score for execution (70%+)
        """
        self.initial_balance = initial_balance
        self.commission = commission
        self.risk_per_trade = risk_per_trade
        self.max_spread = max_spread
        self.min_signal_quality = min_signal_quality
        
        # Initialize tracking variables
        self.current_balance = initial_balance
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.open_trades: List[Trade] = []
        
        # Enhanced tracking for signal quality analysis
        self.signal_quality_stats = {
            'institutional_signals': 0,
            'professional_signals': 0, 
            'standard_signals': 0,
            'below_standard_signals': 0,
            'quality_wins': {},
            'quality_losses': {}
        }
        
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            
        Returns:
            Position size in lots
        """
        try:
            risk_amount = self.current_balance * self.risk_per_trade
            pip_value = 10  # For major pairs, 1 pip = $10 per standard lot
            
            # Calculate pip distance to stop loss
            pip_distance = abs(entry_price - stop_loss) * 10000
            
            if pip_distance <= 0:
                return 0.01  # Minimum position size
            
            # Calculate position size
            position_size = risk_amount / (pip_distance * pip_value)
            
            # Round to 2 decimal places and ensure minimum size
            position_size = max(0.01, round(position_size, 2))
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.01
    
    def enter_trade(self, timestamp: datetime, signal: Dict, current_data: Dict) -> Optional[Trade]:
        """
        Enhanced trade entry with signal quality validation
        
        Args:
            timestamp: Current timestamp
            signal: Enhanced signal dictionary with quality metrics
            current_data: Current market data (bid, ask, spread)
            
        Returns:
            Trade object if trade was entered, None otherwise
        """
        try:
            if not signal.get('valid', False):
                return None
            
            # Enhanced quality validation
            quality_score = signal.get('quality_score', 0.0)
            if quality_score < self.min_signal_quality:
                logger.debug(f"Signal quality {quality_score:.2f} below threshold {self.min_signal_quality}")
                return None
            
            signal_type = signal.get('signal_type', SignalType.WAIT)
            if signal_type == SignalType.WAIT:
                return None
            
            # Check spread
            spread = current_data.get('spread', 0)
            if spread > self.max_spread:
                logger.debug(f"Spread too wide: {spread} pips")
                return None
            
            # Enhanced validation: check for required confluence factors
            confluence_score = signal.get('confluence_score', 0)
            if confluence_score < 3:  # Minimum 3 confluence factors
                logger.debug(f"Insufficient confluence factors: {confluence_score}")
                return None
            
            # Enhanced validation: check pattern validation
            pattern_validations = signal.get('pattern_validations', {})
            valid_patterns = [p for p in pattern_validations.values() if p.get('valid', False)]
            if not valid_patterns:
                logger.debug("No valid patterns detected")
                return None
            
            # Get trade parameters from enhanced signal
            entry_details = signal.get('entry_details', {})
            entry_price = entry_details.get('entry_price', current_data.get('bid', 0))
            stop_loss = entry_details.get('stop_loss', 0)
            take_profit = entry_details.get('take_profit', 0)
            risk_reward_ratio = entry_details.get('risk_reward_ratio', 0)
            
            # Enhanced validation: ensure minimum RR ratio
            if risk_reward_ratio < 2.5:  # Enhanced minimum RR
                logger.debug(f"Risk/reward ratio {risk_reward_ratio:.2f} below minimum 2.5")
                return None
            
            if not all([entry_price, stop_loss, take_profit]):
                logger.warning("Missing trade parameters")
                return None
            
            # Calculate position size
            position_size = self.calculate_position_size(entry_price, stop_loss)
            
            # Track signal quality statistics
            signal_grade = signal.get('grade', 'STANDARD')
            self._update_signal_quality_stats(signal_grade)
            
            # Create enhanced trade
            trade = Trade(
                entry_time=timestamp,
                exit_time=None,
                signal_type=signal_type,
                entry_price=entry_price,
                exit_price=None,
                stop_loss=stop_loss,
                take_profit=take_profit,
                size=position_size,
                commission=self.commission * position_size
            )
            
            # Add enhanced trade metadata
            trade.signal_quality = quality_score
            trade.signal_grade = signal_grade
            trade.confluence_score = confluence_score
            trade.pattern_types = [p.get('entry_type', 'unknown') for p in valid_patterns]
            trade.entry_strategy = signal.get('entry_strategy', 'confluence_entry')
            
            self.trades.append(trade)
            self.open_trades.append(trade)
            
            logger.info(f"Entered {signal_type.value} trade at {entry_price} (Quality: {quality_score:.2f}, Size: {position_size})")
            return trade
            
        except Exception as e:
            logger.error(f"Error entering trade: {str(e)}")
            return None
    
    def _update_signal_quality_stats(self, signal_grade: str):
        """Update signal quality statistics"""
        grade_key = signal_grade.lower() + '_signals'
        if grade_key in self.signal_quality_stats:
            self.signal_quality_stats[grade_key] += 1
    
    def update_trades(self, timestamp: datetime, current_data: Dict):
        """
        Update open trades and check for exits
        
        Args:
            timestamp: Current timestamp
            current_data: Current market data
        """
        try:
            current_bid = current_data.get('bid', 0)
            current_ask = current_data.get('ask', 0)
            
            trades_to_close = []
            
            for trade in self.open_trades:
                if trade.signal_type == SignalType.BUY:
                    # For buy trades, use bid price for exit
                    current_price = current_bid
                    
                    # Check stop loss
                    if current_price <= trade.stop_loss:
                        trade.exit_price = trade.stop_loss
                        trade.exit_time = timestamp
                        trade.status = "stopped_out"
                        trade.exit_reason = "Stop loss hit"
                        trades_to_close.append(trade)
                    
                    # Check take profit
                    elif current_price >= trade.take_profit:
                        trade.exit_price = trade.take_profit
                        trade.exit_time = timestamp
                        trade.status = "target_hit"
                        trade.exit_reason = "Take profit hit"
                        trades_to_close.append(trade)
                
                else:  # SELL trade
                    # For sell trades, use ask price for exit
                    current_price = current_ask
                    
                    # Check stop loss
                    if current_price >= trade.stop_loss:
                        trade.exit_price = trade.stop_loss
                        trade.exit_time = timestamp
                        trade.status = "stopped_out"
                        trade.exit_reason = "Stop loss hit"
                        trades_to_close.append(trade)
                    
                    # Check take profit
                    elif current_price <= trade.take_profit:
                        trade.exit_price = trade.take_profit
                        trade.exit_time = timestamp
                        trade.status = "target_hit"
                        trade.exit_reason = "Take profit hit"
                        trades_to_close.append(trade)
            
            # Close trades and calculate P&L
            for trade in trades_to_close:
                self._close_trade(trade)
                self.open_trades.remove(trade)
                
        except Exception as e:
            logger.error(f"Error updating trades: {str(e)}")
    
    def _close_trade(self, trade: Trade):
        """
        Close a trade and calculate P&L
        
        Args:
            trade: Trade to close
        """
        try:
            if trade.signal_type == SignalType.BUY:
                # Buy trade: profit when exit > entry
                pnl = (trade.exit_price - trade.entry_price) * trade.size * 100000  # Convert to account currency
                pnl_pips = (trade.exit_price - trade.entry_price) * 10000
            else:
                # Sell trade: profit when exit < entry
                pnl = (trade.entry_price - trade.exit_price) * trade.size * 100000
                pnl_pips = (trade.entry_price - trade.exit_price) * 10000
            
            # Subtract commission
            pnl -= trade.commission * 100000  # Convert commission to account currency
            
            trade.pnl = pnl
            trade.pnl_pips = pnl_pips
            
            # Update balance
            self.current_balance += pnl
            
            # Update equity curve
            self.equity_curve.append({
                'timestamp': trade.exit_time,
                'balance': self.current_balance,
                'trade_pnl': pnl,
                'cumulative_pnl': self.current_balance - self.initial_balance
            })
            
            logger.info(f"Closed {trade.signal_type.value} trade: {pnl:.2f} ({pnl_pips:.1f} pips)")
            
        except Exception as e:
            logger.error(f"Error closing trade: {str(e)}")
    
    def run_backtest(self, data: pd.DataFrame, signals: List[Dict]) -> Dict:
        """
        Run complete backtest on historical data
        
        Args:
            data: Historical OHLC data with timestamps
            signals: List of signals with timestamps
            
        Returns:
            Dictionary with backtest results
        """
        try:
            logger.info("Starting backtest")
            
            # Reset state
            self.current_balance = self.initial_balance
            self.trades = []
            self.equity_curve = []
            self.open_trades = []
            
            # Create signal lookup for efficiency
            signal_lookup = {signal['timestamp']: signal for signal in signals}
            
            # Simulate trading
            for i, (timestamp, row) in enumerate(data.iterrows()):
                # Create current market data
                current_data = {
                    'bid': row['Close'],  # Simplified - use close as bid
                    'ask': row['Close'] + 0.00020,  # Add 2 pip spread
                    'spread': 2.0
                }
                
                # Check for new signals
                if timestamp in signal_lookup:
                    signal = signal_lookup[timestamp]
                    self.enter_trade(timestamp, signal, current_data)
                
                # Update existing trades
                self.update_trades(timestamp, current_data)
                
                # Update equity curve
                if i % 100 == 0:  # Update every 100 bars to avoid too much data
                    self.equity_curve.append({
                        'timestamp': timestamp,
                        'balance': self.current_balance,
                        'trade_pnl': 0,
                        'cumulative_pnl': self.current_balance - self.initial_balance
                    })
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics()
            
            # Prepare results
            results = {
                'performance_metrics': metrics,
                'trades': [self._trade_to_dict(trade) for trade in self.trades],
                'equity_curve': self.equity_curve,
                'final_balance': self.current_balance,
                'total_return': (self.current_balance - self.initial_balance) / self.initial_balance * 100
            }
            
            logger.info(f"Backtest completed. Final balance: {self.current_balance:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        try:
            closed_trades = [t for t in self.trades if t.pnl is not None]
            
            if not closed_trades:
                return PerformanceMetrics()
            
            # Basic metrics
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t.pnl > 0])
            losing_trades = len([t for t in closed_trades if t.pnl < 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # P&L metrics
            total_pnl = sum(t.pnl for t in closed_trades)
            total_pnl_pips = sum(t.pnl_pips for t in closed_trades)
            
            wins = [t.pnl for t in closed_trades if t.pnl > 0]
            losses = [t.pnl for t in closed_trades if t.pnl < 0]
            
            avg_win = np.mean(wins) if wins else 0
            avg_loss = abs(np.mean(losses)) if losses else 0
            
            wins_pips = [t.pnl_pips for t in closed_trades if t.pnl_pips > 0]
            losses_pips = [t.pnl_pips for t in closed_trades if t.pnl_pips < 0]
            
            avg_win_pips = np.mean(wins_pips) if wins_pips else 0
            avg_loss_pips = abs(np.mean(losses_pips)) if losses_pips else 0
            
            # Profit factor
            gross_profit = sum(wins) if wins else 0
            gross_loss = abs(sum(losses)) if losses else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Drawdown calculation
            max_drawdown, max_drawdown_pct = self._calculate_drawdown()
            
            # Additional metrics
            largest_win = max(wins) if wins else 0
            largest_loss = abs(min(losses)) if losses else 0
            
            # Consecutive wins/losses
            consecutive_wins, consecutive_losses = self._calculate_consecutive_trades()
            
            # Average trade duration
            trade_durations = []
            for trade in closed_trades:
                if trade.exit_time and trade.entry_time:
                    duration = trade.exit_time - trade.entry_time
                    trade_durations.append(duration)
            
            avg_trade_duration = np.mean(trade_durations) if trade_durations else None
            
            # Sharpe ratio (simplified)
            if len(self.equity_curve) > 1:
                returns = []
                for i in range(1, len(self.equity_curve)):
                    prev_balance = self.equity_curve[i-1]['balance']
                    curr_balance = self.equity_curve[i]['balance']
                    returns.append((curr_balance - prev_balance) / prev_balance)
                
                if returns:
                    return_std = np.std(returns)
                    avg_return = np.mean(returns)
                    sharpe_ratio = avg_return / return_std if return_std > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0
            
            # Recovery factor
            recovery_factor = total_pnl / max_drawdown if max_drawdown > 0 else 0
            
            # Enhanced quality-based performance metrics
            quality_metrics = self._calculate_quality_metrics(closed_trades)
            
            # Create enhanced performance metrics
            metrics = PerformanceMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                total_pnl_pips=total_pnl_pips,
                max_drawdown=max_drawdown,
                max_drawdown_pct=max_drawdown_pct,
                avg_win=avg_win,
                avg_loss=avg_loss,
                avg_win_pips=avg_win_pips,
                avg_loss_pips=avg_loss_pips,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                recovery_factor=recovery_factor,
                largest_win=largest_win,
                largest_loss=largest_loss,
                consecutive_wins=consecutive_wins,
                consecutive_losses=consecutive_losses,
                avg_trade_duration=avg_trade_duration
            )
            
            # Add quality metrics as additional attributes
            metrics.quality_breakdown = quality_metrics
            metrics.signal_quality_stats = self.signal_quality_stats
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return PerformanceMetrics()
    
    def _calculate_quality_metrics(self, closed_trades: List[Trade]) -> Dict:
        """Calculate performance metrics by signal quality grade"""
        quality_metrics = {}
        
        for grade in ['INSTITUTIONAL', 'PROFESSIONAL', 'STANDARD', 'BELOW_STANDARD']:
            grade_trades = [t for t in closed_trades if getattr(t, 'signal_grade', 'STANDARD') == grade]
            
            if grade_trades:
                grade_wins = [t for t in grade_trades if t.pnl > 0]
                grade_win_rate = len(grade_wins) / len(grade_trades)
                grade_total_pnl = sum(t.pnl for t in grade_trades)
                grade_avg_pnl = grade_total_pnl / len(grade_trades)
                
                quality_metrics[grade] = {
                    'trades': len(grade_trades),
                    'win_rate': grade_win_rate,
                    'total_pnl': grade_total_pnl,
                    'avg_pnl_per_trade': grade_avg_pnl,
                    'avg_quality_score': np.mean([getattr(t, 'signal_quality', 0.7) for t in grade_trades])
                }
        
        return quality_metrics
    
    def _calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        try:
            if not self.equity_curve:
                return 0.0, 0.0
            
            peak = self.initial_balance
            max_drawdown = 0.0
            max_drawdown_pct = 0.0
            
            for point in self.equity_curve:
                balance = point['balance']
                if balance > peak:
                    peak = balance
                
                drawdown = peak - balance
                drawdown_pct = drawdown / peak * 100 if peak > 0 else 0
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct
            
            return max_drawdown, max_drawdown_pct
            
        except Exception as e:
            logger.error(f"Error calculating drawdown: {str(e)}")
            return 0.0, 0.0
    
    def _calculate_consecutive_trades(self) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses"""
        try:
            closed_trades = [t for t in self.trades if t.pnl is not None]
            
            if not closed_trades:
                return 0, 0
            
            max_consecutive_wins = 0
            max_consecutive_losses = 0
            current_consecutive_wins = 0
            current_consecutive_losses = 0
            
            for trade in closed_trades:
                if trade.pnl > 0:
                    current_consecutive_wins += 1
                    current_consecutive_losses = 0
                    max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
                else:
                    current_consecutive_losses += 1
                    current_consecutive_wins = 0
                    max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
            
            return max_consecutive_wins, max_consecutive_losses
            
        except Exception as e:
            logger.error(f"Error calculating consecutive trades: {str(e)}")
            return 0, 0
    
    def _trade_to_dict(self, trade: Trade) -> Dict:
        """Convert Trade object to dictionary for serialization"""
        return {
            'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
            'signal_type': trade.signal_type.value,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'stop_loss': trade.stop_loss,
            'take_profit': trade.take_profit,
            'size': trade.size,
            'pnl': trade.pnl,
            'pnl_pips': trade.pnl_pips,
            'commission': trade.commission,
            'status': trade.status,
            'exit_reason': trade.exit_reason
        }
    
    def export_results(self, results: Dict, filename: str):
        """
        Export backtest results to file
        
        Args:
            results: Backtest results dictionary
            filename: Output filename (CSV or JSON)
        """
        try:
            if filename.endswith('.json'):
                # Convert performance metrics to dict for JSON serialization
                if 'performance_metrics' in results:
                    metrics = results['performance_metrics']
                    if hasattr(metrics, '__dict__'):
                        results['performance_metrics'] = {
                            k: str(v) if isinstance(v, timedelta) else v 
                            for k, v in metrics.__dict__.items()
                        }
                
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                    
            elif filename.endswith('.csv'):
                # Export trades to CSV
                trades_df = pd.DataFrame(results.get('trades', []))
                trades_df.to_csv(filename, index=False)
                
            logger.info(f"Results exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")