"""
Asset configuration parser for data_collector.

Parses the assets.txt file to extract symbols, exchanges, and data types.
Supports flexible format with optional data type specifications.
"""

from typing import Dict, List, Tuple, Set


class AssetConfig:
    """Represents a single asset configuration."""
    
    def __init__(self, symbol: str, exchanges: Dict[str, Set[str]]):
        """
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            exchanges: Dict mapping exchange names to set of data types
                      Example: {"bybit": {"ohlc", "funding_rate"}, "deribit": {"dvol"}}
        """
        self.symbol = symbol
        self.exchanges = exchanges
    
    def get_data_types(self, exchange: str) -> Set[str]:
        """Get data types for specific exchange."""
        return self.exchanges.get(exchange, set())
    
    def has_data_type(self, exchange: str, data_type: str) -> bool:
        """Check if exchange has specific data type."""
        return data_type in self.get_data_types(exchange)
    
    def __repr__(self):
        return f"AssetConfig({self.symbol}, {self.exchanges})"


def parse_asset_line(line: str) -> Tuple[str, Dict[str, Set[str]]] or None:
    """
    Parse a single line from assets.txt file.
    
    Format: SYMBOL EXCHANGE[|DATA_TYPES] [ADDITIONAL_EXCHANGES[|DATA_TYPES]]
    
    Examples:
        - "BTCUSDT bybit+bitunix"
        - "BTCUSDT bybit|both+deribit|dvol"
        - "ETHUSDT bybit|funding_rate+bitunix|both"
        - "BTCUSDT bybit|ohlc+bitunix|funding_rate"
    
    Args:
        line: Raw line from assets.txt
        
    Returns:
        Tuple of (symbol, exchanges_dict) or None if invalid
        exchanges_dict: {"exchange_name": {"data_type1", "data_type2"}}
    """
    line = line.strip()
    
    # Skip empty lines and comments
    if not line or line.startswith("#"):
        return None
    
    parts = line.split()
    if len(parts) < 2:
        return None
    
    symbol = parts[0]
    exchange_specs = parts[1:]
    
    exchanges = {}
    
    # Parse each exchange specification
    for spec in exchange_specs:
        # Split by + to handle multiple exchanges
        for exchange_entry in spec.split("+"):
            if "|" in exchange_entry:
                # Has explicit data types: "bybit|both" or "bitunix|funding_rate"
                exchange_name, data_types_str = exchange_entry.split("|", 1)
                data_types = set(data_types_str.split(","))
            else:
                # No data types specified - use defaults
                exchange_name = exchange_entry
                # Default data types based on exchange
                if exchange_name.lower() == "deribit":
                    data_types = {"dvol"}
                elif exchange_name.lower() == "yfinance":
                    data_types = {"ohlc"}
                else:
                    # Bybit, Bitunix: default to both
                    data_types = {"ohlc", "funding_rate"}
            
            exchanges[exchange_name] = data_types
    
    return symbol, exchanges


def parse_assets_file(filepath: str) -> Dict[str, AssetConfig]:
    """
    Parse entire assets.txt file.
    
    Args:
        filepath: Path to assets.txt file
        
    Returns:
        Dict mapping symbol to AssetConfig
    """
    configs = {}
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                result = parse_asset_line(line)
                if result:
                    symbol, exchanges = result
                    configs[symbol] = AssetConfig(symbol, exchanges)
    except FileNotFoundError:
        print(f"Warning: Assets file not found: {filepath}")
        return {}
    
    return configs


# Example usage and defaults
DEFAULT_DATA_TYPES = {
    "bybit": {"ohlc", "funding_rate"},
    "bitunix": {"ohlc", "funding_rate"},
    "deribit": {"dvol"},
    "yfinance": {"ohlc"},
}


if __name__ == "__main__":
    # Test parsing
    test_lines = [
        "BTCUSDT bybit+deribit+bitunix",
        "ETHUSDT bybit|both+deribit|dvol",
        "BNBUSDT bybit|ohlc+bitunix|funding_rate",
        "LINKUSDT bybit|funding_rate",
        "AAPL yfinance",
    ]
    
    print("Testing asset parser:")
    print("=" * 80)
    
    for line in test_lines:
        result = parse_asset_line(line)
        if result:
            symbol, exchanges = result
            config = AssetConfig(symbol, exchanges)
            print(f"\nLine: {line}")
            print(f"  Symbol: {symbol}")
            print(f"  Exchanges: {exchanges}")
            print(f"  Config: {config}")
        else:
            print(f"\nInvalid line: {line}")
