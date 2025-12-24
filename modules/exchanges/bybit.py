import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os

class BybitKline:
    BASE_URL = os.getenv('BYBIT_API_URL', "https://api.bybit.com")
    
    @staticmethod
    def fetch_funding_rate_period(currency: str) -> dict:
        """
        Fetch funding rate settlement period for a perpetual contract from Bybit.
        
        This returns metadata about the funding rate period (e.g., 8 hours, 4 hours, 1 hour).
        This information is static and doesn't change once set for a contract.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            
        Returns:
            dict: Dictionary with keys:
                - 'fundingInterval': The funding rate interval in hours (e.g., 8, 4, 1)
                - 'currency': The trading pair
                - 'timestamp': When this data was fetched
        """
        try:
            url = f"{BybitKline.BASE_URL}/v5/market/instruments-info"
            params = {
                "category": "linear",
                "symbol": currency
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("retCode") != 0:
                print(f"API error fetching funding period for {currency}: {result.get('retMsg', 'Unknown error')}")
                return {}
            
            if "result" not in result or "list" not in result["result"] or not result["result"]["list"]:
                print(f"No instrument info returned for {currency}")
                return {}
            
            instrument = result["result"]["list"][0]
            
            # Extract funding interval (in minutes, convert to hours)
            funding_interval_minutes = int(instrument.get("fundingInterval", 0))
            funding_interval_hours = funding_interval_minutes // 60  # Convert minutes to hours
            
            return {
                "currency": currency,
                "fundingInterval": funding_interval_hours,
                "fundingIntervalMinutes": funding_interval_minutes,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch funding rate period for {currency}: {e}")
            return {}
        except Exception as e:
            print(f"Error processing funding rate period for {currency}: {e}")
            return {}

    @staticmethod
    def fetch_funding_rate(currency, days) -> pd.DataFrame:
        """
        Fetch funding rate history for a perpetual contract.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            days (int): Number of days of history
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
                         where close = funding rate
        """
        try:
            end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
            start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
            all_data = []
            current_start = start_time
            
            while current_start < end_time:
                url = f"{BybitKline.BASE_URL}/v5/market/funding/history"
                params = {
                    "category": "linear",
                    "symbol": currency,
                    "startTime": current_start,
                    "endTime": end_time,
                    "limit": 200
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                result = response.json()
                
                if result.get("retCode") != 0:
                    print(f"API error for {currency} funding rate: {result.get('retMsg', 'Unknown error')}")
                    break
                
                if "result" not in result or "list" not in result["result"]:
                    print(f"No funding rate data returned for {currency}")
                    break
                
                funding_data = result["result"]["list"]
                if not funding_data:
                    break
                
                all_data.extend(funding_data)
                
                oldest_timestamp = int(funding_data[-1]["fundingRateTimestamp"])
                if oldest_timestamp <= current_start or len(funding_data) < 200:
                    break
                
                current_start = oldest_timestamp
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            df['fundingRateTimestamp'] = pd.to_numeric(df['fundingRateTimestamp'])
            df['time'] = pd.to_datetime(df['fundingRateTimestamp'], unit='ms', utc=True)
            df['fundingRate'] = pd.to_numeric(df['fundingRate'])
            
            # Convert to standard OHLCV format (funding rate in all price fields)
            df['open'] = df['fundingRate']
            df['high'] = df['fundingRate']
            df['low'] = df['fundingRate']
            df['close'] = df['fundingRate']
            df['volume'] = 0.0
            
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('time').reset_index(drop=True)
            df = df.drop_duplicates(subset=['time'], keep='last')
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch funding rate for {currency}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing funding rate for {currency}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def fetch_historical_kline(currency, days, resolution, start_time=None, end_time=None) -> pd.DataFrame:
        try:
            # Use provided timestamps or calculate from days
            if end_time is None:
                end_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            else:
                end_timestamp = int(end_time.timestamp() * 1000) if hasattr(end_time, 'timestamp') else int(end_time)
            
            if start_time is None:
                start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            else:
                start_timestamp = int(start_time.timestamp() * 1000) if hasattr(start_time, 'timestamp') else int(start_time)
            
            all_data = []
            current_end = end_timestamp
            
            # Fetch data in chunks (API may have limits)
            while current_end > start_timestamp:
                url = f"{BybitKline.BASE_URL}/v5/market/kline"
                params = {
                    "category": "linear",
                    "symbol": currency,
                    "start": start_timestamp,
                    "end": current_end,
                    "interval": str(resolution),
                    "limit": 1000
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                result = response.json()
                
                if "result" not in result or "list" not in result["result"]:
                    print(f"No kline data returned for {currency}")
                    break
                
                # Parse the candle data
                candles = result["result"]["list"]
                if not candles:
                    break
                    
                all_data.extend(candles)
                
                # Check for continuation
                continuation = result["result"].get("continuation")
                if continuation is None:
                    break
                    
                current_end = continuation
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_numeric(df['timestamp'])
            df['time'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)            
            # Drop the timestamp column and reorder
            df = df[['time', 'open', 'high', 'low', 'close', 'volume', 'turnover']]
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch Kline data: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing Kline data: {e}")
            return pd.DataFrame()
