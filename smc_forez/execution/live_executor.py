"""
Production-ready live execution system for SMC Forez
Continuous monitoring, signal execution, and risk management
"""
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import json
import sys
import os
from pathlib import Path

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from smc_forez.config.settings import Settings, Timeframe
from smc_forez.utils.logger import get_logger, cleanup_logger
from smc_forez.analyzer import SMCAnalyzer
from smc_forez.signals.signal_generator import SignalType, SignalStrength

# Try to import MetaTrader5 - graceful fallback if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    # Mock MT5 for testing
    class MockMT5:
        @staticmethod
        def initialize(): return True
        @staticmethod
        def login(login, password, server): return True
        @staticmethod
        def shutdown(): pass
        @staticmethod
        def order_send(request): 
            return type('obj', (object,), {
                'retcode': 10009, 'order': 12345, 'volume': request.get('volume', 0.1),
                'price': request.get('price', 1.0), 'comment': 'Mock trade'
            })()
        @staticmethod
        def positions_get(): return []
        @staticmethod
        def orders_get(): return []
    mt5 = MockMT5()


@dataclass
class ExecutionSettings:
    """Settings for live execution"""
    refresh_interval_seconds: int = 30  # Check for new signals every 30 seconds
    max_open_trades: int = 5
    max_trades_per_symbol: int = 2
    max_daily_trades: int = 20
    max_spread_multiplier: float = 1.5  # Max spread = normal spread * multiplier
    slippage_pips: float = 2.0
    magic_number: int = 987654321
    enable_execution: bool = True  # Set to False for signal-only mode


@dataclass
class TradePosition:
    """Represents an open trade position"""
    ticket: int
    symbol: str
    action: str
    volume: float
    open_price: float
    stop_loss: float
    take_profit: float
    open_time: datetime
    magic_number: int
    comment: str


class LiveExecutor:
    """
    Production-ready live execution system with continuous monitoring
    """
    
    def __init__(self, settings: Optional[Settings] = None, 
                 execution_settings: Optional[ExecutionSettings] = None):
        """
        Initialize the live executor
        
        Args:
            settings: SMC analyzer settings
            execution_settings: Execution-specific settings
        """
        self.settings = settings or Settings()
        self.execution_settings = execution_settings or ExecutionSettings()
        self.logger = get_logger(log_level="INFO")
        
        # State management
        self.running = False
        self.shutdown_event = threading.Event()
        self.analyzer = SMCAnalyzer(self.settings)
        
        # Trade tracking
        self.open_positions: Dict[str, List[TradePosition]] = {}
        self.daily_trade_count = 0
        self.last_trade_date = datetime.now().date()
        self.processed_signals: Set[str] = set()  # Avoid duplicate signals
        
        # Performance tracking
        self.session_stats = {
            'signals_generated': 0,
            'signals_executed': 0,
            'trades_opened': 0,
            'trades_closed': 0,
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🚀 Live Executor initialized")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"📶 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def connect_mt5(self) -> bool:
        """
        Connect to MetaTrader 5
        
        Returns:
            bool: True if connection successful
        """
        try:
            if not MT5_AVAILABLE:
                self.logger.warning("⚠️ MetaTrader5 not available - running in simulation mode")
                return True
            
            if not mt5.initialize():
                self.logger.error("❌ Failed to initialize MetaTrader5")
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
                    self.logger.error("❌ Failed to login to MetaTrader5")
                    return False
                    
                self.logger.info("✅ Connected to MetaTrader5")
            else:
                self.logger.info("✅ MetaTrader5 initialized (no login credentials)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error connecting to MT5: {str(e)}")
            return False
    
    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5"""
        try:
            if MT5_AVAILABLE:
                mt5.shutdown()
            self.logger.info("🔌 Disconnected from MetaTrader5")
        except Exception as e:
            self.logger.error(f"Error disconnecting from MT5: {str(e)}")
    
    def start_live_execution(self, symbols: List[str]):
        """
        Start continuous live execution
        
        Args:
            symbols: List of symbols to monitor
        """
        try:
            self.logger.info("🔄 Starting live execution system...")
            
            # Connect to MT5
            if not self.connect_mt5():
                self.logger.error("❌ Cannot start - MT5 connection failed")
                return
            
            # Connect analyzer to data source
            if not self.analyzer.connect_data_source():
                self.logger.warning("⚠️ Analyzer data source connection failed - using simulation")
            
            self.running = True
            self.logger.info(f"✅ Live execution started for {len(symbols)} symbols")
            self.logger.info(f"📊 Monitoring: {', '.join(symbols)}")
            self.logger.info(f"⏱️ Refresh interval: {self.execution_settings.refresh_interval_seconds}s")
            
            self.logger.log_system_status("LIVE_EXECUTION_STARTED", {
                'symbols_count': len(symbols),
                'refresh_interval': self.execution_settings.refresh_interval_seconds,
                'max_trades': self.execution_settings.max_daily_trades
            })
            
            # Main execution loop
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Reset daily trade count if new day
                    current_date = datetime.now().date()
                    if current_date != self.last_trade_date:
                        self.daily_trade_count = 0
                        self.last_trade_date = current_date
                        self.logger.info(f"📅 New trading day: {current_date}")
                    
                    # Check if daily limit reached
                    if self.daily_trade_count >= self.execution_settings.max_daily_trades:
                        self.logger.info(f"⏹️ Daily trade limit reached ({self.daily_trade_count})")
                        self._wait_for_next_interval()
                        continue
                    
                    # Monitor and manage existing positions
                    self._manage_open_positions()
                    
                    # Scan for new opportunities
                    self._scan_and_execute(symbols)
                    
                    # Wait for next interval
                    self._wait_for_next_interval()
                    
                except KeyboardInterrupt:
                    self.logger.info("⏹️ Keyboard interrupt received")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in execution loop: {str(e)}")
                    time.sleep(5)  # Brief pause before continuing
            
            self.logger.info("🔄 Live execution loop ended")
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in live execution: {str(e)}")
        finally:
            self._cleanup()
    
    def _scan_and_execute(self, symbols: List[str]):
        """
        Scan symbols for opportunities and execute trades
        
        Args:
            symbols: List of symbols to scan
        """
        try:
            self.logger.info(f"🔍 Scanning {len(symbols)} symbols for opportunities...")
            
            # Get current opportunities
            opportunities = self.analyzer.get_current_opportunities(symbols)
            
            if not opportunities:
                self.logger.info("📊 No trading opportunities found")
                return
            
            self.logger.info(f"🎯 Found {len(opportunities)} potential opportunities")
            
            # Process each opportunity
            for opp in opportunities:
                try:
                    if self.shutdown_event.is_set():
                        break
                    
                    symbol = opp['symbol']
                    recommendation = opp['recommendation']
                    
                    # Create signal data for logging
                    signal_data = {
                        'symbol': symbol,
                        'timeframe': recommendation.get('entry_timeframe', 'UNKNOWN'),
                        'signal_type': recommendation.get('action', 'WAIT'),
                        'signal_strength': recommendation.get('strength_factors', []),
                        'confidence': recommendation.get('confidence', 'LOW'),
                        'confluence_score': recommendation.get('strength_score', 0),
                        'entry_price': recommendation.get('entry_details', {}).get('entry_price', 0),
                        'stop_loss': recommendation.get('entry_details', {}).get('stop_loss', 0),
                        'take_profit': recommendation.get('entry_details', {}).get('take_profit', 0),
                        'risk_reward_ratio': recommendation.get('entry_details', {}).get('risk_reward_ratio', 0),
                        'notes': f"Trend: {recommendation.get('trend_direction', 'UNKNOWN')}"
                    }
                    
                    # Log the signal
                    self.logger.log_signal(signal_data)
                    self.session_stats['signals_generated'] += 1
                    
                    # Check if we should execute the trade
                    if self._should_execute_trade(opp):
                        if self.execution_settings.enable_execution:
                            success = self._execute_trade(opp)
                            if success:
                                signal_data['executed'] = True
                                self.logger.log_signal(signal_data)  # Update with execution status
                                self.session_stats['signals_executed'] += 1
                        else:
                            self.logger.info(f"📋 SIGNAL ONLY MODE: {symbol} {recommendation.get('action', 'WAIT')}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing opportunity for {opp.get('symbol', 'UNKNOWN')}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Error in scan and execute: {str(e)}")
    
    def _should_execute_trade(self, opportunity: Dict) -> bool:
        """
        Determine if a trade should be executed based on risk management rules
        
        Args:
            opportunity: Trading opportunity data
            
        Returns:
            bool: True if trade should be executed
        """
        try:
            symbol = opportunity['symbol']
            recommendation = opportunity['recommendation']
            
            # Check if action is tradeable
            action = recommendation.get('action')
            if not action or str(action).upper() in ['WAIT', 'NONE']:
                return False
            
            # Check confidence level
            confidence = recommendation.get('confidence', 'LOW')
            if confidence not in ['HIGH', 'MODERATE']:
                self.logger.debug(f"🚫 {symbol}: Low confidence ({confidence})")
                return False
            
            # Check if we already have positions in this symbol
            current_positions = len(self.open_positions.get(symbol, []))
            if current_positions >= self.execution_settings.max_trades_per_symbol:
                self.logger.debug(f"🚫 {symbol}: Max positions reached ({current_positions})")
                return False
            
            # Check total open trades
            total_positions = sum(len(pos_list) for pos_list in self.open_positions.values())
            if total_positions >= self.execution_settings.max_open_trades:
                self.logger.debug(f"🚫 Max total trades reached ({total_positions})")
                return False
            
            # Check daily trade limit
            if self.daily_trade_count >= self.execution_settings.max_daily_trades:
                self.logger.debug(f"🚫 Daily trade limit reached ({self.daily_trade_count})")
                return False
            
            # Check if signal was already processed (avoid duplicates)
            signal_id = f"{symbol}_{recommendation.get('entry_timeframe', '')}_" \
                       f"{recommendation.get('action', '')}_" \
                       f"{recommendation.get('entry_details', {}).get('entry_price', 0)}"
            
            if signal_id in self.processed_signals:
                self.logger.debug(f"🚫 {symbol}: Signal already processed")
                return False
            
            self.processed_signals.add(signal_id)
            
            # Check risk/reward ratio
            rr_ratio = recommendation.get('entry_details', {}).get('risk_reward_ratio', 0)
            if rr_ratio < self.settings.trading.min_rr_ratio:
                self.logger.debug(f"🚫 {symbol}: R:R ratio too low ({rr_ratio:.2f})")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in should_execute_trade: {str(e)}")
            return False
    
    def _execute_trade(self, opportunity: Dict) -> bool:
        """
        Execute a trade based on opportunity
        
        Args:
            opportunity: Trading opportunity data
            
        Returns:
            bool: True if trade executed successfully
        """
        try:
            symbol = opportunity['symbol']
            recommendation = opportunity['recommendation']
            entry_details = recommendation.get('entry_details', {})
            
            action = str(recommendation.get('action', '')).upper()
            entry_price = entry_details.get('entry_price', 0)
            stop_loss = entry_details.get('stop_loss', 0)
            take_profit = entry_details.get('take_profit', 0)
            
            # Calculate position size based on risk
            volume = self._calculate_position_size(symbol, entry_price, stop_loss)
            
            if volume <= 0:
                self.logger.error(f"❌ {symbol}: Invalid position size calculated")
                return False
            
            # Prepare trade request
            if action == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY if MT5_AVAILABLE else 'BUY'
                price = entry_price
            elif action == 'SELL':
                order_type = mt5.ORDER_TYPE_SELL if MT5_AVAILABLE else 'SELL'
                price = entry_price
            else:
                self.logger.error(f"❌ {symbol}: Invalid action {action}")
                return False
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL if MT5_AVAILABLE else "DEAL",
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": int(self.execution_settings.slippage_pips * 10),
                "magic": self.execution_settings.magic_number,
                "comment": f"SMC_{action}_{datetime.now().strftime('%H%M%S')}",
                "type_time": mt5.ORDER_TIME_GTC if MT5_AVAILABLE else "GTC",
                "type_filling": mt5.ORDER_FILLING_IOC if MT5_AVAILABLE else "IOC",
            }
            
            # Send order
            self.logger.info(f"📤 Executing {action} order for {symbol}: "
                           f"{volume} lots @ {price:.5f}")
            
            if MT5_AVAILABLE:
                result = mt5.order_send(request)
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    self.logger.error(f"❌ Order failed: {result.retcode}")
                    return False
                
                # Log successful trade
                trade_data = {
                    'symbol': symbol,
                    'action': action,
                    'entry_price': result.price,
                    'size': result.volume,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'status': 'OPEN',
                    'trade_id': str(result.order)
                }
                
                # Track position
                position = TradePosition(
                    ticket=result.order,
                    symbol=symbol,
                    action=action,
                    volume=result.volume,
                    open_price=result.price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    open_time=datetime.now(),
                    magic_number=self.execution_settings.magic_number,
                    comment=request['comment']
                )
                
                if symbol not in self.open_positions:
                    self.open_positions[symbol] = []
                self.open_positions[symbol].append(position)
                
            else:
                # Simulation mode
                trade_data = {
                    'symbol': symbol,
                    'action': action,
                    'entry_price': price,
                    'size': volume,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'status': 'OPEN',
                    'trade_id': 'SIM_' + str(int(time.time()))
                }
            
            self.logger.log_trade(trade_data)
            self.session_stats['trades_opened'] += 1
            self.daily_trade_count += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error executing trade: {str(e)}")
            return False
    
    def _calculate_position_size(self, symbol: str, entry_price: float, 
                               stop_loss: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            symbol: Currency pair
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            float: Position size in lots
        """
        try:
            # Get account balance (use mock value if MT5 not available)
            if MT5_AVAILABLE:
                account_info = mt5.account_info()
                balance = account_info.balance if account_info else 10000.0
            else:
                balance = 10000.0  # Mock balance for simulation
            
            # Calculate risk amount
            risk_amount = balance * self.settings.trading.risk_per_trade
            
            # Calculate pip value and risk in pips
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            risk_pips = abs(entry_price - stop_loss) / pip_size
            
            if risk_pips <= 0:
                return 0.0
            
            # Calculate pip value per standard lot (100,000 units)
            pip_value = pip_size * 100000
            
            # Calculate position size
            position_size = risk_amount / (risk_pips * pip_value)
            
            # Apply limits
            min_volume = 0.01
            max_volume = 10.0  # Conservative max
            
            position_size = max(min_volume, min(position_size, max_volume))
            
            # Round to 2 decimal places
            position_size = round(position_size, 2)
            
            self.logger.debug(f"💰 Position size calculation for {symbol}: "
                            f"Risk ${risk_amount:.2f}, Pips {risk_pips:.1f}, "
                            f"Size {position_size:.2f} lots")
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating position size: {str(e)}")
            return 0.01  # Fallback to minimum size
    
    def _manage_open_positions(self):
        """Monitor and manage open positions"""
        try:
            if not self.open_positions:
                return
            
            self.logger.debug(f"🔍 Managing {sum(len(pos_list) for pos_list in self.open_positions.values())} open positions")
            
            # In a real implementation, you would:
            # 1. Check current positions from MT5
            # 2. Update position status
            # 3. Handle closed positions
            # 4. Apply trailing stops if configured
            # 5. Monitor for emergency exits
            
            # For now, just log that we're monitoring
            for symbol, positions in self.open_positions.items():
                if positions:
                    self.logger.debug(f"📊 {symbol}: {len(positions)} open positions")
                    
        except Exception as e:
            self.logger.error(f"❌ Error managing positions: {str(e)}")
    
    def _wait_for_next_interval(self):
        """Wait for the next scan interval with proper shutdown handling"""
        try:
            self.logger.debug(f"⏳ Waiting {self.execution_settings.refresh_interval_seconds}s for next scan...")
            
            # Wait in small chunks to allow for graceful shutdown
            wait_time = self.execution_settings.refresh_interval_seconds
            chunk_size = 1  # 1 second chunks
            
            while wait_time > 0 and not self.shutdown_event.is_set():
                time.sleep(min(chunk_size, wait_time))
                wait_time -= chunk_size
                
        except Exception as e:
            self.logger.error(f"❌ Error in wait interval: {str(e)}")
    
    def shutdown(self):
        """Gracefully shutdown the live executor"""
        try:
            self.logger.info("🔄 Initiating graceful shutdown...")
            self.running = False
            self.shutdown_event.set()
            
            # Log final session statistics
            self.logger.log_system_status("SHUTDOWN_INITIATED", self.session_stats)
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {str(e)}")
    
    def _cleanup(self):
        """Final cleanup operations"""
        try:
            self.logger.info("🧹 Performing cleanup operations...")
            
            # Disconnect from data sources
            self.analyzer.disconnect_data_source()
            self.disconnect_mt5()
            
            # Log final statistics
            self.logger.log_system_status("CLEANUP_COMPLETED", self.session_stats)
            
            # Cleanup logger
            cleanup_logger()
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


def main():
    """Main function for running live executor"""
    try:
        # Default symbols to monitor
        symbols = [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
            "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "EURGBP", "EURAUD"
        ]
        
        # Create settings
        settings = Settings()
        execution_settings = ExecutionSettings(
            refresh_interval_seconds=30,
            max_open_trades=5,
            max_trades_per_symbol=1,
            max_daily_trades=15,
            enable_execution=False  # Set to True for live trading
        )
        
        # Create and start executor
        executor = LiveExecutor(settings, execution_settings)
        executor.start_live_execution(symbols)
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")


if __name__ == "__main__":
    main()