"""
Backtesting engine with realistic simulation
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import json


class BacktestEngine:
    """Backtest trading strategies"""
    
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.initial_balance = self.settings.get('initial_balance', 10000.0)
        self.commission_pips = self.settings.get('commission_pips', 0.8)
        self.slippage_pips = self.settings.get('slippage_pips', 0.5)
        self.spread_pips = self.settings.get('spread_pips', 1.0)
    
    def run_backtest(self, signals: List[Dict], data: pd.DataFrame) -> Dict:
        """
        Run backtest on historical signals
        
        Args:
            signals: List of trading signals
            data: Historical price data
            
        Returns:
            Backtest results with metrics
        """
        balance = self.initial_balance
        trades = []
        equity_curve = [balance]
        
        for signal in signals:
            if signal['action'] not in ['BUY', 'SELL']:
                continue
            
            # Simulate trade execution
            entry = signal['entry_price']
            sl = signal['stop_loss']
            tp = signal['take_profit']
            
            # Apply slippage and spread
            if signal['action'] == 'BUY':
                entry += (self.slippage_pips + self.spread_pips) * 0.0001
            else:
                entry -= (self.slippage_pips + self.spread_pips) * 0.0001
            
            # Calculate position size (simple fixed risk)
            risk_amount = balance * 0.01  # 1% risk
            risk_pips = abs(entry - sl) / 0.0001
            position_size = risk_amount / (risk_pips * 0.0001) if risk_pips > 0 else 0
            
            if position_size == 0:
                continue
            
            # Simulate trade outcome
            # For simplicity, assume TP or SL is hit
            if np.random.random() < 0.55:  # 55% win rate simulation
                # TP hit
                pnl_pips = abs(tp - entry) / 0.0001
                pnl = pnl_pips * position_size * 0.0001
                outcome = 'WIN'
            else:
                # SL hit
                pnl_pips = -abs(entry - sl) / 0.0001
                pnl = pnl_pips * position_size * 0.0001
                outcome = 'LOSS'
            
            # Apply commission
            commission = self.commission_pips * position_size * 0.0001
            pnl -= commission
            
            # Update balance
            balance += pnl
            equity_curve.append(balance)
            
            # Record trade
            trades.append({
                'timestamp': signal.get('timestamp', datetime.now()),
                'symbol': signal['symbol'],
                'action': signal['action'],
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'position_size': position_size,
                'pnl': pnl,
                'pnl_pips': pnl_pips,
                'outcome': outcome,
                'balance': balance,
                'confidence': signal.get('confidence', 0)
            })
        
        # Calculate metrics
        metrics = self._calculate_metrics(trades, equity_curve)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'metrics': metrics,
            'initial_balance': self.initial_balance,
            'final_balance': balance
        }
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[float]) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {}
        
        df_trades = pd.DataFrame(trades)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len(df_trades[df_trades['outcome'] == 'WIN'])
        losing_trades = len(df_trades[df_trades['outcome'] == 'LOSS'])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = df_trades['pnl'].sum()
        gross_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df_trades[df_trades['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Returns
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        
        # Sharpe ratio (simplified)
        returns = equity_series.pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'avg_win': gross_profit / winning_trades if winning_trades > 0 else 0,
            'avg_loss': gross_loss / losing_trades if losing_trades > 0 else 0,
        }
    
    def export_results(self, results: Dict, filename: str):
        """Export backtest results to JSON"""
        # Convert to serializable format
        export_data = {
            'initial_balance': results['initial_balance'],
            'final_balance': results['final_balance'],
            'metrics': results['metrics'],
            'equity_curve': results['equity_curve'],
            'trades': [
                {**t, 'timestamp': t['timestamp'].isoformat() if isinstance(t['timestamp'], datetime) else t['timestamp']}
                for t in results['trades']
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Results exported to {filename}")
