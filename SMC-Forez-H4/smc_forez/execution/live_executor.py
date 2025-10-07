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
from smc_forez.quality.enhanced_signal_filter import EnhancedSignalQualityFilter, LIVE_TRADING_FILTER
from smc_forez.risk_management.risk_manager import RiskManager, create_risk_manager

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
    """Settings for live execution - optimized for micro accounts"""
    refresh_interval_seconds: int = 1800  # Check for new signals every 30 minutes (1800 seconds)
    max_open_trades: int = 2              # Reduced for micro accounts
    max_trades_per_symbol: int = 3        # Multiple trades per symbol for demo testing
    max_daily_trades: int = 50            # High daily limit for demo account
    max_spread_multiplier: float = 2.0    # Allow higher spread for micro accounts (0.2 * 2.0 = 0.4 max)
    slippage_pips: float = 1.0            # Tighter slippage control for small accounts
    magic_number: int = 142536
    enable_execution: bool = True         # Set to False for signal-only mode
    min_account_balance: float = 1.0      # Minimum balance to allow trading (reduced for micro account testing)
    max_risk_per_trade_micro: float = 0.005  # 0.5% max risk for accounts under $100


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
        
        # == STRATEGIC REFACTOR: Integrate Risk Manager and Quality Filter with Settings ==
        self.risk_manager = create_risk_manager(
            risk_profile="aggressive",  # Aggressive for maximum positions - allows 8 trades
            balance=13.0  # Default micro account balance - will be updated from MT5
        )
        
        # Initialize quality filter with settings-based parameters
        self.quality_filter = EnhancedSignalQualityFilter(
            min_confluence_score=self.settings.quality.min_confluence_score,  # Use count as score threshold
            min_strength_factors=self.settings.quality.min_confluence_score,
            min_rr_ratio=self.settings.quality.min_rr_ratio,
            min_timeframe_agreement=0.66,  # Could be made configurable
            min_trend_confidence=0.7,      # Could be made configurable  
            require_smc_confluence=True  # Default to True for SMC strategy
        )
        self.logger.info("✅ Integrated Enhanced Quality Filter and Risk Manager with settings.")
        
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
            
            # Check if MT5 is already initialized before trying to initialize
            account_info = mt5.account_info()
            if account_info is None:
                # MT5 not initialized yet, try to initialize
                if not mt5.initialize():
                    self.logger.error("❌ Failed to initialize MetaTrader5")
                    self.logger.warning("🔄 Continuing with mock data mode")
                    return True  # Continue with mock data instead of failing
                else:
                    self.logger.info("✅ MT5 initialized successfully")
            else:
                self.logger.info("✅ MT5 already initialized, reusing connection")
            
            # Check if MT5 is already connected/logged in
            account_info = mt5.account_info()
            if account_info is not None:
                self.logger.info(f"✅ Using existing MT5 connection")
                self.logger.info(f"📊 Account: {account_info.login} | Server: {account_info.server}")
                self.logger.info(f"💰 Balance: ${account_info.balance:.2f} | Equity: ${account_info.equity:.2f}")
                
                # Update risk manager with real account balance
                self._update_account_balance()
                return True
            
            # If not connected, try to login with credentials (if provided and not auto mode)
            if (self.settings.mt5_login and self.settings.mt5_login > 0 and
                self.settings.mt5_password and self.settings.mt5_password.strip() and 
                self.settings.mt5_server and self.settings.mt5_server.strip()):
                
                if not mt5.login(
                    self.settings.mt5_login,
                    self.settings.mt5_password,
                    self.settings.mt5_server
                ):
                    self.logger.error("❌ Failed to login to MetaTrader5")
                    self.logger.warning("🔄 Switching to mock data mode for analysis")
                    return True  # Continue with mock data instead of failing
                    
                self.logger.info("✅ Connected to MetaTrader5 with provided credentials")
                
                # Update risk manager with real account balance
                self._update_account_balance()
            else:
                self.logger.warning("⚠️ No existing MT5 connection found and no credentials provided")
                self.logger.info("🔧 Running in mock data mode")
                # Set test balance for simulation
                test_balance = 10000.0
                self.risk_manager.current_balance = test_balance
                self.risk_manager.initial_balance = test_balance
                self.logger.info(f"💰 Using test balance: ${test_balance:.2f}")
            
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
    
    def _update_account_balance(self):
        """Update risk manager with current account balance from MT5"""
        try:
            if not MT5_AVAILABLE:
                return
                
            account_info = mt5.account_info()
            if account_info:
                current_balance = account_info.balance
                self.risk_manager.current_balance = current_balance
                
                # Also update initial balance if this is the first update
                if self.risk_manager.initial_balance == 10000.0:  # Default value
                    self.risk_manager.initial_balance = current_balance
                
                self.logger.info(f"💰 Account balance updated: ${current_balance:.2f}")
                
                # Log risk settings for micro accounts
                if current_balance < 100:  # Micro account
                    self.logger.info(f"🔍 Micro account detected (${current_balance:.2f})")
                    self.logger.info(f"   Risk per trade: {self.risk_manager.risk_params[self.risk_manager.risk_level]['max_position_risk']*100:.1f}%")
                    self.logger.info(f"   Max positions: {self.risk_manager.risk_params[self.risk_manager.risk_level]['max_positions']}")
                    self.logger.info(f"   Min R:R ratio: {self.risk_manager.risk_params[self.risk_manager.risk_level]['min_rr_ratio']}")
            else:
                self.logger.warning("⚠️ Could not retrieve account info from MT5")
                
        except Exception as e:
            self.logger.error(f"❌ Error updating account balance: {str(e)}")
    
    def set_test_balance(self, balance: float):
        """Set test balance for simulation mode"""
        self._test_balance = balance
        if hasattr(self, 'risk_manager'):
            self.risk_manager.current_balance = balance
            self.risk_manager.initial_balance = balance
            self.logger.info(f"💰 Test balance set: ${balance:.2f}")
    
    
    def _normalize_signal_type_string(self, action) -> str:
        """Normalize signal type to lowercase string"""
        from ..utils.signal_structures import normalize_action_string
        return normalize_action_string(action)
    
    def _extract_recommendation_data(self, recommendation: Dict) -> Dict:
        """
        Extract recommendation data, handling both standardized and legacy formats
        """
        # Check if standardized format is available
        if 'standardized' in recommendation:
            std_rec = recommendation['standardized']
            return {
                'action': std_rec.action,
                'entry_timeframe': std_rec.entry_timeframe,
                'strength_factors': std_rec.strength_factors,
                'confidence': std_rec.confidence,
                'strength_score': std_rec.strength_score,
                'confluence_score': std_rec.confluence_score,
                'entry_details': {
                    'entry_price': std_rec.entry_details.entry_price,
                    'stop_loss': std_rec.entry_details.stop_loss,
                    'take_profit': std_rec.entry_details.take_profit,
                    'risk_reward_ratio': std_rec.entry_details.risk_reward_ratio,
                    'confluence_factors': std_rec.entry_details.confluence_factors
                },
                'trend_direction': std_rec.trend_direction,
                'is_valid': std_rec.is_valid,
                'trend_aligned': std_rec.trend_aligned,
                'signal_confluence': std_rec.signal_confluence
            }
        
        # Fall back to legacy format
        return {
            'action': recommendation.get('action', 'WAIT'),
            'entry_timeframe': recommendation.get('entry_timeframe', 'UNKNOWN'),
            'strength_factors': recommendation.get('strength_factors', []),
            'confidence': recommendation.get('confidence', 'LOW'),
            'strength_score': recommendation.get('strength_score', 0),
            'confluence_score': recommendation.get('confluence_score', 0),
            'entry_details': recommendation.get('entry_details', {}),
            'trend_direction': recommendation.get('trend_direction', 'UNKNOWN'),
            'market_bias': recommendation.get('market_bias', 'NEUTRAL'),  # CRITICAL FIX: Include market bias
            'is_valid': True,  # Default for legacy
            'trend_aligned': recommendation.get('trend_direction') != 'CONSOLIDATION',
            'signal_confluence': recommendation.get('signal_confluence', {})  # CRITICAL FIX: Get actual dictionary, not boolean
        }
    
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
            
            # Sync existing MT5 positions with risk manager
            self._sync_existing_positions()
            
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
            self.logger.info(f"🔍 Starting main loop - running: {self.running}, shutdown: {self.shutdown_event.is_set()}")
            while self.running and not self.shutdown_event.is_set():
                self.logger.debug(f"🔄 Main loop iteration - running: {self.running}, shutdown: {self.shutdown_event.is_set()}")
                try:
                    # Reset daily trade count if new day
                    current_date = datetime.now().date()
                    if current_date != self.last_trade_date:
                        self.daily_trade_count = 0
                        self.last_trade_date = current_date
                        self.logger.info(f"📅 New trading day: {current_date}")
                    
                    # Check if daily limit reached
                    if self.daily_trade_count >= self.execution_settings.max_daily_trades:
                        self.logger.info(f"⏹️ Daily trade limit reached ({self.daily_trade_count}) - continuing monitoring only")
                        
                        # Still monitor existing positions even if trade limit reached
                        self._manage_open_positions()
                        
                        # Wait for next interval then continue monitoring
                        self.logger.info(f"⏳ Waiting {self.execution_settings.refresh_interval_seconds}s before next monitoring cycle...")
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
            # === FIX: Update account balance before every scan ===
            self._update_account_balance()
            
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
                    
                    # Extract recommendation data using standardized method
                    rec_data = self._extract_recommendation_data(recommendation)
                    
                    # Create signal data for logging
                    signal_data = {
                        'symbol': symbol,
                        'timeframe': rec_data['entry_timeframe'],
                        'signal_type': rec_data['action'],
                        'signal_strength': rec_data['strength_factors'],
                        'confidence': rec_data['confidence'],
                        'confluence_score': rec_data['strength_score'],
                        'entry_price': rec_data['entry_details'].get('entry_price', 0),
                        'stop_loss': rec_data['entry_details'].get('stop_loss', 0),
                        'take_profit': rec_data['entry_details'].get('take_profit', 0),
                        'risk_reward_ratio': rec_data['entry_details'].get('risk_reward_ratio', 0),
                        'notes': f"Trend: {rec_data['trend_direction']}"
                    }
                    
                    # Log the signal
                    self.logger.log_signal(signal_data)
                    self.session_stats['signals_generated'] += 1
                    
                    # Check if we should execute the trade
                    if self._should_execute_trade(opp):
                        if self.execution_settings.enable_execution:
                            # Pass the full opportunity dictionary
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
        Determine if a trade should be executed based on risk and quality rules.
        This now delegates to the RiskManager and EnhancedSignalQualityFilter.
        """
        try:
            symbol = opportunity['symbol']
            recommendation = opportunity.get('recommendation', {})
            
            # Check minimum account balance first
            if self.risk_manager.current_balance < self.execution_settings.min_account_balance:
                self.logger.error(f"❌ {symbol}: Account balance (${self.risk_manager.current_balance:.2f}) below minimum (${self.execution_settings.min_account_balance:.2f})")
                return False
            
            # Extract recommendation data using standardized method
            rec_data = self._extract_recommendation_data(recommendation)
            entry_details = rec_data['entry_details']
            
            # CRITICAL FIX: Validate signal makes logical sense before execution
            action_str = str(rec_data['action']).upper()
            trend_direction = str(rec_data.get('trend_direction', '')).upper()
            
            # Emergency validation: Don't take BUY signals in DOWNTREND or SELL signals in UPTREND
            if 'BUY' in action_str and 'DOWNTREND' in trend_direction:
                self.logger.error(f"🚨 {symbol}: CRITICAL ERROR - BUY signal in DOWNTREND - BLOCKING TRADE")
                return False
            if 'SELL' in action_str and 'UPTREND' in trend_direction:
                self.logger.error(f"🚨 {symbol}: CRITICAL ERROR - SELL signal in UPTREND - BLOCKING TRADE")
                return False

            # Create a signal object compatible with the quality filter
            from ..utils.signal_structures import create_quality_filter_input_legacy
            signal_for_quality_check = create_quality_filter_input_legacy(symbol, rec_data)

            # 1. Check Quality Filter
            should_execute, quality_reason = self.quality_filter.should_execute_signal(signal_for_quality_check)
            if not should_execute:
                self.logger.info(f"🚫 {symbol}: REJECTED by Quality Filter - {quality_reason}")
                return False

            # 2. Check Risk Manager
            can_trade, risk_reason = self.risk_manager.can_trade(symbol)
            if not can_trade:
                self.logger.info(f"🚫 {symbol}: REJECTED by Risk Manager - {risk_reason}")
                return False

            # 3. Check for duplicate signals (final check)
            signal_id = f"{symbol}_{rec_data.get('entry_timeframe', '')}_{rec_data.get('action', '')}_{entry_details.get('entry_price', 0)}"
            if signal_id in self.processed_signals:
                self.logger.debug(f"🚫 {symbol}: Signal already processed")
                return False
            
            self.logger.info(f"✅ {symbol}: PASSED all checks (Quality & Risk).")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in _should_execute_trade: {str(e)}")
            return False
    
    def _execute_trade(self, opportunity: Dict) -> bool:
        """
        Execute a trade based on opportunity, now using the Risk Manager for position sizing.
        
        Args:
            opportunity: Trading opportunity data
            
        Returns:
            bool: True if trade executed successfully
        """
        try:
            symbol = opportunity['symbol']
            recommendation = opportunity['recommendation']
            entry_details = recommendation.get('entry_details', {})
            setup_type = recommendation.get('setup_type', 'pullback')  # Added setup type detection
            
            action_enum = recommendation.get('action')
            self.logger.debug(f"🔍 {symbol}: Raw action_enum: {action_enum} (type: {type(action_enum)})")
            action = action_enum.value if hasattr(action_enum, 'value') else str(action_enum).upper()
            self.logger.debug(f"🔍 {symbol}: Action after extraction: '{action}'")
            if action.startswith('SIGNALTYPE.'):
                action = action.replace('SIGNALTYPE.', '')
                self.logger.debug(f"🔍 {symbol}: Action after cleanup: '{action}'")
            # Ensure action is always uppercase for validation
            action = action.upper()
            self.logger.debug(f"🔍 {symbol}: Final action: '{action}'")
            entry_price = entry_details.get('entry_price', 0)
            stop_loss = entry_details.get('stop_loss', 0)
            take_profit = entry_details.get('take_profit', 0)
            
            # CRITICAL: Validate signal direction consistency before execution
            if not self._validate_signal_direction_consistency(symbol, action, entry_price, stop_loss, take_profit):
                self.logger.error(f"🚨 {symbol}: Signal direction validation failed - REJECTING TRADE")
                return False
                
            # ADDITIONAL CRITICAL CHECK: Validate R:R makes sense
            if action.upper() == 'BUY':
                actual_risk = entry_price - stop_loss
                actual_reward = take_profit - entry_price
            else:
                actual_risk = stop_loss - entry_price  
                actual_reward = entry_price - take_profit
                
            if actual_risk <= 0 or actual_reward <= 0:
                self.logger.error(f"🚨 {symbol}: Invalid risk/reward - Risk: {actual_risk:.5f}, Reward: {actual_reward:.5f}")
                return False
                
            actual_rr = actual_reward / actual_risk
            if actual_rr < 1.5:
                self.logger.error(f"🚨 {symbol}: Poor R:R ratio {actual_rr:.2f} - REJECTING TRADE")
                return False
            
            # Validate and adjust stop levels for broker requirements
            self.logger.debug(f"🔍 {symbol}: Validating stops - Entry: {entry_price:.5f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}")
            adjusted_sl, adjusted_tp = self._validate_stop_levels(symbol, entry_price, stop_loss, take_profit, action)
            
            if adjusted_sl is None or adjusted_tp is None:
                self.logger.error(f"❌ {symbol}: Cannot adjust stop levels to meet broker requirements")
                return False
            
            # Log adjustments if made
            if abs(adjusted_sl - stop_loss) > 0.00001:
                self.logger.warning(f"⚠️ {symbol}: Stop loss adjusted from {stop_loss:.5f} to {adjusted_sl:.5f}")
            if abs(adjusted_tp - take_profit) > 0.00001:
                self.logger.warning(f"⚠️ {symbol}: Take profit adjusted from {take_profit:.5f} to {adjusted_tp:.5f}")
            
            # CRITICAL: Validate R:R after adjustments to ensure trade remains profitable
            adjusted_risk = abs(entry_price - adjusted_sl)
            adjusted_reward = abs(adjusted_tp - entry_price)
            adjusted_rr = adjusted_reward / adjusted_risk if adjusted_risk > 0 else 0
            
            if adjusted_rr < 2.0:  # Minimum 1:2 R:R after adjustments
                self.logger.error(f"❌ {symbol}: Adjusted R:R ({adjusted_rr:.2f}) below minimum (2.0) - REJECTING TRADE")
                self.logger.error(f"   Original R:R was likely better but broker adjustments made it unprofitable")
                return False
            
            self.logger.info(f"✅ {symbol}: Adjusted R:R: {adjusted_rr:.2f} (Risk: {adjusted_risk:.5f}, Reward: {adjusted_reward:.5f})")
            self.logger.debug(f"✅ {symbol}: Final stops - SL: {adjusted_sl:.5f}, TP: {adjusted_tp:.5f}")
            
            # == STRATEGIC REFACTOR: Use Risk Manager for Position Sizing ==
            volume, position_risk = self.risk_manager.calculate_position_size(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=adjusted_sl
            )
            
            if volume <= 0:
                self.logger.error(f"❌ {symbol}: Invalid position size calculated by Risk Manager.")
                return False
            
            # Always use the signal's exact entry price - this is key!
            # Use market orders to execute immediately (after our fixes)
            action_str = str(action).upper()
            if MT5_AVAILABLE:
                # Get symbol info for digits and other properties
                symbol_info = mt5.symbol_info(symbol)
                if not symbol_info:
                    self.logger.error(f"❌ {symbol}: Cannot get symbol info")
                    return False
                    
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    self.logger.error(f"❌ {symbol}: Cannot get current tick data")
                    return False
                
                current_bid = tick.bid
                current_ask = tick.ask
                
                self.logger.info(f"🎯 {symbol}: Signal entry: {entry_price:.5f}, Market - Bid: {current_bid:.5f}, Ask: {current_ask:.5f}")
                
                # CRITICAL FIX: Final entry price sanity check
                spread = current_ask - current_bid
                if 'BUY' in action_str:
                    price_diff = abs(entry_price - current_ask)
                    if price_diff > spread * 5:  # Entry price more than 5 spreads away
                        self.logger.warning(f"⚠️ {symbol}: BUY entry {entry_price:.5f} far from ask {current_ask:.5f} (diff: {price_diff:.5f})")
                else:
                    price_diff = abs(entry_price - current_bid)
                    if price_diff > spread * 5:  # Entry price more than 5 spreads away
                        self.logger.warning(f"⚠️ {symbol}: SELL entry {entry_price:.5f} far from bid {current_bid:.5f} (diff: {price_diff:.5f})")
                
                # CRITICAL FIX: Use market orders to execute at exact SMC entry prices
                # SMC analysis provides precise entry points - we should respect them
                # Use the calculated SMC entry price, not market price
                price = entry_price
                
                # Determine if we should use market order (price very close) or pending order
                price_diff_pips = abs(entry_price - (current_ask if 'BUY' in action_str else current_bid)) * (10000 if symbol_info.digits == 5 else 1000)
                
                if price_diff_pips <= 2.0:  # If SMC entry is within 2 pips of current price
                    # Use market order for immediate execution
                    if 'BUY' in action_str:
                        order_type = mt5.ORDER_TYPE_BUY
                        action_type = mt5.TRADE_ACTION_DEAL
                        price = current_ask  # Market orders need current market price
                        self.logger.info(f"📤 {symbol}: BUY MARKET order (SMC entry {entry_price:.5f} within 2 pips of market {current_ask:.5f})")
                    elif 'SELL' in action_str:
                        order_type = mt5.ORDER_TYPE_SELL
                        action_type = mt5.TRADE_ACTION_DEAL
                        price = current_bid  # Market orders need current market price
                        self.logger.info(f"📤 {symbol}: SELL MARKET order (SMC entry {entry_price:.5f} within 2 pips of market {current_bid:.5f})")
                else:
                    # Use pending order at exact SMC entry price
                    if 'BUY' in action_str:
                        if entry_price > current_ask:
                            order_type = mt5.ORDER_TYPE_BUY_STOP  # Buy when price goes up to entry
                        else:
                            order_type = mt5.ORDER_TYPE_BUY_LIMIT  # Buy when price comes down to entry
                        action_type = mt5.TRADE_ACTION_PENDING
                        price = entry_price  # Use exact SMC entry price
                        self.logger.info(f"📤 {symbol}: BUY {'STOP' if entry_price > current_ask else 'LIMIT'} order at SMC entry {entry_price:.5f} (market: {current_ask:.5f})")
                    elif 'SELL' in action_str:
                        if entry_price < current_bid:
                            order_type = mt5.ORDER_TYPE_SELL_STOP  # Sell when price goes down to entry
                        else:
                            order_type = mt5.ORDER_TYPE_SELL_LIMIT  # Sell when price comes up to entry
                        action_type = mt5.TRADE_ACTION_PENDING
                        price = entry_price  # Use exact SMC entry price
                        self.logger.info(f"📤 {symbol}: SELL {'STOP' if entry_price < current_bid else 'LIMIT'} order at SMC entry {entry_price:.5f} (market: {current_bid:.5f})")
                    else:
                        self.logger.error(f"❌ {symbol}: Invalid action {action}")
                        return False
                    
                # Set appropriate filling mode based on order type
                if action_type == mt5.TRADE_ACTION_DEAL:
                    filling_mode = mt5.ORDER_FILLING_FOK  # Market orders
                else:
                    filling_mode = mt5.ORDER_FILLING_RETURN  # Pending orders
                
            else:
                # Fallback for testing without MT5
                if 'BUY' in action_str:
                    order_type = 'BUY'
                elif 'SELL' in action_str:
                    order_type = 'SELL'
                else:
                    self.logger.error(f"❌ {symbol}: Invalid action {action}")
                    return False
                
                price = entry_price
                action_type = "PENDING"
                filling_mode = "FOK"

            request = {
                "action": action_type,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": adjusted_sl,
                "tp": adjusted_tp,
                "deviation": int(self.execution_settings.slippage_pips * 10),
                "magic": self.execution_settings.magic_number,
                "comment": f"SMC_{action}_{datetime.now().strftime('%H%M%S')}",
                "type_time": mt5.ORDER_TIME_GTC if MT5_AVAILABLE else "GTC",
                "type_filling": filling_mode,
            }
            
            # Send order
            if MT5_AVAILABLE:
                order_description = "pending" if action_type == mt5.TRADE_ACTION_PENDING else "market"
            else:
                order_description = "pending"  # All orders use signal entry prices
                
            self.logger.info(f"📤 Executing {order_description} {action} order for {symbol}: "
                           f"{volume} lots @ {price:.5f} (SL: {adjusted_sl:.5f}, TP: {adjusted_tp:.5f})")
            
            # Debug: Log the exact request being sent
            if MT5_AVAILABLE:
                self.logger.debug(f"🔍 {symbol}: Order request - Action: {action_type}, Type: {order_type}, Volume: {volume}, "
                                f"Price: {price:.5f}, SL: {adjusted_sl:.5f}, TP: {adjusted_tp:.5f}, "
                                f"Deviation: {int(self.execution_settings.slippage_pips * 10)}")
            else:
                self.logger.debug(f"🔍 {symbol}: Order request - Action: {action_type}, Volume: {volume}, "
                                f"Price: {price:.5f}, SL: {adjusted_sl:.5f}, TP: {adjusted_tp:.5f}")
            
            if MT5_AVAILABLE:
                # Validate symbol is available and tradeable
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    self.logger.warning(f"⚠️ {symbol}: Symbol not available on this broker - skipping")
                    return False
                    
                if not symbol_info.visible:
                    # Try to enable symbol in Market Watch
                    if not mt5.symbol_select(symbol, True):
                        self.logger.warning(f"⚠️ {symbol}: Cannot enable symbol in Market Watch - skipping")
                        return False
                
                # Check trading session and minimum volume
                if hasattr(symbol_info, 'volume_min') and volume < symbol_info.volume_min:
                    self.logger.warning(f"⚠️ {symbol}: Volume {volume:.2f} below minimum {symbol_info.volume_min:.2f} - adjusting")
                    volume = symbol_info.volume_min
                    request['volume'] = volume
                
                # Check MT5 connection status before sending order
                account_info = mt5.account_info()
                if account_info is None:
                    self.logger.error(f"❌ {symbol}: MT5 connection lost - reinitializing...")
                    if not mt5.initialize():
                        self.logger.error(f"❌ {symbol}: Failed to reinitialize MT5")
                        return False
                
                result = mt5.order_send(request)
                
                if result is None:
                    self.logger.error(f"❌ {symbol}: Order send failed - No response from MT5")
                    self.logger.error(f"❌ {symbol}: MT5 last error: {mt5.last_error()}")
                    return False
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    # Get error description
                    error_desc = {
                        mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stops",
                        mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume", 
                        mt5.TRADE_RETCODE_MARKET_CLOSED: "Market closed",
                        mt5.TRADE_RETCODE_NO_MONEY: "Insufficient funds",
                        mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
                        mt5.TRADE_RETCODE_REQUOTE: "Requote",
                        mt5.TRADE_RETCODE_REJECT: "Request rejected",
                        mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
                        mt5.TRADE_RETCODE_INVALID_FILL: "Invalid fill",
                        mt5.TRADE_RETCODE_TOO_MANY_REQUESTS: "Too many requests"
                    }.get(result.retcode, f"Unknown error {result.retcode}")
                    
                    self.logger.error(f"❌ {symbol}: Order failed - {error_desc} (Code: {result.retcode})")
                    return False
                
                # Success - all orders are now pending orders using signal prices
                self.logger.info(f"✅ {symbol}: Pending order placed - Order: {result.order}, will execute at signal price {price:.5f}")
                
                # == STRATEGIC REFACTOR: Add position to Risk Manager ==
                self.risk_manager.add_position(position_risk)
                self.processed_signals.add(f"{symbol}_{recommendation.get('entry_timeframe', '')}_{action}_{entry_price}")

                # Update trade tracking
                self.daily_trade_count += 1
                self.session_stats['signals_executed'] += 1
                
                return True
            
            if MT5_AVAILABLE:
                # Check MT5 connection status before sending order
                account_info = mt5.account_info()
                if account_info is None:
                    self.logger.error(f"❌ {symbol}: MT5 connection lost - reinitializing...")
                    if not mt5.initialize():
                        self.logger.error(f"❌ {symbol}: Failed to reinitialize MT5")
                        return False
                
                result = mt5.order_send(request)
                
                if result is None:
                    self.logger.error(f"❌ {symbol}: Order send failed - No response from MT5")
                    self.logger.error(f"❌ {symbol}: MT5 last error: {mt5.last_error()}")
                    return False
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    # Get error description
                    error_desc = {
                        mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stops",
                        mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume", 
                        mt5.TRADE_RETCODE_MARKET_CLOSED: "Market closed",
                        mt5.TRADE_RETCODE_NO_MONEY: "Insufficient funds",
                        mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
                        mt5.TRADE_RETCODE_REQUOTE: "Requote",
                        mt5.TRADE_RETCODE_REJECT: "Request rejected",
                        mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
                        mt5.TRADE_RETCODE_INVALID_FILL: "Invalid fill",
                        mt5.TRADE_RETCODE_TOO_MANY_REQUESTS: "Too many requests"
                    }.get(result.retcode, f"Unknown error {result.retcode}")
                    
                    self.logger.error(f"❌ {symbol}: Order failed - {error_desc} (Code: {result.retcode})")
                    if hasattr(result, 'comment'):
                        self.logger.error(f"❌ {symbol}: MT5 Comment: {result.comment}")
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
                
                # == STRATEGIC REFACTOR: Add position to Risk Manager ==
                self.risk_manager.add_position(position_risk)
                self.processed_signals.add(f"{symbol}_{recommendation.get('entry_timeframe', '')}_{action}_{entry_price}")

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
    
    def _validate_signal_direction_consistency(self, symbol: str, action: str, 
                                             entry_price: float, stop_loss: float, 
                                             take_profit: float) -> bool:
        """
        Critical validation to ensure signal direction consistency at execution level.
        This is a final safety check to prevent trading signals with incorrect directions.
        
        Args:
            symbol: Trading symbol
            action: BUY or SELL action
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            bool: True if signal direction is valid, False otherwise
        """
        try:
            self.logger.debug(f"🔍 {symbol}: Final direction validation for {action}")
            self.logger.debug(f"   Entry: {entry_price:.5f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}")
            
            if action == 'BUY':
                # For BUY trades:
                # - Stop loss MUST be below entry price
                # - Take profit MUST be above entry price
                
                if stop_loss >= entry_price:
                    self.logger.error(f"🚨 {symbol}: BUY execution blocked - SL {stop_loss:.5f} not below entry {entry_price:.5f}")
                    return False
                    
                if take_profit <= entry_price:
                    self.logger.error(f"🚨 {symbol}: BUY execution blocked - TP {take_profit:.5f} not above entry {entry_price:.5f}")
                    return False
                    
                self.logger.debug(f"✅ {symbol}: BUY signal direction valid for execution")
                return True
                
            elif action == 'SELL':
                # For SELL trades:
                # - Stop loss MUST be above entry price
                # - Take profit MUST be below entry price
                
                if stop_loss <= entry_price:
                    self.logger.error(f"🚨 {symbol}: SELL execution blocked - SL {stop_loss:.5f} not above entry {entry_price:.5f}")
                    return False
                    
                if take_profit >= entry_price:
                    self.logger.error(f"🚨 {symbol}: SELL execution blocked - TP {take_profit:.5f} not below entry {entry_price:.5f}")
                    return False
                    
                self.logger.debug(f"✅ {symbol}: SELL signal direction valid for execution")
                return True
                
            else:
                self.logger.error(f"🚨 {symbol}: Unknown action '{action}' - execution blocked")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {symbol}: Error in direction validation: {e}")
            return False

    def _validate_stop_levels(self, symbol: str, entry_price: float, 
                             stop_loss: float, take_profit: float, action: str) -> tuple:
        """
        Validate and adjust stop loss and take profit levels for broker requirements
        
        Args:
            symbol: Currency pair
            entry_price: Entry price
            stop_loss: Original stop loss
            take_profit: Original take profit
            action: Trade action (BUY/SELL)
            
        Returns:
            tuple: (adjusted_stop_loss, adjusted_take_profit) or (None, None) if invalid
        """
        try:
            # Get symbol info from MT5 if available
            if MT5_AVAILABLE:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    min_stop_level = symbol_info.trade_stops_level
                    point = symbol_info.point
                    
                    # If broker has no minimum stop level requirement, validate basic logic but don't enforce artificial minimums
                    if min_stop_level == 0:
                        self.logger.debug(f"📋 {symbol}: Broker has no minimum stop distance - validating basic logic only")
                        
                        # Still validate basic order logic (SL/TP direction)
                        if action.upper() == 'BUY':
                            if stop_loss >= entry_price:
                                self.logger.error(f"❌ {symbol}: Invalid SL for BUY - SL ({stop_loss:.5f}) must be below entry ({entry_price:.5f})")
                                return None, None
                            if take_profit <= entry_price:
                                self.logger.error(f"❌ {symbol}: Invalid TP for BUY - TP ({take_profit:.5f}) must be above entry ({entry_price:.5f})")
                                return None, None
                        else:  # SELL
                            if stop_loss <= entry_price:
                                self.logger.error(f"❌ {symbol}: Invalid SL for SELL - SL ({stop_loss:.5f}) must be above entry ({entry_price:.5f})")
                                return None, None
                            if take_profit >= entry_price:
                                self.logger.error(f"❌ {symbol}: Invalid TP for SELL - TP ({take_profit:.5f}) must be below entry ({entry_price:.5f})")
                                return None, None
                        
                        # Return original levels unchanged - broker allows any distance
                        return stop_loss, take_profit
                else:
                    # Fallback defaults when symbol info unavailable
                    min_stop_level = 10  # 10 points minimum
                    point = 0.0001 if 'JPY' not in symbol else 0.01
            else:
                # Conservative minimum distances for mock mode
                if 'JPY' in symbol:
                    min_stop_level = 100  # 10.0 pips for JPY pairs
                    point = 0.01
                else:
                    min_stop_level = 100  # 10.0 pips for major pairs
                    point = 0.0001
            
            # Convert minimum distance to price
            min_distance = min_stop_level * point
            
            # Validate and adjust stop loss
            if action.upper() == 'BUY':
                # For BUY: SL must be below entry, TP must be above entry
                if stop_loss >= entry_price:
                    self.logger.error(f"❌ {symbol}: Invalid SL for BUY - SL must be below entry")
                    return None, None
                
                # Ensure minimum distance
                min_sl = entry_price - min_distance
                adjusted_sl = min(stop_loss, min_sl)
                
                # Validate take profit
                if take_profit <= entry_price:
                    self.logger.error(f"❌ {symbol}: Invalid TP for BUY - TP must be above entry")
                    return None, None
                
                min_tp = entry_price + min_distance
                adjusted_tp = max(take_profit, min_tp)
                
            else:  # SELL
                # For SELL: SL must be above entry, TP must be below entry
                if stop_loss <= entry_price:
                    self.logger.error(f"❌ {symbol}: Invalid SL for SELL - SL must be above entry")
                    return None, None
                
                # Ensure minimum distance
                min_sl = entry_price + min_distance
                adjusted_sl = max(stop_loss, min_sl)
                
                # Validate take profit
                if take_profit >= entry_price:
                    self.logger.error(f"❌ {symbol}: Invalid TP for SELL - TP must be below entry")
                    return None, None
                
                min_tp = entry_price - min_distance
                adjusted_tp = min(take_profit, min_tp)
            
            # Validate risk/reward ratio after adjustments
            risk = abs(entry_price - adjusted_sl)
            reward = abs(adjusted_tp - entry_price)
            
            if risk <= 0 or reward <= 0:
                self.logger.error(f"❌ {symbol}: Invalid risk/reward after adjustment")
                return None, None
            
            rr_ratio = reward / risk
            if rr_ratio < 1.0:  # Minimum 1:1 ratio
                self.logger.warning(f"⚠️ {symbol}: R:R ratio {rr_ratio:.2f} below 1:1 after adjustment")
            
            self.logger.debug(f"✅ {symbol}: Stop levels validated - SL: {adjusted_sl:.5f}, TP: {adjusted_tp:.5f}, R:R: {rr_ratio:.2f}")
            
            return adjusted_sl, adjusted_tp
            
        except Exception as e:
            self.logger.error(f"❌ Error validating stop levels for {symbol}: {str(e)}")
            return None, None

    def _calculate_position_size(self, symbol: str, entry_price: float, 
                               stop_loss: float) -> float:
        """
        DEPRECATED: Position sizing is now handled by the RiskManager.
        This method is kept for potential fallback or debugging.
        
        Args:
            symbol: Currency pair
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            float: Position size in lots
        """
        try:
            self.logger.warning("Deprecated: _calculate_position_size should not be called directly. Use RiskManager.")
            
            # Fallback to minimum size for safety if ever called
            return 0.01
            
        except Exception as e:
            self.logger.error(f"❌ Error in deprecated _calculate_position_size: {str(e)}")
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
            next_scan_time = datetime.now() + timedelta(seconds=self.execution_settings.refresh_interval_seconds)
            self.logger.info(f"⏳ Waiting {self.execution_settings.refresh_interval_seconds}s for next scan (next: {next_scan_time.strftime('%H:%M:%S')})...")
            
            # Wait in small chunks to allow for graceful shutdown
            wait_time = self.execution_settings.refresh_interval_seconds
            chunk_size = 10  # 10 second chunks for better responsiveness
            chunks_waited = 0
            total_chunks = wait_time // chunk_size
            
            while wait_time > 0 and not self.shutdown_event.is_set():
                sleep_time = min(chunk_size, wait_time)
                time.sleep(sleep_time)
                wait_time -= sleep_time
                chunks_waited += 1
                
                # Log progress every 30 seconds during longer waits
                if chunks_waited % 3 == 0 and wait_time > 30:
                    remaining_minutes = wait_time // 60
                    self.logger.debug(f"⏳ Still waiting... {remaining_minutes}m {wait_time % 60}s remaining")
            
            if not self.shutdown_event.is_set():
                self.logger.info(f"⏰ Wait completed - resuming monitoring cycle")
                
        except Exception as e:
            self.logger.error(f"❌ Error in wait interval: {str(e)}")
    
    def _sync_existing_positions(self):
        """Sync existing MT5 positions with risk manager at startup"""
        try:
            self.logger.info("🔄 Syncing existing MT5 positions with risk manager...")
            
            # Get current account balance and recreate risk manager with correct limits
            account_info = mt5.account_info()
            if account_info:
                from smc_forez.risk_management.risk_manager import create_risk_manager
                self.risk_manager = create_risk_manager("aggressive", account_info.balance)
                self.logger.info(f"📊 Risk manager updated with balance ${account_info.balance:.2f}")
                self.logger.info(f"📈 Max portfolio risk: {self.risk_manager.max_portfolio_risk*100:.1f}%")
                self.logger.info(f"📈 Max positions: {self.risk_manager.risk_params[self.risk_manager.risk_level]['max_positions']}")
            
            # Get current MT5 positions
            positions = mt5.positions_get()
            if not positions:
                self.logger.info("📊 No existing MT5 positions found")
                return
            
            synced_count = 0
            for position in positions:
                try:
                    symbol = position.symbol
                    
                    # Get symbol info for calculations
                    symbol_info = mt5.symbol_info(symbol)
                    if not symbol_info:
                        self.logger.warning(f"⚠️ Cannot get info for {symbol}, skipping position sync")
                        continue
                    
                    # Calculate realistic position risk percentage
                    # Since we don't have the original stop loss, estimate risk based on typical SMC risk (1-2%)
                    # This is much more realistic than using full notional value
                    account_info = mt5.account_info()
                    
                    # Estimate risk based on position size
                    # For micro accounts: 1.0 lot ≈ 1.5% risk, 0.5 lot ≈ 0.75% risk
                    estimated_risk_per_lot = 0.015  # 1.5% per standard lot
                    risk_percentage = position.volume * estimated_risk_per_lot
                    
                    # Create PositionRisk object
                    from smc_forez.risk_management.risk_manager import PositionRisk
                    risk_amount = account_info.balance * risk_percentage  # Convert percentage to dollar amount
                    position_risk = PositionRisk(
                        symbol=symbol,
                        position_size=position.volume,
                        risk_amount=risk_amount,
                        risk_percentage=risk_percentage,
                        stop_distance_pips=100.0,  # Default estimate
                        correlation_factor=1.0  # Default
                    )
                    
                    # Add to risk manager
                    self.risk_manager.add_position(position_risk)
                    synced_count += 1
                    
                    self.logger.info(f"✅ Synced {symbol}: {position.volume} lots, Risk: {risk_percentage*100:.2f}%")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error syncing position {position.symbol}: {str(e)}")
                    continue
            
            self.logger.info(f"📊 Successfully synced {synced_count} positions with risk manager")
            
            # Log current portfolio risk
            current_risk = sum(pos.risk_percentage for pos in self.risk_manager.open_positions.values())
            self.logger.info(f"📈 Current portfolio risk: {current_risk*100:.2f}% (Max: {self.risk_manager.max_portfolio_risk*100:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing existing positions: {str(e)}")
    
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
            "EURUSDm", "GBPUSDm", "USDJPYm", "AUDUSDm", "USDCADm", "USDCHFm",
            "NZDUSDm", "EURJPYm", "GBPJPYm", "AUDJPYm", "EURGBPm", "EURAUDm"
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