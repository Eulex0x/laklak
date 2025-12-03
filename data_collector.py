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

from modules.exchanges.bybit import BybitKline
from modules.exchanges.deribit import DeribitDVOL
from modules.exchanges.yfinance import YFinanceKline
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
        self.yfinance = YFinanceKline()
        self.writer = InfluxDBWriter(batch_size=batch_size)
        self.stats = {
            "total_assets": 0,
            "successful_assets": 0,
            "failed_assets": 0,
            "total_points": 0,
            "skipped_points": 0
        }
    
    def load_assets(self, assets_file: str = "assets.txt") -> list:
        """
        Load the list of assets from a file with exchange specifications.
        
        Format: SYMBOL [exchanges]
        Examples:
            BTCUSDT bybit+deribit
            BTC-USD yfinance
            AAPL yfinance
        
        Args:
            assets_file (str): Path to the assets file
            
        Returns:
            list: List of tuples (symbol, exchanges_list)
        """
        if not os.path.exists(assets_file):
            self.logger.error(f"Assets file not found: {assets_file}")
            return []
        
        try:
            assets = []
            with open(assets_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    parts = line.split()
                    symbol = parts[0]
                    
                    # Parse exchanges (default to bybit only)
                    if len(parts) > 1:
                        exchanges_str = parts[1]
                        exchanges = exchanges_str.split("+")
                    else:
                        exchanges = ["bybit"]
                    
                    assets.append((symbol, exchanges))
            
            self.logger.info(f"Loaded {len(assets)} assets from {assets_file}")
            return assets
        
        except Exception as e:
            self.logger.error(f"Failed to load coins file: {e}")
            return []
    
    def fetch_and_store_asset(self, symbol: str, exchanges: list) -> bool:
        """
        Fetch data for a single asset and store it in InfluxDB.
        Fetches data from specified exchanges only.
        
        Args:
            symbol (str): The asset symbol (e.g., BTCUSDT, BTC-USD, AAPL)
            exchanges (list): List of exchanges to fetch from (e.g., ['bybit', 'deribit', 'yfinance'])
            
        Returns:
            bool: True if at least one data source was successful, False otherwise
        """
        config = get_config()
        success_flags = {"bybit": False, "deribit": False, "yfinance": False}
        total_valid_points = 0
        
        # Fetch Bybit Kline Data (only if specified)
        if "bybit" in exchanges:
            try:
                self.logger.debug(f"Fetching Bybit kline data for {symbol}")
                
                df_bybit = self.bybit.fetch_historical_kline(
                    currency=symbol,
                    days=config["DAYS"],
                    resolution=config["RESOLUTION_KLINE"]
                )
                
                if not df_bybit.empty:
                    # Write to InfluxDB with exchange-specific symbol
                    db_symbol = f"{symbol}_BYBIT"
                    valid_points = self.writer.write_market_data(
                        df=df_bybit,
                        symbol=db_symbol,
                        exchange="Bybit",
                        data_type="kline"
                    )
                    
                    if valid_points > 0:
                        total_valid_points += valid_points
                        success_flags["bybit"] = True
                        self.logger.info(f"Bybit: Successfully processed {valid_points} kline points for {db_symbol}")
                    else:
                        self.logger.warning(f"Bybit: No valid kline data points for {symbol}")
                else:
                    self.logger.warning(f"Bybit: No kline data returned for {symbol}")
            
            except Exception as e:
                self.logger.error(f"Bybit: Failed to process kline data for {symbol}: {e}", exc_info=False)
            
            # Also fetch funding rate for Bybit perpetual contracts
            try:
                self.logger.debug(f"Fetching Bybit funding rate for {symbol}")
                
                df_funding = self.bybit.fetch_funding_rate(
                    currency=symbol,
                    days=config["DAYS"]
                )
                
                if not df_funding.empty:
                    # Write to InfluxDB with naming: SYMBOL_fundingrate_bybit
                    db_symbol = f"{symbol}_fundingrate_bybit"
                    valid_points = self.writer.write_market_data(
                        df=df_funding,
                        symbol=db_symbol,
                        exchange="Bybit",
                        data_type="funding_rate"
                    )
                    
                    if valid_points > 0:
                        total_valid_points += valid_points
                        self.logger.info(f"Bybit: Successfully processed {valid_points} funding rate points for {db_symbol}")
                    else:
                        self.logger.debug(f"Bybit: No valid funding rate data points for {symbol}")
                else:
                    self.logger.debug(f"Bybit: No funding rate data returned for {symbol}")
            
            except Exception as e:
                self.logger.debug(f"Bybit: Failed to process funding rate for {symbol}: {e}")
        
        # Fetch Deribit DVOL Data (only if specified)
        if "deribit" in exchanges:
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
                    # Write to InfluxDB with data-type specific symbol
                    # DVOL is volatility, not price, so use descriptive naming
                    db_symbol = f"{base_currency}_DVOL"
                    valid_points = self.writer.write_market_data(
                        df=df_deribit,
                        symbol=db_symbol,
                        exchange="Deribit",
                        data_type="dvol"
                    )
                    
                    if valid_points > 0:
                        total_valid_points += valid_points
                        success_flags["deribit"] = True
                        self.logger.info(f"Deribit: Successfully processed {valid_points} DVOL points for {db_symbol}")
                    else:
                        self.logger.warning(f"Deribit: No valid DVOL data points for {base_currency}")
                else:
                    self.logger.warning(f"Deribit: No DVOL data returned for {base_currency}")
            
            except Exception as e:
                self.logger.error(f"Deribit: Failed to process DVOL data for {symbol}: {e}", exc_info=False)
        
        # Fetch Yahoo Finance Data (only if specified)
        if "yfinance" in exchanges:
            try:
                self.logger.debug(f"Fetching Yahoo Finance data for {symbol}")
                
                # Convert interval format if needed (e.g., 60 -> "1h")
                yf_interval = str(config.get("RESOLUTION_KLINE", 60))
                if yf_interval == "60":
                    yf_interval = "1h"
                elif yf_interval == "1":
                    yf_interval = "1m"
                elif yf_interval == "1D":
                    yf_interval = "1d"
                
                df_yfinance = self.yfinance.fetch_historical_kline(
                    symbol=symbol,
                    days=config["DAYS"],
                    interval=yf_interval
                )
                
                if not df_yfinance.empty:
                    # Write to InfluxDB with exchange-specific symbol
                    db_symbol = f"{symbol}_YFINANCE"
                    valid_points = self.writer.write_market_data(
                        df=df_yfinance,
                        symbol=db_symbol,
                        exchange="YFinance",
                        data_type="kline"
                    )
                    
                    if valid_points > 0:
                        total_valid_points += valid_points
                        success_flags["yfinance"] = True
                        self.logger.info(f"YFinance: Successfully processed {valid_points} kline points for {db_symbol}")
                    else:
                        self.logger.warning(f"YFinance: No valid kline data points for {symbol}")
                else:
                    self.logger.warning(f"YFinance: No kline data returned for {symbol}")
            
            except Exception as e:
                self.logger.error(f"YFinance: Failed to process kline data for {symbol}: {e}", exc_info=False)
        
        # Update statistics
        any_success = any(success_flags.values())
        if any_success:
            self.stats["successful_assets"] += 1
            self.stats["total_points"] += total_valid_points
            success_str = ", ".join([f"{k}: {v}" for k, v in success_flags.items() if v])
            self.logger.info(f"Total: Successfully processed {total_valid_points} points for {symbol} ({success_str})")
            return True
        else:
            self.stats["failed_assets"] += 1
            return False
    
    def run(self, assets_file: str = "assets.txt") -> None:
        """
        Run the data collection process.
        
        Args:
            assets_file (str): Path to the assets file
        """
        self.logger.info("="*80)
        self.logger.info("Starting market data collection")
        self.logger.info("="*80)
        
        start_time = datetime.now()
        
        # Load assets
        assets = self.load_assets(assets_file)
        if not assets:
            self.logger.error("No assets to process, exiting")
            return
        
        self.stats["total_assets"] = len(assets)
        
        # Process each asset
        for i, (symbol, exchanges) in enumerate(assets, 1):
            exchanges_str = "+".join(exchanges)
            self.logger.info(f"[{i}/{len(assets)}] Processing {symbol} (exchanges: {exchanges_str})")
            self.fetch_and_store_asset(symbol, exchanges)
        
        # Flush remaining data
        self.logger.info("Flushing remaining data to InfluxDB...")
        self.writer.flush()
        
        # Close connection
        self.writer.close()
        
        # Log statistics
        elapsed_time = (datetime.now() - start_time).total_seconds()
        self.logger.info("="*80)
        self.logger.info("Data collection completed")
        self.logger.info(f"Total assets: {self.stats['total_assets']}")
        self.logger.info(f"Successful: {self.stats['successful_assets']}")
        self.logger.info(f"Failed: {self.stats['failed_assets']}")
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
        collector.run(assets_file="assets.txt")
        
    except KeyboardInterrupt:
        logger.info("Data collection interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
