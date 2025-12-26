# Asset Configuration CSV Format Guide

## Overview

The `assets.csv` file uses a professional CSV format to specify which exchanges to fetch OHLC data and funding rate data from for each trading pair.

## Format

```
symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+bitunix,bitunix
ETHUSDT,bybit+bitunix,bybit+bitunix
BTC-USD,yfinance,
```

### Columns

| Column | Description | Example |
|--------|-------------|---------|
| `symbol` | Trading pair or ticker symbol | `BTCUSDT`, `BTC-USD`, `ETHUSDT` |
| `ohlc_exchanges` | Exchanges to fetch OHLC price data from (separate multiple with `+`) | `bybit+bitunix`, `yfinance` |
| `funding_rate_exchanges` | Exchanges to fetch funding rate data from (separate multiple with `+`) | `bybit`, `bitunix`, leave empty for none |

## Supported Exchanges

- **bybit** - Bybit perpetual futures exchange
- **bitunix** - Bitunix perpetual futures exchange
- **deribit** - Deribit options exchange (OHLC only, special DVOL storage)
- **yfinance** - Yahoo Finance (stock/forex data)

## Use Cases

### Example 1: OHLC from both, funding_rate from one
```
BTCUSDT,bybit+bitunix,bitunix
```
- Fetch OHLC price data from: **bybit** and **bitunix**
- Fetch funding_rate data from: **bitunix only**
- Use case: Compare OHLC prices across exchanges but use single exchange for funding rates

### Example 2: Both data types from both exchanges
```
ETHUSDT,bybit+bitunix,bybit+bitunix
```
- Fetch OHLC price data from: **bybit** and **bitunix**
- Fetch funding_rate data from: **bybit** and **bitunix**
- Use case: Complete data redundancy across both exchanges

### Example 3: OHLC only, no funding rate
```
XLMUSDT,bybit+bitunix,
```
- Fetch OHLC price data from: **bybit** and **bitunix**
- Fetch funding_rate data from: **none** (empty column)
- Use case: Only interested in price data, no funding rates needed

### Example 4: Yahoo Finance (stock/forex)
```
BTC=F,yfinance,
^GSPC,yfinance,
AAPL,yfinance,
```
- Fetch OHLC price data from: **yfinance**
- Fetch funding_rate data from: **none** (stocks/forex don't have funding rates)
- Use case: Stock indices, forex, commodities

### Example 5: Deribit DVOL (special case)
```
BTC,deribit,
ETH,deribit,
```
- Fetch DVOL (volatility) data from: **deribit**
- Stored as: `BTC_DVOL` and `ETH_DVOL` in InfluxDB
- Use case: Deribit volatility indices for derivatives pricing

## Data Collection Behavior

### OHLC Data
- Fetches Open, High, Low, Close price data
- Stored in InfluxDB measurement: `market_data`
- Metric names: `SYMBOL_EXCHANGE` (e.g., `BTCUSDT_BYBIT`)

### Funding Rate Data
- Fetches current and historical funding rates (perpetual futures only)
- Stored in InfluxDB measurement: `market_data` with tag `data_type=funding_rate`
- Perpetual futures exchanges: bybit, bitunix

### DVOL Data (Deribit Volatility)
- Special volatility indices from Deribit
- Available for: BTC and ETH only
- Stored as: `BTC_DVOL`, `ETH_DVOL` in InfluxDB

## Parser Implementation

The `modules/csv_asset_parser.py` module provides:

```python
from modules.csv_asset_parser import parse_csv_assets

# Parse all assets
configs = parse_csv_assets("assets.csv")

# Check if an exchange provides OHLC
btc = configs["BTCUSDT"]
btc.has_ohlc("bybit")          # True
btc.has_ohlc("bitunix")        # True

# Check if an exchange provides funding rate
btc.has_funding_rate("bybit")   # True
btc.has_funding_rate("bitunix") # False (only has OHLC)
```

## Example Asset Configuration

```csv
symbol,ohlc_exchanges,funding_rate_exchanges
BTCUSDT,bybit+deribit+bitunix,bybit+bitunix
ETHUSDT,bybit+deribit+bitunix,bybit+bitunix
XLMUSDT,bybit+bitunix,bybit+bitunix
XRPUSDT,bybit+bitunix,bybit+bitunix
BTC-USD,yfinance,
ETH=F,yfinance,
```

## Integration with data_collector.py

The data collector uses the CSV parser to determine:

1. **Which exchanges to query** for each symbol
2. **Which data types to fetch** per exchange
3. **Whether to fetch OHLC** for each exchange
4. **Whether to fetch funding_rate** for each exchange

Example logic:
```python
configs = parse_csv_assets("assets.csv")

for symbol, config in configs.items():
    # OHLC collection
    for exchange in config.ohlc_exchanges:
        fetch_ohlc(symbol, exchange)
    
    # Funding rate collection
    for exchange in config.funding_rate_exchanges:
        fetch_funding_rate(symbol, exchange)
```

## Maintenance

### Adding New Assets
1. Open `assets.csv`
2. Add a new row with the symbol and exchanges
3. Save and commit

### Removing Assets
1. Delete the row from `assets.csv`
2. Optionally clean up old data from InfluxDB

### Modifying Exchange Configuration
1. Edit the `ohlc_exchanges` or `funding_rate_exchanges` columns
2. Changes take effect on next data collection cycle

## Comments and Structure

The CSV file supports comment lines (lines starting with `#`) for documentation and organization:

```csv
# Crypto assets with multiple sources
BTCUSDT,bybit+deribit+bitunix,bybit+bitunix
ETHUSDT,bybit+deribit+bitunix,bybit+bitunix

# Single exchange assets
BNBUSDT,bybit,bybit

# Yahoo Finance (stocks/forex)
BTC-USD,yfinance,
^GSPC,yfinance,
```

## Performance Considerations

- CSV parsing happens once on startup
- Results cached in memory for O(1) lookups
- No database queries needed to check configuration
- Minimal overhead: ~1-5ms for 244 assets

## Backward Compatibility

The new CSV format is designed to completely replace the old text format:
- Easier to parse programmatically
- Professional industry-standard format
- Supports complex exchange/data-type combinations
- Self-documenting with clear column headers
