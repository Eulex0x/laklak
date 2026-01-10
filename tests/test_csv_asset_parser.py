"""
Test suite for CSV asset parser module.

Tests the csv_asset_parser module with various configurations and edge cases.
"""

import pytest
import tempfile
import os
from modules.csv_asset_parser import AssetConfig, parse_csv_assets


class TestAssetConfig:
    """Tests for AssetConfig class."""
    
    def test_asset_config_creation(self):
        """Test creating an AssetConfig instance."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit", "bitunix"],
            funding_rate_exchanges=["bybit"]
        )
        assert config.symbol == "BTCUSDT"
        assert config.ohlc_exchanges == ["bybit", "bitunix"]
        assert config.funding_rate_exchanges == ["bybit"]
    
    def test_has_ohlc_true(self):
        """Test has_ohlc returns True when exchange in list."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit", "bitunix"],
            funding_rate_exchanges=["bybit"]
        )
        assert config.has_ohlc("bybit") is True
        assert config.has_ohlc("bitunix") is True
    
    def test_has_ohlc_false(self):
        """Test has_ohlc returns False when exchange not in list."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit"],
            funding_rate_exchanges=["bybit"]
        )
        assert config.has_ohlc("bitunix") is False
        assert config.has_ohlc("deribit") is False
    
    def test_has_ohlc_case_insensitive(self):
        """Test has_ohlc is case-insensitive."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit", "bitunix"],
            funding_rate_exchanges=["bybit"]
        )
        assert config.has_ohlc("BYBIT") is True
        assert config.has_ohlc("ByBit") is True
        assert config.has_ohlc("BITUNIX") is True
    
    def test_has_funding_rate_true(self):
        """Test has_funding_rate returns True when exchange in list."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit"],
            funding_rate_exchanges=["bybit", "bitunix"]
        )
        assert config.has_funding_rate("bybit") is True
        assert config.has_funding_rate("bitunix") is True
    
    def test_has_funding_rate_false(self):
        """Test has_funding_rate returns False when exchange not in list."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit"],
            funding_rate_exchanges=["bitunix"]
        )
        assert config.has_funding_rate("bybit") is False
        assert config.has_funding_rate("deribit") is False
    
    def test_has_funding_rate_empty(self):
        """Test has_funding_rate with empty list."""
        config = AssetConfig(
            symbol="BTC-USD",
            ohlc_exchanges=["yfinance"],
            funding_rate_exchanges=[]
        )
        assert config.has_funding_rate("yfinance") is False
    
    def test_asset_config_repr(self):
        """Test string representation of AssetConfig."""
        config = AssetConfig(
            symbol="BTCUSDT",
            ohlc_exchanges=["bybit"],
            funding_rate_exchanges=["bybit"]
        )
        repr_str = repr(config)
        assert "BTCUSDT" in repr_str
        assert "bybit" in repr_str


class TestCSVParsing:
    """Tests for CSV parsing functionality."""
    
    def test_parse_valid_csv(self):
        """Test parsing a valid CSV file."""
        csv_content = """symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+bitunix,bybit
ETHUSDT,bybit,bybit
BTC-USD,yfinance,
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            assert len(configs) == 3
            assert "BTCUSDT" in configs
            assert "ETHUSDT" in configs
            assert "BTC-USD" in configs
        finally:
            os.unlink(filepath)
    
    def test_parse_csv_with_comments(self):
        """Test parsing CSV file with comment lines."""
        csv_content = """# This is a comment
# Another comment
symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+bitunix,bybit
# Middle comment
ETHUSDT,bybit,bybit
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            assert len(configs) == 2
            assert "BTCUSDT" in configs
            assert "ETHUSDT" in configs
        finally:
            os.unlink(filepath)
    
    def test_parse_csv_with_whitespace(self):
        """Test parsing CSV handles whitespace correctly."""
        csv_content = """symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,  bybit + bitunix  ,  bybit
ETHUSDT,bybit,bybit
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            btc = configs["BTCUSDT"]
            # Whitespace should be stripped
            assert "bybit" in btc.ohlc_exchanges
            assert "bitunix" in btc.ohlc_exchanges
        finally:
            os.unlink(filepath)
    
    def test_parse_csv_empty_funding_rate(self):
        """Test parsing CSV with empty funding_rate_exchanges."""
        csv_content = """symbol,ohlc_exchanges,funding_rate_exchanges
BTC-USD,yfinance,
BTCUSDT,bybit+bitunix,bybit
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            btc_usd = configs["BTC-USD"]
            assert btc_usd.funding_rate_exchanges == []
            assert btc_usd.ohlc_exchanges == ["yfinance"]
        finally:
            os.unlink(filepath)
    
    def test_parse_csv_multiple_exchanges(self):
        """Test parsing CSV with multiple exchanges per column."""
        csv_content = """symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+deribit+bitunix,bybit+bitunix
ETHUSDT,bybit+bitunix,bybit+bitunix
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            btc = configs["BTCUSDT"]
            assert len(btc.ohlc_exchanges) == 3
            assert "bybit" in btc.ohlc_exchanges
            assert "deribit" in btc.ohlc_exchanges
            assert "bitunix" in btc.ohlc_exchanges
            assert len(btc.funding_rate_exchanges) == 2
        finally:
            os.unlink(filepath)
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_csv_assets("/nonexistent/path/assets.csv")
    
    def test_parse_real_assets_file(self):
        """Test parsing the actual assets.csv file."""
        if os.path.exists("assets.csv"):
            configs = parse_csv_assets("assets.csv")
            
            # Should have parsed successfully
            assert len(configs) > 0
            
            # Check specific known assets
            assert "BTCUSDT" in configs
            assert "ETHUSDT" in configs
            
            # BTCUSDT should have binance in OHLC
            btc = configs["BTCUSDT"]
            assert btc.has_ohlc("binance")
            # BTCUSDT should have funding rates from multiple exchanges
            assert btc.has_funding_rate("bybit")
            assert btc.has_funding_rate("bitunix")
            assert btc.has_funding_rate("hyperliquid")
            
            # Yahoo Finance assets should have no funding_rate
            if "BTC=F" in configs:
                btc_f = configs["BTC=F"]
                assert btc_f.has_ohlc("yfinance")
                assert not btc_f.has_funding_rate("yfinance")


class TestIntegration:
    """Integration tests for asset parser."""
    
    def test_example_from_spec(self):
        """Test the example from user specification."""
        csv_content = """symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+bitunix,bitunix
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            btc = configs["BTCUSDT"]
            
            # OHLC from both
            assert btc.has_ohlc("bybit")
            assert btc.has_ohlc("bitunix")
            
            # Funding rate only from bitunix
            assert btc.has_funding_rate("bitunix")
            assert not btc.has_funding_rate("bybit")
        finally:
            os.unlink(filepath)
    
    def test_different_configs_per_symbol(self):
        """Test different configurations for different symbols."""
        csv_content = """symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+bitunix,bitunix
ETHUSDT,bybit+bitunix,bybit+bitunix
XLMUSDT,bybit+bitunix,
BTC-USD,yfinance,
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            filepath = f.name
        
        try:
            configs = parse_csv_assets(filepath)
            
            # BTC: OHLC both, funding_rate bitunix only
            btc = configs["BTCUSDT"]
            assert btc.has_funding_rate("bitunix")
            assert not btc.has_funding_rate("bybit")
            
            # ETH: OHLC and funding_rate both
            eth = configs["ETHUSDT"]
            assert eth.has_funding_rate("bybit")
            assert eth.has_funding_rate("bitunix")
            
            # XLM: OHLC only
            xlm = configs["XLMUSDT"]
            assert xlm.has_ohlc("bybit")
            assert not xlm.has_funding_rate("bybit")
            
            # BTC-USD: OHLC only
            btc_usd = configs["BTC-USD"]
            assert btc_usd.has_ohlc("yfinance")
            assert not btc_usd.has_funding_rate("yfinance")
        finally:
            os.unlink(filepath)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
