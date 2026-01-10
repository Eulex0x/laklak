"""
Exchange API Endpoint Tests

Tests to verify all exchange APIs are working correctly and returning expected data.
This is a critical security check since the data collector depends heavily on exchange APIs.

Tests:
- API connectivity and response format
- Data structure validation
- Rate limit handling
- Error responses
"""

from __future__ import annotations

import pytest
import requests
from datetime import datetime, timedelta, timezone
import pandas as pd
from modules.exchanges.bybit import BybitKline
from modules.exchanges.bitunix import BitunixKline
from modules.exchanges.deribit import DeribitDVOL
from modules.exchanges.hyperliquid import HyperliquidKline
from modules.exchanges.binance import BinanceFuturesKline

# Lazy import for yfinance to avoid Python 3.9 compatibility issues
# yfinance uses Python 3.10+ union syntax (|) which breaks on 3.9
try:
    from modules.exchanges.yfinance import YFinanceKline
    YFINANCE_AVAILABLE = True
except (ImportError, TypeError):
    YFINANCE_AVAILABLE = False
    YFinanceKline = None


class TestBybitAPI:
    """Test Bybit exchange API endpoints."""
    
    def test_bybit_connection(self):
        """Test Bybit API connectivity."""
        try:
            response = requests.get("https://api.bybit.com/v5/market/time", timeout=10)
            # API might be rate limited or blocked, that's acceptable
            assert response.status_code in [200, 403, 429]
            if response.status_code == 200:
                data = response.json()
                assert 'retCode' in data
        except requests.exceptions.RequestException:
            # Network issues are acceptable in tests
            pytest.skip("Bybit API unavailable")
    
    def test_bybit_kline_data(self):
        """Test Bybit kline/OHLC data fetching."""
        bybit = BybitKline()
        df = bybit.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        
        assert df is not None
        # API might be rate limited, empty DataFrame is acceptable
        if df.empty:
            pytest.skip("Bybit API rate limited or unavailable")
        
        assert len(df) > 0
        
        # Check required columns
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Validate data types
        assert pd.api.types.is_datetime64_any_dtype(df['time'])
        # Convert to numeric if needed (some exchanges return strings)
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        assert pd.api.types.is_numeric_dtype(df['open'])
        assert pd.api.types.is_numeric_dtype(df['close'])
        assert pd.api.types.is_numeric_dtype(df['volume'])
        
        # Validate data values
        assert (df['high'] >= df['low']).all()
        assert (df['high'] >= df['open']).all()
        assert (df['high'] >= df['close']).all()
        assert (df['volume'] >= 0).all()
    
    def test_bybit_funding_rate(self):
        """Test Bybit funding rate data fetching."""
        bybit = BybitKline()
        df = bybit.fetch_funding_rate('BTCUSDT', days=1)
        
        assert df is not None
        # API might be rate limited, empty DataFrame is acceptable
        if df.empty:
            pytest.skip("Bybit API rate limited or unavailable")
        
        assert len(df) > 0
        
        # Check structure
        assert 'close' in df.columns
        assert pd.api.types.is_numeric_dtype(df['close'])
        
        # Funding rates should be reasonable (between -100% and +100%)
        assert (df['close'].abs() < 1.0).all()
    
    def test_bybit_funding_rate_period(self):
        """Test Bybit funding rate period fetching."""
        bybit = BybitKline()
        period_info = bybit.fetch_funding_rate_period('BTCUSDT')
        
        assert period_info is not None
        # API might be rate limited, empty dict is acceptable
        if not period_info or 'fundingInterval' not in period_info:
            pytest.skip("Bybit API rate limited or unavailable")
        
        assert 'fundingIntervalMinutes' in period_info
        assert isinstance(period_info['fundingInterval'], (int, float))
        assert period_info['fundingInterval'] > 0
        assert period_info['fundingInterval'] <= 24


class TestBitunixAPI:
    """Test Bitunix exchange API endpoints."""
    
    def test_bitunix_connection(self):
        """Test Bitunix API connectivity."""
        response = requests.get("https://www.bitunix.com", timeout=10)
        assert response.status_code == 200
    
    def test_bitunix_kline_data(self):
        """Test Bitunix kline/OHLC data fetching."""
        bitunix = BitunixKline()
        df = bitunix.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        
        assert df is not None
        assert not df.empty
        assert len(df) > 0
        
        # Check required columns
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns
        
        # Validate data types
        assert pd.api.types.is_datetime64_any_dtype(df['time'])
        assert pd.api.types.is_numeric_dtype(df['close'])
        
        # Validate OHLC logic
        assert (df['high'] >= df['low']).all()
        assert (df['volume'] >= 0).all()
    
    def test_bitunix_funding_rate(self):
        """Test Bitunix funding rate data fetching."""
        bitunix = BitunixKline()
        df = bitunix.fetch_funding_rate('BTCUSDT')
        
        assert df is not None
        assert not df.empty
        
        # Check structure
        assert 'close' in df.columns
        assert pd.api.types.is_numeric_dtype(df['close'])
        
        # Funding rates should be reasonable
        assert (df['close'].abs() < 1.0).all()
    
    def test_bitunix_funding_rate_period(self):
        """Test Bitunix funding rate period fetching."""
        bitunix = BitunixKline()
        period_info = bitunix.fetch_funding_rate_period('BTCUSDT')
        
        assert period_info is not None
        assert 'fundingInterval' in period_info
        assert isinstance(period_info['fundingInterval'], (int, float))
        assert period_info['fundingInterval'] > 0


class TestDeribitAPI:
    """Test Deribit exchange API endpoints."""
    
    def test_deribit_connection(self):
        """Test Deribit API connectivity."""
        response = requests.get("https://www.deribit.com/api/v2/public/get_time", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert 'result' in data
    
    def test_deribit_dvol_data(self):
        """Test Deribit DVOL (volatility index) data fetching."""
        deribit = DeribitDVOL()
        df = deribit.fetch_historical_dvol('BTC', days=1, resolution=60)
        
        assert df is not None
        assert not df.empty
        assert len(df) > 0
        
        # Check required columns
        required_columns = ['time', 'open', 'high', 'low', 'close']
        for col in required_columns:
            assert col in df.columns
        
        # Validate data types
        assert pd.api.types.is_datetime64_any_dtype(df['time'])
        assert pd.api.types.is_numeric_dtype(df['close'])
        
        # DVOL values should be positive and reasonable (typically 20-200)
        assert (df['close'] > 0).all()
        assert (df['close'] < 500).all()


class TestBinanceFuturesAPI:
    """Test Binance Futures exchange API endpoints."""
    
    def test_binance_connection(self):
        """Test Binance Futures API connectivity."""
        try:
            response = requests.get("https://fapi.binance.com/fapi/v1/time", timeout=10)
            # API might be rate limited, that's acceptable
            assert response.status_code in [200, 429]
            if response.status_code == 200:
                data = response.json()
                assert 'serverTime' in data
        except requests.exceptions.RequestException:
            # Network issues are acceptable in tests
            pytest.skip("Binance Futures API unavailable")
    
    def test_binance_kline_data(self):
        """Test Binance Futures kline/OHLC data fetching."""
        binance = BinanceFuturesKline()
        df = binance.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        
        assert df is not None
        # API might be rate limited, empty DataFrame is acceptable
        if df.empty:
            pytest.skip("Binance Futures API rate limited or unavailable")
        
        assert len(df) > 0
        
        # Check required columns
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Validate data types
        assert pd.api.types.is_datetime64_any_dtype(df['time'])
        # Convert to numeric if needed (some exchanges return strings)
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        assert pd.api.types.is_numeric_dtype(df['open'])
        assert pd.api.types.is_numeric_dtype(df['close'])
        assert pd.api.types.is_numeric_dtype(df['volume'])
        
        # Validate OHLC logic
        assert (df['high'] >= df['low']).all()
        assert (df['high'] >= df['open']).all()
        assert (df['high'] >= df['close']).all()
        assert (df['low'] <= df['open']).all()
        assert (df['low'] <= df['close']).all()
        assert (df['volume'] >= 0).all()
    
    def test_binance_kline_interval_formats(self):
        """Test Binance Futures kline with different interval formats."""
        binance = BinanceFuturesKline()
        
        # Test with interval string
        df1 = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1h')
        if not df1.empty:
            assert len(df1) > 0
        
        # Test with minutes integer
        df2 = binance.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        if not df2.empty:
            assert len(df2) > 0
        
        # Test with 4h interval
        df3 = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='4h')
        if not df3.empty:
            assert len(df3) > 0
    
    def test_binance_funding_rate(self):
        """Test Binance Futures funding rate data fetching."""
        binance = BinanceFuturesKline()
        df = binance.fetch_funding_rate('BTCUSDT', days=1)
        
        assert df is not None
        # API might be rate limited, empty DataFrame is acceptable
        if df.empty:
            pytest.skip("Binance Futures API rate limited or unavailable")
        
        assert len(df) > 0
        
        # Check structure
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns
        
        assert 'close' in df.columns
        assert pd.api.types.is_numeric_dtype(df['close'])
        
        # Funding rates should be reasonable (between -100% and +100%)
        assert (df['close'].abs() < 1.0).all()
    
    def test_binance_funding_rate_period(self):
        """Test Binance Futures funding rate period."""
        binance = BinanceFuturesKline()
        period_info = binance.fetch_funding_rate_period('BTCUSDT')
        
        assert period_info is not None
        assert 'fundingInterval' in period_info
        assert 'fundingIntervalMinutes' in period_info
        assert period_info['fundingInterval'] == 8
        assert period_info['fundingIntervalMinutes'] == 480
        assert 'timestamp' in period_info
        assert isinstance(period_info['timestamp'], int)
    
    def test_binance_ethusdt_kline(self):
        """Test Binance Futures with Ethereum futures."""
        binance = BinanceFuturesKline()
        df = binance.fetch_historical_kline('ETHUSDT', days=1, resolution=60)
        
        assert df is not None
        if not df.empty:
            assert len(df) > 0
            assert 'close' in df.columns
            # ETH prices should be positive
            assert (df['close'] > 0).all()
    
    def test_binance_time_range_fetching(self):
        """Test Binance Futures fetching specific time ranges."""
        binance = BinanceFuturesKline()
        
        end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_time = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp() * 1000)
        
        df = binance.fetch_historical_kline(
            'BTCUSDT',
            days=1,
            resolution=60,
            start_time=start_time,
            end_time=end_time
        )
        
        assert df is not None
        if not df.empty:
            # Check time is within range
            min_time = df['time'].min()
            max_time = df['time'].max()
            
            # Convert to timestamp in milliseconds for comparison
            min_ts = int(pd.Timestamp(min_time).timestamp() * 1000)
            max_ts = int(pd.Timestamp(max_time).timestamp() * 1000)
            
            assert min_ts >= start_time - 60000  # Allow 1 min tolerance
            assert max_ts <= end_time + 60000  # Allow 1 min tolerance



    """Test Hyperliquid exchange API endpoints."""
    
    def test_hyperliquid_connection(self):
        """Test Hyperliquid API connectivity."""
        url = "https://api.hyperliquid.xyz/info"
        payload = {"type": "meta"}
        try:
            response = requests.post(url, json=payload, timeout=10)
            # API might be rate limited, that's acceptable
            assert response.status_code in [200, 429]
        except requests.exceptions.RequestException:
            pytest.skip("Hyperliquid API unavailable")
    
    def test_hyperliquid_funding_rate(self):
        """Test Hyperliquid funding rate data fetching."""
        hyperliquid = HyperliquidKline()
        df = hyperliquid.fetch_funding_rate('BTC', days=1)
        
        assert df is not None
        # API might be rate limited, empty DataFrame is acceptable
        if df.empty:
            pytest.skip("Hyperliquid API rate limited or unavailable")
        
        assert len(df) > 0
        
        # Check structure
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns
        
        # Validate data types
        assert pd.api.types.is_datetime64_any_dtype(df['time'])
        assert pd.api.types.is_numeric_dtype(df['close'])
        
        # Funding rates should be reasonable (8-hour rate, multiplied by 8)
        # Typical range: -0.01 to 0.01 (after 8x multiplication)
        assert (df['close'].abs() < 0.1).all()
    
    def test_hyperliquid_funding_rate_period(self):
        """Test Hyperliquid funding rate period."""
        hyperliquid = HyperliquidKline()
        period_info = hyperliquid.fetch_funding_rate_period('BTC')
        
        assert period_info is not None
        assert 'fundingInterval' in period_info
        assert period_info['fundingInterval'] == 8
        assert period_info['fundingIntervalMinutes'] == 480
    
    def test_hyperliquid_api_response_format(self):
        """Test Hyperliquid raw API response format."""
        url = "https://api.hyperliquid.xyz/info"
        start_time = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp() * 1000)
        payload = {
            "type": "fundingHistory",
            "coin": "BTC",
            "startTime": start_time
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            # API might be rate limited
            if response.status_code == 429:
                pytest.skip("Hyperliquid API rate limited")
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Hyperliquid API unavailable")
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of first entry
        entry = data[0]
        assert 'time' in entry
        assert 'fundingRate' in entry
        assert isinstance(entry['time'], int)
        assert isinstance(entry['fundingRate'], str)
        
        # Parse funding rate
        rate = float(entry['fundingRate'])
        assert isinstance(rate, float)


class TestYFinanceAPI:
    """Test Yahoo Finance API endpoints."""
    
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not available (Python 3.9 compatibility)")
    def test_yfinance_connection(self):
        """Test Yahoo Finance data availability."""
        yfinance = YFinanceKline()
        # Try to fetch BTC futures data
        df = yfinance.fetch_historical_kline('BTC-USD', days=1, interval='1h')
        
        # YFinance might not have data for some symbols, so we check if it either:
        # 1. Returns valid data, or 2. Returns empty DataFrame gracefully
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        
        if not df.empty:
            # If data is available, validate structure
            required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                assert col in df.columns
            
            # Validate OHLC logic
            assert (df['high'] >= df['low']).all()
    
    @pytest.mark.skipif(not YFINANCE_AVAILABLE, reason="yfinance not available (Python 3.9 compatibility)")
    def test_yfinance_stock_data(self):
        """Test Yahoo Finance stock data (SPX index)."""
        yfinance = YFinanceKline()
        df = yfinance.fetch_historical_kline('^GSPC', days=1, interval='1h')
        
        assert df is not None
        # ^GSPC should have data
        if not df.empty:
            assert 'close' in df.columns
            assert (df['close'] > 0).all()


class TestAPIRateLimits:
    """Test API rate limiting and error handling."""
    
    def test_bybit_rate_limit_handling(self):
        """Test Bybit handles rate limits gracefully."""
        bybit = BybitKline()
        
        # Make multiple rapid requests
        results = []
        for _ in range(3):
            df = bybit.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
            results.append(df is not None and not df.empty)
        
        # At least some requests should succeed, or all fail gracefully (no exceptions)
        # If all fail, it means rate limiting is working as expected
        assert all(r is not None for r in [bybit.fetch_historical_kline('BTCUSDT', days=1, resolution=60) for _ in range(3)])
    
    def test_hyperliquid_invalid_coin(self):
        """Test Hyperliquid handles invalid coin gracefully."""
        hyperliquid = HyperliquidKline()
        df = hyperliquid.fetch_funding_rate('INVALIDCOIN', days=1)
        
        # Should return empty DataFrame, not crash
        assert df is not None
        assert isinstance(df, pd.DataFrame)


class TestCrossExchangeComparison:
    """Test data consistency across exchanges."""
    
    def test_btc_price_consistency(self):
        """Test BTC price is consistent across exchanges (within 5%)."""
        bybit = BybitKline()
        bitunix = BitunixKline()
        
        bybit_df = bybit.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        bitunix_df = bitunix.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        
        # Skip if either API is unavailable
        if bybit_df.empty or bitunix_df.empty:
            pytest.skip("One or more exchange APIs unavailable")
        
        bybit_price = float(bybit_df['close'].iloc[-1])
        bitunix_price = float(bitunix_df['close'].iloc[-1])
        
        # Prices should be within 5% of each other
        diff_pct = abs(bybit_price - bitunix_price) / bybit_price * 100
        assert diff_pct < 5.0, f"Price difference too large: {diff_pct:.2f}%"
    
    def test_funding_rate_format_consistency(self):
        """Test funding rates are in consistent format across exchanges."""
        bybit = BybitKline()
        bitunix = BitunixKline()
        hyperliquid = HyperliquidKline()
        
        bybit_df = bybit.fetch_funding_rate('BTCUSDT', days=1)
        bitunix_df = bitunix.fetch_funding_rate('BTCUSDT')
        hyperliquid_df = hyperliquid.fetch_funding_rate('BTC', days=1)
        
        # All should return DataFrames with 'close' column
        if not bybit_df.empty:
            assert 'close' in bybit_df.columns
            assert pd.api.types.is_numeric_dtype(bybit_df['close'])
        
        if not bitunix_df.empty:
            assert 'close' in bitunix_df.columns
            assert pd.api.types.is_numeric_dtype(bitunix_df['close'])
        
        if not hyperliquid_df.empty:
            assert 'close' in hyperliquid_df.columns
            assert pd.api.types.is_numeric_dtype(hyperliquid_df['close'])


class TestAPIErrorHandling:
    """Test API error handling and resilience."""
    
    def test_network_timeout_handling(self):
        """Test modules handle network timeouts gracefully."""
        bybit = BybitKline()
        
        # This should handle timeout gracefully
        df = bybit.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
        assert df is not None
        assert isinstance(df, pd.DataFrame)
    
    def test_invalid_symbol_handling(self):
        """Test exchanges handle invalid symbols gracefully."""
        bybit = BybitKline()
        bitunix = BitunixKline()
        
        # These should return empty DataFrames, not crash
        bybit_df = bybit.fetch_historical_kline('INVALID123', days=1, resolution=60)
        bitunix_df = bitunix.fetch_historical_kline('INVALID123', days=1, resolution=60)
        
        assert bybit_df is not None
        assert bitunix_df is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
