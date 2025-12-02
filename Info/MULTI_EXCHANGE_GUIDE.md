# Market Data Collector - Multi-Exchange Support

## Overview
This project has been restructured to support multiple data providers/exchanges in a unified way. You can now collect data from Bybit, Deribit, and Yahoo Finance, and all data is stored with exchange-specific identifiers for easy querying.

## New Structure

```
market_data/
├── modules/               # Core functionality modules
│   ├── __init__.py
│   ├── influx_writer.py   # InfluxDB writer
│   └── exchanges/         # Exchange/Provider modules
│       ├── __init__.py
│       ├── bybit.py       # Bybit exchange (crypto futures)
│       ├── deribit.py     # Deribit exchange (DVOL/volatility)
│       └── yfinance.py    # Yahoo Finance (stocks, crypto, indices)
├── assets.txt             # NEW: Asset configuration (was coins.txt)
├── data_collector.py      # Main data collector
├── backfill.py            # Historical data backfill
└── config.py
```

## Key Changes

### 1. Exchange Modules (`modules/exchanges/` folder)
All exchange-specific data fetching logic is now in the `modules/exchanges/` folder:
- `bybit.py` - Bybit crypto exchange (BTCUSDT, ETHUSDT, etc.)
- `deribit.py` - Deribit volatility index (DVOL for BTC, ETH)
- `yfinance.py` - Yahoo Finance (BTC-USD, AAPL, ^GSPC, etc.)

### 2. Assets Configuration (`assets.txt`)
The `coins.txt` file has been renamed to `assets.txt` to reflect that it now supports all types of market data (crypto, stocks, indices, etc.).

**Format:**
```
SYMBOL EXCHANGE [ADDITIONAL_EXCHANGES]
```

**Examples:**
```
# Crypto from multiple sources
BTCUSDT bybit+deribit      # Fetch from both Bybit and Deribit
ETHUSDT bybit+deribit      # Fetch from both Bybit and Deribit
SOLUSDT bybit              # Fetch only from Bybit

# Traditional markets via Yahoo Finance
BTC-USD yfinance           # Bitcoin price from Yahoo Finance
AAPL yfinance              # Apple stock
GOOGL yfinance             # Google stock
^GSPC yfinance             # S&P 500 index
^DJI yfinance              # Dow Jones index
```

### 3. Database Symbol Naming Convention
All data is now stored with descriptive identifiers:

**Format for Price Data:** `SYMBOL_EXCHANGE`
**Format for Volatility Data:** `BASECURRENCY_DVOL`

**Examples:**
- `BTCUSDT_BYBIT` - Bitcoin/USDT price from Bybit
- `BTC_DVOL` - Bitcoin implied volatility (DVOL) from Deribit
- `ETH_DVOL` - Ethereum implied volatility (DVOL) from Deribit
- `BTC-USD_YFINANCE` - Bitcoin/USD price from Yahoo Finance
- `AAPL_YFINANCE` - Apple stock price from Yahoo Finance
- `^GSPC_YFINANCE` - S&P 500 index from Yahoo Finance

This makes it easy to:
- Query specific price data: `SELECT * FROM market_data WHERE symbol = 'BTCUSDT_BYBIT'`
- Query volatility data: `SELECT * FROM market_data WHERE symbol = 'BTC_DVOL'`
- Compare BTC price across exchanges: `SELECT * FROM market_data WHERE symbol =~ /^BTC.*_(BYBIT|YFINANCE)$/`
- Filter by exchange: `SELECT * FROM market_data WHERE exchange = 'YFinance'`
- Filter by data type: `SELECT * FROM market_data WHERE data_type = 'dvol'`

## Usage

### Adding New Assets

Edit `assets.txt` and add your desired assets:

```
# For crypto from Bybit
DOGEUSDT bybit

# For Yahoo Finance (stocks/crypto/indices)
TSLA yfinance              # Tesla stock
ETH-USD yfinance           # Ethereum from Yahoo Finance
^VIX yfinance              # VIX volatility index

# For multiple sources
BTCUSDT bybit+deribit      # Get both price and volatility
```

### Running the Collector

```bash
python data_collector.py
```

The collector will:
1. Read all assets from `assets.txt`
2. Fetch data from specified exchanges
3. Store data with exchange-specific symbols (e.g., `BTCUSDT_BYBIT`, `AAPL_YFINANCE`)
4. Log all operations

### Querying Data from InfluxDB

```sql
# Query BTC price from Bybit
SELECT * FROM market_data WHERE symbol = 'BTCUSDT_BYBIT'

# Query BTC implied volatility
SELECT * FROM market_data WHERE symbol = 'BTC_DVOL'

# Query all price data for BTC across exchanges
SELECT * FROM market_data WHERE symbol =~ /^BTC.*_(BYBIT|YFINANCE)$/

# Query all assets from Yahoo Finance
SELECT * FROM market_data WHERE exchange = 'YFinance'

# Query by data type
SELECT * FROM market_data WHERE data_type = 'kline'    # Price data
SELECT * FROM market_data WHERE data_type = 'dvol'     # Volatility data

# Compare BTC price across exchanges
SELECT * FROM market_data 
WHERE (symbol = 'BTCUSDT_BYBIT' OR symbol = 'BTC-USD_YFINANCE')
AND time > now() - 24h

# Get BTC price and volatility together
SELECT * FROM market_data 
WHERE (symbol = 'BTCUSDT_BYBIT' OR symbol = 'BTC_DVOL')
AND time > now() - 24h
```

### Grafana Queries

In Grafana, you can easily create dashboards that:
- Compare prices across exchanges
- Monitor multiple assets from different sources
- Track volatility alongside price

Example query:
```sql
SELECT mean("close") 
FROM "market_data" 
WHERE symbol =~ /^BTCUSDT_/ 
AND $timeFilter 
GROUP BY time($__interval), symbol
```

## Yahoo Finance Symbol Examples

### Cryptocurrencies
- `BTC-USD` - Bitcoin
- `ETH-USD` - Ethereum
- `DOGE-USD` - Dogecoin
- `ADA-USD` - Cardano

### Stocks
- `AAPL` - Apple
- `GOOGL` - Google
- `MSFT` - Microsoft
- `TSLA` - Tesla
- `NVDA` - NVIDIA

### Indices
- `^GSPC` - S&P 500
- `^DJI` - Dow Jones
- `^IXIC` - NASDAQ
- `^VIX` - Volatility Index

### Forex
- `EURUSD=X` - Euro/USD
- `GBPUSD=X` - British Pound/USD

### Commodities
- `GC=F` - Gold Futures
- `CL=F` - Crude Oil Futures

## Migration Notes

If you're upgrading from the old structure:

1. **Rename file:** `coins.txt` → `assets.txt` (or keep both)
2. **Old imports still work:** The old module files are preserved for backward compatibility
3. **Database compatibility:** Existing data remains accessible
4. **New data format:** New data will use the `SYMBOL_EXCHANGE` format

## Supported Exchanges

| Exchange | Type | Symbols | Data Type | Notes |
|----------|------|---------|-----------|-------|
| Bybit | Crypto | BTCUSDT, ETHUSDT, etc. | OHLCV | Futures market |
| Deribit | Crypto | BTC, ETH | DVOL (volatility) | Volatility index only |
| Yahoo Finance | All | BTC-USD, AAPL, ^GSPC, etc. | OHLCV | Stocks, crypto, indices, forex, commodities |

## Configuration

Update your `config.py` if needed:

```python
# Interval formats by exchange:
# Bybit: "1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"
# Deribit: "1", "60", "3600", "43200", "1D"
# Yahoo Finance: "1m", "2m", "5m", "15m", "30m", "60m", "1h", "1d", "5d", "1wk", "1mo"

RESOLUTION_KLINE = "60"  # Will be converted appropriately for each exchange
```

## Benefits

1. **Unified Interface:** All exchanges use the same pattern
2. **Easy Comparison:** Compare BTC price from Bybit vs Yahoo Finance
3. **Flexible Queries:** Use exchange tags to filter and aggregate data
4. **Scalable:** Easy to add new exchanges (just create a new module in `exchanges/`)
5. **Clear Naming:** Database symbols clearly show the source
6. **Mixed Data:** Combine crypto, stocks, and indices in one system

## Troubleshooting

### Import Errors
If you see import errors, make sure the `exchanges/` folder has an `__init__.py` file.

### Yahoo Finance Symbols
Yahoo Finance uses different symbol formats. Check their website for the correct format:
- Stocks: Usually just the ticker (AAPL, MSFT)
- Crypto: Add -USD (BTC-USD, ETH-USD)
- Indices: Start with ^ (^GSPC, ^DJI)
- Forex: Add =X (EURUSD=X)
- Futures: Add =F (GC=F, CL=F)

### Interval Compatibility
Different exchanges support different intervals. The collector automatically converts where possible:
- Bybit "60" → Yahoo Finance "1h"
- Bybit "1D" → Yahoo Finance "1d"

## Future Enhancements

Potential additions to the `exchanges/` folder:
- Binance
- Coinbase
- Kraken
- Interactive Brokers
- Alpha Vantage
- Custom data sources
