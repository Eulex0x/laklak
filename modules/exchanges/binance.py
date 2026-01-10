import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from typing import Union
import os
import logging

logger = logging.getLogger('binance')


class BinanceFuturesKline:
    """
    Binance Futures exchange API integration for fetching OHLC data.
    
    Binance Futures API: https://fapi.binance.com
    """
    BASE_URL = os.getenv('BINANCE_API_URL', "https://fapi.binance.com")
    
    # Mapping of interval strings to their values
    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M",
        # Legacy support for minutes as integers
        "60": "1h",
        "240": "4h",
        "1440": "1d",
    }
    
    @staticmethod
    def fetch_historical_kline(
        symbol: str,
        days: int,
        resolution: Union[int, str] = 60,
        start_time=None,
        end_time=None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Binance Futures.
        
        Args:
            symbol (str): Trading pair (e.g., "BTCUSDT")
            days (int): Number of days to fetch (used if start_time not provided)
            resolution (int | str): Time resolution in minutes or interval string.
                - Integer minutes: 60, 240, 1440, etc.
                - Interval strings: "1m", "5m", "1h", "4h", "1d", etc.
            start_time: Optional start timestamp in milliseconds
            end_time: Optional end timestamp in milliseconds
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        try:
            # Convert resolution to interval string
            if isinstance(resolution, int):
                # Convert minutes to interval string
                interval = BinanceFuturesKline.INTERVAL_MAP.get(str(resolution), "1h")
            else:
                interval = BinanceFuturesKline.INTERVAL_MAP.get(str(resolution), resolution)
            
            # Calculate time range
            if end_time is None:
                end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            if start_time is None:
                start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
            all_data = []
            current_start = start_time
            
            # Binance limits to 1500 klines per request
            while current_start < end_time:
                url = f"{BinanceFuturesKline.BASE_URL}/fapi/v1/klines"
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": current_start,
                    "endTime": end_time,
                    "limit": 1500
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict) and "code" in data:
                    # Error response
                    error_msg = data.get('msg', 'Unknown error')
                    error_msg_lower = error_msg.lower()
                    if "symbol invalid" in error_msg_lower or "not found" in error_msg_lower or "invalid symbol" in error_msg_lower:
                        logger.debug(f"Symbol {symbol} not available on Binance (skipping)")
                    else:
                        logger.warning(f"API error for {symbol} funding rate: {error_msg}")
                    break
                
                if not data or len(data) == 0:
                    break
                
                all_data.extend(data)
                
                # Move to next batch
                # Each kline entry has timestamps at indices 0 (open) and 6 (close)
                current_start = data[-1][6] + 1  # Move to after the last kline
                
                # Prevent infinite loops
                if len(data) < 1500:
                    break
            
            if not all_data:
                print(f"No kline data returned for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            # Binance returns: [open_time, open, high, low, close, volume, ...]
            df = pd.DataFrame(
                all_data,
                columns=[
                    'time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ]
            )
            
            # Convert time from milliseconds to datetime
            df['time'] = pd.to_datetime(df['time'], unit='ms', utc=True)
            
            # Select and convert required columns
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']].copy()
            
            # Convert price/volume columns to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch kline data for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing kline data for {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def fetch_funding_rate_period(symbol: str) -> dict:
        """
        Fetch funding rate settlement period for a perpetual contract from Binance Futures.
        
        Binance Futures uses an 8-hour funding rate period.
        
        Args:
            symbol (str): Trading pair (e.g., "BTCUSDT")
            
        Returns:
            dict: Dictionary with keys:
                - 'fundingInterval': The funding rate interval in hours (8 for Binance)
                - 'symbol': The trading pair
                - 'timestamp': When this data was fetched
                - 'method': 'constant' (Binance uses fixed 8h period)
        """
        try:
            return {
                "symbol": symbol,
                "fundingInterval": 8,  # Binance Futures uses fixed 8-hour funding rate period
                "fundingIntervalMinutes": 480,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "method": "constant",
                "note": "Binance Futures uses fixed 8-hour funding rate period"
            }
        except Exception as e:
            print(f"Error fetching funding rate period for {symbol}: {e}")
            return {
                "symbol": symbol,
                "fundingInterval": 8,
                "fundingIntervalMinutes": 480,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "method": "error",
                "note": f"Error: {str(e)[:50]}"
            }
    
    @staticmethod
    def fetch_funding_rate(symbol: str, days: int = 1) -> pd.DataFrame:
        """
        Fetch funding rate history for a perpetual contract from Binance Futures.
        
        Args:
            symbol (str): Trading pair (e.g., "BTCUSDT")
            days (int): Number of days of history to fetch
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
                         where close = funding rate
        """
        try:
            # Calculate time range
            end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
            all_data = []
            current_start = start_time
            
            # Binance limits to 1000 records per request
            while current_start < end_time:
                url = f"{BinanceFuturesKline.BASE_URL}/fapi/v1/fundingRate"
                params = {
                    "symbol": symbol,
                    "startTime": current_start,
                    "endTime": end_time,
                    "limit": 1000
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict) and "code" in data:
                    # Error response
                    error_msg = data.get('msg', 'Unknown error').lower()
                    if "symbol invalid" in error_msg or "not found" in error_msg or "invalid symbol" in error_msg:
                        logger.debug(f"Symbol {symbol} not available on Binance (skipping)")
                    else:
                        logger.warning(f"API error for {symbol} funding rate: {data.get('msg', 'Unknown error')}")
                    break
                
                if not data or len(data) == 0:
                    break
                
                all_data.extend(data)
                
                # Move to next batch
                current_start = data[-1]['fundingTime'] + 1
                
                # Prevent infinite loops
                if len(data) < 1000:
                    break
            
            if not all_data:
                print(f"No funding rate data returned for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            
            # Rename columns to match standard format
            df = df.rename(columns={'fundingTime': 'time', 'fundingRate': 'close'})
            
            # Convert time from milliseconds to datetime
            df['time'] = pd.to_datetime(df['time'], unit='ms', utc=True)
            
            # Convert funding rate to float
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # Select required columns
            df = df[['time', 'close']].copy()
            
            # Add OHLCV columns (for funding rate, all OHLCV = funding rate)
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0  # Volume not applicable for funding rates
            
            # Reorder columns
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch funding rate for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing funding rate for {symbol}: {e}")
            return pd.DataFrame()
