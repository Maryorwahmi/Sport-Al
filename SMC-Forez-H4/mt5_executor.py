#!/usr/bin/env python3
"""
MT5 Signal Executor for SMC Forez
Executes valid trading signals on MetaTrader 5 platform
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.signals.signal_generator import SignalType

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import MetaTrader5 - graceful fallback if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    logger.warning("MetaTrader5 not available - running in simulation mode")
    MT5_AVAILABLE = False
    # Create a mock MT5 module for testing
    class MockMT5:
        @staticmethod
        def initialize(): return True
        @staticmethod
        def login(login, password, server): return True
        @staticmethod
        def shutdown(): pass
        @staticmethod
        def symbol_info(symbol): return type('obj', (object,), {'ask': 1.1000, 'bid': 1.0998, 'spread': 2})()
        @staticmethod
        def order_send(request): 
            return type('obj', (object,), {
                'retcode': 10009, 'deal': 12345, 'order': 12345, 'volume': request.get('volume', 0.1),
                'price': request.get('price', 1.1000), 'bid': 1.0998, 'ask': 1.1000, 'comment': 'Success'
            })()
        @staticmethod
        def last_error(): return (0, "No error")
        @staticmethod
        def TRADE_ACTION_DEAL(): return 1
        @staticmethod
        def ORDER_TYPE_BUY(): return 0
        @staticmethod
        def ORDER_TYPE_SELL(): return 1
        @staticmethod
        def ORDER_FILLING_IOC(): return 1
    
    mt5 = MockMT5()


@dataclass
class ExecutedTrade:
    """Represents an executed trade"""
    signal_id: str
    symbol: str
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float
    ticket: int
    execution_time: datetime
    status: str = "executed"
    mt5_response: Optional[Dict] = None


class MT5Executor:
    """Executes trading signals on MetaTrader 5"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.connected = False
        self.executed_trades = []
        self.trades_dir = Path("executed_trades")
        self.trades_dir.mkdir(exist_ok=True)
        
        # Trading parameters
        self.max_position_size = 1.0  # Maximum position size
        self.min_position_size = 0.01  # Minimum position size
        self.max_spread = 5.0  # Maximum spread to execute (pips)
        self.slippage = 3  # Maximum slippage (pips)
        
    def connect_mt5(self) -> bool:
        """
        Connect to MetaTrader 5
        
        Returns:
            True if connection successful
        """
        try:
            if not MT5_AVAILABLE:
                logger.info("MT5 not available - using simulation mode")
                self.connected = True
                return True
                
            # Initialize MT5
            if not mt5.initialize():
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            # Login if credentials provided
            if (self.settings.mt5_login and 
                self.settings.mt5_password and 
                self.settings.mt5_server):
                
                if not mt5.login(
                    self.settings.mt5_login,
                    self.settings.mt5_password,
                    self.settings.mt5_server
                ):
                    error = mt5.last_error()
                    logger.error(f"MT5 login failed: {error}")
                    mt5.shutdown()
                    return False
                    
                logger.info(f"✓ Connected to MT5 server: {self.settings.mt5_server}")
            else:
                logger.info("✓ Connected to MT5 (demo mode - no credentials)")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {str(e)}")
            return False
    
    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5"""
        if self.connected and MT5_AVAILABLE:
            mt5.shutdown()
            self.connected = False
            logger.info("✓ Disconnected from MT5")
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information from MT5
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Symbol info dictionary or None
        """
        try:
            if not self.connected:
                logger.error("Not connected to MT5")
                return None
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol {symbol} not found")
                return None
            
            return {
                'ask': symbol_info.ask,
                'bid': symbol_info.bid,
                'spread': symbol_info.spread,
                'point': getattr(symbol_info, 'point', 0.00001),
                'digits': getattr(symbol_info, 'digits', 5),
                'trade_allowed': True  # Always allow trading in simulation mode
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {str(e)}")
            return None
    
    def calculate_position_size(self, signal: Dict, symbol_info: Dict) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            signal: Trading signal
            symbol_info: Symbol information
            
        Returns:
            Position size in lots
        """
        try:
            # Calculate risk per trade in account currency
            account_balance = 10000.0  # Default balance - should come from MT5 account info
            risk_amount = account_balance * self.settings.trading.risk_per_trade
            
            # Calculate pip value
            point = symbol_info.get('point', 0.00001)
            
            # Calculate stop loss distance in pips
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            
            pip_distance = abs(entry_price - stop_loss) / point
            
            if pip_distance <= 0:
                return self.min_position_size
            
            # For JPY pairs, pip value is different
            if 'JPY' in signal['symbol']:
                pip_value = point * 100000  # 1 lot = 100,000 units
            else:
                pip_value = point * 100000  # 1 lot = 100,000 units
            
            # Calculate position size
            position_size = risk_amount / (pip_distance * pip_value)
            
            # Round to 2 decimal places and apply limits
            position_size = round(position_size, 2)
            position_size = max(self.min_position_size, min(self.max_position_size, position_size))
            
            logger.info(f"Calculated position size: {position_size} lots (Risk: ${risk_amount:.2f}, Pip distance: {pip_distance:.1f})")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return self.min_position_size
    
    def validate_signal(self, signal: Dict) -> Tuple[bool, str]:
        """
        Validate signal before execution
        
        Args:
            signal: Trading signal to validate
            
        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['symbol', 'signal_type', 'entry_price', 'stop_loss', 'take_profit']
        for field in required_fields:
            if field not in signal:
                return False, f"Missing required field: {field}"
        
        # Check signal validity
        if not signal.get('valid', False):
            return False, "Signal marked as invalid"
        
        # Check confidence threshold
        confidence = signal.get('confidence', 0)
        if confidence < 0.7:
            return False, f"Confidence too low: {confidence:.2f} < 0.7"
        
        # Check risk/reward ratio
        rr_ratio = signal.get('risk_reward_ratio', 0)
        if rr_ratio < self.settings.trading.min_rr_ratio:
            return False, f"R:R ratio too low: {rr_ratio:.2f} < {self.settings.trading.min_rr_ratio}"
        
        # Check price levels
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        
        signal_type = signal['signal_type']
        if hasattr(signal_type, 'value'):
            signal_type = signal_type.value
        
        if signal_type.upper() == 'BUY':
            if stop_loss >= entry_price:
                return False, "Invalid BUY signal: stop loss must be below entry price"
            if take_profit <= entry_price:
                return False, "Invalid BUY signal: take profit must be above entry price"
        elif signal_type.upper() == 'SELL':
            if stop_loss <= entry_price:
                return False, "Invalid SELL signal: stop loss must be above entry price"
            if take_profit >= entry_price:
                return False, "Invalid SELL signal: take profit must be below entry price"
        
        return True, "Signal valid"
    
    def execute_signal(self, signal: Dict) -> Optional[ExecutedTrade]:
        """
        Execute trading signal on MT5
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            ExecutedTrade object if successful, None otherwise
        """
        try:
            if not self.connected:
                logger.error("Not connected to MT5")
                return None
            
            # Validate signal
            is_valid, error_msg = self.validate_signal(signal)
            if not is_valid:
                logger.error(f"Signal validation failed: {error_msg}")
                return None
            
            symbol = signal['symbol']
            
            # Get current symbol info
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                logger.error(f"Could not get symbol info for {symbol}")
                return None
            
            # Check if trading is allowed
            if not symbol_info.get('trade_allowed', True):
                logger.error(f"Trading not allowed for {symbol}")
                return None
            
            # Check spread
            current_spread = symbol_info.get('spread', 0)
            if current_spread > self.max_spread:
                logger.error(f"Spread too wide: {current_spread} > {self.max_spread}")
                return None
            
            # Calculate position size
            position_size = self.calculate_position_size(signal, symbol_info)
            
            # Determine order type
            signal_type = signal['signal_type']
            if hasattr(signal_type, 'value'):
                signal_type = signal_type.value
            
            if signal_type.upper() == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY() if MT5_AVAILABLE else 0
                price = symbol_info['ask']
            else:  # SELL
                order_type = mt5.ORDER_TYPE_SELL() if MT5_AVAILABLE else 1
                price = symbol_info['bid']
            
            # Prepare trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL() if MT5_AVAILABLE else 1,
                "symbol": symbol,
                "volume": position_size,
                "type": order_type,
                "price": price,
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "deviation": self.slippage,
                "magic": 12345,  # Expert Advisor ID
                "comment": f"SMC_Signal_{datetime.now().strftime('%H%M%S')}",
                "type_time": getattr(mt5, 'ORDER_TIME_GTC', 0)() if MT5_AVAILABLE else 0,
                "type_filling": mt5.ORDER_FILLING_IOC() if MT5_AVAILABLE else 1,
            }
            
            # Send order
            logger.info(f"Executing {signal_type.upper()} order for {symbol}")
            logger.info(f"Entry: {price:.5f}, SL: {signal['stop_loss']:.5f}, TP: {signal['take_profit']:.5f}")
            logger.info(f"Volume: {position_size} lots")
            
            result = mt5.order_send(request)
            
            # Check result
            if result.retcode != 10009:  # TRADE_RETCODE_DONE
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
            
            # Create executed trade record
            executed_trade = ExecutedTrade(
                signal_id=signal.get('timestamp', datetime.now().isoformat()),
                symbol=symbol,
                signal_type=signal_type.upper(),
                entry_price=result.price,
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit'],
                volume=result.volume,
                ticket=result.order,
                execution_time=datetime.now(),
                mt5_response={
                    'retcode': result.retcode,
                    'deal': result.deal,
                    'order': result.order,
                    'volume': result.volume,
                    'price': result.price,
                    'bid': result.bid,
                    'ask': result.ask,
                    'comment': result.comment
                }
            )
            
            self.executed_trades.append(executed_trade)
            
            logger.info(f"✅ Order executed successfully!")
            logger.info(f"   Ticket: {result.order}")
            logger.info(f"   Deal: {result.deal}")
            logger.info(f"   Execution Price: {result.price:.5f}")
            logger.info(f"   Volume: {result.volume} lots")
            
            return executed_trade
            
        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
            return None
    
    def execute_signals_from_file(self, signals_file: str) -> List[ExecutedTrade]:
        """
        Execute signals from a JSON file
        
        Args:
            signals_file: Path to signals JSON file
            
        Returns:
            List of executed trades
        """
        try:
            with open(signals_file, 'r') as f:
                data = json.load(f)
            
            signals = data.get('signals', [])
            logger.info(f"Loading {len(signals)} signals from {signals_file}")
            
            executed_trades = []
            
            for i, signal in enumerate(signals):
                logger.info(f"\n{'='*60}")
                logger.info(f"EXECUTING SIGNAL {i+1}/{len(signals)}")
                logger.info(f"{'='*60}")
                
                # Convert string signal_type back to enum if needed
                if isinstance(signal.get('signal_type'), str):
                    signal_type_str = signal['signal_type'].upper()
                    if signal_type_str == 'BUY':
                        signal['signal_type'] = SignalType.BUY
                    elif signal_type_str == 'SELL':
                        signal['signal_type'] = SignalType.SELL
                
                executed_trade = self.execute_signal(signal)
                
                if executed_trade:
                    executed_trades.append(executed_trade)
                    logger.info(f"✅ Signal {i+1} executed successfully")
                else:
                    logger.error(f"❌ Signal {i+1} execution failed")
                
                # Small delay between executions
                time.sleep(1)
            
            logger.info(f"\n📊 EXECUTION SUMMARY")
            logger.info(f"   Total Signals: {len(signals)}")
            logger.info(f"   Successfully Executed: {len(executed_trades)}")
            logger.info(f"   Failed: {len(signals) - len(executed_trades)}")
            
            return executed_trades
            
        except Exception as e:
            logger.error(f"Error executing signals from file: {str(e)}")
            return []
    
    def save_executed_trades(self, executed_trades: List[ExecutedTrade], filename: Optional[str] = None) -> str:
        """
        Save executed trades to JSON file
        
        Args:
            executed_trades: List of executed trades
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"executed_trades_{timestamp}.json"
        
        filepath = self.trades_dir / filename
        
        # Convert to serializable format
        trades_data = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': len(executed_trades),
            'trades': []
        }
        
        for trade in executed_trades:
            trade_dict = {
                'signal_id': trade.signal_id,
                'symbol': trade.symbol,
                'signal_type': trade.signal_type,
                'entry_price': trade.entry_price,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'volume': trade.volume,
                'ticket': trade.ticket,
                'execution_time': trade.execution_time.isoformat(),
                'status': trade.status,
                'mt5_response': trade.mt5_response
            }
            trades_data['trades'].append(trade_dict)
        
        with open(filepath, 'w') as f:
            json.dump(trades_data, f, indent=2, default=str)
        
        logger.info(f"✓ Executed trades saved to: {filepath}")
        return str(filepath)
    
    def monitor_trades(self, check_interval: int = 60):
        """
        Monitor executed trades (placeholder for future implementation)
        
        Args:
            check_interval: Seconds between checks
        """
        logger.info("Trade monitoring not yet implemented")
        # Future: Monitor SL/TP hits, trailing stops, etc.


def main():
    """Main function to test MT5 executor"""
    print("🚀 SMC FOREZ - MT5 SIGNAL EXECUTOR")
    print("="*60)
    
    # Initialize settings
    settings = Settings()
    
    # Create executor
    executor = MT5Executor(settings)
    
    # Connect to MT5
    print("🔌 CONNECTING TO MT5")
    print("-" * 30)
    
    if executor.connect_mt5():
        print("✅ Connected to MT5 successfully")
    else:
        print("❌ Failed to connect to MT5")
        return
    
    try:
        # Check for recent signal files
        signals_dir = Path("live_signals")
        if signals_dir.exists():
            signal_files = list(signals_dir.glob("live_signals_*.json"))
            if signal_files:
                # Get most recent signal file
                latest_file = max(signal_files, key=lambda x: x.stat().st_mtime)
                print(f"\n📁 FOUND RECENT SIGNALS")
                print("-" * 30)
                print(f"Latest signals file: {latest_file.name}")
                
                execute = input("Execute these signals? (y/n): ").strip().lower()
                if execute == 'y':
                    print("\n⚡ EXECUTING SIGNALS")
                    print("-" * 30)
                    
                    executed_trades = executor.execute_signals_from_file(str(latest_file))
                    
                    if executed_trades:
                        # Save executed trades
                        trades_file = executor.save_executed_trades(executed_trades)
                        print(f"\n💾 Executed trades saved to: {trades_file}")
                        
                        # Print summary
                        print(f"\n📊 EXECUTION SUMMARY")
                        print("-" * 30)
                        for trade in executed_trades:
                            print(f"✅ {trade.symbol} {trade.signal_type} @ {trade.entry_price:.5f}")
                    
                    print("\n✅ Signal execution completed")
                else:
                    print("❌ Signal execution cancelled")
            else:
                print("📁 No signal files found in live_signals directory")
        else:
            print("📁 live_signals directory not found")
            
        # Test with a sample signal
        print(f"\n🧪 TESTING WITH SAMPLE SIGNAL")
        print("-" * 30)
        
        sample_signal = {
            'timestamp': datetime.now().isoformat(),
            'symbol': 'EURUSD',
            'signal_type': SignalType.BUY,
            'entry_price': 1.1000,
            'stop_loss': 1.0950,
            'take_profit': 1.1075,
            'confidence': 0.85,
            'risk_reward_ratio': 2.5,
            'valid': True
        }
        
        test_execution = input("Test with sample EURUSD signal? (y/n): ").strip().lower()
        if test_execution == 'y':
            executed_trade = executor.execute_signal(sample_signal)
            if executed_trade:
                print("✅ Sample signal executed successfully")
                executor.save_executed_trades([executed_trade])
            else:
                print("❌ Sample signal execution failed")
    
    finally:
        # Disconnect
        executor.disconnect_mt5()
        print("\n📝 MT5 executor finished")


if __name__ == "__main__":
    main()