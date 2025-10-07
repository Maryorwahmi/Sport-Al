"""
Enhanced logging system for SMC Forez
Provides structured logging with multiple outputs and performance tracking
"""
import logging
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import sys
import os


@dataclass
class TradeLog:
    """Structure for trade logging"""
    timestamp: str
    symbol: str
    action: str
    entry_price: float
    exit_price: Optional[float] = None
    size: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: Optional[float] = None
    pips: Optional[float] = None
    status: str = 'OPEN'
    trade_id: Optional[str] = None


@dataclass
class SignalLog:
    """Structure for signal logging"""
    timestamp: str
    symbol: str
    timeframe: str
    signal_type: str
    strength: str
    confidence: str
    confluence_score: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    executed: bool = False
    notes: Optional[str] = None


@dataclass
class SessionReport:
    """Structure for session reporting"""
    session_start: str
    session_end: Optional[str] = None
    total_signals: int = 0
    executed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_pips: float = 0.0
    max_drawdown: float = 0.0
    symbols_analyzed: List[str] = None
    errors_count: int = 0
    uptime_minutes: float = 0.0


class SMCLogger:
    """
    Professional logging system for SMC Forez with multiple output formats
    """
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Initialize the logging system
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Session tracking
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        # Data storage
        self.trade_logs: List[TradeLog] = []
        self.signal_logs: List[SignalLog] = []
        self.session_report = SessionReport(
            session_start=self.session_start.isoformat(),
            symbols_analyzed=[]
        )
        
        # Setup logging
        self._setup_logging(log_level)
        
        # File paths
        self.trades_csv = self.log_dir / f"trades_{self.session_id}.csv"
        self.signals_csv = self.log_dir / f"signals_{self.session_id}.csv"
        self.session_json = self.log_dir / f"session_{self.session_id}.json"
        
        self.logger.info("🚀 SMC Forez Logger initialized")
        self.logger.info(f"📁 Log directory: {self.log_dir.absolute()}")
        self.logger.info(f"🆔 Session ID: {self.session_id}")
    
    def _setup_logging(self, log_level: str):
        """Setup structured logging with multiple handlers"""
        
        # Create logger
        self.logger = logging.getLogger('SMCForez')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Console formatter with colors
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File formatter with more detail
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Main log file handler
        main_log_file = self.log_dir / f"main_{self.session_id}.log"
        file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Error log file handler
        error_log_file = self.log_dir / f"errors_{self.session_id}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setFormatter(file_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        self.session_report.errors_count += 1
    
    def log_signal(self, signal_data: Dict):
        """
        Log a trading signal
        
        Args:
            signal_data: Signal information dictionary
        """
        try:
            signal_log = SignalLog(
                timestamp=datetime.now().isoformat(),
                symbol=signal_data.get('symbol', 'UNKNOWN'),
                timeframe=signal_data.get('timeframe', 'UNKNOWN'),
                signal_type=str(signal_data.get('signal_type', 'UNKNOWN')),
                strength=str(signal_data.get('signal_strength', 'UNKNOWN')),
                confidence=str(signal_data.get('confidence', 'UNKNOWN')),
                confluence_score=signal_data.get('confluence_score', 0.0),
                entry_price=signal_data.get('entry_price', 0.0),
                stop_loss=signal_data.get('stop_loss', 0.0),
                take_profit=signal_data.get('take_profit', 0.0),
                risk_reward_ratio=signal_data.get('risk_reward_ratio', 0.0),
                executed=signal_data.get('executed', False),
                notes=signal_data.get('notes', '')
            )
            
            self.signal_logs.append(signal_log)
            self.session_report.total_signals += 1
            
            # Add symbol to analyzed list
            symbol = signal_data.get('symbol', 'UNKNOWN')
            if symbol not in self.session_report.symbols_analyzed:
                self.session_report.symbols_analyzed.append(symbol)
            
            self.info(f"📡 SIGNAL: {signal_log.symbol} {signal_log.signal_type} "
                     f"@{signal_log.entry_price:.5f} | Confidence: {signal_log.confidence} "
                     f"| R:R {signal_log.risk_reward_ratio:.2f}")
            
            # Save to CSV
            self._save_signals_csv()
            
        except Exception as e:
            self.error(f"Error logging signal: {str(e)}")
    
    def log_trade(self, trade_data: Dict):
        """
        Log a trade execution
        
        Args:
            trade_data: Trade information dictionary
        """
        try:
            trade_log = TradeLog(
                timestamp=datetime.now().isoformat(),
                symbol=trade_data.get('symbol', 'UNKNOWN'),
                action=trade_data.get('action', 'UNKNOWN'),
                entry_price=trade_data.get('entry_price', 0.0),
                exit_price=trade_data.get('exit_price'),
                size=trade_data.get('size', 0.0),
                stop_loss=trade_data.get('stop_loss'),
                take_profit=trade_data.get('take_profit'),
                pnl=trade_data.get('pnl'),
                pips=trade_data.get('pips'),
                status=trade_data.get('status', 'OPEN'),
                trade_id=trade_data.get('trade_id')
            )
            
            self.trade_logs.append(trade_log)
            
            if trade_log.status == 'OPEN':
                self.session_report.executed_trades += 1
                self.info(f"💼 TRADE OPENED: {trade_log.symbol} {trade_log.action} "
                         f"{trade_log.size} lots @{trade_log.entry_price:.5f}")
            
            elif trade_log.status == 'CLOSED':
                if trade_log.pnl and trade_log.pnl > 0:
                    self.session_report.winning_trades += 1
                    self.info(f"✅ TRADE CLOSED: {trade_log.symbol} "
                             f"P&L: +${trade_log.pnl:.2f} (+{trade_log.pips:.1f} pips)")
                else:
                    self.session_report.losing_trades += 1
                    self.info(f"❌ TRADE CLOSED: {trade_log.symbol} "
                             f"P&L: ${trade_log.pnl:.2f} ({trade_log.pips:.1f} pips)")
                
                if trade_log.pnl:
                    self.session_report.total_pnl += trade_log.pnl
                if trade_log.pips:
                    self.session_report.total_pips += trade_log.pips
            
            # Save to CSV
            self._save_trades_csv()
            
        except Exception as e:
            self.error(f"Error logging trade: {str(e)}")
    
    def log_analysis_step(self, step: str, symbol: str, timeframe: str, 
                         details: Optional[Dict] = None):
        """
        Log analysis steps for debugging
        
        Args:
            step: Analysis step name
            symbol: Symbol being analyzed
            timeframe: Timeframe
            details: Additional details dictionary
        """
        details_str = ""
        if details:
            details_str = " | " + " | ".join([f"{k}: {v}" for k, v in details.items()])
        
        self.debug(f"🔍 {step}: {symbol} {timeframe}{details_str}")
    
    def log_data_fetch(self, symbol: str, timeframe: str, bars_count: int, 
                      success: bool, error_msg: Optional[str] = None):
        """
        Log data fetching operations
        
        Args:
            symbol: Symbol
            timeframe: Timeframe
            bars_count: Number of bars fetched
            success: Whether fetch was successful
            error_msg: Error message if failed
        """
        if success:
            self.info(f"📊 DATA FETCH: {symbol} {timeframe} - {bars_count} bars")
        else:
            self.error(f"📊 DATA FETCH FAILED: {symbol} {timeframe} - {error_msg}")
    
    def log_system_status(self, status: str, details: Optional[Dict] = None):
        """
        Log system status updates
        
        Args:
            status: Status message
            details: Additional details
        """
        details_str = ""
        if details:
            details_str = " | " + " | ".join([f"{k}: {v}" for k, v in details.items()])
        
        self.info(f"⚙️ SYSTEM: {status}{details_str}")
    
    def _save_signals_csv(self):
        """Save signals to CSV file"""
        try:
            if self.signal_logs:
                df = pd.DataFrame([asdict(log) for log in self.signal_logs])
                df.to_csv(self.signals_csv, index=False)
        except Exception as e:
            self.error(f"Error saving signals CSV: {str(e)}")
    
    def _save_trades_csv(self):
        """Save trades to CSV file"""
        try:
            if self.trade_logs:
                df = pd.DataFrame([asdict(log) for log in self.trade_logs])
                df.to_csv(self.trades_csv, index=False)
        except Exception as e:
            self.error(f"Error saving trades CSV: {str(e)}")
    
    def save_session_report(self):
        """Save session report to JSON"""
        try:
            # Update session end time and uptime
            session_end = datetime.now()
            self.session_report.session_end = session_end.isoformat()
            self.session_report.uptime_minutes = (session_end - self.session_start).total_seconds() / 60
            
            # Calculate performance metrics
            if self.session_report.executed_trades > 0:
                win_rate = (self.session_report.winning_trades / 
                           (self.session_report.winning_trades + self.session_report.losing_trades))
                self.session_report.win_rate = win_rate
            
            # Save to JSON
            with open(self.session_json, 'w') as f:
                json.dump(asdict(self.session_report), f, indent=2)
            
            self.info(f"💾 Session report saved: {self.session_json}")
            
        except Exception as e:
            self.error(f"Error saving session report: {str(e)}")
    
    def print_session_summary(self):
        """Print a comprehensive session summary"""
        try:
            session_end = datetime.now()
            uptime = (session_end - self.session_start).total_seconds() / 60
            
            print("\n" + "="*80)
            print("🎯 SMC FOREZ SESSION SUMMARY")
            print("="*80)
            print(f"📅 Session: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')} - "
                  f"{session_end.strftime('%H:%M:%S')}")
            print(f"⏱️ Uptime: {uptime:.1f} minutes")
            print(f"🆔 Session ID: {self.session_id}")
            print()
            
            print("📊 SIGNAL STATISTICS")
            print("-" * 40)
            print(f"Total Signals Generated: {self.session_report.total_signals}")
            print(f"Symbols Analyzed: {len(self.session_report.symbols_analyzed)}")
            print(f"Symbols List: {', '.join(self.session_report.symbols_analyzed[:10])}")
            if len(self.session_report.symbols_analyzed) > 10:
                print(f"             ... and {len(self.session_report.symbols_analyzed) - 10} more")
            print()
            
            print("💼 TRADING STATISTICS")
            print("-" * 40)
            print(f"Trades Executed: {self.session_report.executed_trades}")
            print(f"Winning Trades: {self.session_report.winning_trades}")
            print(f"Losing Trades: {self.session_report.losing_trades}")
            
            total_closed = self.session_report.winning_trades + self.session_report.losing_trades
            if total_closed > 0:
                win_rate = (self.session_report.winning_trades / total_closed) * 100
                print(f"Win Rate: {win_rate:.1f}%")
            
            print(f"Total P&L: ${self.session_report.total_pnl:.2f}")
            print(f"Total Pips: {self.session_report.total_pips:.1f}")
            print()
            
            print("⚠️ SYSTEM STATISTICS")
            print("-" * 40)
            print(f"Errors Encountered: {self.session_report.errors_count}")
            print()
            
            print("📁 FILES GENERATED")
            print("-" * 40)
            print(f"Main Log: {self.log_dir}/main_{self.session_id}.log")
            print(f"Trades CSV: {self.trades_csv}")
            print(f"Signals CSV: {self.signals_csv}")
            print(f"Session JSON: {self.session_json}")
            print("="*80)
            
        except Exception as e:
            self.error(f"Error printing session summary: {str(e)}")
    
    def cleanup(self):
        """Cleanup logging system"""
        try:
            self.save_session_report()
            self.print_session_summary()
            self.info("🔄 SMC Forez Logger cleanup completed")
            
            # Close file handlers
            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    
        except Exception as e:
            print(f"Error during logger cleanup: {str(e)}")


# Global logger instance
_global_logger: Optional[SMCLogger] = None


def get_logger(log_dir: str = "logs", log_level: str = "INFO") -> SMCLogger:
    """
    Get global logger instance (singleton pattern)
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level
        
    Returns:
        SMCLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = SMCLogger(log_dir, log_level)
    return _global_logger


def cleanup_logger():
    """Cleanup global logger"""
    global _global_logger
    if _global_logger is not None:
        _global_logger.cleanup()
        _global_logger = None