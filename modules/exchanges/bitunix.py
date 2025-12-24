import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import os
from influxdb import InfluxDBClient


class BitunixKline:
    BASE_URL = os.getenv('BITUNIX_API_URL', "https://fapi.bitunix.com")
    
    @staticmethod
    def fetch_historical_kline(currency, days, resolution, start_time=None, end_time=None) -> pd.DataFrame:
        """
        Fetch historical kline/candlestick data from Bitunix.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            days (int): Number of days of history (used if start_time/end_time not provided)
            resolution (int): Interval in minutes (e.g., 1, 5, 15, 30, 60)
            start_time: Optional start datetime (overrides days calculation)
            end_time: Optional end datetime (default is now)
            
        Returns:
            pd.DataFrame: DataFrame with columns ['time', 'open', 'high', 'low', 'close', 'volume']
        """
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
            
            # Ensure all fields are converted to proper types
            # Convert timestamp to datetime (Bitunix uses milliseconds or seconds)
            try:
                # Try milliseconds first
                time_numeric = pd.to_numeric(df['time'], errors='coerce')
                # If values are too large, they're likely milliseconds; if small, seconds
                if time_numeric.max() > 10000000000:  # Likely milliseconds (year 2286 in seconds)
                    df['time'] = pd.to_datetime(time_numeric, unit='ms', utc=True)
                else:
                    df['time'] = pd.to_datetime(time_numeric, unit='s', utc=True)
            except Exception as e:
                print(f"Error converting time field for {currency}: {e}")
                return pd.DataFrame()
            
            # Convert numeric fields with error handling
            try:
                df['open'] = pd.to_numeric(df['open'], errors='coerce')
                df['high'] = pd.to_numeric(df['high'], errors='coerce')
                df['low'] = pd.to_numeric(df['low'], errors='coerce')
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                df['volume'] = pd.to_numeric(df['baseVol'], errors='coerce')  # Use baseVol as volume
            except Exception as e:
                print(f"Error converting numeric fields for {currency}: {e}")
                return pd.DataFrame()
            
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
    def fetch_funding_rate_period(currency: str, days: int = 7) -> dict:
        """
        Get the funding rate settlement period for Bitunix from the internal API.
        
        First tries the official Bitunix market settings API endpoint, then falls back
        to InfluxDB analysis if the API fails.
        
        Args:
            currency (str): Trading pair (e.g., "BTCUSDT")
            days (int): Days for InfluxDB fallback analysis (default: 7)
            
        Returns:
            dict: Dictionary with keys:
                - 'fundingInterval': The funding rate interval in hours
                - 'currency': The trading pair
                - 'timestamp': When this data was fetched
                - 'method': 'api' or 'influxdb_analysis' or 'default'
                - 'note': Description of how data was obtained
        """
        try:
            # First try the internal API endpoint
            api_url = "https://api.bitunix.com/futures/futures/market/setting/list"
            headers = {
                "accept": "*/*",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0 and "data" in result:
                data = result["data"]
                # Navigate through the response structure
                if "tradingGroups" in data and len(data["tradingGroups"]) > 0:
                    symbols = data["tradingGroups"][0].get("symbols", [])
                    contract = next((s for s in symbols if s.get("symbol") == currency), None)
                    
                    if contract and "fundingInterval" in contract:
                        funding_interval = int(contract["fundingInterval"])
                        return {
                            "currency": currency,
                            "fundingInterval": funding_interval,
                            "fundingIntervalMinutes": funding_interval * 60,
                            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                            "method": "api",
                            "note": "Retrieved from Bitunix market settings API"
                        }
        except Exception as api_error:
            print(f"API lookup failed for {currency}, trying InfluxDB: {api_error}")
        
        # Fallback to InfluxDB analysis
        try:
            # Connect to InfluxDB
            host = os.getenv('INFLUXDB_HOST', 'localhost')
            port = int(os.getenv('INFLUXDB_PORT', 8086))
            database = os.getenv('INFLUXDB_DATABASE', 'market_data')
            
            client = InfluxDBClient(host=host, port=port, database=database)
            
            # Query historical funding rates for Bitunix
            symbol_key = f"{currency}_fundingrate_bitunix"
            query = f'''SELECT "close" FROM "market_data" 
                       WHERE "symbol"='{symbol_key}' AND "exchange"='Bitunix' 
                       AND time > now() - {days}d 
                       ORDER BY time DESC'''
            
            result = client.query(query)
            client.close()
            
            if not result:
                # No data in InfluxDB, use default
                return {
                    "currency": currency,
                    "fundingInterval": 8,
                    "fundingIntervalMinutes": 480,
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "method": "default",
                    "note": "No historical funding rate data in InfluxDB"
                }
            
            # Extract funding rates with timestamps
            funding_rates = []
            for point in result.get_points():
                try:
                    timestamp = pd.Timestamp(point['time'])
                    rate = float(point['close'])
                    funding_rates.append({'time': timestamp, 'rate': rate})
                except (ValueError, TypeError, KeyError):
                    continue
            
            if len(funding_rates) < 2:
                return {
                    "currency": currency,
                    "fundingInterval": 8,
                    "fundingIntervalMinutes": 480,
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "method": "default",
                    "note": "Insufficient funding rate data points"
                }
            
            # Sort by time
            funding_rates.sort(key=lambda x: x['time'])
            
            # Calculate intervals between distinct funding rate changes
            intervals_hours = []
            last_rate = None
            last_change_time = None
            
            for rate_info in funding_rates:
                current_rate = rate_info['rate']
                current_time = rate_info['time']
                
                # Only count when the rate changes
                if last_rate is not None and current_rate != last_rate and last_change_time is not None:
                    interval = (current_time - last_change_time).total_seconds() / 3600
                    intervals_hours.append(interval)
                    last_change_time = current_time
                elif last_rate is None:
                    last_change_time = current_time
                
                last_rate = current_rate
            
            if not intervals_hours:
                # No distinct changes found, use time between all points
                intervals_hours = []
                for i in range(1, len(funding_rates)):
                    interval = (funding_rates[i]['time'] - funding_rates[i-1]['time']).total_seconds() / 3600
                    intervals_hours.append(interval)
            
            if intervals_hours:
                # Filter out outliers (gaps > 24 hours typically indicate collection stops)
                regular_intervals = [x for x in intervals_hours if x <= 24]
                
                if regular_intervals:
                    # Find the most common interval (round to 0.5 hour)
                    rounded_intervals = [round(x * 2) / 2 for x in regular_intervals]
                    from collections import Counter
                    interval_counts = Counter(rounded_intervals)
                    most_common_rounded = interval_counts.most_common(1)[0][0]
                else:
                    most_common_rounded = 8
                
                # Determine period based on analysis
                if most_common_rounded > 0 and most_common_rounded < 1:
                    # Sub-hourly updates (real-time or continuous)
                    period = 8  # Use standard period when rates update continuously
                elif most_common_rounded < 2:
                    period = 1
                elif most_common_rounded < 6:
                    period = 4
                else:
                    period = 8
                
                return {
                    "currency": currency,
                    "fundingInterval": int(period),
                    "fundingIntervalMinutes": int(period * 60),
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "method": "influxdb_analysis",
                    "note": f"Analysis of {len(regular_intervals)} rate changes"
                }
            
            # Default fallback
            return {
                "currency": currency,
                "fundingInterval": 8,
                "fundingIntervalMinutes": 480,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "method": "default",
                "note": "Could not analyze intervals"
            }
            
        except Exception as e:
            print(f"Error analyzing funding rate period from InfluxDB for {currency}: {e}")
            return {
                "currency": currency,
                "fundingInterval": 8,
                "fundingIntervalMinutes": 480,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "method": "default",
                "note": f"Error: {str(e)[:50]}"
            }
    
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
            funding_rate = funding_rate / 100.0  # Convert percentage to decimal
            
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
