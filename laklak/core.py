"""
Core Laklak functionality - Simple API for data collection
"""

from typing import Optional, Union, List, Dict
from datetime import datetime, timedelta
import logging
import sys
import os
import pandas as pd

from modules.exchanges.bybit import BybitKline
from modules.exchanges.deribit import DeribitDVOL
from modules.exchanges.yfinance import YFinanceKline
from modules.influx_writer import InfluxDBWriter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Timeframe mapping: user-friendly to minutes
TIMEFRAME_MAP = {
    '1m': 1, '1min': 1,
    '3m': 3, '3min': 3,
    '5m': 5, '5min': 5,
    '15m': 15, '15min': 15,
    '30m': 30, '30min': 30,
    '1h': 60, '1hour': 60,
    '2h': 120, '2hour': 120,
    '4h': 240, '4hour': 240,
    '6h': 360, '6hour': 360,
    '12h': 720, '12hour': 720,
    '1d': 1440, '1day': 1440,
    '1w': 10080, '1week': 10080,
    '1M': 43200, '1month': 43200,
}

# Maximum supported periods per timeframe (based on 1000 candle limit)
# Calculated as: (1000 candles * timeframe_minutes) / (24 * 60) = max_days
MAX_PERIODS = {
    1: 0.7,      # 1min: ~17 hours (1000min / 1440)
    3: 2,        # 3min: ~2 days (3000min / 1440)
    5: 3,        # 5min: ~3.5 days (5000min / 1440)
    15: 10,      # 15min: ~10 days (15000min / 1440)
    30: 21,      # 30min: ~21 days (30000min / 1440)
    60: 42,      # 1hour: ~42 days (60000min / 1440) - API limit!
    120: 83,     # 2hour: ~83 days
    240: 167,    # 4hour: ~167 days (5.5 months)
    360: 250,    # 6hour: ~250 days (8 months)
    720: 500,    # 12hour: ~500 days (1.4 years)
    1440: 1000,  # 1day: ~1000 days (2.7 years)
    10080: 3650, # 1week: up to 10 years (generous for yfinance)
    43200: 3650, # 1month: up to 10 years (generous for yfinance)
}


class Laklak:
    """
    Simple, unified interface for collecting financial market data.
    
    Examples:
        >>> fetcher = Laklak()
        >>> fetcher.collect("BTCUSDT", exchange="bybit")
        >>> fetcher.collect(["BTCUSDT", "ETHUSDT"], exchange="bybit")
        >>> fetcher.backfill("AAPL", exchange="yfinance", days=30)
    """
    
    def __init__(self, 
                 use_influxdb: bool = True,
                 influx_host: Optional[str] = None, 
                 influx_port: Optional[int] = None,
                 influx_db: Optional[str] = None,
                 influx_username: Optional[str] = None,
                 influx_password: Optional[str] = None):
        """
        Initialize Laklak with optional InfluxDB configuration.
        
        Args:
            use_influxdb: Whether to use InfluxDB (default: True)
            influx_host: InfluxDB host (default from env: localhost)
            influx_port: InfluxDB port (default from env: 8086)
            influx_db: InfluxDB database name (default from env: market_data)
            influx_username: InfluxDB username (optional)
            influx_password: InfluxDB password (optional)
        """
        self.use_influxdb = use_influxdb
        self.influx_host = influx_host
        self.influx_port = influx_port
        self.influx_db = influx_db
        self.influx_username = influx_username
        self.influx_password = influx_password
        self.writer = None
        
    def _get_writer(self) -> Optional[InfluxDBWriter]:
        """Get or create InfluxDB writer instance."""
        if not self.use_influxdb:
            return None
            
        if self.writer is None:
            self.writer = InfluxDBWriter(
                host=self.influx_host,
                port=self.influx_port,
                database=self.influx_db,
                username=self.influx_username,
                password=self.influx_password
            )
        return self.writer
    
    def _convert_to_influx_format(self, df, symbol, exchange, data_type):
        """Convert DataFrame to InfluxDB format."""
        data_points = []
        for _, row in df.iterrows():
            point = {
                "measurement": "market_data",
                "tags": {
                    "symbol": f"{symbol}_{exchange.upper()}",
                    "exchange": exchange,
                    "data_type": data_type
                },
                "time": row.get('timestamp', row.name),
                "fields": {}
            }
            
            # Add available fields
            for field in ['open', 'high', 'low', 'close', 'volume']:
                if field in row:
                    point["fields"][field] = float(row[field])
            
            if point["fields"]:  # Only add if we have fields
                data_points.append(point)
        
        return data_points
    
    def _parse_timeframe(self, timeframe: Union[str, int]) -> int:
        """
        Parse timeframe string to minutes.
        
        Args:
            timeframe: Timeframe as string ('1h', '5m', '1d') or int (minutes)
            
        Returns:
            int: Timeframe in minutes
        """
        if isinstance(timeframe, int):
            return timeframe
        
        timeframe_lower = timeframe.lower()
        if timeframe_lower in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[timeframe_lower]
        
        raise ValueError(
            f"Invalid timeframe '{timeframe}'. "
            f"Supported: {', '.join(sorted(set(TIMEFRAME_MAP.keys())))}"
        )
    
    def _validate_period(self, timeframe_minutes: int, days: float) -> float:
        """
        Validate and adjust period based on timeframe limits.
        
        Args:
            timeframe_minutes: Timeframe in minutes
            days: Requested days
            
        Returns:
            float: Adjusted days (capped at maximum)
        """
        max_days = MAX_PERIODS.get(timeframe_minutes, 365)
        if days > max_days:
            logger.warning(
                f"Requested {days} days exceeds maximum {max_days} days for "
                f"{timeframe_minutes}min timeframe. Capping to {max_days} days."
            )
            return max_days
        return days

    def collect(self, 
                symbols: Union[str, List[str]], 
                exchange: str,
                timeframe: Union[str, int] = '1h',
                period: Union[str, int] = 30) -> Union[bool, Dict[str, pd.DataFrame]]:
        """
        Collect latest data for one or more symbols.
        
        Args:
            symbols: Single symbol or list of symbols
            exchange: Exchange name ('bybit', 'deribit', 'yfinance')
            timeframe: Time interval - string like '1m', '5m', '15m', '1h', '4h', '1d', '1w'
                      or integer in minutes (default: '1h')
            period: Data period - string like '7d', '30d', '1y' or integer days
                   (default: 30 days)
            
        Returns:
            If use_influxdb=True: bool (True if successful)
            If use_influxdb=False: Dict[str, pd.DataFrame] (symbol -> DataFrame with OHLCV data)
            
        Note:
            Bybit API limits responses to 1000 candles. Period is automatically capped:
            - 1min: max ~17 hours
            - 5min: max ~3.5 days
            - 15min: max ~10 days
            - 1hour: max ~42 days (not 1 year!)
            - 4hour: max ~167 days (~5.5 months)
            - 1day: max ~1000 days (~2.7 years)
            
        Examples:
            >>> # 1 hour candles, last 30 days (default, within limit)
            >>> fetcher.collect("BTCUSDT", exchange="bybit")
            
            >>> # 5 minute candles, last 3 days (within limit)
            >>> fetcher.collect("BTCUSDT", exchange="bybit", timeframe="5m", period=3)
            
            >>> # 4 hour candles, last 5 months (within limit)
            >>> fetcher.collect("ETHUSDT", exchange="bybit", timeframe="4h", period=150)
            
            >>> # Daily candles, last 2 years (within limit)
            >>> fetcher.collect(["AAPL", "GOOGL"], exchange="yfinance", timeframe="1d", period=730)
            
            >>> # 15 min candles, 10 days (max for this timeframe)
            >>> fetcher.collect(["BTC-USD", "ETH-USD"], exchange="yfinance", timeframe="15m", period=10)
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # Parse timeframe
        resolution = self._parse_timeframe(timeframe)
        
        # Parse period (support '7d', '30d', '1y' format)
        if isinstance(period, str):
            period_lower = period.lower()
            if period_lower.endswith('d'):
                days = float(period_lower[:-1])
            elif period_lower.endswith('w'):
                days = float(period_lower[:-1]) * 7
            elif period_lower.endswith('m'):
                days = float(period_lower[:-1]) * 30
            elif period_lower.endswith('y'):
                days = float(period_lower[:-1]) * 365
            else:
                days = float(period)
        else:
            days = float(period)
        
        # Validate period for timeframe
        days = self._validate_period(resolution, days)
        
        exchange = exchange.lower()
        writer = self._get_writer()
        
        logger.info(
            f"Collecting {len(symbols)} symbols from {exchange} "
            f"[timeframe: {timeframe}, period: {days} days]"
        )
        
        # Store collected DataFrames when InfluxDB is disabled
        collected_data = {} if not self.use_influxdb else None
        success_count = 0
        
        for symbol in symbols:
            try:
                data = None
                df_raw = None
                
                if exchange == "bybit":
                    df_raw = BybitKline.fetch_historical_kline(symbol, days, resolution)
                    if df_raw is not None and not df_raw.empty:
                        data = self._convert_to_influx_format(df_raw, symbol, "bybit", "kline")
                elif exchange == "deribit":
                    base_currency = symbol.replace("USDT", "").replace("USD", "")
                    df_raw = DeribitDVOL.fetch_historical_dvol(base_currency, days, resolution * 60)
                    if df_raw is not None and not df_raw.empty:
                        data = self._convert_to_influx_format(df_raw, f"{base_currency}_DVOL", "deribit", "dvol")
                elif exchange == "yfinance":
                    df_raw = YFinanceKline.fetch_historical_data(symbol, days, resolution)
                    if df_raw is not None and not df_raw.empty:
                        data = self._convert_to_influx_format(df_raw, symbol, "yfinance", "kline")
                else:
                    logger.error(f"Unknown exchange: {exchange}")
                    continue
                
                if data and len(data) > 0:
                    if writer:
                        writer.write_batch(data)
                        logger.info(f"✓ Collected and wrote {len(data)} points for {symbol}")
                    else:
                        # Store DataFrame for return when InfluxDB is disabled
                        if df_raw is not None:
                            collected_data[symbol] = df_raw
                        logger.info(f"✓ Collected {len(data)} points for {symbol} (InfluxDB disabled)")
                    success_count += 1
                else:
                    logger.warning(f"✗ No data returned for {symbol}")
                    
            except Exception as e:
                logger.error(f"✗ Failed to collect {symbol}: {str(e)}")
                continue
        
        logger.info(f"Collection complete: {success_count}/{len(symbols)} successful")
        
        # Return data or success status depending on mode
        if self.use_influxdb:
            return success_count == len(symbols)
        else:
            return collected_data
    
    def backfill(self,
                 symbols: Union[str, List[str]],
                 exchange: str,
                 timeframe: Union[str, int] = '4h',
                 period: Union[str, int] = 150) -> Union[bool, Dict[str, pd.DataFrame]]:
        """
        Backfill historical data for symbols.
        
        Args:
            symbols: Single symbol or list of symbols
            exchange: Exchange name ('bybit', 'deribit', 'yfinance')
            timeframe: Time interval like '1m', '5m', '15m', '1h', '4h', '1d' (default: '4h')
            period: How far back - string like '30d', '1y' or integer days (default: 150 days ~5 months)
            
        Returns:
            If use_influxdb=True: bool (True if successful)
            If use_influxdb=False: Dict[str, pd.DataFrame] (symbol -> DataFrame with OHLCV data)
            
        Note:
            Default changed to 4h/150d to respect Bybit's 1000 candle limit.
            For 1 hour data, max period is ~42 days (1000 hours).
            
        Examples:
            >>> # 4 hour candles, 150 days (default, ~900 candles)
            >>> fetcher.backfill("BTCUSDT", exchange="bybit")
            
            >>> # Daily candles, 2 years (~730 candles)
            >>> fetcher.backfill("BTCUSDT", exchange="bybit", timeframe="1d", period="2y")
            
            >>> # 1 hour candles, 40 days (~960 candles, within limit)
            >>> fetcher.backfill("ETHUSDT", exchange="bybit", timeframe="1h", period=40)
            
            >>> # 4 hour candles, 6 months (within limit)
            >>> fetcher.backfill(["AAPL", "GOOGL"], exchange="yfinance", timeframe="4h", period=180)
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        logger.info(f"Starting backfill: {len(symbols)} symbols, timeframe={timeframe}, period={period}")
        
        return self.collect(symbols, exchange, timeframe, period)


# Convenience functions for simple usage
def collect(symbol: Union[str, List[str]], 
            exchange: str,
            timeframe: Union[str, int] = '1h',
            period: Union[str, int] = 30,
            **kwargs) -> Union[bool, Dict[str, pd.DataFrame]]:
    """
    Quick function to collect data without creating a Laklak instance.
    
    Args:
        symbol: Single symbol or list of symbols
        exchange: Exchange name ('bybit', 'deribit', 'yfinance')
        timeframe: Time interval - '1m', '5m', '15m', '1h', '4h', '1d', '1w' (default: '1h')
        period: Data period - '7d', '30d', '1y' or integer days (default: 30)
        **kwargs: Additional arguments (e.g., use_influxdb=False to get data back)
    
    Returns:
        If use_influxdb=True (default): bool (True if successful)
        If use_influxdb=False: Dict[str, pd.DataFrame] (symbol -> DataFrame with OHLCV data)
    
    Examples:
        >>> from laklak import collect
        >>> 
        >>> # Write to InfluxDB (default behavior)
        >>> collect("BTCUSDT", exchange="bybit")
        >>> 
        >>> # Get data as DataFrame without InfluxDB
        >>> data = collect("BTCUSDT", exchange="bybit", timeframe="5m", period="7d", use_influxdb=False)
        >>> btc_df = data["BTCUSDT"]
        >>> print(btc_df.head())
        >>> 
        >>> # Multiple symbols
        >>> data = collect(["AAPL", "GOOGL"], exchange="yfinance", timeframe="1d", period="1y", use_influxdb=False)
        >>> aapl_df = data["AAPL"]
        >>> googl_df = data["GOOGL"]
    """
    fetcher = Laklak(**kwargs)
    return fetcher.collect(symbol, exchange, timeframe, period)


def backfill(symbol: Union[str, List[str]], 
             exchange: str,
             timeframe: Union[str, int] = '4h',
             period: Union[str, int] = 150,
             **kwargs) -> Union[bool, Dict[str, pd.DataFrame]]:
    """
    Quick function to backfill data without creating a Laklak instance.
    
    Args:
        symbol: Single symbol or list of symbols
        exchange: Exchange name ('bybit', 'deribit', 'yfinance')
        timeframe: Time interval like '1h', '4h', '1d' (default: '4h')
        period: How far back - '30d', '1y' or integer days (default: 150 days)
        **kwargs: Additional arguments (e.g., use_influxdb=False to get data back)
    
    Returns:
        If use_influxdb=True (default): bool (True if successful)
        If use_influxdb=False: Dict[str, pd.DataFrame] (symbol -> DataFrame with OHLCV data)
    
    Note:
        Default is 4h/150d to respect Bybit's 1000 candle limit (~900 candles).
    
    Examples:
        >>> from laklak import backfill
        >>> 
        >>> # Write to InfluxDB (default)
        >>> backfill("BTCUSDT", exchange="bybit")
        >>> 
        >>> # Get data without InfluxDB
        >>> data = backfill("BTCUSDT", exchange="bybit", timeframe="1d", period="2y", use_influxdb=False)
        >>> btc_df = data["BTCUSDT"]
        >>> 
        >>> # 1 hour, 40 days (~960 candles, safe)
        >>> data = backfill("ETHUSDT", exchange="bybit", timeframe="1h", period=40, use_influxdb=False)
    """
    fetcher = Laklak(**kwargs)
    return fetcher.backfill(symbol, exchange, timeframe, period)
