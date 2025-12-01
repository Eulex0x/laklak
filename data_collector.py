#!/usr/bin/env python3

"""
Market Data Collector for InfluxDB

This script fetches 1-hour OHLCV data for multiple coins from Bybit
and stores it in InfluxDB. It is designed to run once per hour via cron.

Features:
- Fetches data for all coins listed in coins.txt
- Validates data before writing to InfluxDB
- Handles errors gracefully and continues processing
- Logs all operations for monitoring and debugging
- Configurable batch size for performance optimization
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
from pathlib import Path

from modules.bybit_klin import BybitKline
from modules.deribit_dvol import DeribitDVOL
from modules.influx_writer import InfluxDBWriter
from config import get_config

# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(log_file: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging to both file and console.
    
    Args:
        log_file (str): Path to the log file
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("data_collector")
    logger.setLevel(getattr(logging, log_level))
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5  # Keep 5 backup files
    )
    file_handler.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# ============================================================================
# Main Data Collection Logic
# ============================================================================

class DataCollector:
    """
    Main data collector class that orchestrates fetching and storing market data.
    """
    
    def __init__(self, logger: logging.Logger, batch_size: int = 2):
        """
        Initialize the data collector.
        
        Args:
            logger (logging.Logger): Logger instance
            batch_size (int): Batch size for InfluxDB writes
        """
        self.logger = logger
        self.batch_size = batch_size
        self.bybit = BybitKline()
        self.deribit = DeribitDVOL()
        self.writer = InfluxDBWriter(batch_size=batch_size)
        self.stats = {
            "total_coins": 0,
            "successful_coins": 0,
            "failed_coins": 0,
            "total_points": 0,
            "skipped_points": 0
        }
    
    def load_coins(self, coins_file: str = "coins.txt") -> list:
        """
        Load the list of coins from a file.
        
        Args:
            coins_file (str): Path to the coins file
            
        Returns:
            list: List of coin symbols
        """
        if not os.path.exists(coins_file):
            self.logger.error(f"Coins file not found: {coins_file}")
            return []
        
        try:
            with open(coins_file, "r") as f:
                coins = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
            self.logger.info(f"Loaded {len(coins)} coins from {coins_file}")
            return coins
        
        except Exception as e:
            self.logger.error(f"Failed to load coins file: {e}")
            return []
    
    def fetch_and_store_coin(self, symbol: str) -> bool:
        """
        Fetch data for a single coin and store it in InfluxDB.
        Fetches both Bybit kline data and Deribit DVOL data.
        
        Args:
            symbol (str): The coin symbol (e.g., BTCUSDT)
            
        Returns:
            bool: True if at least one data source was successful, False otherwise
        """
        config = get_config()
        bybit_success = False
        deribit_success = False
        total_valid_points = 0
        
        # Fetch Bybit Kline Data
        try:
            self.logger.debug(f"Fetching Bybit kline data for {symbol}")
            
            df_bybit = self.bybit.fetch_historical_kline(
                currency=symbol,
                days=config["DAYS"],
                resolution=config["RESOLUTION_KLINE"]
            )
            
            if not df_bybit.empty:
                # Write to InfluxDB
                valid_points = self.writer.write_market_data(
                    df=df_bybit,
                    symbol=symbol,
                    exchange="Bybit",
                    data_type="kline"
                )
                
                if valid_points > 0:
                    total_valid_points += valid_points
                    bybit_success = True
                    self.logger.info(f"Bybit: Successfully processed {valid_points} kline points for {symbol}")
                else:
                    self.logger.warning(f"Bybit: No valid kline data points for {symbol}")
            else:
                self.logger.warning(f"Bybit: No kline data returned for {symbol}")
        
        except Exception as e:
            self.logger.error(f"Bybit: Failed to process kline data for {symbol}: {e}", exc_info=False)
        
        # Fetch Deribit DVOL Data
        try:
            # Extract base currency (BTC from BTCUSDT, ETH from ETHUSDT)
            base_currency = symbol.replace("USDT", "").replace("USDC", "")
            
            self.logger.debug(f"Fetching Deribit DVOL data for {base_currency}")
            
            # Deribit resolution needs to be in minutes (convert from Bybit format if needed)
            deribit_resolution = config["RESOLUTION_KLINE"]
            
            df_deribit = self.deribit.fetch_historical_dvol(
                currency=base_currency,
                days=config["DAYS"],
                resolution=deribit_resolution
            )
            
            if not df_deribit.empty:
                # Write to InfluxDB
                valid_points = self.writer.write_market_data(
                    df=df_deribit,
                    symbol=symbol,
                    exchange="Deribit",
                    data_type="dvol"
                )
                
                if valid_points > 0:
                    total_valid_points += valid_points
                    deribit_success = True
                    self.logger.info(f"Deribit: Successfully processed {valid_points} DVOL points for {symbol}")
                else:
                    self.logger.warning(f"Deribit: No valid DVOL data points for {symbol}")
            else:
                self.logger.warning(f"Deribit: No DVOL data returned for {base_currency}")
        
        except Exception as e:
            self.logger.error(f"Deribit: Failed to process DVOL data for {symbol}: {e}", exc_info=False)
        
        # Update statistics
        if bybit_success or deribit_success:
            self.stats["successful_coins"] += 1
            self.stats["total_points"] += total_valid_points
            self.logger.info(f"Total: Successfully processed {total_valid_points} points for {symbol} (Bybit: {bybit_success}, Deribit: {deribit_success})")
            return True
        else:
            self.stats["failed_coins"] += 1
            return False
    
    def run(self, coins_file: str = "coins.txt") -> None:
        """
        Run the data collection process.
        
        Args:
            coins_file (str): Path to the coins file
        """
        self.logger.info("="*80)
        self.logger.info("Starting market data collection")
        self.logger.info("="*80)
        
        start_time = datetime.now()
        
        # Load coins
        coins = self.load_coins(coins_file)
        if not coins:
            self.logger.error("No coins to process, exiting")
            return
        
        self.stats["total_coins"] = len(coins)
        
        # Process each coin
        for i, symbol in enumerate(coins, 1):
            self.logger.info(f"[{i}/{len(coins)}] Processing {symbol}")
            self.fetch_and_store_coin(symbol)
        
        # Flush remaining data
        self.logger.info("Flushing remaining data to InfluxDB...")
        self.writer.flush()
        
        # Close connection
        self.writer.close()
        
        # Log statistics
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.logger.info("="*80)
        self.logger.info("Data collection completed")
        self.logger.info(f"Total coins: {self.stats['total_coins']}")
        self.logger.info(f"Successful: {self.stats['successful_coins']}")
        self.logger.info(f"Failed: {self.stats['failed_coins']}")
        self.logger.info(f"Total points written: {self.stats['total_points']}")
        self.logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")
        self.logger.info("="*80)


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point for the data collector."""
    
    # Load configuration
    config = get_config()
    
    # Set up logging
    logger = setup_logging(
        log_file=config["LOG_FILE"],
        log_level=config["LOG_LEVEL"]
    )
    
    try:
        # Create and run collector
        collector = DataCollector(
            logger=logger,
            batch_size=config["INFLUXDB_BATCH_SIZE"]
        )
        collector.run(coins_file="coins.txt")
        
    except KeyboardInterrupt:
        logger.info("Data collection interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
