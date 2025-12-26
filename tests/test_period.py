"""Tests for funding period functionality."""

import sys
import os
import pandas as pd
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.influx_writer import InfluxDBWriter
from config import SETTINGS


class TestPeriodCache:
    """Test period caching functionality."""
    
    def test_period_cache_initialization(self):
        """Test that period cache is initialized."""
        writer = InfluxDBWriter()
        assert hasattr(writer, 'period_cache')
        assert isinstance(writer.period_cache, dict)
        assert len(writer.period_cache) == 0
    
    def test_set_funding_period(self):
        """Test setting funding periods."""
        writer = InfluxDBWriter()
        
        # Set a period
        writer.set_funding_period("BTCUSDT", "bybit", "8")
        
        # Verify it's in cache
        assert "BTCUSDT:bybit" in writer.period_cache
        assert writer.period_cache["BTCUSDT:bybit"] == "8"
    
    def test_get_funding_period_existing(self):
        """Test retrieving existing funding period."""
        writer = InfluxDBWriter()
        
        writer.set_funding_period("ETHUSDT", "bybit", "4")
        retrieved = writer.get_funding_period("ETHUSDT", "bybit")
        
        assert retrieved == "4"
    
    def test_get_funding_period_missing(self):
        """Test that missing period returns 'unknown'."""
        writer = InfluxDBWriter()
        
        retrieved = writer.get_funding_period("UNKNOWN", "unknown")
        
        assert retrieved == "unknown"
    
    def test_period_format_number_only(self):
        """Test that period is stored as string number only (not with 'h' suffix)."""
        writer = InfluxDBWriter()
        
        # Set period as number string
        writer.set_funding_period("BTCUSDT", "bybit", "8")
        period = writer.get_funding_period("BTCUSDT", "bybit")
        
        # Verify it's a number string without 'h'
        assert period == "8"
        assert "h" not in str(period)
        assert str(period).isdigit()
    
    def test_multiple_symbols_cache(self):
        """Test caching multiple symbols."""
        writer = InfluxDBWriter()
        
        periods = {
            ("BTCUSDT", "bybit"): "8",
            ("ETHUSDT", "bybit"): "4",
            ("BNBUSDT", "bybit"): "8",
        }
        
        for (symbol, exchange), period in periods.items():
            writer.set_funding_period(symbol, exchange, period)
        
        # Verify all cached
        assert len(writer.period_cache) == 3
        
        # Verify retrieval
        for (symbol, exchange), expected_period in periods.items():
            retrieved = writer.get_funding_period(symbol, exchange)
            assert retrieved == expected_period
    
    def test_period_different_exchanges(self):
        """Test that same symbol on different exchanges are cached separately."""
        writer = InfluxDBWriter()
        
        writer.set_funding_period("BTCUSDT", "bybit", "8")
        writer.set_funding_period("BTCUSDT", "bitunix", "8")
        
        # Both should be cached separately
        assert writer.get_funding_period("BTCUSDT", "bybit") == "8"
        assert writer.get_funding_period("BTCUSDT", "bitunix") == "8"
        
        # Verify cache keys are different
        assert "BTCUSDT:bybit" in writer.period_cache
        assert "BTCUSDT:bitunix" in writer.period_cache


class TestPeriodInMarketData:
    """Test that periods are written correctly to market_data."""
    
    def test_period_parameter_in_write_market_data(self):
        """Test that write_market_data accepts period parameter."""
        writer = InfluxDBWriter(batch_size=10)
        
        # Create test data
        df = pd.DataFrame([
            {
                "time": datetime.now(timezone.utc),
                "open": 100,
                "high": 105,
                "low": 99,
                "close": 102,
                "volume": 1000,
            }
        ])
        
        # Set period
        writer.set_funding_period("BTCUSDT", "bybit", "8")
        period = writer.get_funding_period("BTCUSDT", "bybit")
        
        # Write with period
        points = writer.write_market_data(
            df=df,
            symbol="BTCUSDT",
            exchange="bybit",
            data_type="kline",
            period=period
        )
        
        # Should write successfully
        assert points > 0
    
    def test_period_default_value(self):
        """Test that period defaults to 'unknown' when not provided."""
        writer = InfluxDBWriter(batch_size=10)
        
        df = pd.DataFrame([
            {
                "time": datetime.now(timezone.utc),
                "open": 100,
                "high": 105,
                "low": 99,
                "close": 102,
                "volume": 1000,
            }
        ])
        
        # Write without setting period (should default to "unknown")
        points = writer.write_market_data(
            df=df,
            symbol="BTCUSDT",
            exchange="bybit",
            data_type="kline"
            # period not specified - defaults to "unknown"
        )
        
        # Should still write successfully
        assert points > 0
    
    def test_funding_rate_with_period(self):
        """Test writing funding_rate data with period tag."""
        writer = InfluxDBWriter(batch_size=10)
        
        # Create funding_rate data
        now = datetime.now(timezone.utc)
        df = pd.DataFrame([
            {
                "time": now,
                "open": 0.000125,
                "high": 0.000130,
                "low": 0.000120,
                "close": 0.000125,
                "volume": 1,
            },
            {
                "time": now - timedelta(hours=1),
                "open": 0.000120,
                "high": 0.000125,
                "low": 0.000115,
                "close": 0.000120,
                "volume": 1,
            }
        ])
        
        # Set period
        writer.set_funding_period("BTCUSDT", "bybit", "8")
        period = writer.get_funding_period("BTCUSDT", "bybit")
        
        # Write funding_rate with period
        points = writer.write_market_data(
            df=df,
            symbol="BTCUSDT",
            exchange="bybit",
            data_type="funding_rate",
            period=period
        )
        
        # Should write successfully
        assert points == 2


class TestDeprecatedMethods:
    """Test that old methods have been removed."""
    
    def test_write_funding_rate_period_removed(self):
        """Test that write_funding_rate_period method no longer exists."""
        writer = InfluxDBWriter()
        
        assert not hasattr(writer, 'write_funding_rate_period')
    
    def test_funding_rate_period_exists_removed(self):
        """Test that funding_rate_period_exists method no longer exists."""
        writer = InfluxDBWriter()
        
        assert not hasattr(writer, 'funding_rate_period_exists')


if __name__ == "__main__":
    # Run tests
    import pytest
    pytest.main([__file__, "-v"])
