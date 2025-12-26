# Funding Period Integration - Usage Guide

## Overview

The InfluxDB writer now supports adding funding period information as a **tag** to every `market_data` point, eliminating the need for a separate `funding_rate_period` measurement.

### Benefits
- ✅ Cleaner database schema (single measurement for all market data)
- ✅ Efficient period lookup (in-memory cache, no DB queries per row)
- ✅ Period accessible in queries: `WHERE period='8h'`
- ✅ Backward compatible (old methods still work)

---

## Quick Example

```python
from modules.influx_writer import InfluxDBWriter
import pandas as pd

# Initialize writer
writer = InfluxDBWriter(batch_size=1000)

# Cache funding periods (do this once at startup)
writer.set_funding_period("BTCUSDT", "bybit", "8h")
writer.set_funding_period("ETHUSDT", "bybit", "8h")
writer.set_funding_period("BNBUSDT", "bybit", "4h")

# When writing market data, pass the period
period = writer.get_funding_period("BTCUSDT", "bybit")  # Returns "8h"

df = pd.DataFrame([
    {"time": "2025-12-26T10:00:00Z", "open": 100, "high": 105, "low": 99, "close": 102, "volume": 1000},
])

writer.write_market_data(
    df=df,
    symbol="BTCUSDT",
    exchange="bybit",
    data_type="kline",
    period=period  # Pass the period here
)

writer.flush()
```

### Resulting Line Protocol
```
market_data,symbol=BTCUSDT,exchange=bybit,data_type=kline,period=8h open=100,high=105,low=99,close=102,volume=1000 1703587200000
```

---

## Production Implementation

### Step 1: Load Periods at Startup

```python
from modules.influx_writer import InfluxDBWriter

writer = InfluxDBWriter(batch_size=1000)

# Load funding periods from your reference data
periods_data = {
    ("BTCUSDT", "bybit"): "8h",
    ("ETHUSDT", "bybit"): "8h",
    ("BNBUSDT", "bybit"): "4h",
    ("SOLUSDT", "bybit"): "1h",
    # ... load from your source (API, DB, config file, etc.)
}

# Cache all periods
for (symbol, exchange), period in periods_data.items():
    writer.set_funding_period(symbol, exchange, period)
```

### Step 2: Use Periods When Writing Data

```python
def fetch_and_store_asset(symbol, exchange):
    """Example: Process one asset"""
    
    # Get the cached period
    period = writer.get_funding_period(symbol, exchange)
    
    # Fetch OHLC data
    df = fetch_kline_data(symbol, exchange)
    
    # Write to InfluxDB with period tag
    valid_points = writer.write_market_data(
        df=df,
        symbol=symbol,
        exchange=exchange,
        data_type="kline",
        period=period  # ← Pass period here
    )
    
    return valid_points

# Process all symbols
for symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT"]:
    fetch_and_store_asset(symbol, "bybit")

writer.flush()
```

### Step 3: Query Data with Period Filter

```python
# Query Bitcoin data with 8-hour funding period
query = "SELECT * FROM market_data WHERE symbol='BTCUSDT' AND period='8h'"

# Query all altcoins with 4-hour period
query = "SELECT * FROM market_data WHERE period='4h'"

# Query specific exchange with unknown period (defaults)
query = "SELECT * FROM market_data WHERE exchange='bybit' AND period='unknown'"
```

---

## API Reference

### `set_funding_period(symbol, exchange, period)`
Cache a funding period for a symbol+exchange pair.

```python
writer.set_funding_period("BTCUSDT", "bybit", "8h")
writer.set_funding_period("ETHUSDT", "deribit", "4h")
```

### `get_funding_period(symbol, exchange)`
Retrieve a cached funding period. Returns "unknown" if not found.

```python
period = writer.get_funding_period("BTCUSDT", "bybit")  # Returns "8h"
period = writer.get_funding_period("UNKNOWN", "unknown")  # Returns "unknown"
```

### `write_market_data(..., period="unknown")`
Write market data with period tag.

```python
writer.write_market_data(
    df=ohlc_df,
    symbol="BTCUSDT",
    exchange="bybit",
    data_type="kline",
    period="8h"  # New parameter
)
```

---

## Handling Missing Periods

If a period is not in the cache, it defaults to `"unknown"`:

```python
# If not cached, defaults to "unknown"
writer.write_market_data(
    df=df,
    symbol="UNKNOWN_PAIR",
    exchange="unknown_exchange",
    period="unknown"  # ← Will default to "unknown"
)
```

---

## Migration from Old System

### Old (Separate Table)
```python
# Old way - separate funding_rate_period measurement
writer.write_funding_rate_period("BTCUSDT", "bybit", 8)
```

### New (Tag-Based)
```python
# New way - period as tag on market_data
writer.set_funding_period("BTCUSDT", "bybit", "8h")
writer.write_market_data(..., period="8h")
```

Both methods still work for backward compatibility, but **the new tag-based approach is preferred** for better data organization.

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| `set_funding_period()` | O(1) | In-memory dict insertion |
| `get_funding_period()` | O(1) | In-memory dict lookup |
| Write 1K points with period | Same as before | No database queries |

**Cache miss rate:** 0% after initial load (assuming symbols don't change frequently)

---

## Example: Loading Periods from Bybit API

```python
from modules.exchanges.bybit import BybitKline

writer = InfluxDBWriter(batch_size=1000)
bybit = BybitKline()

# Load funding periods from Bybit for all symbols
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

for symbol in symbols:
    period_info = bybit.fetch_funding_rate_period(symbol)
    if period_info and "fundingInterval" in period_info:
        period_hours = period_info["fundingInterval"]
        period_str = f"{period_hours}h"
        writer.set_funding_period(symbol, "bybit", period_str)
        print(f"Cached: {symbol} = {period_str}")
```

---

## Summary

✅ **Single measurement** - All market data in `market_data` table
✅ **Tags include period** - Each point has `period=8h` etc.
✅ **Cached lookups** - O(1) performance for 1000+ pairs
✅ **Clean queries** - Filter by period: `WHERE period='8h'`
✅ **Backward compatible** - Old methods still work
