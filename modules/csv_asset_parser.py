"""
CSV Asset Parser Module

Parses assets.csv file with the following structure:
    symbol,ohlc_exchanges,funding_rate_exchanges
    BTCUSDT,bybit+bitunix,bitunix
    ETHUSDT,bybit+bitunix,bybit+bitunix

This module provides:
- AssetConfig: Class representing asset configuration
- parse_csv_assets(): Function to parse assets.csv file
"""

import csv
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AssetConfig:
    """Represents a single asset configuration from CSV."""
    
    symbol: str
    ohlc_exchanges: List[str]
    funding_rate_exchanges: List[str]
    
    def has_ohlc(self, exchange: str) -> bool:
        """Check if exchange is configured to fetch OHLC data."""
        return exchange.lower() in [e.lower() for e in self.ohlc_exchanges]
    
    def has_funding_rate(self, exchange: str) -> bool:
        """Check if exchange is configured to fetch funding rate data."""
        return exchange.lower() in [e.lower() for e in self.funding_rate_exchanges]
    
    def __repr__(self) -> str:
        ohlc_str = "+".join(self.ohlc_exchanges) if self.ohlc_exchanges else "none"
        fr_str = "+".join(self.funding_rate_exchanges) if self.funding_rate_exchanges else "none"
        return f"AssetConfig(symbol={self.symbol}, ohlc={ohlc_str}, funding_rate={fr_str})"


def parse_csv_assets(filepath: str) -> Dict[str, AssetConfig]:
    """
    Parse assets.csv file and return dictionary of symbol -> AssetConfig.
    
    Args:
        filepath: Path to assets.csv file
        
    Returns:
        Dictionary mapping symbol to AssetConfig
        
    Example:
        >>> configs = parse_csv_assets("assets.csv")
        >>> btc_config = configs["BTCUSDT"]
        >>> btc_config.has_ohlc("bybit")  # True
        >>> btc_config.has_funding_rate("bitunix")  # True
    """
    configs: Dict[str, AssetConfig] = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Skip comment lines at the beginning
            lines = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)
            
            # Parse CSV from filtered lines
            reader = csv.DictReader(lines)
            
            if reader.fieldnames != ['symbol', 'ohlc_exchanges', 'funding_rate_exchanges']:
                raise ValueError(
                    f"Invalid CSV header. Expected: symbol,ohlc_exchanges,funding_rate_exchanges "
                    f"Got: {','.join(reader.fieldnames) if reader.fieldnames else 'None'}"
                )
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                try:
                    symbol = row['symbol'].strip()
                    
                    # Skip empty lines or comments
                    if not symbol or symbol.startswith('#'):
                        continue
                    
                    # Parse exchanges - split by + and strip whitespace
                    ohlc_raw = row['ohlc_exchanges'].strip()
                    funding_rate_raw = row['funding_rate_exchanges'].strip()
                    
                    ohlc_exchanges = [e.strip() for e in ohlc_raw.split('+') if e.strip()]
                    funding_rate_exchanges = [e.strip() for e in funding_rate_raw.split('+') if e.strip()]
                    
                    config = AssetConfig(
                        symbol=symbol,
                        ohlc_exchanges=ohlc_exchanges,
                        funding_rate_exchanges=funding_rate_exchanges
                    )
                    
                    configs[symbol] = config
                    
                except Exception as e:
                    raise ValueError(f"Error parsing row {row_num}: {row}. {str(e)}")
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Assets CSV file not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error parsing assets.csv: {str(e)}")
    
    return configs


def print_asset_summary(configs: Dict[str, AssetConfig]) -> None:
    """Print summary of all asset configurations."""
    print("\n" + "="*80)
    print("ASSET CONFIGURATION SUMMARY")
    print("="*80)
    
    for symbol, config in sorted(configs.items()):
        ohlc = "+".join(config.ohlc_exchanges) if config.ohlc_exchanges else "NONE"
        funding_rate = "+".join(config.funding_rate_exchanges) if config.funding_rate_exchanges else "NONE"
        print(f"{symbol:12} | OHLC: {ohlc:30} | Funding Rate: {funding_rate}")
    
    print("="*80)
    print(f"Total assets configured: {len(configs)}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Test parsing
    try:
        assets = parse_csv_assets("assets.csv")
        print(f"✓ Successfully parsed {len(assets)} assets from assets.csv\n")
        
        # Show examples
        test_symbols = ["BTCUSDT", "ETHUSDT", "BTC=F"]
        print("Example configurations:")
        for symbol in test_symbols:
            if symbol in assets:
                config = assets[symbol]
                print(f"  {config}")
        
        print_asset_summary(assets)
        
    except Exception as e:
        print(f"✗ Error: {e}")
