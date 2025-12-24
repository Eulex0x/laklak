"""
Historical Data Backfill Script for InfluxDB

This script fetches historical 1-minute OHLCV data for multiple coins from Bybit
and stores it in InfluxDB. It handles the API limit of 1000 points by fetching
data in smaller date ranges.

Features:
- Fetches 1-minute candle data in configurable date ranges
- Respects API limit of 1000 points per request
- Breaks large time periods into multiple requests
- Skips data points that already exist in InfluxDB
- Validates data before writing to InfluxDB
- Handles errors gracefully and continues processing
- Logs all operations for monitoring and debugging
- Configurable batch size for performance optimization
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime, timedelta

from modules.exchanges.bybit import BybitKline
from modules.exchanges.yfinance import YFinanceKline
from modules.exchanges.bitunix import BitunixKline
from modules.exchanges.deribit import DeribitDVOL
from modules.influx_writer import InfluxDBWriter
from config import get_config

# ============================================================================
# ⚙️ BACKFILL SETTINGS - EDIT THESE VALUES BEFORE RUNNING
# ============================================================================

BACKFILL_CONFIG = {
    # ═══════════════════════════════════════════════════════════════════════
    # Time Period Settings
    # ═══════════════════════════════════════════════════════════════════════
    "TOTAL_DAYS": 90,                   # Total days to backfill (90 days = 3 months)
                                         # This will be split into chunks to respect 1000 point limit
    
    "CHUNK_SIZE_DAYS": 0.7,             # Days per API request (smaller = more requests, ~1000 points)
                                         # For 1-minute data: 0.7 days ≈ 1000 minutes ≈ 1000 points
                                         # Adjust if needed based on your interval
    
    # ═══════════════════════════════════════════════════════════════════════
    # Timeframe/Interval Settings
    # ═══════════════════════════════════════════════════════════════════════
    "BYBIT_RESOLUTION": "1",            # Bybit timeframe (MUST be "1" for 1-minute data)
                                        #   "1"  = 1 minute (for backfill)
                                        #   "5"  = 5 minutes
                                        #   "15" = 15 minutes
                                        #   "60" = 1 hour
                                        #   "D"  = 1 day (Daily)
    
    "YFINANCE_INTERVAL": "1m",          # YFinance interval:
                                        #   "1m"  = 1 minute
                                        #   "5m"  = 5 minutes
                                        #   "15m" = 15 minutes
                                        #   "1h"  = 1 hour
                                        #   "1d"  = 1 day (Daily)
    
    # ═══════════════════════════════════════════════════════════════════════
    # File Settings
    # ═══════════════════════════════════════════════════════════════════════
    "ASSETS_FILE": "assets.txt",        # File containing list of coins/assets
    
    # ═══════════════════════════════════════════════════════════════════════
    # Performance Settings
    # ═══════════════════════════════════════════════════════════════════════
    "BATCH_SIZE": 500,                  # Number of records to batch (2-1000)
                                        # Lower = safer, Higher = faster
}

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
    Historical data backfill class that fetches 1-minute candle data in chunks
    to respect the 1000 points API limit.
    """
    
    def __init__(self, logger: logging.Logger, batch_size: int = 500, 
                 total_days: int = 30, chunk_size_days: float = 0.7,
                 bybit_resolution: str = "1", yfinance_interval: str = "1m"):
        """
        Initialize the backfill processor.
        
        Args:
            logger (logging.Logger): Logger instance
            batch_size (int): Batch size for InfluxDB writes
            total_days (int): Total number of days to backfill
            chunk_size_days (float): Days per API request (e.g., 0.7 = ~1000 minutes)
            bybit_resolution (str): Bybit timeframe resolution
            yfinance_interval (str): YFinance interval
        """
        self.logger = logger
        self.batch_size = batch_size
        self.total_days = total_days
        self.chunk_size_days = chunk_size_days
        self.bybit_resolution = bybit_resolution
        self.yfinance_interval = yfinance_interval
        self.bybit = BybitKline()
        self.bitunix = BitunixKline()
        self.deribit = DeribitDVOL()
        self.yfinance = YFinanceKline()
        self.writer = InfluxDBWriter(batch_size=batch_size)
        self.stats = {
            "total_coins": 0,
            "successful_coins": 0,
            "failed_coins": 0,
            "total_points": 0,
            "skipped_duplicates": 0,
            "total_chunks": 0,
        }
    
    def load_coins(self, coins_file: str = "coins.txt") -> list:
        """
        Load the list of coins from a file with exchange specifications.
        
        Format: SYMBOL [exchanges]
        Examples:
            BTCUSDT bybit
            BTC-USD yfinance
            AAPL yfinance
        
        Args:
            coins_file (str): Path to the coins file
            
        Returns:
            list: List of tuples (symbol, exchanges_list)
        """
        if not os.path.exists(coins_file):
            self.logger.error(f"Coins file not found: {coins_file}")
            return []
        
        try:
            assets = []
            with open(coins_file, "r") as f:
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
            
            self.logger.info(f"Loaded {len(assets)} coins from {coins_file}")
            return assets
        
        except Exception as e:
            self.logger.error(f"Failed to load coins file: {e}")
            return []
    
    @staticmethod
    def _convert_to_yfinance_symbol(symbol: str) -> str:
        """
        Convert trading symbol to YFinance futures format.
        Examples: BTCUSDT -> BTC=F, ETHUSDT -> ETH=F
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT, ETH=F, etc.)
            
        Returns:
            YFinance symbol format (e.g., BTC=F)
        """
        # If already has =F suffix, return as-is
        if symbol.endswith('=F'):
            return symbol
        
        # Remove common suffixes and add =F
        for suffix in ['USDT', 'USDC', 'USD', 'BUSD', 'PERP']:
            if symbol.endswith(suffix):
                base = symbol[:-len(suffix)]
                return f"{base}=F"
        
        # If no suffix found, just add =F
        return f"{symbol}=F"
    
    def backfill_coin(self, symbol: str, exchanges: list) -> bool:
        """
        Fetch historical data for a single coin in date chunks and store it in InfluxDB.
        
        Breaks the total time period into smaller chunks to respect the 1000 points API limit.
        
        Args:
            symbol (str): The coin symbol (e.g., BTCUSDT, BTC-USD)
            exchanges (list): List of exchanges to fetch from
            
        Returns:
            bool: True if at least one exchange was successful, False otherwise
        """
        any_success = False
        total_points_written = 0
        
        # Calculate date chunks
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.total_days)
        
        self.logger.info(f"Fetching {symbol} from {start_date.date()} to {end_date.date()} in {self.chunk_size_days} day chunks")
        
        # Generate chunks
        chunk_starts = []
        current_date = start_date
        while current_date < end_date:
            chunk_starts.append(current_date)
            current_date += timedelta(days=self.chunk_size_days)
        
        total_chunks = len(chunk_starts)
        self.stats["total_chunks"] += total_chunks
        
        # Fetch from Bybit if specified
        if "bybit" in exchanges:
            try:
                for chunk_num, chunk_start in enumerate(chunk_starts, 1):
                    chunk_end = chunk_start + timedelta(days=self.chunk_size_days)
                    if chunk_end > end_date:
                        chunk_end = end_date
                    
                    chunk_days = (chunk_end - chunk_start).total_seconds() / 86400
                    
                    self.logger.debug(f"Bybit [{chunk_num}/{total_chunks}] {symbol}: {chunk_start.date()} to {chunk_end.date()} ({chunk_days:.2f} days)")
                    
                    try:
                        df = self.bybit.fetch_historical_kline(
                            currency=symbol,
                            days=chunk_days,
                            resolution=self.bybit_resolution,
                            start_time=chunk_start,
                            end_time=chunk_end
                        )
                        
                        if not df.empty:
                            valid_points = self.writer.write_market_data(
                                df=df,
                                symbol=symbol,
                                exchange="Bybit",
                                data_type="kline"
                            )
                            
                            if valid_points > 0:
                                total_points_written += valid_points
                                any_success = True
                                self.logger.debug(f"Bybit [{chunk_num}/{total_chunks}] {symbol}: Wrote {valid_points} points")
                        else:
                            self.logger.debug(f"Bybit [{chunk_num}/{total_chunks}] {symbol}: No data returned")
                    
                    except Exception as e:
                        self.logger.warning(f"Bybit [{chunk_num}/{total_chunks}] {symbol}: Chunk error: {e}")
                        continue
                
                if any_success:
                    self.logger.info(f"Bybit: Successfully backfilled {total_points_written} points for {symbol}")
                else:
                    self.logger.warning(f"Bybit: No data written for {symbol}")
            
            except Exception as e:
                self.logger.error(f"Bybit: Failed to backfill {symbol}: {e}", exc_info=False)
        
        # Fetch from YFinance if specified (only for supported coins: BTC, ETH, XRP, SOL)
        yfinance_supported = {"BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"}
        
        if "yfinance" in exchanges and symbol in yfinance_supported:
            try:
                for chunk_num, chunk_start in enumerate(chunk_starts, 1):
                    chunk_end = chunk_start + timedelta(days=self.chunk_size_days)
                    if chunk_end > end_date:
                        chunk_end = end_date
                    
                    chunk_days = (chunk_end - chunk_start).total_seconds() / 86400
                    
                    self.logger.debug(f"YFinance [{chunk_num}/{total_chunks}] {symbol}: {chunk_start.date()} to {chunk_end.date()}")
                    
                    try:
                        # Convert symbol for YFinance (e.g., BTCUSDT -> BTC=F)
                        yfinance_symbol = self._convert_to_yfinance_symbol(symbol)
                        
                        df = self.yfinance.fetch_historical_kline(
                            symbol=yfinance_symbol,
                            days=chunk_days,
                            interval=self.yfinance_interval,
                            start_time=chunk_start,
                            end_time=chunk_end
                        )
                        
                        if not df.empty:
                            valid_points = self.writer.write_market_data(
                                df=df,
                                symbol=symbol,
                                exchange="YFinance",
                                data_type="kline"
                            )
                            
                            if valid_points > 0:
                                total_points_written += valid_points
                                any_success = True
                                self.logger.debug(f"YFinance [{chunk_num}/{total_chunks}] {symbol}: Wrote {valid_points} points")
                        else:
                            self.logger.debug(f"YFinance [{chunk_num}/{total_chunks}] {symbol}: No data returned")
                    
                    except Exception as e:
                        self.logger.warning(f"YFinance [{chunk_num}/{total_chunks}] {symbol}: Chunk error: {e}")
                        continue
                
                if any_success:
                    self.logger.info(f"YFinance: Successfully backfilled {total_points_written} points for {symbol}")
                else:
                    self.logger.warning(f"YFinance: No data written for {symbol}")
            
            except Exception as e:
                self.logger.error(f"YFinance: Failed to backfill {symbol}: {e}", exc_info=False)
        
        # Fetch from Bitunix if specified
        if "bitunix" in exchanges:
            try:
                for chunk_num, chunk_start in enumerate(chunk_starts, 1):
                    chunk_end = chunk_start + timedelta(days=self.chunk_size_days)
                    if chunk_end > end_date:
                        chunk_end = end_date
                    
                    chunk_days = (chunk_end - chunk_start).total_seconds() / 86400
                    
                    self.logger.debug(f"Bitunix [{chunk_num}/{total_chunks}] {symbol}: {chunk_start.date()} to {chunk_end.date()} ({chunk_days:.2f} days)")
                    
                    try:
                        df = self.bitunix.fetch_historical_kline(
                            currency=symbol,
                            days=chunk_days,
                            resolution=1,  # 1-minute for bitunix
                            start_time=chunk_start,
                            end_time=chunk_end
                        )
                        
                        if not df.empty:
                            valid_points = self.writer.write_market_data(
                                df=df,
                                symbol=symbol,
                                exchange="Bitunix",
                                data_type="kline"
                            )
                            
                            if valid_points > 0:
                                total_points_written += valid_points
                                any_success = True
                                self.logger.debug(f"Bitunix [{chunk_num}/{total_chunks}] {symbol}: Wrote {valid_points} points")
                        else:
                            self.logger.debug(f"Bitunix [{chunk_num}/{total_chunks}] {symbol}: No data returned")
                    
                    except Exception as e:
                        self.logger.warning(f"Bitunix [{chunk_num}/{total_chunks}] {symbol}: Chunk error: {e}")
                        continue
                
                if any_success:
                    self.logger.info(f"Bitunix: Successfully backfilled {total_points_written} points for {symbol}")
                else:
                    self.logger.warning(f"Bitunix: No data written for {symbol}")
            
            except Exception as e:
                self.logger.error(f"Bitunix: Failed to backfill {symbol}: {e}", exc_info=False)
        
        # Fetch from Deribit if specified
        if "deribit" in exchanges:
            try:
                for chunk_num, chunk_start in enumerate(chunk_starts, 1):
                    chunk_end = chunk_start + timedelta(days=self.chunk_size_days)
                    if chunk_end > end_date:
                        chunk_end = end_date
                    
                    chunk_days = (chunk_end - chunk_start).total_seconds() / 86400
                    
                    self.logger.debug(f"Deribit [{chunk_num}/{total_chunks}] {symbol}: {chunk_start.date()} to {chunk_end.date()} ({chunk_days:.2f} days)")
                    
                    try:
                        df = self.deribit.fetch_historical_dvol(
                            currency=symbol,
                            days=chunk_days,
                            resolution="1",  # 1-minute for deribit
                            start_time=chunk_start,
                            end_time=chunk_end
                        )
                        
                        if not df.empty:
                            valid_points = self.writer.write_market_data(
                                df=df,
                                symbol=symbol,
                                exchange="Deribit",
                                data_type="kline"
                            )
                            
                            if valid_points > 0:
                                total_points_written += valid_points
                                any_success = True
                                self.logger.debug(f"Deribit [{chunk_num}/{total_chunks}] {symbol}: Wrote {valid_points} points")
                        else:
                            self.logger.debug(f"Deribit [{chunk_num}/{total_chunks}] {symbol}: No data returned")
                    
                    except Exception as e:
                        self.logger.warning(f"Deribit [{chunk_num}/{total_chunks}] {symbol}: Chunk error: {e}")
                        continue
                
                if any_success:
                    self.logger.info(f"Deribit: Successfully backfilled {total_points_written} points for {symbol}")
                else:
                    self.logger.warning(f"Deribit: No data written for {symbol}")
            
            except Exception as e:
                self.logger.error(f"Deribit: Failed to backfill {symbol}: {e}", exc_info=False)
        
        # Update stats
        if any_success:
            self.stats["successful_coins"] += 1
            self.stats["total_points"] += total_points_written
            return True
        else:
            self.stats["failed_coins"] += 1
            return False
    
    def run(self, coins_file: str = "coins.txt") -> None:
        """
        Run the historical data backfill process.
        
        Args:
            coins_file (str): Path to the coins file
        """
        self.logger.info("="*80)
        total_days_msg = f"total {self.total_days} days in {self.chunk_size_days}-day chunks (~{int(self.total_days/self.chunk_size_days)} chunks)"
        self.logger.info(f"Starting historical data backfill ({total_days_msg})")
        self.logger.info("="*80)
        
        start_time = datetime.now()
        
        # Load coins
        coins = self.load_coins(coins_file)
        if not coins:
            self.logger.error("No coins to process, exiting")
            return
        
        self.stats["total_coins"] = len(coins)
        
        # Process each coin
        for i, (symbol, exchanges) in enumerate(coins, 1):
            exchanges_str = "+".join(exchanges)
            self.logger.info(f"[{i}/{len(coins)}] Backfilling {symbol} ({exchanges_str})")
            self.backfill_coin(symbol, exchanges)
        
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
    
    # Print backfill settings for user confirmation
    logger.info("="*80)
    logger.info("BACKFILL CONFIGURATION")
    logger.info("="*80)
    logger.info(f"Total days to backfill:  {BACKFILL_CONFIG['TOTAL_DAYS']}")
    logger.info(f"Chunk size (days):       {BACKFILL_CONFIG['CHUNK_SIZE_DAYS']}")
    total_chunks = int(BACKFILL_CONFIG['TOTAL_DAYS'] / BACKFILL_CONFIG['CHUNK_SIZE_DAYS'])
    logger.info(f"Total chunks:            ~{total_chunks}")
    logger.info(f"Bybit resolution:        {BACKFILL_CONFIG['BYBIT_RESOLUTION']} (1-minute data)")
    logger.info(f"YFinance interval:       {BACKFILL_CONFIG['YFINANCE_INTERVAL']}")
    logger.info(f"Assets file:             {BACKFILL_CONFIG['ASSETS_FILE']}")
    logger.info(f"Batch size:              {BACKFILL_CONFIG['BATCH_SIZE']}")
    logger.info("="*80)
    
    try:
        # Create and run backfill
        backfill = HistoricalBackfill(
            logger=logger,
            batch_size=BACKFILL_CONFIG["BATCH_SIZE"],
            total_days=BACKFILL_CONFIG["TOTAL_DAYS"],
            chunk_size_days=BACKFILL_CONFIG["CHUNK_SIZE_DAYS"],
            bybit_resolution=BACKFILL_CONFIG["BYBIT_RESOLUTION"],
            yfinance_interval=BACKFILL_CONFIG["YFINANCE_INTERVAL"]
        )
        backfill.run(coins_file=BACKFILL_CONFIG["ASSETS_FILE"])
        
    except KeyboardInterrupt:
        logger.info("Historical backfill interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
