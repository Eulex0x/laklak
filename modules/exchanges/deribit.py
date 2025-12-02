import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os

class DeribitDVOL:
    BASE_URL = os.getenv('DERIBIT_API_URL', "https://www.deribit.com/api/v2")
    
    @staticmethod
    def fetch_historical_dvol(currency, days, resolution) -> pd.DataFrame:
        """
        Fetch historical DVOL (volatility index) data from Deribit.
        
        Args:
            currency: The currency symbol (BTC, ETH, USDC, USDT, EURR)
            days: Number of days to fetch (will fetch in chunks if needed)
            resolution: Time resolution - "1" (1min), "60" (1hr), "3600" (1day), "43200" (12hr), "1D" (1day)
        
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        try:
            # Calculate timestamps
            end_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
            all_data = []
            current_end = end_timestamp
            
            # Fetch data in chunks (API may have limits)
            while current_end > start_timestamp:
                url = f"{DeribitDVOL.BASE_URL}/public/get_volatility_index_data"
                params = {
                    "currency": currency,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": current_end,
                    "resolution": resolution 
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                result = response.json()
                
                if "result" not in result or "data" not in result["result"]:
                    print(f"No volatility index data returned for {currency}")
                    break
                
                # Parse the candle data
                candles = result["result"]["data"]
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
            
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_numeric(df['timestamp'])
            df['time'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            
            # Add volume column with 0 (DVOL doesn't have volume, but InfluxDB writer expects it)
            df['volume'] = 0.0
            
            # Drop the timestamp column and reorder
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch DVOL data: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing DVOL data: {e}")
            return pd.DataFrame()
