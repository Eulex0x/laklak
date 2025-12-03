import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os

class BybitKline:
    BASE_URL = os.getenv('BYBIT_API_URL', "https://api.bybit.com")
    
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
    def fetch_historical_kline(currency, days, resolution) -> pd.DataFrame:
        try:
            # Calculate timestamps
            end_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
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
                
                response = requests.get(url, params=params)
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
