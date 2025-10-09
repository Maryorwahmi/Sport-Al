"""
Risk management module
"""
from typing import Dict, Tuple


class RiskManager:
    """Position sizing and risk management"""
    
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.risk_per_trade = self.settings.get('risk_per_trade', 0.01)
        self.max_portfolio_risk = self.settings.get('max_portfolio_risk', 0.05)
        self.max_position_size = self.settings.get('max_position_size', 0.1)
        self.max_concurrent_trades = self.settings.get('max_concurrent_trades', 3)
        self.max_daily_loss = self.settings.get('max_daily_loss', 0.03)
        
        self.open_positions = []
        self.daily_pnl = 0.0
    
    def calculate_position_size(self, account_balance: float, entry_price: float,
                                stop_loss: float, pip_value: float = 1.0) -> Tuple[float, Dict]:
        """
        Calculate position size based on risk
        
        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss: Stop loss price
            pip_value: Value of 1 pip for the symbol
            
        Returns:
            (position_size, risk_data)
        """
        # Calculate risk in pips
        risk_pips = abs(entry_price - stop_loss) / 0.0001
        
        # Calculate position size
        risk_amount = account_balance * self.risk_per_trade
        position_size = risk_amount / (risk_pips * pip_value)
        
        # Apply maximum position size limit
        max_size = account_balance * self.max_position_size / entry_price
        position_size = min(position_size, max_size)
        
        risk_data = {
            'position_size': position_size,
            'risk_amount': position_size * risk_pips * pip_value,
            'risk_pct': (position_size * risk_pips * pip_value) / account_balance,
            'risk_pips': risk_pips
        }
        
        return position_size, risk_data
    
    def can_trade(self, symbol: str, account_balance: float) -> Tuple[bool, str]:
        """Check if new trade is allowed"""
        # Check concurrent trades limit
        if len(self.open_positions) >= self.max_concurrent_trades:
            return False, f"Maximum concurrent trades ({self.max_concurrent_trades}) reached"
        
        # Check daily loss limit
        if self.daily_pnl < -(account_balance * self.max_daily_loss):
            return False, f"Daily loss limit ({self.max_daily_loss:.1%}) reached"
        
        # Check portfolio risk
        total_risk = sum(pos.get('risk_pct', 0) for pos in self.open_positions)
        if total_risk >= self.max_portfolio_risk:
            return False, f"Portfolio risk limit ({self.max_portfolio_risk:.1%}) reached"
        
        return True, "OK"
    
    def add_position(self, position: Dict):
        """Add an open position"""
        self.open_positions.append(position)
    
    def close_position(self, position_id: str, pnl: float):
        """Close a position and update P&L"""
        self.open_positions = [p for p in self.open_positions if p.get('id') != position_id]
        self.daily_pnl += pnl
    
    def reset_daily(self):
        """Reset daily counters"""
        self.daily_pnl = 0.0
