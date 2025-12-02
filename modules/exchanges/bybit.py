import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from config import get_config

class BybitKline:
    BASE_URL = get_config().get('BYBIT_API_URL', "https://api.bybit.com")
    
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
