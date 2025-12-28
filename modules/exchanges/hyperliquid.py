import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os


class HyperliquidKline:
    """
    Hyperliquid exchange API integration for fetching funding rates and market data.
    
    The Hyperliquid API is a POST-based API at https://api.hyperliquid.xyz/info
    """
    BASE_URL = os.getenv('HYPERLIQUID_API_URL', "https://api.hyperliquid.xyz")
    
    @staticmethod
    def fetch_funding_rate_period(coin: str) -> dict:
        """
        Get the funding rate settlement period for Hyperliquid.
        
        Hyperliquid uses an 8-hour funding period for all perpetuals.
        But the funding rate that we get is the hourly rate which is based on 8 hour period devided by 8.
        This is a fixed constant and doesn't need to be fetched from the API.
        
        Args:
            coin (str): Trading coin base (e.g., "BTC", "ETH")
            
        Returns:
            dict: Dictionary with keys:
                - 'fundingInterval': The funding rate interval in hours (8 for Hyperliquid)
                - 'coin': The coin
                - 'timestamp': When this data was fetched
                - 'method': 'constant' (since Hyperliquid uses fixed 8h period)
                - 'note': Description
        """
        try:
            return {
                "coin": coin,
                "fundingInterval": 8,  # Hyperliquid uses fixed 8-hour funding rate period
                "fundingIntervalMinutes": 480,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "method": "constant",
                "note": "Hyperliquid uses fixed 8-hour funding rate period"
            }
        except Exception as e:
            print(f"Error fetching funding rate period for {coin}: {e}")
            return {
                "coin": coin,
                "fundingInterval": 8,
                "fundingIntervalMinutes": 480,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "method": "error",
                "note": f"Error: {str(e)[:50]}"
            }

    @staticmethod
    def fetch_funding_rate(coin: str, days: int = 1) -> pd.DataFrame:
        """
        Fetch funding rate history for a perpetual contract from Hyperliquid.
        
        Fetches the funding history for the specified coin and returns the most recent
        funding rate as a DataFrame in the standard format.
        
        Note: Hyperliquid API returns hourly funding rates (the 8-hour rate divided by 8).
        This method multiplies by 8 to return the full 8-hour funding rate for the settlement period.
        
        Args:
            coin (str): Coin symbol (e.g., "BTC", "ETH", "SOL")
            days (int): Number of days of history to fetch (used to calculate startTime)
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
                         where close = 8-hour funding rate (hourly rate × 8), 
                         and other OHLC fields = funding rate value
        """
        try:
            # Calculate start time (in milliseconds)
            start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            
            url = f"{HyperliquidKline.BASE_URL}/info"
            payload = {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": start_time
            }
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            # Check if result is a list of funding rate entries
            if not isinstance(result, list):
                print(f"Unexpected response format for {coin}: {result}")
                return pd.DataFrame()
            
            if len(result) == 0:
                print(f"No funding rate data returned for {coin}")
                return pd.DataFrame()
            
            # Get the most recent funding rate entry (last entry in the list)
            latest_entry = result[-1]
            
            # Parse the entry
            # Hyperliquid returns: {"time": timestamp_ms, "fundingRate": rate_as_string}
            # Example: "0.000100635" means the hourly rate (which is the 8-hour rate divided by 8)
            # We multiply by 8 to get the full 8-hour funding rate for the settlement period
            funding_rate_str = latest_entry.get("fundingRate", "0")
            hourly_rate = float(funding_rate_str)  # Hourly rate in decimal format
            funding_rate = hourly_rate * 8  # Convert to 8-hour funding rate
            
            # Get the timestamp
            timestamp_ms = latest_entry.get("time", int(datetime.now(timezone.utc).timestamp() * 1000))
            time = pd.Timestamp(timestamp_ms, unit='ms', tz='UTC')
            
            # Create DataFrame in standard format with 8-hour funding rate
            df = pd.DataFrame([{
                'time': time,
                'open': funding_rate,
                'high': funding_rate,
                'low': funding_rate,
                'close': funding_rate,
                'volume': 0.0
            }])
            
            return df
            
        except requests.exceptions.Timeout:
            print(f"Timeout fetching funding rate for {coin} from Hyperliquid")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch funding rate for {coin} from Hyperliquid: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error processing funding rate for {coin} from Hyperliquid: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_latest_funding_rate(coin: str) -> dict:
        """
        Get the most recent funding rate for a symbol from Hyperliquid.
        
        Args:
            coin (str): Coin symbol (e.g., "BTC", "ETH")
            
        Returns:
            dict: {
                'coin': str,
                'fundingRate': float,
                'time': datetime,
                'success': bool
            }
        """
        try:
            df = HyperliquidKline.fetch_funding_rate(coin, days=1)
            
            if df.empty:
                return {
                    'coin': coin,
                    'fundingRate': None,
                    'time': None,
                    'success': False
                }
            
            latest = df.iloc[0]
            return {
                'coin': coin,
                'fundingRate': latest['close'],
                'time': latest['time'],
                'success': True
            }
            
        except Exception as e:
            print(f"Error getting latest funding rate for {coin}: {e}")
            return {
                'coin': coin,
                'fundingRate': None,
                'time': None,
                'success': False
            }

    @staticmethod
    def fetch_historical_kline(currency: str, days: int, resolution: int, start_time=None, end_time=None) -> pd.DataFrame:
        """
        Fetch historical kline/candlestick data from Hyperliquid.
        
        Note: Hyperliquid API does not provide historical candlestick data directly.
        This is a placeholder implementation that returns empty DataFrame.
        Users should use Bybit or other exchanges for OHLC data.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            days (int): Number of days of history
            resolution (int): Interval in minutes
            start_time: Optional start datetime
            end_time: Optional end datetime
            
        Returns:
            pd.DataFrame: Empty DataFrame (Hyperliquid doesn't provide candlestick data)
        """
        print(f"Warning: Hyperliquid API does not provide historical candlestick data.")
        print(f"Please use Bybit, Deribit, or other exchanges for OHLC data.")
        return pd.DataFrame()

    @staticmethod
    def format_funding_rate(rate: float, format_type: str = 'decimal') -> str:
        """
        Format funding rate for display or further processing.
        
        Args:
            rate (float): Funding rate in decimal format (e.g., 0.0001)
            format_type (str): Format type:
                - 'decimal': Raw decimal (0.0001)
                - 'percentage': As percentage (0.01%)
                - 'basis_points': As basis points (1 bp)
                - 'fixed': Fixed 8 decimal places (0.00010000)
        
        Returns:
            str: Formatted funding rate
        """
        if format_type == 'percentage':
            return f"{rate * 100:.10f}%"
        elif format_type == 'basis_points':
            return f"{rate * 10000:.4f} bp"
        elif format_type == 'fixed':
            return f"{rate:.8f}"
        else:  # decimal
            return f"{rate}"

    @staticmethod
    def convert_rate_to_annual(rate: float, period_hours: int = 8) -> float:
        """
        Convert funding rate to annualized percentage.
        
        Args:
            rate (float): Funding rate in decimal format (e.g., 0.0001 = 0.01%)
            period_hours (int): Funding period in hours (default: 8 for Hyperliquid)
        
        Returns:
            float: Annualized funding rate as percentage
        
        Example:
            >>> rate = 0.0001  # 0.01% per 8 hours
            >>> annual = convert_rate_to_annual(rate, 8)
            >>> print(f"{annual:.2f}%")  # Output: "10.95%"
        """
        periods_per_year = 365 * 24 / period_hours
        annual_rate = rate * 100 * periods_per_year
        return annual_rate

