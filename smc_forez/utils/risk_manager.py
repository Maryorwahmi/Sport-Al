"""
Advanced risk management module for SMC Forez
Portfolio-level risk control and position sizing
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum


class RiskLevel(Enum):
    """Risk level classification"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics"""
    total_exposure: float = 0.0
    total_risk: float = 0.0
    max_drawdown: float = 0.0
    daily_var: float = 0.0  # Value at Risk
    correlation_risk: float = 0.0
    leverage_ratio: float = 0.0


@dataclass
class PositionRisk:
    """Individual position risk metrics"""
    symbol: str
    position_size: float
    risk_amount: float
    risk_percentage: float
    stop_distance_pips: float
    correlation_factor: float = 1.0


class RiskManager:
    """
    Advanced risk management system with portfolio-level controls
    """
    
    def __init__(self, 
                 initial_balance: float = 10000.0,
                 risk_level: RiskLevel = RiskLevel.CONSERVATIVE,
                 max_portfolio_risk: float = 0.05,  # 5% max portfolio risk
                 max_correlation_exposure: float = 0.15,  # 15% max correlated exposure
                 max_daily_loss: float = 0.02):  # 2% max daily loss
        """
        Initialize risk manager
        
        Args:
            initial_balance: Starting account balance
            risk_level: Risk profile (conservative, moderate, aggressive)
            max_portfolio_risk: Maximum total portfolio risk percentage
            max_correlation_exposure: Maximum exposure to correlated positions
            max_daily_loss: Maximum allowed daily loss percentage
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.risk_level = risk_level
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation_exposure = max_correlation_exposure
        self.max_daily_loss = max_daily_loss
        
        # Position tracking
        self.open_positions: Dict[str, PositionRisk] = {}
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.now().date()
        
        # Correlation matrix for major pairs
        self.correlation_matrix = self._create_correlation_matrix()
        
        # Risk parameters by level
        self.risk_params = {
            RiskLevel.CONSERVATIVE: {
                'max_position_risk': 0.01,  # 1% per position
                'max_positions': 3,
                'min_rr_ratio': 2.5,
                'max_leverage': 5.0
            },
            RiskLevel.MODERATE: {
                'max_position_risk': 0.02,  # 2% per position
                'max_positions': 5,
                'min_rr_ratio': 2.0,
                'max_leverage': 10.0
            },
            RiskLevel.AGGRESSIVE: {
                'max_position_risk': 0.03,  # 3% per position
                'max_positions': 8,
                'min_rr_ratio': 1.8,
                'max_leverage': 20.0
            }
        }
    
    def _create_correlation_matrix(self) -> Dict[Tuple[str, str], float]:
        """Create correlation matrix for major currency pairs"""
        correlations = {
            # EUR pairs
            ('EURUSD', 'EURGBP'): 0.6,
            ('EURUSD', 'EURJPY'): 0.7,
            ('EURUSD', 'EURAUD'): 0.8,
            ('EURUSD', 'EURCHF'): 0.9,
            
            # GBP pairs
            ('GBPUSD', 'EURGBP'): -0.7,
            ('GBPUSD', 'GBPJPY'): 0.8,
            ('GBPUSD', 'GBPAUD'): 0.9,
            ('GBPUSD', 'GBPCHF'): 0.8,
            
            # USD pairs
            ('EURUSD', 'GBPUSD'): 0.6,
            ('EURUSD', 'AUDUSD'): 0.7,
            ('EURUSD', 'NZDUSD'): 0.6,
            ('EURUSD', 'USDCAD'): -0.7,
            ('EURUSD', 'USDCHF'): -0.8,
            ('EURUSD', 'USDJPY'): -0.3,
            
            # JPY pairs
            ('USDJPY', 'EURJPY'): 0.8,
            ('USDJPY', 'GBPJPY'): 0.7,
            ('USDJPY', 'AUDJPY'): 0.6,
            
            # Commodity currencies
            ('AUDUSD', 'NZDUSD'): 0.8,
            ('AUDUSD', 'USDCAD'): -0.5,
            
            # Safe haven
            ('USDCHF', 'USDJPY'): 0.4,
        }
        
        # Add reverse correlations
        reverse_correlations = {}
        for (pair1, pair2), corr in correlations.items():
            reverse_correlations[(pair2, pair1)] = corr
        
        correlations.update(reverse_correlations)
        return correlations
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two currency pairs"""
        return self.correlation_matrix.get((symbol1, symbol2), 0.0)
    
    def calculate_position_size(self, 
                              symbol: str,
                              entry_price: float,
                              stop_loss: float,
                              confidence: float = 1.0) -> Tuple[float, PositionRisk]:
        """
        Calculate optimal position size with risk management
        
        Args:
            symbol: Currency pair
            entry_price: Entry price
            stop_loss: Stop loss price
            confidence: Signal confidence (0.0-1.0)
            
        Returns:
            Tuple of (position_size, position_risk)
        """
        try:
            # Reset daily tracking if new day
            self._check_daily_reset()
            
            # Get risk parameters for current risk level
            params = self.risk_params[self.risk_level]
            
            # Check if we can add more positions
            if len(self.open_positions) >= params['max_positions']:
                return 0.0, None
            
            # Check daily loss limit
            if self.daily_pnl <= -self.current_balance * self.max_daily_loss:
                return 0.0, None
            
            # Calculate base position risk
            base_risk = params['max_position_risk'] * confidence
            
            # Adjust for correlation risk
            correlation_adjustment = self._calculate_correlation_adjustment(symbol)
            adjusted_risk = base_risk * correlation_adjustment
            
            # Calculate pip value and risk
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            risk_pips = abs(entry_price - stop_loss) / pip_size
            
            if risk_pips <= 0:
                return 0.0, None
            
            # Calculate position size
            risk_amount = self.current_balance * adjusted_risk
            pip_value = pip_size * 100000  # Standard lot
            position_size = risk_amount / (risk_pips * pip_value)
            
            # Apply size limits
            min_size = 0.01
            max_size = 10.0
            position_size = max(min_size, min(position_size, max_size))
            position_size = round(position_size, 2)
            
            # Check portfolio risk limits
            portfolio_risk = self._calculate_portfolio_risk(
                symbol, position_size, risk_pips * pip_value
            )
            
            if portfolio_risk.total_risk > self.max_portfolio_risk:
                # Scale down position to meet portfolio limit
                scale_factor = self.max_portfolio_risk / portfolio_risk.total_risk
                position_size *= scale_factor
                position_size = round(position_size, 2)
                risk_amount *= scale_factor
            
            # Create position risk object
            position_risk = PositionRisk(
                symbol=symbol,
                position_size=position_size,
                risk_amount=risk_amount,
                risk_percentage=risk_amount / self.current_balance,
                stop_distance_pips=risk_pips,
                correlation_factor=correlation_adjustment
            )
            
            return position_size, position_risk
            
        except Exception as e:
            print(f"Error calculating position size: {str(e)}")
            return 0.01, None
    
    def _calculate_correlation_adjustment(self, symbol: str) -> float:
        """Calculate correlation adjustment factor"""
        if not self.open_positions:
            return 1.0
        
        max_correlation = 0.0
        total_correlated_exposure = 0.0
        
        for existing_symbol, existing_pos in self.open_positions.items():
            correlation = abs(self.get_correlation(symbol, existing_symbol))
            max_correlation = max(max_correlation, correlation)
            
            if correlation > 0.5:  # Significantly correlated
                total_correlated_exposure += existing_pos.risk_percentage
        
        # Reduce position size if high correlation or exposure
        correlation_factor = 1.0 - (max_correlation * 0.5)
        
        if total_correlated_exposure > self.max_correlation_exposure:
            exposure_factor = self.max_correlation_exposure / total_correlated_exposure
            correlation_factor *= exposure_factor
        
        return max(0.2, correlation_factor)  # Minimum 20% of base size
    
    def _calculate_portfolio_risk(self, 
                                new_symbol: str, 
                                new_size: float, 
                                new_risk: float) -> PortfolioRisk:
        """Calculate portfolio-level risk metrics"""
        total_risk = new_risk
        total_exposure = new_size * 100000  # Convert to base currency
        
        # Add existing positions
        for pos in self.open_positions.values():
            total_risk += pos.risk_amount
            total_exposure += pos.position_size * 100000
        
        # Calculate risk as percentage of balance
        risk_percentage = total_risk / self.current_balance
        leverage = total_exposure / self.current_balance
        
        return PortfolioRisk(
            total_exposure=total_exposure,
            total_risk=risk_percentage,
            leverage_ratio=leverage
        )
    
    def add_position(self, position_risk: PositionRisk):
        """Add a new position to risk tracking"""
        self.open_positions[position_risk.symbol] = position_risk
    
    def remove_position(self, symbol: str, pnl: float):
        """Remove a position and update P&L"""
        if symbol in self.open_positions:
            del self.open_positions[symbol]
        
        self.daily_pnl += pnl
        self.current_balance += pnl
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
    
    def _check_daily_reset(self):
        """Reset daily tracking if new day"""
        current_date = datetime.now().date()
        if current_date != self.daily_reset_time:
            self.daily_pnl = 0.0
            self.daily_reset_time = current_date
    
    def can_trade(self, symbol: str, signal_confidence: float = 1.0) -> Tuple[bool, str]:
        """
        Check if we can trade based on risk rules
        
        Args:
            symbol: Currency pair
            signal_confidence: Signal confidence level
            
        Returns:
            Tuple of (can_trade, reason)
        """
        self._check_daily_reset()
        
        params = self.risk_params[self.risk_level]
        
        # Check position count
        if len(self.open_positions) >= params['max_positions']:
            return False, f"Maximum positions reached ({params['max_positions']})"
        
        # Check daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / self.current_balance
        if self.daily_pnl < 0 and daily_loss_pct >= self.max_daily_loss:
            return False, f"Daily loss limit reached ({daily_loss_pct:.1%})"
        
        # Check if symbol already has position
        if symbol in self.open_positions:
            return False, f"Position already exists for {symbol}"
        
        # Check correlation exposure
        correlated_exposure = 0.0
        for existing_symbol, pos in self.open_positions.items():
            correlation = abs(self.get_correlation(symbol, existing_symbol))
            if correlation > 0.5:
                correlated_exposure += pos.risk_percentage
        
        if correlated_exposure > self.max_correlation_exposure:
            return False, f"Correlation exposure limit exceeded ({correlated_exposure:.1%})"
        
        # Check portfolio risk
        current_portfolio_risk = sum(pos.risk_percentage for pos in self.open_positions.values())
        if current_portfolio_risk >= self.max_portfolio_risk * 0.8:  # 80% of max
            return False, f"Portfolio risk too high ({current_portfolio_risk:.1%})"
        
        return True, "OK"
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        self._check_daily_reset()
        
        total_positions = len(self.open_positions)
        total_risk = sum(pos.risk_percentage for pos in self.open_positions.values())
        total_exposure = sum(pos.position_size * 100000 for pos in self.open_positions.values())
        leverage = total_exposure / self.current_balance if self.current_balance > 0 else 0
        
        daily_return_pct = (self.daily_pnl / self.current_balance) * 100
        total_return_pct = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        return {
            'account_balance': self.current_balance,
            'initial_balance': self.initial_balance,
            'daily_pnl': self.daily_pnl,
            'daily_return_pct': daily_return_pct,
            'total_return_pct': total_return_pct,
            'risk_level': self.risk_level.value,
            'total_positions': total_positions,
            'total_risk_pct': total_risk * 100,
            'leverage_ratio': leverage,
            'max_positions': self.risk_params[self.risk_level]['max_positions'],
            'remaining_risk_capacity': (self.max_portfolio_risk - total_risk) * 100,
            'daily_loss_limit_pct': self.max_daily_loss * 100,
            'daily_loss_used_pct': abs(self.daily_pnl / self.current_balance) * 100 if self.daily_pnl < 0 else 0,
        }
    
    def print_risk_report(self):
        """Print a formatted risk report"""
        summary = self.get_risk_summary()
        
        print("\n" + "="*60)
        print("📊 RISK MANAGEMENT REPORT")
        print("="*60)
        
        print(f"💰 Account Balance:     ${summary['account_balance']:,.2f}")
        print(f"📈 Daily P&L:           ${summary['daily_pnl']:+.2f} ({summary['daily_return_pct']:+.2f}%)")
        print(f"📊 Total Return:        {summary['total_return_pct']:+.2f}%")
        print(f"🎯 Risk Level:          {summary['risk_level'].upper()}")
        print()
        
        print("📍 POSITION RISK")
        print("-" * 30)
        print(f"Open Positions:         {summary['total_positions']}/{summary['max_positions']}")
        print(f"Portfolio Risk:         {summary['total_risk_pct']:.2f}%")
        print(f"Remaining Capacity:     {summary['remaining_risk_capacity']:.2f}%")
        print(f"Leverage Ratio:         {summary['leverage_ratio']:.2f}x")
        print()
        
        print("⚠️ DAILY LIMITS")
        print("-" * 30)
        print(f"Daily Loss Limit:       {summary['daily_loss_limit_pct']:.1f}%")
        print(f"Daily Loss Used:        {summary['daily_loss_used_pct']:.2f}%")
        print()
        
        if self.open_positions:
            print("📋 OPEN POSITIONS")
            print("-" * 30)
            for symbol, pos in self.open_positions.items():
                print(f"{symbol}: {pos.position_size:.2f} lots "
                      f"(Risk: {pos.risk_percentage*100:.2f}%, "
                      f"Corr: {pos.correlation_factor:.2f})")
        
        print("="*60)


def create_risk_manager(risk_profile: str = "conservative", 
                       balance: float = 10000.0) -> RiskManager:
    """
    Factory function to create risk manager with predefined profiles
    
    Args:
        risk_profile: "conservative", "moderate", or "aggressive"
        balance: Account balance
        
    Returns:
        Configured RiskManager instance
    """
    risk_level_map = {
        "conservative": RiskLevel.CONSERVATIVE,
        "moderate": RiskLevel.MODERATE,
        "aggressive": RiskLevel.AGGRESSIVE
    }
    
    risk_level = risk_level_map.get(risk_profile.lower(), RiskLevel.CONSERVATIVE)
    
    return RiskManager(
        initial_balance=balance,
        risk_level=risk_level
    )