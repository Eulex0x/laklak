import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os

class DeribitDVOL:
    BASE_URL = os.getenv('DERIBIT_API_URL', "https://www.deribit.com/api/v2")
    
    @staticmethod
    def _extract_currency(symbol: str) -> str:
        """
        Extract currency code from trading symbol.
        Examples: BTCUSDT -> BTC, ETHUSDT -> ETH, BTC -> BTC
        """
        # Remove common suffixes
        for suffix in ['USDT', 'USDC', 'USD', 'PERP']:
            if symbol.endswith(suffix):
                return symbol[:-len(suffix)]
        # If no suffix found, return as-is (already currency code)
        return symbol
    
    @staticmethod
    def fetch_historical_dvol(currency, days, resolution, start_time=None, end_time=None) -> pd.DataFrame:
        """
        Fetch historical DVOL (volatility index) data from Deribit.
        
        Args:
            currency: The currency symbol (can be BTC, ETH, BTCUSDT, ETHUSDT, etc.)
                     Deribit supported currencies: BTC, ETH, SOL, USDC, etc.
            days: Number of days to fetch (used if start_time/end_time not provided)
            resolution: Time resolution - "1" (1min), "60" (1hr), "3600" (1day), "43200" (12hr), "1D" (1day)
            start_time: Optional start datetime (overrides days calculation)
            end_time: Optional end datetime (default is now)
        
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        try:
            # Extract currency code from symbol (e.g., BTCUSDT -> BTC)
            deribit_currency = DeribitDVOL._extract_currency(currency)
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
                url = f"{DeribitDVOL.BASE_URL}/public/get_volatility_index_data"
                params = {
                    "currency": deribit_currency,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": current_end,
                    "resolution": resolution 
                }
                
                response = requests.get(url, params=params, timeout=10)
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
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # 400 Bad Request - likely unsupported currency for Deribit
                # Silently skip instead of logging errors
                return pd.DataFrame()
            print(f"Failed to fetch DVOL data: {e}")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch DVOL data: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing DVOL data: {e}")
            return pd.DataFrame()
