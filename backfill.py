"""
Historical Data Backfill Script for InfluxDB

This script fetches historical 1-hour OHLCV data for multiple coins from Bybit
and stores it in InfluxDB. This is a one-time operation to populate the database
with historical data for backtesting and analysis.

Features:
- Fetches up to 365 days of historical data
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

from modules.exchanges.bybit import BybitKline
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
    logger = logging.getLogger("backfill")
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
# Main Backfill Logic
# ============================================================================

class HistoricalBackfill:
    """
    Historical data backfill class that orchestrates fetching and storing historical market data.
    """
    
    def __init__(self, logger: logging.Logger, batch_size: int = 2, days: int = 365):
        """
        Initialize the backfill processor.
        
        Args:
            logger (logging.Logger): Logger instance
            batch_size (int): Batch size for InfluxDB writes
            days (int): Number of days of historical data to fetch
        """
        self.logger = logger
        self.batch_size = batch_size
        self.days = days
        self.bybit = BybitKline()
        self.writer = InfluxDBWriter(batch_size=batch_size)
        self.stats = {
            "total_coins": 0,
            "successful_coins": 0,
            "failed_coins": 0,
            "total_points": 0,
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
    
    def backfill_coin(self, symbol: str) -> bool:
        """
        Fetch historical data for a single coin and store it in InfluxDB.
        
        Args:
            symbol (str): The coin symbol (e.g., BTCUSDT)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.debug(f"Fetching {self.days} days of historical data for {symbol}")
            
            # Fetch historical data
            df = self.bybit.fetch_historical_kline(
                currency=symbol,
                days=self.days,
                resolution=60  # 1 hour
            )
            
            if df.empty:
                self.logger.warning(f"No historical data returned for {symbol}")
                self.stats["failed_coins"] += 1
                return False
            
            # Write to InfluxDB
            valid_points = self.writer.write_market_data(
                df=df,
                symbol=symbol,
                exchange="Bybit",
                data_type="kline"
            )
            
            if valid_points == 0:
                self.logger.warning(f"No valid data points for {symbol}")
                self.stats["failed_coins"] += 1
                return False
            
            self.stats["successful_coins"] += 1
            self.stats["total_points"] += valid_points
            self.logger.info(f"Successfully backfilled {valid_points} points for {symbol}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to backfill {symbol}: {e}", exc_info=True)
            self.stats["failed_coins"] += 1
            return False
    
    def run(self, coins_file: str = "coins.txt") -> None:
        """
        Run the historical data backfill process.
        
        Args:
            coins_file (str): Path to the coins file
        """
        self.logger.info("="*80)
        self.logger.info(f"Starting historical data backfill ({self.days} days)")
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
            self.logger.info(f"[{i}/{len(coins)}] Backfilling {symbol}")
            self.backfill_coin(symbol)
        
        # Flush remaining data
        self.logger.info("Flushing remaining data to InfluxDB...")
        self.writer.flush()
        
        # Close connection
        self.writer.close()
        
        # Log statistics
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.logger.info("="*80)
        self.logger.info("Historical data backfill completed")
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
    """Main entry point for the historical backfill script."""
    
    # Load configuration
    config = get_config()
    
    # Set up logging
    logger = setup_logging(
        log_file=config["LOG_FILE"].replace("collector", "backfill"),
        log_level=config["LOG_LEVEL"]
    )
    
    try:
        # Create and run backfill
        backfill = HistoricalBackfill(
            logger=logger,
            batch_size=config["INFLUXDB_BATCH_SIZE"],
            days=365  # Fetch 1 year of historical data
        )
        backfill.run(coins_file="assets.txt")
        
    except KeyboardInterrupt:
        logger.info("Historical backfill interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
