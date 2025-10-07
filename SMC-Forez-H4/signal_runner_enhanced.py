#!/usr/bin/env python3
"""
Enhanced Continuous Signal Runner for SMC Forez using Real Multi-Timeframe Analysis
Generates high-quality signals using the actual SMC analyzer with professional market structure analysis
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
import threading
from dataclasses import asdict

# Add project to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from smc_forez.analyzer import SMCAnalyzer
from smc_forez.config.settings import Settings, Timeframe
from smc_forez.signals.signal_generator import SignalType, SignalStrength
from smc_forez.execution.live_executor import LiveExecutor, ExecutionSettings

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_runner_enhanced.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedSignalRunner:
    """
    Enhanced signal runner that now acts as a lightweight wrapper 
    to configure and run the powerful LiveExecutor.
    """
    
    def __init__(self, settings: Optional[Settings] = None, execution_settings: Optional[ExecutionSettings] = None):
        """Initialize the enhanced signal runner"""
        self.settings = settings or Settings()
        self.execution_settings = execution_settings or ExecutionSettings()
        
        # The analyzer is now managed by the LiveExecutor, but we can keep settings here.
        self.settings.timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]
        
        # Initialize Live Executor - This is now the heart of the system
        self.executor = LiveExecutor(self.settings, self.execution_settings)
        
        # Currency pairs to analyze
        self.symbols = [
            "EURUSDm", "GBPUSDm", "USDJPYm", "USDCHFm", "USDCADm", "AUDUSDm", "NZDUSDm",
            "EURGBPm", "EURJPYm", "EURAUDm", "EURCHm", "EURCADm",
            "GBPJPYm", "GBPAUDm", "GBPCHFm", "GBPCADm",
            "AUDJPYm", "AUDNZDm", "AUDCHFm", "AUDCADm",
            "CADJPYm", "CHFJPYm", "CADCHFm", "NZDJPYm", "NZDCHFm", "NZDCADm",
            "XAUUSDm"
        ]

        self.is_running = False
        
    def start(self):
        """Starts the live execution process managed by the LiveExecutor."""
        logger.info("🚀 Starting the Enhanced Signal Runner...")
        self.is_running = True
        
        # The executor now handles its own lifecycle, including connections.
        # We just need to start it.
        try:
            # The executor's start method is blocking and contains the main loop
            self.executor.start_live_execution(self.symbols)
            
        except KeyboardInterrupt:
            logger.info("🛑 Runner stopped by user.")
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred in the runner: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("📝 Runner has finished.")

    def stop(self):
        """Stops the runner and the underlying LiveExecutor."""
        logger.info("🔌 Initiating shutdown of the Enhanced Signal Runner...")
        self.executor.shutdown() # Gracefully shut down the executor
        self.is_running = False


def main():
    """Main function to run enhanced signal generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SMC Forez - Enhanced Continuous Signal Runner")
    # The 'mode' argument is no longer relevant as the executor runs a continuous loop.
    # We keep it for backward compatibility but it's ignored.
    parser.add_argument(
        '--mode', 
        choices=['single', 'loop'], 
        default='loop',
        help="[DEPRECATED] Run mode is now always a continuous loop."
    )
    parser.add_argument(
        '--no-execute',
        action='store_true',
        help='Disable live trade execution (signals only mode)'
    )
    args = parser.parse_args()

    # Execution is enabled by default, disabled with --no-execute
    execute = not args.no_execute

    print("*** SMC FOREZ - ENHANCED CONTINUOUS SIGNAL RUNNER ***")
    print("="*80)
    
    # Initialize settings
    settings = Settings()
    execution_settings = ExecutionSettings(enable_execution=execute)
    
    # Create enhanced signal runner
    runner = EnhancedSignalRunner(settings, execution_settings)
    
    print(f"[CONFIG] ENHANCED CONFIGURATION")
    print("-" * 40)
    print(f"   Symbols: {len(runner.symbols)} currency pairs")
    print(f"   Analysis: Real SMC Multi-Timeframe")
    print(f"   Timeframes: {[tf.value for tf in settings.timeframes]}")
    print(f"   Quality Filtering: Centralized in LiveExecutor (Enhanced)")
    print(f"   Risk Management: Centralized in LiveExecutor (Portfolio-Aware)")
    print(f"   Execution Enabled: {execute}")
    print()
    
    if execute:
        print("⚠️  WARNING: Live execution enabled! Starting automatically...")
        print("🚀 Live trading will begin in 3 seconds...")
        import time
        time.sleep(3)

    try:
        print("Starting continuous signal processing via LiveExecutor...")
        print("Press Ctrl+C to stop")
        runner.start()
    
    except KeyboardInterrupt:
        print("\n⏹️ Enhanced signal runner interrupted by user.")
        runner.stop()
    except Exception as e:
        print(f"\n[ERROR] A fatal error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()