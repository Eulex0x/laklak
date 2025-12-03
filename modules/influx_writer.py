"""
InfluxDB Writer Module for Market Data

This module provides a robust interface for writing OHLCV market data to InfluxDB 1.6.
Features:
- Configurable batch size for efficient writes
- Data validation to ensure data integrity
- Comprehensive logging for debugging and monitoring
- Error handling with graceful continuation
- Support for multiple exchanges and data types
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from influxdb import InfluxDBClient
import os

logger = logging.getLogger(__name__)


class InfluxDBWriter:
    """
    A robust writer for storing market data in InfluxDB 1.6.
    
    This class handles:
    - Connection management to InfluxDB
    - Data validation before writing
    - Batch processing for efficient writes
    - Comprehensive error handling and logging
    """

    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 username: str = None,
                 password: str = None,
                 batch_size: int = 2):
        """
        Initialize the InfluxDB writer.
        
        Args:
            host (str): InfluxDB host. Defaults to INFLUXDB_HOST env var or 'localhost'
            port (int): InfluxDB port. Defaults to INFLUXDB_PORT env var or 8086
            database (str): InfluxDB database. Defaults to INFLUXDB_DATABASE env var or 'market_data'
            username (str): InfluxDB username. Defaults to INFLUXDB_USERNAME env var or None
            password (str): InfluxDB password. Defaults to INFLUXDB_PASSWORD env var or None
            batch_size (int): Number of data points to batch before writing to InfluxDB.
                            Default is 2. Can be increased to 100, 1000, etc. for production.
        """
        self.host = host or os.getenv("INFLUXDB_HOST", "localhost")
        self.port = port or int(os.getenv("INFLUXDB_PORT", "8086"))
        self.database = database or os.getenv("INFLUXDB_DATABASE", "market_data")
        self.username = username or os.getenv("INFLUXDB_USERNAME")
        self.password = password or os.getenv("INFLUXDB_PASSWORD")
        self.batch_size = batch_size
        self.batch: List[Dict[str, Any]] = []
        
        logger.info(f"Initializing InfluxDB Writer: {self.host}:{self.port}/{self.database}")
        logger.info(f"Batch size set to: {self.batch_size}")
        
        try:
            # Connect to InfluxDB
            self.client = InfluxDBClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )
            
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to InfluxDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    def _validate_row(self, row: Dict[str, Any], symbol: str, data_type: str = "kline") -> bool:
        """
        Validate a single data row before writing to InfluxDB.
        
        Checks for:
        - Required fields are present and not null
        - Numeric fields are valid numbers
        - Timestamp is valid
        
        Args:
            row (Dict): The data row to validate
            symbol (str): The trading symbol (for logging)
            data_type (str): The data type (kline, funding_rate, dvol, etc.)
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["open", "high", "low", "close", "volume", "time"]
        
        # Check for missing fields
        for field in required_fields:
            if field not in row:
                logger.warning(f"Missing field '{field}' for {symbol}")
                return False
        
        # Check for null/NaN values
        for field in ["open", "high", "low", "close", "volume"]:
            value = row[field]
            if value is None or (isinstance(value, float) and pd.isna(value)):
                logger.warning(f"Null value in field '{field}' for {symbol}")
                return False
        
        # Validate numeric fields
        # Note: Funding rates can be negative (shorts pay longs), so skip negative check for them
        allow_negative = (data_type == "funding_rate")
        
        for field in ["open", "high", "low", "close", "volume"]:
            try:
                float_value = float(row[field])
                if not allow_negative and float_value < 0:
                    logger.warning(f"Negative value in field '{field}' for {symbol}: {float_value}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid numeric value in field '{field}' for {symbol}: {row[field]}")
                return False
        
        # Validate timestamp
        try:
            if isinstance(row["time"], str):
                datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
            elif isinstance(row["time"], pd.Timestamp):
                pass  # pandas Timestamp is valid
            elif isinstance(row["time"], int):
                # Unix timestamp in milliseconds
                if row["time"] < 0 or row["time"] > 9999999999999:
                    logger.warning(f"Invalid timestamp for {symbol}: {row['time']}")
                    return False
            else:
                logger.warning(f"Invalid timestamp type for {symbol}: {type(row['time'])}")
                return False
        except Exception as e:
            logger.warning(f"Timestamp validation error for {symbol}: {e}")
            return False
        
        return True

    def _create_point(
        self,
        row: Dict[str, Any],
        symbol: str,
        exchange: str,
        data_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a data row into an InfluxDB point.
        
        Args:
            row (Dict): The data row
            symbol (str): The trading symbol (e.g., BTCUSDT)
            exchange (str): The exchange name (e.g., Bybit)
            data_type (str): The data type (e.g., kline, dvol, funding_rate)
            
        Returns:
            Dict: An InfluxDB point, or None if validation fails
        """
        # Validate the row (pass data_type to allow negative values for funding rates)
        if not self._validate_row(row, symbol, data_type):
            return None
        
        try:
            # Convert timestamp to milliseconds if needed
            timestamp = row["time"]
            if isinstance(timestamp, pd.Timestamp):
                timestamp_ms = int(timestamp.timestamp() * 1000)
            elif isinstance(timestamp, str):
                timestamp_ms = int(pd.Timestamp(timestamp).timestamp() * 1000)
            elif isinstance(timestamp, int):
                # Assume it's already in milliseconds
                timestamp_ms = timestamp
            else:
                logger.warning(f"Unable to convert timestamp for {symbol}: {timestamp}")
                return None
            
            # Create the InfluxDB point
            point = {
                "measurement": "market_data",
                "tags": {
                    "symbol": symbol,
                    "exchange": exchange,
                    "data_type": data_type
                },
                "time": timestamp_ms,
                "fields": {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"])
                }
            }
            
            return point
            
        except Exception as e:
            logger.error(f"Error creating point for {symbol}: {e}")
            return None

    def add_to_batch(
        self,
        row: Dict[str, Any],
        symbol: str,
        exchange: str,
        data_type: str
    ) -> None:
        """
        Add a data row to the batch.
        
        If the batch reaches the configured batch_size, it will be automatically
        written to InfluxDB.
        
        Args:
            row (Dict): The data row
            symbol (str): The trading symbol
            exchange (str): The exchange name
            data_type (str): The data type
        """
        point = self._create_point(row, symbol, exchange, data_type)
        
        if point is not None:
            self.batch.append(point)
            logger.debug(f"Added point for {symbol} to batch (size: {len(self.batch)}/{self.batch_size})")
            
            # Write if batch is full
            if len(self.batch) >= self.batch_size:
                self.flush()
        else:
            logger.warning(f"Skipped invalid data point for {symbol}")

    def write_market_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        exchange: str,
        data_type: str = "kline"
    ) -> int:
        """
        Write a DataFrame of market data to InfluxDB.
        
        This method iterates through the DataFrame and adds each row to the batch.
        Invalid rows are skipped with a warning logged.
        
        Args:
            df (pd.DataFrame): DataFrame containing OHLCV data with columns:
                              [time, open, high, low, close, volume]
            symbol (str): The trading symbol (e.g., BTCUSDT)
            exchange (str): The exchange name (e.g., Bybit)
            data_type (str): The data type (default: kline)
            
        Returns:
            int: Number of valid data points added to the batch
        """
        if df.empty:
            logger.warning(f"Empty DataFrame provided for {symbol}")
            return 0
        
        valid_count = 0
        
        for index, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                point = self._create_point(row_dict, symbol, exchange, data_type)
                
                if point is not None:
                    self.batch.append(point)
                    valid_count += 1
                    
                    # Write if batch is full
                    if len(self.batch) >= self.batch_size:
                        self.flush()
                else:
                    logger.debug(f"Skipped invalid row for {symbol} at index {index}")
                    
            except Exception as e:
                logger.error(f"Error processing row for {symbol} at index {index}: {e}")
                continue
        
        logger.info(f"Processed {valid_count} valid data points for {symbol}")
        return valid_count

    def flush(self) -> bool:
        """
        Write all batched points to InfluxDB.
        
        Returns:
            bool: True if write was successful, False otherwise
        """
        if not self.batch:
            logger.debug("Batch is empty, nothing to flush")
            return True
        
        try:
            batch_size = len(self.batch)
            logger.info(f"Flushing batch of {batch_size} points to InfluxDB...")
            
            # Write to InfluxDB
            self.client.write_points(
                self.batch,
                time_precision='ms',
                batch_size=self.batch_size
            )
            
            logger.info(f"Successfully wrote {batch_size} points to InfluxDB")
            self.batch = []
            return True
            
        except Exception as e:
            logger.error(f"Failed to write batch to InfluxDB: {e}")
            logger.warning(f"Batch of {len(self.batch)} points will be retried on next flush")
            return False

    def close(self) -> None:
        """
        Flush any remaining batched points and close the connection.
        
        This should be called at the end of the application to ensure
        all data is written to InfluxDB.
        """
        logger.info("Closing InfluxDB writer...")
        
        # Flush remaining points
        if self.batch:
            logger.info(f"Flushing {len(self.batch)} remaining points...")
            self.flush()
        
        # Close connection
        try:
            self.client.close()
            logger.info("InfluxDB connection closed")
        except Exception as e:
            logger.error(f"Error closing InfluxDB connection: {e}")

    def get_batch_size(self) -> int:
        """Get the current batch size setting."""
        return self.batch_size

    def set_batch_size(self, batch_size: int) -> None:
        """
        Update the batch size.
        
        This can be called to upgrade the batch size for better performance
        in production environments.
        
        Args:
            batch_size (int): The new batch size
        """
        logger.info(f"Updating batch size from {self.batch_size} to {batch_size}")
        self.batch_size = batch_size

    def get_current_batch_count(self) -> int:
        """Get the number of points currently in the batch."""
        return len(self.batch)
