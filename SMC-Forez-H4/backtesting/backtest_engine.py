"""
Comprehensive Backtesting Engine for SMC Forez Trading System
Includes all requested metrics: Win Rate, Profit Factor, Expected Payoff, 
Max Drawdown, Sharpe Ratio, Recovery Factor, Average Trade Duration, Consecutive Losses
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Signal type enumeration"""
    BUY = "buy"
    SELL = "sell"
    WAIT = "wait"


@dataclass
class Trade:
    """Represents a single trade with complete information"""
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
    quality_score: float = 0.0
    confluence_score: int = 0
    timeframe: str = ""
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary for serialization"""
        result = asdict(self)
        result['signal_type'] = self.signal_type.value
        result['entry_time'] = self.entry_time.isoformat() if self.entry_time else None
        result['exit_time'] = self.exit_time.isoformat() if self.exit_time else None
        return result


@dataclass
class PerformanceMetrics:
    """Comprehensive trading performance metrics"""
    # Basic metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    
    # Win rate
    win_rate: float = 0.0
    
    # Profit metrics
    total_pnl: float = 0.0
    total_pnl_pips: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    
    # Profit factor
    profit_factor: float = 0.0
    
    # Expected payoff
    expected_payoff: float = 0.0
    expected_payoff_pips: float = 0.0
    
    # Drawdown
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    
    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    recovery_factor: float = 0.0
    
    # Win/Loss analysis
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_win_pips: float = 0.0
    avg_loss_pips: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Consecutive trades (stress test)
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Trade duration
    avg_trade_duration: Optional[timedelta] = None
    avg_winning_duration: Optional[timedelta] = None
    avg_losing_duration: Optional[timedelta] = None
    
    # Additional metrics
    avg_rr_ratio: float = 0.0
    total_commission: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for serialization"""
        result = asdict(self)
        # Convert timedelta to string
        if self.avg_trade_duration:
            result['avg_trade_duration'] = str(self.avg_trade_duration)
        if self.avg_winning_duration:
            result['avg_winning_duration'] = str(self.avg_winning_duration)
        if self.avg_losing_duration:
            result['avg_losing_duration'] = str(self.avg_losing_duration)
        return result


class BacktestEngine:
    """
    Comprehensive backtesting engine with multi-timeframe support
    and detailed performance analytics
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        commission: float = 0.00007,
        risk_per_trade: float = 0.015,
        max_spread: float = 2.0,
        min_signal_quality: float = 0.70
    ):
        """
        Initialize backtesting engine
        
        Args:
            initial_balance: Starting account balance
            commission: Commission per trade (in decimal, e.g., 0.00007 = 0.7 pips)
            risk_per_trade: Risk per trade as percentage of balance
            max_spread: Maximum spread to accept trades (in pips)
            min_signal_quality: Minimum signal quality score
        """
        self.initial_balance = initial_balance
        self.commission = commission
        self.risk_per_trade = risk_per_trade
        self.max_spread = max_spread
        self.min_signal_quality = min_signal_quality
        
        # State tracking
        self.current_balance = initial_balance
        self.peak_balance = initial_balance
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.open_trades: List[Trade] = []
        
        # Timeframe data cache (for multi-timeframe synchronous backtesting)
        self.timeframe_data_cache: Dict[str, pd.DataFrame] = {}
        
    def cache_timeframe_data(self, timeframe: str, data: pd.DataFrame):
        """
        Cache data for a specific timeframe
        
        Args:
            timeframe: Timeframe identifier (e.g., 'H4', 'H1', 'M15')
            data: OHLC data for the timeframe
        """
        self.timeframe_data_cache[timeframe] = data.copy()
        logger.info(f"Cached {len(data)} bars for {timeframe}")
        
    def align_timeframe_data(self, reference_timestamp: datetime) -> Dict[str, pd.DataFrame]:
        """
        Get aligned data for all cached timeframes up to reference timestamp
        
        Args:
            reference_timestamp: Reference timestamp for data alignment
            
        Returns:
            Dictionary of timeframe -> data up to reference timestamp
        """
        aligned_data = {}
        for timeframe, data in self.timeframe_data_cache.items():
            # Get data up to reference timestamp
            mask = data.index <= reference_timestamp
            aligned_data[timeframe] = data[mask].copy()
        return aligned_data
        
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
                return 0.01
            
            # Calculate position size
            position_size = risk_amount / (pip_distance * pip_value)
            
            # Round to 2 decimal places and ensure minimum size
            position_size = max(0.01, min(10.0, round(position_size, 2)))
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.01
    
    def enter_trade(
        self,
        timestamp: datetime,
        signal: Dict,
        current_data: Dict,
        timeframe: str = "H1"
    ) -> Optional[Trade]:
        """
        Enter a trade based on signal
        
        Args:
            timestamp: Current timestamp
            signal: Signal dictionary with entry details
            current_data: Current market data
            timeframe: Timeframe of the signal
            
        Returns:
            Trade object if trade was entered, None otherwise
        """
        try:
            if not signal.get('valid', False):
                return None
            
            # Validate signal quality
            quality_score = signal.get('quality_score', 0.0)
            if quality_score < self.min_signal_quality:
                logger.debug(f"Signal quality {quality_score:.2f} below threshold")
                return None
            
            # Extract signal details
            signal_type_str = signal.get('signal_type')
            if hasattr(signal_type_str, 'value'):
                signal_type = SignalType(signal_type_str.value)
            else:
                signal_type = SignalType(str(signal_type_str).lower())
            
            if signal_type == SignalType.WAIT:
                return None
            
            entry_details = signal.get('entry_details', {})
            if not entry_details:
                return None
            
            entry_price = entry_details.get('entry_price')
            stop_loss = entry_details.get('stop_loss')
            take_profit = entry_details.get('take_profit')
            
            if not all([entry_price, stop_loss, take_profit]):
                return None
            
            # Calculate position size
            position_size = self.calculate_position_size(entry_price, stop_loss)
            
            # Create trade
            trade = Trade(
                entry_time=timestamp,
                exit_time=None,
                signal_type=signal_type,
                entry_price=entry_price,
                exit_price=None,
                stop_loss=stop_loss,
                take_profit=take_profit,
                size=position_size,
                quality_score=quality_score,
                confluence_score=signal.get('confluence_score', 0),
                timeframe=timeframe,
                status="open"
            )
            
            self.open_trades.append(trade)
            logger.info(f"Entered {signal_type.value} trade at {entry_price}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error entering trade: {str(e)}")
            return None
    
    def update_trades(self, timestamp: datetime, current_data: Dict):
        """
        Update open trades based on current market data
        
        Args:
            timestamp: Current timestamp
            current_data: Current market data
        """
        closed_trades = []
        
        for trade in self.open_trades:
            # Check if trade should be closed
            should_close, exit_price, exit_reason = self._should_close_trade(
                trade, current_data
            )
            
            if should_close:
                # Close the trade
                trade.exit_time = timestamp
                trade.exit_price = exit_price
                trade.status = "closed"
                trade.exit_reason = exit_reason
                
                # Calculate P&L
                if trade.signal_type == SignalType.BUY:
                    trade.pnl = (exit_price - trade.entry_price) * trade.size * 100000
                    trade.pnl_pips = (exit_price - trade.entry_price) * 10000
                else:  # SELL
                    trade.pnl = (trade.entry_price - exit_price) * trade.size * 100000
                    trade.pnl_pips = (trade.entry_price - exit_price) * 10000
                
                # Apply commission
                commission_cost = self.commission * trade.size * 100000
                trade.pnl -= commission_cost
                trade.commission = commission_cost
                
                # Update balance
                self.current_balance += trade.pnl
                
                # Track peak balance for drawdown
                if self.current_balance > self.peak_balance:
                    self.peak_balance = self.current_balance
                
                # Record equity point
                self.equity_curve.append({
                    'timestamp': timestamp,
                    'balance': self.current_balance,
                    'trade_pnl': trade.pnl
                })
                
                # Add to closed trades list
                self.trades.append(trade)
                closed_trades.append(trade)
                
                logger.info(
                    f"Closed {trade.signal_type.value} trade: "
                    f"P&L = ${trade.pnl:.2f} ({trade.pnl_pips:.1f} pips) - {exit_reason}"
                )
        
        # Remove closed trades from open trades
        for trade in closed_trades:
            self.open_trades.remove(trade)
    
    def _should_close_trade(
        self,
        trade: Trade,
        current_data: Dict
    ) -> Tuple[bool, Optional[float], str]:
        """
        Check if trade should be closed
        
        Args:
            trade: Trade to check
            current_data: Current market data
            
        Returns:
            Tuple of (should_close, exit_price, exit_reason)
        """
        current_price = current_data.get('Close', current_data.get('close', 0))
        high = current_data.get('High', current_data.get('high', current_price))
        low = current_data.get('Low', current_data.get('low', current_price))
        
        if trade.signal_type == SignalType.BUY:
            # Check if stop loss hit
            if low <= trade.stop_loss:
                return True, trade.stop_loss, "stop_loss"
            # Check if take profit hit
            if high >= trade.take_profit:
                return True, trade.take_profit, "take_profit"
        else:  # SELL
            # Check if stop loss hit
            if high >= trade.stop_loss:
                return True, trade.stop_loss, "stop_loss"
            # Check if take profit hit
            if low <= trade.take_profit:
                return True, trade.take_profit, "take_profit"
        
        return False, None, ""
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        signals: List[Dict],
        symbol: str = "EURUSD"
    ) -> Dict:
        """
        Run complete backtest on historical data with multi-timeframe support
        
        Args:
            data: Historical OHLC data with timestamps
            signals: List of signals with timestamps
            symbol: Trading symbol
            
        Returns:
            Dictionary with comprehensive backtest results
        """
        try:
            logger.info(f"Starting backtest for {symbol}")
            
            # Reset state
            self.current_balance = self.initial_balance
            self.peak_balance = self.initial_balance
            self.trades = []
            self.equity_curve = []
            self.open_trades = []
            
            # Create signal lookup
            signal_lookup = {
                pd.Timestamp(signal['timestamp']): signal 
                for signal in signals if 'timestamp' in signal
            }
            
            # Iterate through historical data
            for timestamp, row in data.iterrows():
                # Convert timestamp if needed
                if not isinstance(timestamp, pd.Timestamp):
                    timestamp = pd.Timestamp(timestamp)
                
                # Create current market data
                current_data = {
                    'Open': row.get('Open', row.get('open', 0)),
                    'High': row.get('High', row.get('high', 0)),
                    'Low': row.get('Low', row.get('low', 0)),
                    'Close': row.get('Close', row.get('close', 0)),
                    'Volume': row.get('Volume', row.get('volume', 0))
                }
                
                # Update existing trades
                self.update_trades(timestamp, current_data)
                
                # Check for new signal
                if timestamp in signal_lookup:
                    signal = signal_lookup[timestamp]
                    self.enter_trade(timestamp, signal, current_data)
            
            # Close any remaining open trades
            if self.open_trades:
                final_timestamp = data.index[-1]
                final_price = data.iloc[-1]['Close']
                for trade in self.open_trades[:]:
                    trade.exit_time = final_timestamp
                    trade.exit_price = final_price
                    trade.status = "closed"
                    trade.exit_reason = "end_of_backtest"
                    
                    # Calculate P&L
                    if trade.signal_type == SignalType.BUY:
                        trade.pnl = (final_price - trade.entry_price) * trade.size * 100000
                        trade.pnl_pips = (final_price - trade.entry_price) * 10000
                    else:
                        trade.pnl = (trade.entry_price - final_price) * trade.size * 100000
                        trade.pnl_pips = (trade.entry_price - final_price) * 10000
                    
                    trade.pnl -= self.commission * trade.size * 100000
                    self.current_balance += trade.pnl
                    self.trades.append(trade)
                
                self.open_trades = []
            
            # Calculate performance metrics
            metrics = self._calculate_comprehensive_metrics()
            
            # Prepare results
            results = {
                'symbol': symbol,
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'metrics': metrics.to_dict(),
                'trades': [trade.to_dict() for trade in self.trades],
                'equity_curve': self.equity_curve,
                'total_signals': len(signals),
                'executed_trades': len(self.trades)
            }
            
            logger.info(f"Backtest completed: {len(self.trades)} trades executed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in backtest: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_comprehensive_metrics(self) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics including all requested metrics
        """
        metrics = PerformanceMetrics()
        
        if not self.trades:
            return metrics
        
        # Separate winning and losing trades
        wins = [t.pnl for t in self.trades if t.pnl and t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl and t.pnl < 0]
        breakeven = [t for t in self.trades if t.pnl == 0]
        
        wins_pips = [t.pnl_pips for t in self.trades if t.pnl_pips and t.pnl_pips > 0]
        losses_pips = [t.pnl_pips for t in self.trades if t.pnl_pips and t.pnl_pips < 0]
        
        # Basic counts
        metrics.total_trades = len(self.trades)
        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.breakeven_trades = len(breakeven)
        
        # Win rate
        metrics.win_rate = (len(wins) / len(self.trades) * 100) if self.trades else 0.0
        
        # P&L
        metrics.total_pnl = sum(t.pnl for t in self.trades if t.pnl)
        metrics.total_pnl_pips = sum(t.pnl_pips for t in self.trades if t.pnl_pips)
        metrics.gross_profit = sum(wins) if wins else 0.0
        metrics.gross_loss = abs(sum(losses)) if losses else 0.0
        
        # Profit factor
        metrics.profit_factor = (
            metrics.gross_profit / metrics.gross_loss 
            if metrics.gross_loss > 0 else 0.0
        )
        
        # Expected payoff (average P&L per trade)
        metrics.expected_payoff = metrics.total_pnl / len(self.trades) if self.trades else 0.0
        metrics.expected_payoff_pips = (
            metrics.total_pnl_pips / len(self.trades) if self.trades else 0.0
        )
        
        # Average wins and losses
        metrics.avg_win = np.mean(wins) if wins else 0.0
        metrics.avg_loss = abs(np.mean(losses)) if losses else 0.0
        metrics.avg_win_pips = np.mean(wins_pips) if wins_pips else 0.0
        metrics.avg_loss_pips = abs(np.mean(losses_pips)) if losses_pips else 0.0
        metrics.largest_win = max(wins) if wins else 0.0
        metrics.largest_loss = abs(min(losses)) if losses else 0.0
        
        # Drawdown calculation
        metrics.max_drawdown, metrics.max_drawdown_pct = self._calculate_drawdown()
        
        # Sharpe ratio
        metrics.sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Recovery factor
        metrics.recovery_factor = (
            metrics.total_pnl / metrics.max_drawdown 
            if metrics.max_drawdown > 0 else 0.0
        )
        
        # Consecutive wins/losses (stress test)
        consecutive_stats = self._calculate_consecutive_trades()
        metrics.max_consecutive_wins = consecutive_stats['max_wins']
        metrics.max_consecutive_losses = consecutive_stats['max_losses']
        
        # Trade duration
        duration_stats = self._calculate_trade_durations()
        metrics.avg_trade_duration = duration_stats['avg_duration']
        metrics.avg_winning_duration = duration_stats['avg_winning_duration']
        metrics.avg_losing_duration = duration_stats['avg_losing_duration']
        
        # Additional metrics
        rr_ratios = []
        for trade in self.trades:
            if trade.signal_type == SignalType.BUY:
                risk = trade.entry_price - trade.stop_loss
                if trade.exit_price:
                    reward = trade.exit_price - trade.entry_price
                    if risk > 0:
                        rr_ratios.append(reward / risk)
            else:
                risk = trade.stop_loss - trade.entry_price
                if trade.exit_price:
                    reward = trade.entry_price - trade.exit_price
                    if risk > 0:
                        rr_ratios.append(reward / risk)
        
        metrics.avg_rr_ratio = np.mean(rr_ratios) if rr_ratios else 0.0
        metrics.total_commission = sum(t.commission for t in self.trades if t.commission)
        
        return metrics
    
    def _calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown in absolute and percentage terms"""
        if not self.equity_curve:
            return 0.0, 0.0
        
        balances = [point['balance'] for point in self.equity_curve]
        peak = self.initial_balance
        max_dd = 0.0
        max_dd_pct = 0.0
        
        for balance in balances:
            if balance > peak:
                peak = balance
            
            drawdown = peak - balance
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0.0
            
            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_pct = drawdown_pct
        
        return max_dd, max_dd_pct
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio (risk-adjusted returns)"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_balance = self.equity_curve[i-1]['balance']
            curr_balance = self.equity_curve[i]['balance']
            if prev_balance > 0:
                returns.append((curr_balance - prev_balance) / prev_balance)
        
        if not returns:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe ratio (assuming daily returns)
        sharpe = (avg_return - risk_free_rate) / std_return * np.sqrt(252)
        
        return sharpe
    
    def _calculate_consecutive_trades(self) -> Dict:
        """Calculate maximum consecutive wins and losses"""
        if not self.trades:
            return {'max_wins': 0, 'max_losses': 0}
        
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        last_result = None
        
        for trade in self.trades:
            if not trade.pnl:
                continue
            
            is_win = trade.pnl > 0
            
            if last_result is None:
                current_streak = 1
            elif is_win == last_result:
                current_streak += 1
            else:
                current_streak = 1
            
            if is_win:
                max_win_streak = max(max_win_streak, current_streak)
            else:
                max_loss_streak = max(max_loss_streak, current_streak)
            
            last_result = is_win
        
        return {
            'max_wins': max_win_streak,
            'max_losses': max_loss_streak
        }
    
    def _calculate_trade_durations(self) -> Dict:
        """Calculate average trade durations"""
        all_durations = []
        winning_durations = []
        losing_durations = []
        
        for trade in self.trades:
            if trade.entry_time and trade.exit_time:
                duration = trade.exit_time - trade.entry_time
                all_durations.append(duration)
                
                if trade.pnl and trade.pnl > 0:
                    winning_durations.append(duration)
                elif trade.pnl and trade.pnl < 0:
                    losing_durations.append(duration)
        
        return {
            'avg_duration': (
                sum(all_durations, timedelta()) / len(all_durations)
                if all_durations else None
            ),
            'avg_winning_duration': (
                sum(winning_durations, timedelta()) / len(winning_durations)
                if winning_durations else None
            ),
            'avg_losing_duration': (
                sum(losing_durations, timedelta()) / len(losing_durations)
                if losing_durations else None
            )
        }
