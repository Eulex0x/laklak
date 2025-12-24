import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone

class YFinanceKline:
    
    @staticmethod
    def fetch_historical_kline(symbol: str, days: int, interval: str, start_time=None, end_time=None) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Yahoo Finance.
        
        Args:
            symbol: The ticker symbol (e.g., BTC-USD, AAPL, ^GSPC)
            days: Number of days to fetch (used if start_time/end_time not provided)
            interval: Time resolution - "1m", "2m", "5m", "15m", "30m", "60m", "90m", 
                     "1h", "1d", "5d", "1wk", "1mo", "3mo"
            start_time: Optional start datetime (overrides days calculation)
            end_time: Optional end datetime (default is now)
        
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        try:
            # Use provided timestamps or calculate from days
            if end_time is None:
                end_date = datetime.now(timezone.utc)
            else:
                end_date = end_time if isinstance(end_time, datetime) else datetime.fromtimestamp(end_time, tz=timezone.utc)
            
            if start_time is None:
                start_date = end_date - timedelta(days=days)
            else:
                start_date = start_time if isinstance(start_time, datetime) else datetime.fromtimestamp(start_time, tz=timezone.utc)
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True
            )
            
            if df.empty:
                print(f"No kline data returned for {symbol}")
                return pd.DataFrame()
            
            # Reset index to make datetime a column
            df = df.reset_index()
            
            # Rename columns to match standard format
            column_mapping = {
                'Date': 'time',
                'Datetime': 'time',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure time column is timezone-aware UTC
            if 'time' in df.columns:
                if df['time'].dt.tz is None:
                    df['time'] = df['time'].dt.tz_localize('UTC')
                else:
                    df['time'] = df['time'].dt.tz_convert('UTC')
            
            # Select and reorder columns
            available_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in available_columns if col in df.columns]]
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            # Convert price columns to float
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    df[col] = df[col].astype(float)
            
            if 'volume' in df.columns:
                df['volume'] = df['volume'].astype(float)
            
            return df
            
        except Exception as e:
            print(f"Failed to fetch kline data for {symbol}: {e}")
            return pd.DataFrame()
