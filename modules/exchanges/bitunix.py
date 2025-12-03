import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os


class BitunixKline:
    BASE_URL = os.getenv('BITUNIX_API_URL', "https://fapi.bitunix.com")
    
    @staticmethod
    def fetch_historical_kline(currency, days, resolution) -> pd.DataFrame:
        """
        Fetch historical kline/candlestick data from Bitunix.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            days (int): Number of days of history
            resolution (int): Interval in minutes (e.g., 1, 5, 15, 30, 60)
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        try:
            # Calculate timestamps (Bitunix uses milliseconds)
            end_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
            # Convert resolution to interval format (e.g., "15m", "1h", "1d")
            if resolution < 60:
                interval = f"{resolution}m"
            elif resolution == 60:
                interval = "1h"
            elif resolution == 240:
                interval = "4h"
            elif resolution == 1440:
                interval = "1d"
            else:
                interval = f"{resolution}m"
            
            url = f"{BitunixKline.BASE_URL}/api/v1/futures/market/kline"
            params = {
                "symbol": currency,
                "startTime": start_timestamp,
                "endTime": end_timestamp,
                "interval": interval
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Check response status
            if result.get("code") != 0:
                error_msg = result.get("msg", "Unknown error")
                print(f"API error for {currency}: {error_msg}")
                return pd.DataFrame()
            
            # Extract kline data
            if "data" not in result or not result["data"]:
                print(f"No kline data returned for {currency}")
                return pd.DataFrame()
            
            candles = result["data"]
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            
            # Convert timestamp to datetime (Bitunix uses milliseconds)
            df['time'] = pd.to_datetime(pd.to_numeric(df['time']), unit='ms', utc=True)
            
            # Convert numeric fields
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            df['volume'] = pd.to_numeric(df['baseVol'])  # Use baseVol as volume
            
            # Select and reorder columns
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        except requests.exceptions.Timeout:
            print(f"Timeout fetching kline data for {currency} from Bitunix")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch kline data for {currency} from Bitunix: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing kline data for {currency} from Bitunix: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def fetch_funding_rate(currency) -> pd.DataFrame:
        """
        Fetch current funding rate for a perpetual contract from Bitunix.
        
        Note: Bitunix API only returns current funding rate, not historical data.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
                         where close = funding rate
        """
        try:
            url = f"{BitunixKline.BASE_URL}/api/v1/futures/market/funding_rate"
            params = {
                "symbol": currency
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Check response status
            if result.get("code") != 0:
                error_msg = result.get("msg", "Unknown error")
                print(f"API error for {currency} funding rate: {error_msg}")
                return pd.DataFrame()
            
            # Extract funding rate data
            if "data" not in result:
                print(f"No funding rate data returned for {currency}")
                return pd.DataFrame()
            
            data = result["data"]
            funding_rate = float(data.get("fundingRate", 0))
            
            # Create DataFrame with current timestamp
            current_time = datetime.now(timezone.utc)
            
            df = pd.DataFrame([{
                'time': current_time,
                'open': funding_rate,
                'high': funding_rate,
                'low': funding_rate,
                'close': funding_rate,
                'volume': 0.0
            }])
            
            return df
            
        except requests.exceptions.Timeout:
            print(f"Timeout fetching funding rate for {currency} from Bitunix")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch funding rate for {currency} from Bitunix: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing funding rate for {currency} from Bitunix: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_latest_funding_rate(currency) -> dict:
        """
        Get the most recent funding rate and market data for a symbol.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            
        Returns:
            dict: {
                'symbol': str,
                'fundingRate': float,
                'markPrice': float,
                'lastPrice': float,
                'timestamp': datetime
            }
        """
        try:
            url = f"{BitunixKline.BASE_URL}/api/v1/futures/market/funding_rate"
            params = {
                "symbol": currency
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0 or "data" not in result:
                return {}
            
            data = result["data"]
            
            return {
                'symbol': data.get('symbol'),
                'fundingRate': float(data.get('fundingRate', 0)),
                'markPrice': float(data.get('markPrice', 0)),
                'lastPrice': float(data.get('lastPrice', 0)),
                'timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            print(f"Error fetching latest funding rate for {currency} from Bitunix: {e}")
            return {}
